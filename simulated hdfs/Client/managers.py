import numpy as np
from basics import SuperBlock,Node,User
from toolkit import *
import threading
import asyncio
import functools
import queue
import time

# 发送消息队列
Send_Queue=queue.Queue(maxsize=100)
# 接收消息队列
Recv_Queue=queue.Queue(maxsize=100)
cluster_config={
    'Name':'DataNode_1',
    'NameNode':('127.0.0.1',8888),
    'SelfNode':('127.0.0.1',9120)
}
def maintain_client():
    loop=asyncio.new_event_loop()
    # 用于传递心跳包
    async def echo():
        while True:
            await asyncio.sleep(20)
            try:
                reader,writer =await asyncio.open_connection(*cluster_config['NameNode'])
            except Exception:
                continue
            message={
                'Type':'heart_jump',
                'Name':cluster_config['Name']
            }
            print('send',message)
            writer.write(bytes('{}'.format(message),encoding='utf-8'))
            await writer.drain()
            writer.close()
    loop.create_task(echo())

    #用于切分大文件的函数
    async def handle_schedule(reader,writer):
        data = await reader.read(1000)
        command=data.decode()
        addr = writer.get_extra_info('peername')
        print('Received:',eval(command))
        Recv_Queue.put(eval(command))
        pass   
    loop.create_task(asyncio.start_server(handle_schedule,*cluster_config['SelfNode']))
 
    async def resend():
        while True:
            if Send_Queue.empty():
                await asyncio.sleep(0.2)
                continue
            while not Send_Queue.empty():
                reader,writer = reader,writer =await asyncio.open_connection(*cluster_config['NameNode'])
                message=Send_Queue.get()
                print('resend:',message)
                try:
                    writer.write(bytes('{}'.format(message),encoding='utf-8'))
                except Exception:
                    print('write fail')
                await writer.drain()
                writer.close()
    loop.create_task(resend())

    loop.run_forever()



class FileSystem(object):
    def __init__(self):
        self.super_block=SuperBlock(block_num=12000)
        self.file_manager=FileManager(self.super_block)
        self.user_manager=UserManager()
        self.parameter=[None,None]
        self.operation=None
        self.basic_info={
            'sys_name':'GreilFS'
        }

        self.result=""
        self.current_path="root\\"
        
        # 通讯线程
        self.network_thread = None

        print('*************************************************************')
        print('******            This is GreilFS DataNode             ******')
        print('******                      V1.0                       ******')
        print('*************************************************************')

    def parse_command(self,inputs):
        boxes=inputs.split()
        if len(boxes)==0:
            return True
        operation = boxes[0]
        if operation =='exit':
            return False
        elif operation=='clear':
            print('\n'*20)
            return True
        elif operation=='help':
            print("[mkdir]:Create a new directory\n[ls]:List all the file\n[more]:Check the details\n[vi]:Create a new file")
            print("[cd]:Go to a diretory\n[rm]:Delete a file or directory\n[find]:Search the subfile in the current directory")
            print("[exit]:Exit and save")
            return True
        elif operation in("mkdir","ls","vi","more","cd",'rm','find'):
            if len(boxes)==3:
                self.operation=boxes[0]
                self.parameter[0]=boxes[1]
                self.parameter[1]=boxes[2]
            elif len(boxes)==2:
                self.operation=boxes[0]
                self.parameter[0] = boxes[1]
            elif len(boxes)==1:
                self.operation=boxes[0]
            return True
        else:
            print('-bash:',operation,':command not found')
            return True       
    
    def recv_input(self):
        cflag=True
        while cflag == True:
            inputs = input(self.basic_info['sys_name']+self.current_path+":")
            if self.parse_command(inputs):
                self.answer()
                self.operation,self.parameter=None,[None,None]
            else:
                cflag=False

    def keep_network_open(self,netloop):
        asyncio.set_event_loop(netloop)
        asyncio.ensure_future(maintain_client())
        netloop.run_forever()
        
    def start(self):
        #异步网络接收通讯
        self.network_thread = threading.Thread(target=maintain_client)
        self.network_thread.start()
        #后台任务执行线程
        self.backend_thread = threading.Thread(target=self.keep_answering)
        self.backend_thread.start()
        #同步网络接收输入
        self.recv_input()
    
    def keep_answering(self):
        while True:
            if Recv_Queue.empty():
                time.sleep(0.5)
                continue
            while not Recv_Queue.empty():
                command=Recv_Queue.get()
                if command['Type'] == 'Save':
                    content,block_index=command['Content'],command['Block']
                    self.handle_vi(content,block_index)
                elif command['Type'] == 'Load':
                    position,block_index,max_pos=command['Position'],command['Block'],command['Max_Pos']
                    self.handle_more(position,block_index,max_pos)
                elif command['Type'] == 'Rebuild':
                    # 获得要返回的block_index
                    reget_block,resave_block,repost_addr=command['Reget_Block'],command['Resave_Block'],command['Repost']
                    self.handle_rebuild(reget_block,resave_block,repost_addr)

    
    def answer(self):
        if self.operation=="mkdir":
            self.mkdir()
        elif self.operation=="ls":
            self.ls()
            print(self.result)
        elif self.operation=="vi":
            self.vi()
            print(self.result)
        elif self.operation=="more":
            self.more()
            print(self.result)
        elif self.operation=="cd":
            self.cd()
        elif self.operation=="rm":
            self.rm()
        elif self.operation=="find":
            self.find()
            print("search result:\n",self.result)

    def roll_back(self):
        anchor=2
        while self.current_path[-anchor]!='\\':
            anchor=anchor+1
        self.current_path=self.current_path[:-anchor+1]
        print(self.current_path)

    def mkdir(self):
        location_index=self.user_manager.get_current_dir_index()
        try:
            #要创建的文件夹名字
            name=self.parameter[0]
        except IndexError:
            self.result="command error"
            return

        #当前的位置索引和上一级inode索引
        data={
            '.':name,
            '..':location_index
        }

        index=self.file_manager.save(data=data,sign="dir")
        #print("New directory file name: ",name," node index: ",index)
        #更新目录信息，把原来的删除，存一个新的
        #print("Current Dir node index ", location_index)
        index=self.file_manager.update_dir_file(location_index,{name:index})
        #print("Current Dir is saved in inode index ",index)
        #更新当前目录
        self.user_manager.set_current_dir_index(index)
        self.result="mkdir succeed"

    def ls(self):
        location_index=self.user_manager.get_current_dir_index()
        dir_data=self.file_manager.load(location_index,'dir')

        dir_data.pop('.')
        dir_data.pop('..')

        result = ""
        if not dir_data:
            print("None")
        else:
            for key in dir_data:
                result=result+key+"\n"

        self.result=result

    def handle_vi(self,content,block_index):
        self.file_manager.block_manager.handle_save(content,block_index)

    def vi(self):
        file_name=self.parameter[0]
        try:
            stopword = ":q"  # 输入停止符
            content = ""
            #print("stopword",stopword )
            for line in iter(input, stopword):  # 输入为空行，表示输入结束
                content += line + '\n'
        except IndexError:
            self.result = 'Command error!'
            return

        index=self.file_manager.save(content,sign='txt')
        loc_index=self.user_manager.get_current_dir_index()
        self.file_manager.update_dir_file(loc_index, {file_name: index})
        self.result="Create successfully"

    def handle_more(self,position,block_index,max_pos):
        data = self.file_manager.block_manager.read_data(block_index)
        print('data:',data)
        command={
            'Type':'Display',
            'Content':transform(data,to_type='text'),
            'Position':position,
            'Max_Pos':max_pos
        }
        Send_Queue.put(command)

    def handle_rebuild(self,reget_block,resave_block,repost_addr):
        data = self.file_manager.block_manager.read_data(reget_block)
        # 取出要获得的数据
        command={
            'Type':'Rebuild',
            'Content':transform(data,to_type='text'),
            'Block':reget_block,
            'Repost':repost_addr
        }
        Send_Queue.put(command)

    def more(self):
        location_index=self.user_manager.get_current_dir_index()
        dir_data=self.file_manager.load(location_index=location_index,data_type='dir')
        try:
            file_name=self.parameter[0]
            index=dir_data[file_name]
        except KeyError:
            print("Can not find the file!")
            return

        data=self.file_manager.load(location_index=index,data_type='text')
        self.result=data

    def cd(self):
        if self.parameter[0]=='.':
            return
        elif self.parameter[0]=="..":
            self.roll_back()
        else:
            self.current_path=self.current_path+self.parameter[0]+"\\"
        location_index=self.user_manager.get_current_dir_index()
        dir_data=self.file_manager.load(location_index=location_index,data_type='dir')
        try:
            directory_name=self.parameter[0]
            index=dir_data[directory_name]
        except KeyError:
            print("Not a directory!")
            return

        next_location_index=index
        self.user_manager.set_current_dir_index(next_location_index)
        next_dir_data=self.file_manager.load(location_index=next_location_index,data_type='dir')
        self.result=next_dir_data
        #print("cd: ",self.result)

    def rm(self):
        location_index = self.user_manager.get_current_dir_index()
        dir_data=self.file_manager.load(location_index,'dir')
        #找到这一项
        try:
            target=self.parameter[0]
            target_index = dir_data[target]
        except KeyError:
            print("The file or directory doesn't exist")
            return

        self.rm_subfile(target_index)
        self.file_manager.update_dir_file(location_index, {target: target_index}, 'del')
        #print(self.file_manager.node_manager.map)

    def rm_subfile(self,target_index):
        node=self.file_manager.node_manager.get_node(target_index)
        #print("target: ", target_index, "node_sign: ", node.sign)
        if node.sign=='txt':
            self.file_manager.delete(target_index)
        elif node.sign=='dir':
            target_dir_data=self.file_manager.load(target_index,'dir')
            for key,value in target_dir_data.items():
                if key!='.' and key!='..':
                    scan_node=self.file_manager.node_manager.get_node(value)
                    if scan_node.sign=='txt':
                        self.file_manager.delete(value)
                    elif scan_node.sign=='dir':
                        self.rm_subfile(value)
            self.file_manager.delete(target_index)

    def find(self):
        location_index=self.user_manager.get_current_dir_index()
        current_dir_data=self.file_manager.load(location_index=location_index,data_type='dir')
        name_list=self.file_manager.subfile(location_index,current_dir_data['.'])

        try:
            file_name=self.parameter[0]
        except IndexError:
            self.result='Command Error!'
            return

        find_list=list(
            filter(lambda x:file_name in x.split('\\').pop(),name_list)
        )
        result=""
        if find_list:
            for i in find_list:
                result=result+i
                result=result+'\n'
            result=result+'\n'
        else:
            result='Not found'

        self.result=result



class FileManager(object):
    def __init__(self,super_block):
        self.node_manager=NodeManager(super_block.bit,super_block.node_num)
        self.block_manager=BlockManager(
            super_block.bit,super_block.data_block_size,super_block.data_block_num)

        root_dir={
            '.':'root',
            '..':0
        }
        root_index=self.save(data=root_dir,sign='dir')
        # print("Root dir node index is ",root_index)
        # print("File Manager initialized.")
        pass

    def save(self,data,sign):
        data=transform(data)
        #记录字节流的长度
        size=len(data)
        #在数据区存入数据
        block_indexs=self.block_manager.save(data)
        # print('Data has been saved in blocks: ',block_indexs)
        #在i节点写入文件
        return self.node_manager.save(block_indexs,size,sign)

    def update_dir_file(self,location_index,new_dict,flag='add'):
        #读取原来的目录文件信息
        dir_data=self.load(location_index,'dir')
        # print("Dir ",dir_data)
        if flag=='del':
            keys=new_dict.keys()
            for key in keys:
                del dir_data[key]
        else:
            dir_data.update(new_dict)

        # print('Dir Updated:',dir_data)
        #删除了原来的目录节点
        self.delete(location_index)
        #把更新的目录信息在另一个节点存入
        index=self.save(dir_data,'dir')
        return index

    def load(self,location_index,data_type):
        node=self.node_manager.get_node(location_index)
        block_indexs=node.get_block_indexs()
        # print("block indexs ",block_indexs)
        data=self.block_manager.read_data(block_indexs)
        data=transform(data,data_type)
        return data

    def delete(self,node_index):
        # print('Delete node index',node_index)
        blocks_indexs=self.node_manager.get_block_indexs(node_index)
        # print('Delete block index',blocks_indexs)
        self.block_manager.wipe(blocks_indexs)
        self.node_manager.wipe(node_index)

    def subfile(self,index,dir_name):
        # print("dir_name",dir_name)
        file_list=[]
        dir_data=self.load(index,'dir')

        for key,value in dir_data.items():
            file_list.append(key)
            if key!='.' and key!='..':
                node=self.node_manager.get_node(value)
                if node.sign=='dir':
                    file_list.extend(self.subfile(value,key))

        file_list=[dir_name+'\\' + base_name for base_name in file_list ]
        return file_list



class NodeManager():
    def __init__(self,bit,num):
        self.map=np.zeros((bit,int(num/bit)))
        self.nodes=[]
        for i in range(num):
            node=Node()
            self.nodes.append(node)
        # print("Node Manager initialized")
        pass

    def save(self,block_indexs,size,sign):
        index=self.allocate_nodes()
        node=self.get_node(index)
        node.set_file_size(size)
        node.set_block_indexs(block_indexs)
        node.set_sign(sign)

        return index

    def allocate_nodes(self):
        node_index=np.where(self.map==0)
        #该i节点被使用
        node_index_x=node_index[0][0]
        node_index_y=node_index[1][0]
        self.map[node_index_x][node_index_y]=1
        one_node_index=xy_to_index(self.map.shape[1],node_index_x,node_index_y)
        #返回分配的i-node节点索引
        return one_node_index

    #擦除某一节点
    def wipe(self,index):
        # print("node ",index, "wiping...")
        target=self.get_node(index)
        target=Node()
        x,y=index_to_xy(self.map.shape[0],self.map.shape[1],index)
        self.map[x][y]=0



    #返回指定下标的索引节点
    def get_node(self,index):
        return self.nodes[index]

    def get_block_indexs(self,index):
        indexs=self.nodes[index].get_block_indexs()
        return indexs


class BlockManager():
    def __init__(self,bit,size,num):
        self.block_size=size
        self.map=np.zeros((bit,int(num/bit)))
        #self.blocks 是存储数据的实体
        self.blocks=[b'']*num
        # print("Block Manager initialized")
        pass

    def handle_save(self,content,block_index):
        #content = transform(content)
        self.write_data(content,block_index)
    
    def save(self,data):
        # print("type of data ",type(data))
        size=len(data)
        #分配内存块
        indexs=self.allocate_blocks(size)
        #对要分配的内存块写入数据
        self.write_data(data,indexs)
        return indexs

    def allocate_blocks(self,size):
        allocated_block_num=int(size/self.block_size)+1
        block_indexs=[]
        data_block_index=np.where(self.map==0)

        for i in range(allocated_block_num):
            block_index_x=data_block_index[0][i]
            block_index_y=data_block_index[1][i]
            data_block_index_clean=xy_to_index(self.map.shape[1],block_index_x,block_index_y)
            block_indexs.append(data_block_index_clean)
            #加入索引中，修改位图状态
            self.map[block_index_x][block_index_y]=1
        #block_indexs中存储了一个文件所有使用的block号
        return block_indexs

    def wipe(self,indexs):
        assert(type(indexs)==list)
        self.wipe_data(content=b'',indexs=indexs)

        for index in indexs:
            x,y=index_to_xy(self.map.shape[0],self.map.shape[1],index)
            self.map[x][y]=0

    def wipe_data(self,content,indexs):
        for i in range(len(indexs)):
            self.blocks[indexs[i]]=content[i*self.block_size:(i+1)*self.block_size]

    def write_data(self,data,indexs):
        if type(indexs)==list:
            for i in range(len(indexs)):
                self.blocks[indexs[i]]=data[i*self.block_size:(i+1)*self.block_size]
        else:
            self.blocks[indexs] = data
        print('Check distributed write:',indexs,data)

    def read_data(self,indexs):
        file_data=[]
        byte_data=b''
        if type(indexs)==list:
            #逐块加载block内容
            for index in indexs:
                file_data.append(self.blocks[index])
            for file_data_block in file_data:
                byte_data=byte_data+file_data_block
        elif type(indexs)==int:
            print('read_data_blocks:',self.blocks[indexs])
            byte_data = byte_data + self.blocks[indexs]
        return byte_data



class UserManager(object):
    def __init__(self):
        self.user=None
        self.register()

    def register(self):
        self.user=User()

    def get_current_dir_index(self):
        return self.user.dir_index

    def set_current_dir_index(self,new_index):
        self.user.dir_index=new_index