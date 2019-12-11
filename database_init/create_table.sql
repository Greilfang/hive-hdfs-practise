create database if not exists movie_shop;
use movie_shop;

--装载电影数据
drop table if exists movie;
create table movie(
    movie_id int,
    name String,
    price Double,
    ranking Double,
    information String
)
ROW FORMAT DELIMITED FIELDS TERMINATED by '\t';
load data local inpath 'file:///home/zhou/Desktop/movie_info.csv' overwrite into table movie;


--装载评论数据
drop table if exists review;
create table review(
    review_id int,
    movie_id int,
    ranking Double,
    content String
)
ROW FORMAT DELIMITED FIELDS TERMINATED by '\t';
load data local inpath 'file:///home/zhou/Desktop/review.csv' overwrite into table review;

--装载订单数据
drop table if exists order_info;
create table order_info(
    order_id int,
    movie_id int,
    movie_name String,
    movie_num int,
    price_sum Double,
    create_time String
)
ROW FORMAT DELIMITED FIELDS TERMINATED by '\t';
load data local inpath 'file:///home/zhou/Desktop/order.csv' overwrite into table order_info;
