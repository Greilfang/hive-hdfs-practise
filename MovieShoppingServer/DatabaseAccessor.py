import json
import threading
import time
from impala.dbapi import connect
import impala.sqlalchemy
import sqlalchemy.orm
from sqlalchemy import Column, create_engine, ForeignKey, func
from sqlalchemy.orm import relationship, noload, lazyload
from sqlalchemy.ext.declarative import declarative_base

# 创建对象的基类:
Base = declarative_base()

class Review(Base):
    # 表的名字:
    __tablename__ = 'review'

    # 表的结构:
    review_id = Column(impala.sqlalchemy.Integer, primary_key=True)
    movie_id = Column(impala.sqlalchemy.Integer, ForeignKey("movie.movie_id"))
    ranking = Column(impala.sqlalchemy.Float)
    content = Column(impala.sqlalchemy.String)

    def get_dict(self):
        return {'review_id': self.review_id, 'movie_id': self.movie_id,
                'ranking': self.ranking, 'content': self.content}


class Movie(Base):
    # 表的名字:
    __tablename__ = 'movie'

    # 表的结构:
    movie_id = Column(impala.sqlalchemy.Integer, primary_key=True)
    name = Column(impala.sqlalchemy.String)
    price = Column(impala.sqlalchemy.Float)
    ranking = Column(impala.sqlalchemy.Float)
    information = Column(impala.sqlalchemy.String)
    reviews = relationship("Review")

    def get_dict(self):
        result = {'movie_id': self.movie_id, 'name': self.name, 'price': self.price,
                  'ranking': self.ranking, 'information': json.loads(self.information)}
        review_list = []
        for review in self.reviews:
            review_list.append(review.get_dict())
        result['reviews'] = review_list
        return result


class Order(Base):
    # 表的名字:
    __tablename__ = 'order_info'

    # 表的结构:
    order_id = Column(impala.sqlalchemy.Integer, primary_key=True)
    movie_id = Column(impala.sqlalchemy.Integer, ForeignKey("movie.movie_id"))
    movie_name = Column(impala.sqlalchemy.String)
    movie_num = Column(impala.sqlalchemy.Integer)
    price_sum = Column(impala.sqlalchemy.Float)
    create_time = Column(impala.sqlalchemy.String)
    movie = relationship("Movie")

    def get_dict(self):
        result = {'order_id': self.order_id, 'movie_id': self.movie_id, 'movie_num': self.movie_num,
                  'price_sum': self.price_sum, 'create_time': self.create_time, 'movie_name': self.movie_name}
        return result


class DBAccessor:
    @staticmethod
    def conn():
        return connect(host='master.mycdh.com',
                       port=21050,
                       database='movie_shop',
                       timeout=60,
                       user='hive',
                       password='Admin_123')

    @staticmethod
    def get_dict(items):
        item_list = []
        for item in items:
            item_list.append(item.get_dict())
        return item_list

    def __init__(self):
        self.engine = create_engine("impala://", creator=DBAccessor.conn)
        self.DBSession = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.lock = threading.Lock()

    def query_movie(self, movie_id):
        session = self.DBSession()
        result = session.query(Movie).filter(Movie.movie_id == movie_id).all()
        session.close
        return result

    def query_movie_list(self, start_from, limitation, search_key):
        session = self.DBSession()
        result = session.query(Movie).options(noload(Movie.reviews)).filter(Movie.name.like(search_key))\
            .order_by(Movie.movie_id).limit(limitation).offset(start_from).all()
        session.close()
        return result

    def query_order_list(self, start_from, limitation, search_time="%"):
        session = self.DBSession()
        result = session.query(Order).options(noload(Order.movie)).filter(Order.create_time.like(search_time))\
            .order_by(Order.create_time.desc()).limit(limitation).offset(start_from).all()
        session.close()
        return result

    def query_recommend_movie_list(self, start_from, limitation):
        session = self.DBSession()
        result = session.query(Movie).options(noload(Movie.reviews)).order_by((Movie.ranking.desc())).\
            filter(Movie.ranking.isnot(None)).limit(limitation).offset(start_from).all()
        session.close()
        return result

    def insert_order(self, item):
        session = self.DBSession()
        self.lock.acquire()
        try:
            order_id = session.query(func.max(Order.order_id)).one()[0]+1
            movie_id = int(item['movie_id'])
            movie_name = item['movie_name']
            movie_num = int(item['movie_num'])
            price_sum = float('%.1f' % item['price_sum'])
            session.add(Order(order_id=order_id, price_sum=price_sum, movie_id=movie_id, movie_num=movie_num,
                              movie_name=movie_name,
                              create_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
            session.commit()
        except BaseException:
            print("Error")
        finally:
            self.lock.release()
            session.close()





