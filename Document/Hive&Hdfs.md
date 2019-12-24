# <center>Hive and HDFS</center>

​																																										

>1651718	方沛
>
>1751659	周宇东
>
>1753356	李哲

这份文档描述了我们项目实现的功能和实现逻辑。

文档中的代码只占全部的很少一部分，详情可见：[项目地址](https://github.com/Greilfang/hive-hdfs-practise)

**目录：**

[TOC]

## 一. 模拟HDFS的GreilFS

### **1.1 项目介绍**

模拟了HDFS的部分功能,操作方式类似Linux下的命令行。

**支持命令：**

1. **mkdir：**创建一个文件目录

2. **ls**：     列出当前目录下所有文件

3. **vi**：     写入一个文件，回车按:q保存退出（只支持可转为bytes的文件）

4. **more**:查看当前目录下指定文件的内容

5. **cd：**  进去或退出目录

6. **exit:**   退出

### 1.2 实现功能

1. NameNode管理命名空间, DataNode 管理数据存储

   > 由NameNode负责管理所有文件的路径信息，而DataNode存储所有数据块，DataNode自行决定数据块的存放位置
   >

2. 文件的分布式存放

   > NameNode为每一个要保存的文件创建3个副本；当一个文件大于一个数据块的大小时，NameNode 将自动将文件分块，并保证所有的DataNode分别存放一部分数据块。

3. 文件的分布式读取

   > NameNode只保存文件夹信息的数据块, 没有保存文件内容的数据块,当用户读取的时候,将通过文件夹信息找到该数据块所在DataNode及具体位置,并将其范围，同时保证返回的不同数据块能保持写入时的顺序。

4. 心跳机制

   > 和HDFS一样，GreilFS执行间隔为3秒的心跳策略，NameNode对DataNode的存活状态进行检测，NameNode不会对已经标识为`Dead` 的节点发起任何读写请求。而只要DataNode≥1，整个集群仍保持可用。

5. 冗余策略

   > 只要DataNode≥1， 无论多少及哪个DataNode 故障，对同一数据， 集群始终能保持有3份副本。 
   >

6. 节点一致性

   > 代码中保存了所有DataNode和NameNode的接口, 即任何一个节点可以即成为DataNode又成为NameNode。

### 1.3 实现细节

#### 1.3.1 类设计

对每一个节点的文件系统，只要采用的是类`ufs`的文件系统，即文件系统分为四个操作类。

+ **UserManager**

  用于保存并管理用户权限的类。

+ **FileManager**

  + **NodeManager**：用于管理node信息，即文件目录信息。
  + **BlockManager：**用于管理数据块内容的存取，即文件内容的管理。
  
+ **SuperBlock**

  超级块，保存了文件系统的基础配置信息，包括支持文件总大小，多少个文件，几级目录等。

  

**类图:**

![](C:\Users\t470p\Desktop\云计算文档\image\类图.png)

#### 1.3.2 交互

该分布式文件系统采用多线程+协程的异步实现,执行操作遵循统一的`command`主要分为3个线程:

+ **用户输入线程**:

  专门用于用户输入命令的线程。

+ **任务调度线程**：

  + 心跳协程：用于检测DataNode存活状态。

  + 消息协程：用于NameNode向DataNode的数据块存取命令和DataNode对NameNode的数据回送。
  
+ **后台线程**：

  执行任务调度线程收到的命令。
  
  
  

**任务队列所有命令:**

DataNode可发布的命令

```Python
# DataNode 失效命令
# @ Type:任务类型
# @ Target:失效节点编号
command = {
    'Type':'Replic',
    'Target':k
}

# 要求DataNode 储存数据块
# @ Type:任务类型
# @ Target: 要发送的DataNode
# @ Content: 储存内容
# @ Block: 要储存的Block编号
command={
    'Type':'Save',
    'Target':target,
    'Content':transform(content),
    'Block':block
}

# 要求DataNode 回送副本执行冗余策略
# @ Type:任务类型
# @ Target: 副本所在DataNode
# @ Reget_Block: 副本所在Block
# @ Resave: 转存DataNode分配的Block位置
# @ Repost: 转存DataNode的ip地址
command={
    'Type':'Rebuild',
    'Target':cluster_config[k]['addr'],
    'Reget_Block':resilance[k][0],
    'Resave_Block':block_index,
    'Repost':cluster_config[belonger]['addr']
}

# 要求DataNode 读取数据块
# @ Type:任务类型
# @ Target: 发送目标
# @ Position: 要读取的数据是整个文件第几块
# @ Max_Pos: 该文件一共有几块数据
# @ Block: 分配给DataNode保存数据的Block编号
command={
    'Type':'Load',
    'Target':self.cluster_config[node_name]['addr'],
    'Position':i,
    'Max_Pos':len(block_indexs),
    'Block':block_index['clean']
}
```

  DataNode可发布的命令

```Python
# 回送 NameNode要求读取的命令
# @ Type: 任务类型
# @ Content: 回送内容 
# @ Position: 要读取的数据是整个文件第几块
# @ Max_Pos: 该文件一共有几块数据
command={
    'Type':'Display',
    'Content':transform(data,to_type='text'),
    'Position':position,
    'Max_Pos':max_pos
}

# 去除NameNode要求重建的副本数据
# 回送 NameNode要求读取的命令
# @ Type: 任务类型
# @ Content: 回送内容 
# @ Block: 要得到该副本的另一个DataNode
# @ Repost: 要得到该副本的另一个DataNode被分配的Block
command={
    'Type':'Rebuild',
    'Content':transform(data,to_type='text'),
    'Block':reget_block,
    'Repost':repost_addr
}
# 心跳包
# @ Type: 任务类型
# @ Name: NameNode节点 
message={
    'Type':'heart_jump',
    'Name':cluster_config['Name']
}
```

![](C:\Users\t470p\Desktop\云计算文档\image\交互.png)



#### 1.3.3 实现细节（与实现功能一一对应）

1. NameNode管理命名空间, DataNode 管理数据存储

> NameNode 同时拥有BlockMangager和NodeManager的操作权限， DataNode被剥夺NodeManager的操作权限，只能够被动根据任务队列的信息执行。



2. 分布式存放:

> 用户输入 `vi` 执行写入操作，`:q`保存文件信息, NameNode按字节统计文件长度，计算需要的数据块个数， 查找每个DataNode 有多少空闲数据块，将数据块的保存任务均匀分配到每个DataNode，为每一个数据块的保存编写命令等待发送。

以 vi （写入文件）为例

```Python
# Server.py
    def vi(self):
        # 接收输入并转化成bit流
        file_name=self.parameter[0]
        try:
            stopword = ":q"  # 输入停止符
            content = ""
            for line in iter(input, stopword):  # 输入为空行，表示输入结束
                content += line + '\n'
        except IndexError:
            self.result = 'Command error!'
            return
        content = transform(content)
        filesize = len(content)
        # 为文件安排储存位置信息的node节点 和 数据信息的block节点
        replic_nodes,replic_blocks=self.file_manager.schedule_save(filesize,sign='txt',replic=3)
        # 更新当前目录的node 信息 ,加入新文件的node位置
        loc_index=self.user_manager.get_current_dir_index()
        self.file_manager.update_dir_file(loc_index, {file_name: replic_nodes})
        
        # 为每一个数据块分配具体要保存的内容
        bc=self.file_manager.block_manager.block_size
        content_part_num=len(replic_blocks[0])
        # 逐数据块建立副本
        for i in range(content_part_num):
            resilance={'node':replic_nodes}
            for blocks in replic_blocks:
                #print('block:',blocks[i])
                node_name,client_block_index=blocks[i]['name'],blocks[i]['clean']
                # 编写指令
                command={
                    # 类型: 保存
                    'Type':'Save',
                    # 目标DataNode
                    'Target':self.cluster_config[node_name]['addr'],
                    # 要保存的内容
                    'Content':content[bc*i:bc*(i+1)],
                    # 要保存的数据块
                    'Block':client_block_index
                }
                # 记录副本的node节点信息
                if node_name in resilance:
                    resilance[node_name].append(client_block_index)
                else:
                    resilance[node_name]=[client_block_index]
                 # 投放保存任务
                Send_Queue.put(command)
            # 保副本位置信息
            self.file_manager.block_manager.resilance_map.append(resilance)
        self.result='Save Successfully'
```




3.  分布式读取

> 用户输入 `more+[file_name]` 执行查看文件操作， NameNode从当前目录查找出保存文件位置的node信息，node信息中找到目标文件的block信息存在哪个DataNode上，从将数据块的读取任务发送到DataNode，为每一个数据块的读取编写命令等待发送。

以 more (查看文件信息) 为例:

```Python
# NameNode.py
   def more(self):
        location_index=self.user_manager.get_current_dir_index()
        # 取出当前目录,目录信息保存在NameNode的block里
        assert(type(dir_data)==dict)
        dir_data=self.file_manager.load(location_index=location_index,data_type='dir')
        try:
            # 根据传入的参数确定文件名file_name,尝试按该名字读取该目录
            file_name=self.parameter[0]
            # indexs 保存了数据的元信息的node位置
            indexs=dir_data[file_name]
        except KeyError:
            # 若不存在文件名, 返回错误信息
            print("No such file")
            return
        # 从node中查找到数据块所在DataNode 和具体block位置
        node_index=indexs[0]
        block_indexs=self.file_manager.schedule_load(location_index=node_index)
        # 创建任务
        for i,block_index in enumerate(block_indexs):
            node_name=block_index['name']
            command={
                	# 任务类别
                    'Type':'Load',
                	# 具体的DataNode
                    'Target':self.cluster_config[node_name]['addr'],
                	# 该数据块是该文件按顺序的第几块
                    'Position':i,
                	# 该文件一共有几块
                    'Max_Pos':len(block_indexs),
                	# DataNode 要读取的数据块号
                    'Block':block_index['clean']
            }
            # 投放任务
            Send_Queue.put(command)
```

```Python
# DataNode.py
# 此时已经收到类型为 `load` 的命令 
def handle_more(self,position,block_index,max_pos):
    # 可以看到执行逻辑中没有node_manager的参与
    # 读取数据块
    data = self.file_manager.block_manager.read_data(block_index)
    print('data:',data)
    # 编写内容回送命令
    command={
        'Type':'Display',
        'Content':transform(data,to_type='text'),
        'Position':position,
        'Max_Pos':max_pos
    }
    # 投放回送队列
    Send_Queue.put(command)
```



4. 心跳机制

   > 在任务调度线程的心跳协程中实现，使用了`Python`的`Asynico` 异步通信模块, 继承其中的 `Protocal` 基类自定义了一套通信协议,以下是协议中部分代码。

心跳代码实现：

```Python
# NameNode.py
def start(self):
        #异步网络接收通讯
        self.network_thread = threading.Thread(target=maintain_server)
        self.network_thread.start()
        #后台程序执行进程
        self.backend_thread=threading.Thread(target=self.keep_answering)
        self.backend_thread.start()
        #同步网络接收输入
        self.recv_input()
# 主任务循环执行函数
def maintain_server():
    loop=asyncio.new_event_loop()
    async def handle_echo_resend(reader,writer):
        # 非阻塞读取DataNode指令
        data = await reader.read(1000)
        message=data.decode()
        message = eval(message)
        # DataNode 发送的其他指令
        if message['Type'] == 'Display':
            Recv_Queue.put(message)
           # 心跳包
        elif message['Type'] == 'heart_jump':
            # 计算当前
            present_time=now()
            # 能收到心跳说明自己没有挂掉, 先更新自己状态
            cluster_config['NameNode']['last_echo']=present_time
            # 更新发送者的状态
            name=message['Name']
            cluster_config[name]['last_echo']=present_time
            cluster_config[name]['status']='Alive'
            # 检测所有节点存活状态
            for k,v in cluster_config.items():
                #跳过集群里挂掉的的DataNode
                if v['status']=='Dead':continue
                # 每个DataNode 应 3s 发送一次心跳, 4.5s未收到说明该节点已经挂掉
                if present_time - v['last_echo']>4.5:
                    print(k,'is dead')
                    v['status']='Dead'
                    #准备执行冗余策略
                    message={
                        'Type':'Replic',
                        'Target':k
                    }
                    Recv_Queue.put(message)
        # 其他指令
        elif message['Type']=='Rebuild':
            Recv_Queue.put(message)

    loop.create_task(asyncio.start_server(handle_echo_resend,*cluster_config['NameNode']['addr']))
    # 发送调度信息
    async def schedule():
        while True:
            # 持续读取用户请求
            # 若无请求
            if Send_Queue.empty():
                await asyncio.sleep(0.2)
                continue
            # 有请求
            else:
                message=Send_Queue.get()
                try:
                    reader,writer = await asyncio.open_connection(*(message['Target']))
                except Exception:
                    print('Address Error')
                writer.write(bytes('{}'.format(message),encoding='utf-8'))
                await writer.drain()
                
    loop.create_task(schedule())
    # 除了 KeyInterrupt 否则保持运行
    loop.run_forever()
```

```Python
# DataNode.py
def start(self):
    #异步网络接收通讯
    self.network_thread = threading.Thread(target=maintain_client)
    self.network_thread.start()
    #后台任务执行线程
    self.backend_thread = threading.Thread(target=self.keep_answering)
    self.backend_thread.start()
    #同步网络接收输入
    self.recv_input()
# 主任务循环
def maintain_client():
    loop=asyncio.new_event_loop()
    # 用于发送心跳包
    async def echo():
        while True:
            await asyncio.sleep(3)
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

    #用于接收来自NameNode的调度曼联
    async def handle_schedule(reader,writer):
        data = await reader.read(1000)
        command=data.decode()
        addr = writer.get_extra_info('peername')
        print('Received:',eval(command))
        Recv_Queue.put(eval(command))
    loop.create_task(asyncio.start_server(handle_schedule,*cluster_config['SelfNode']))
    
    # NameNode让其 `load ` 指定数据块内容, 将该块内容会送给NameNode 供用户读取
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
    # 除了 KeyInterrupt 否则保持运行
    loop.run_forever()
```



5. 冗余策略

> 紧接上面的心跳机制,。
>
> 举例说明流程：
>
> ​		将一个节点A表示为`Dead`，NameNode 查找出该节点上原先保存了数据块a,b,c。
>
> ​		通过NameNode中的 block_manager下 的 `resilance_map`依次找到a,b,c各自三个副本的node之间一共9块数据的node节		点.
>
> ​		并找到保存这些数据块副本的其他节点, 从这些读取副本内容复制到3份
>
> ​		将复制的数据发到为`Alive` 的节点.
>
> ​		删去之前9个node里失效的,增加新分配的.

`resilance_map` 内容图解:

对数据块1的三个副本,resilance_map会负责在其中维护一个对象用于记录它们的信息,

图中数据块1在`NameNode_Resilance_Map`的内容包含如下信息:

1. 该文件的三个副本存在 DataNode_1 的17号数据块,DataNode_2 的2016号数据块, DataNode_3的19号数据块上
2. 记录"今天天气真好,我去公园玩了,哈哈哈哈哈" 的全部数据块1,2,3位置信息可以从在 第6,9,10号node上找到。

所以当数据丢失后,`Resilance_Map` 首先会重新分配 (1)中数据块，其次通过inode找到所有数据块信息，删除已经丢失的Block的编号，加入新分配的Block编号。

![](C:\Users\t470p\Desktop\云计算文档\image\resillance_map.png)





以重建副本的函数为例:

```Python
def rebuild_replication(self,target):
    resilances = self.file_manager.block_manager.resilance_map
    nodes=list(self.file_manager.block_manager.maps.keys())
    # 遍历依赖关系,查看一个DataNode挂了后哪些数据块的副本数目少于了3个
    for resilance in resilances:
        if target in resilance and len(resilance.keys())>2:
            anchor=0
            replaced_blocks=[[],[]]
            # 删除block和该节点的依赖关系
            temporary_store=copy.deepcopy(resilance[target])
            # 删除挂掉节点的依赖关系
            del resilance[target]
            # 分配新节点
            for replaced_index in temporary_store:
                replaced_blocks[0].append({'name':target,'clean':replaced_index})
                # 不能向集群中已经挂掉的DataNode分配新节点
                while not cluster_config[nodes[anchor]]['status'] =='Alive':
                    anchor=(anchor+1)%len(nodes)
                    belonger,block_index=self.file_manager.block_manager.allocate_blocks(size=0,to_type='file',anchor=anchor)[0].values()
                    replaced_blocks[1].append({'name':belonger,'clean':block_index})
                    #得到要获得拷贝数据的节点
                    k = list(resilance.keys())[-1]
                    if belonger in resilance:
                        resilance[belonger].append(block_index)
                        else:
                            resilance[belonger]=block_index
                    
                            command={
                                # 类型: 重建副本
                                'Type':'Rebuild',
                                # 取剩余副本的DataNode
                                'Target':cluster_config[k]['addr'],
                                # 副本block位置
                                'Reget_Block':resilance[k][0],
                                # 复制副本并转存的DataNode的block位置
                                'Resave_Block':block_index,
                                # 转存副本目标IP地址
                                'Repost':cluster_config[belonger]['addr']
                            }
                            Send_Queue.put(command)
                            #发出命令之后更新nodes
                            for node_index in resilance['node']:
                                block_indexs = self.file_manager.node_manager.get_block_indexs(node_index)
                                print(block_indexs)
                                context_part_num = len(block_indexs)
                                for i in range(context_part_num):
                                    if block_indexs[i] in replaced_blocks[0]:
                                        index=replaced_blocks[0].index(block_indexs[i])
                                        block_indexs[i]=replaced_blocks[1][index]
                                        #print('replaced:',replaced_blocks[1][index])
                                        #print('after changed:')
                                        #print(block_indexs)
                                        self.file_manager.node_manager.reset_block_indexs(node_index,block_indexs)

```



6. 节点一致性

> 为所有节点实现了DataNode和NameNode两套接口。每个节点根据配置信息确定自己的角色是 DataNode 还是NameNode





## 二. 使用Hadoop集群完成一个销售模块

### 2.1  前端

#### 2.1.1 概述

- 本项目实质是一个电影票销售系统——普通用户可以查看电影信息，购买所需的电影票；管理员可以查看订单信息，了解销售情况。
- 使用框架：Vue.js
- 组件库：Element UI
- 托管平台：GitHub

#### 2.1.2 实现功能

**用户:**

1. 查看电影列表

2. 根据关键词检索具有特定名称的电影

3.  得到系统推荐的高分电影

4. 查看电影详情

5. 购票

**管理员:**

1. 查看订单列表
2. 对特定年或月或日的订单进行筛选
3. 查看最近几年的销售情况
4. 查看某一年的销售情况

**部分截图:**

![](.\lz_doc\image\movie_list.png)



![](.\lz_doc\image\movie_detail_1.png)



![](.\lz_doc\image\order_list.png)



#### 2.1.3 代码描述

![](.\lz_doc\image\src_file.png)



- **routers.js:** 定义了基本的路由。

- **Index.js:** 为索引页，内容非常简单，header 里有一个标题，而 main 里有两个登陆的按钮。

- **MovieList.vue:** 为电影详情页的主干，Boarding.vue 为 aside 里的口碑榜，而 MovieCard.vue 则是 main 部分的每一张电影卡片，不同的 vue 文件间通过 props 属性进行数据传递。电影列表的分页使用了 Element UI 提供的分页器。

- **Detail.vue:** 为电影详情页，中间的购票 button 绑定了打开 dialog 的方法，在 dialog 中可插入新的订单条目，即购票。

- **OrderList.vue:** 为订单列表页，上方使用了 Element UI 提供的 Nav Menu，下面的 table 展示数据。中间的日期选择器通过 selectOrder 函数进行订单的筛选。

  ```
  selectOrder: function() {
      this.date_str = this.year + "-" + this.month + "-" + this.day + "%";
      console.log(this.date_str);
      this.orderTable = [];
      this.start_from = 0;
      this.generateData();
  },
  generateData: function() {
      this.is_loading = true;
      this.scroll_top = document.documentElement.scrollTop;
      axios
          .post(`/api/query_order_list`, {
              start_from: this.start_from,
              limitation: this.limitation,
              time_limitation: this.date_str
          })
          .then(res => {
              this.start_from += this.limitation;
              if (res.data.length == 0) {
                  this.has_more = false;
              } else {
                  this.has_more = true;
              }
              this.orderTable = this.orderTable.concat(res.data);
              this.is_loading = false;
          });
  }
  ```

- **Chart.vue:** 为销售情况页。最上面也是导航栏，下面通过 create_year_charts 和 create_pie_chart 创建了两张图表。



### 2.2 后端

#### 2.2.1 数据库架构

**使用组件**:

- Hadoop
  使用Hadoop作为数据库存储的底层结构，实现了数据的分布式存储
- Hive
  使用Hive来完成数据库表结构的构建以及原始数据的导入
- Impala
  由于Hive的查询构建基于Map Reduce，延迟较高，查询速度较弱，不适用于实时查询系统，因此本项目使用了Impala作为数据库查询工具，Impala与Hive共享数据库元数据，并且提供了比Hive更快的查询速度

**节点结构**

- 本项目使用了三台主机来搭建分布式集群，分别为Master，Slave1，Slave2，其中Master担任Name Node和Data Node两个角色，Slave1和Slave2作为Data Node

  ![](.\image\node.png)





**数据库表结构:**

- 为提高查询性能，数据库并不完全遵守第三范式，包含一定的冗余
- 因为考虑到我们引入的冗余数据（电影相关信息）并不需要修改，因此这么做是比较合理的

![](.\image\table.png)



#### 2.2.2 后端服务器

**后端服务器**

采用前后端分离的方式进行web应用的开发



**运行环境及依赖**

- 使用python 3.7进行开发
- 使用flask框架进行server端开发
- 使用ORM框架Sqlalchemy以及Impala驱动impyla连接数据库并进行查询操作
- 使用flask组件flask_cors来实现跨域访问



#### 2.2.3 实现接口

**电影列表查询**

- 接口url:`/api/query_movie_list`

- method: POST

- 功能描述: 查询电影列表的信息，支持分页操作

- 参数说明

  - body参数

    ```javascript
    {start_from,limitation,search_key}
    //start_from: 所查询电影列表在数据库中的起始位置
    //limitation: 查询电影的数据条数
    //search_key: 用于搜索电影使用，为空时则查询任意电影，支持模糊搜索
    ```

- 返回数据格式

  - 数据类型: JSON数组

  - 格式样例:

    ```javascript
    [{movie_id,name,price,ranking,information},...]
    // movie_id: Integer 电影的编号
    // name: String 电影的名字
    // price: Double 电影的价格
    // ranking: Double 电影的评分
    // information: Object 包含电影的其他信息
    ```

**推荐电影列表查询**

- 接口url:`/api/recommend_movie_list`

- method: POST

- 功能描述: 查询推荐电影列表的信息，根据评分进行排序，支持分页操作

- 参数说明

  - body参数

    ```javascript
    {start_from,limitation,search_key}
    //start_from: 所查询电影列表在数据库中的起始位置(按评分排序)
    //limitation: 查询电影的数据条数
    ```

- 返回数据格式

  - 数据类型: JSON数组

  - 格式样例:

    ```javascript
    [{movie_id,name,price,ranking,information},...]
    // movie_id: Integer 电影的编号
    // name: String 电影的名字
    // price: Double 电影的价格
    // ranking: Double 电影的评分
    // information: Object 包含电影的其他信息
    ```


**电影详情查询**

- 接口url:`/api/query_movie/<int:movie_id>`

- method: POST

- 功能描述: 根据movie_id查询某条电影的信息及评论

- 参数说明:
  路径参数`movie_id: Integer类型 电影ID`

- 返回数据格式

  - 数据类型: JSON数组

  - 格式样例:

    ```javascript
    [{movie_id,name,price,ranking,information，
      reviews:[{review_id,movie_id,ranking,content},...]}]
    // 保证数组内至多只有一条数据
    // movie_id: Integer 电影的编号
    // name: String 电影的名字
    // price: Double 电影的价格
    // ranking: Double 电影的评分
    // information: Json Object 包含电影的其他信息
    // reviews: Json Array 
    //			内部每条数据包含一下数据:
    //			review_id: Integer 评论编号
    //			movie_id: Integer 评论的电影编号
    //			ranking: Double 该用户对电影的评分
    //			content: String 评论的内容
    ```

**查询订单列表**

- 接口url: `/api/query_order_list`

- 功能描述: 查询订单列表的信息，支持分页操作

- 参数说明

  - body参数

    ```javascript
    {start_from,limitation,search_key}
    // start_from: 所查询订单列表在数据库中的起始位置
    // limitation: 查询订单的数据条数
    // time_limitation: 用于限制订单访问，使用形如'yyyy-mm-dd%'形式的字符串，yyyy为年份， //				  mm为月份，dd为具体天数，不需要进行限定的时间字符串可用%替换
    ```

- 返回数据格式

  - 数据类型: JSON数组

  - 格式样例:

    ```javascript
    [{order_id,movie_id,movie_name,movie_num,price_sum,create_time},...]
    // order_id: 订单编号
    // movie_id: 购买的电影编号
    // movie_name: 购买的电影名字
    // movie_num: 购买的电影总数
    // price_sum: 总共支付的钱数
    // create_time: 下订单的时间
    ```

**购买电影**

- 接口url: `/api/insert_order`

- 功能描述: 查询订单列表的信息，支持分页操作

- 参数说明

  - body参数

    ```javascript
    {item:{movie_id,movie_name,movie_num,price_sum}}
    // movie_id: 购买电影的id
    // movie_name: 购买电影的名字
    // movie_num: 购买电影的份数
    // price_sum: 总价
    ```

- 返回数据格式

  - 字符串
  - 内容:`"success"`



#### 2.2.4 运行方式

- 安装python库flask,flask_cors,sqlalchemy,impyla
- 运行`python Server.py`即可
- 监听端口为12450

