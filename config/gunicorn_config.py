# -*- coding: utf-8 -*-

# @Time    : 2020/8/6 下午9:15
# @Author  : gaoqi

import gevent.monkey

gevent.monkey.patch_all()

# 启动的进程数
bind = '0.0.0.0:2060'  # 绑定的ip已经端口号
workers = 2  # 进程数
threads = 4  # 指定每个进程开启的线程数，官方推荐设置为核心数的两至四倍
backlog = 2048  # 允许挂起的连接数的最大值，官方推荐这个值设在64-2048
timeout = 180  # 超时时间，单位秒
worker_class = "gevent"  # 工作方式，使用gevent模式，默认的是sync模式（并发只有1个），可选值eventlet、gevent、tornado、gthread、giohttp
worker_connections = 2000  # 进程链接数，默认值1000，同时链接客户端的阀值，这个设置只对进程工作方式为Eventlet和Gevent的产生影响
daemon = True  # 守护进程，默认值是False，守护进程形式来运行Gunicorn进程
pidfile = 'log/gunicorn.pid'  # 设置pid文件的文件名，如果不设置的话，不会创建pid文件，默认值是None
# proc_name="myflask"      #默认值default_proc_name，即gunicorn（需要额外安装setproctitle），但是测试没有生效，需要深入看看？？
# pythonpath='/home/kevin/test/.my_env/bin'  # 将这些路径加到python path去

loglevel = 'info'  # 日志级别，这个日志级别指的是错误日志的级别，而访问日志的级别无法设置，可以是debug，info，warning，error，critical
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'  # 设置gunicorn访问日志格式，错误日志无法设置
accesslog = "./log/access.log"  # 访问日志文件的路径
errorlog = "./log/error.log"  # 错误日志文件的路径
x_forwarded_for_header = 'X-FORWARDED-FOR'
