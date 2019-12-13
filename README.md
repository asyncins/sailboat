# Sailboat

![Sailboat slogen](https://github.com/asyncins/sailboat/blob/master/image/sailboat-slogen.png)

Management Platform For Python Spider Project

⛵️Sailboat 意为帆船 

它是一个专为非框架类 Python 项目准备的轻量级项目管理平台。

在没有 Sailboat 之前，你编写的框架类爬虫项目可以通过框架配套的服务进行部署和管理，例如 Scrapy 与 Scrapyd 的形式。

但如果你只是想一些小东西 **例如用 Requests 或 Aiohttp 编写网络程序**，不想使用 Scrapy 这样的框架时，你无法将你写好的项目放到服务器上**管理**。

或许你可以写一个 Linux Shell，让它可以定时启动。这个过程中你会发现很多问题：

- 如何获得项目运行产生的日志？
- 有几十个项目要设置定时任务，有什么能去写 Shell 的好方法吗？
- 可能你都不知道部署了哪些项目。
- 甚至你连哪些项目执行过，哪些没执行都不知道。
- 如何才能捕获到项目发生的异常，并及时通知我？
- 散兵游勇，称不上团队，跟别说管理。
- ……

Sailboat 就是为了解决这些问题而编写的，具体功能如下：

- 用户注册/登录/更新/查询
- 适合团队作战的角色权限 Superuser/Developer/Other/Anonymous
- 项目文件打包
- 项目部署/查看/删除
- 项目定时调度/删除调度计划/查看调度计划
- 查看执行记录
- 查看项目执行是产生的日志
- 自动监控项目，自动整理异常信息，当产生异常时通过钉钉（默认）或其它方式通知你
- 带有数据展示的工作台，你可以在工作台看到服务器资源信息、项目数据总览和统计类数据

# 安装

Python 版本说明：

> Sailboat 开发时使用的是 Python 3.6，建议在同等版本环境中使用。
> 请自行准备 Python 运行环境，此处不再赘述

### 第 1 步

Sailboat 是一个前后分离的项目，并没有打包成安装包，也就是说无法使用 pip 安装它。首先，你要将 Sailboat clone 到你的服务器：

```
# current path /root/www/
$ git clone git@github.com:asyncins/sailboat.git
```
假设当前路径为 /root/www，那么命令执行后 www 目录下就会多出 sailboat 目录。

### 第 2 步
项目中使用到的第三方库记录在 sailboat/rements.txt 中，你可以使用：

```
$ pip install -r sailboat/rements.txt
```
这个命令会帮助你一次性完成项目依赖的安装。

### 第 3 步

数据库选用的是 MongoDB。在开始前，你需要按照 [MongoDB 官方指引](https://docs.mongodb.com/manual/installation/)在服务器上安装并启动 MongoDB。


### 第 4 步

Sailboat 基于 Python Web 开发框架 Flask，它的部署必然要安装 uWSGI 和 Nginx。不过你不要慌，这份文档很清晰，照做就是。

按照 [Nginx 官方指引](http://nginx.org/en/docs/install.html)在服务器上安装并启动 Nginx。

按照 [uWSGI 官方指引](https://uwsgi-docs.readthedocs.io/en/latest/Install.html)在服务器上安装 uWSGI


### 第 5 步 检查配置文件

Sailboat 已经为你准备好了 Nginx 配置文件 sailboat/sailboat.conf：

```
upstream webserver {
    # server unix:///path/to/your/mysite/mysite.sock; # for a file socket
    server 127.0.0.1:3031; # uwsgi的端口
}

server {
    # the port your site will be served on
    listen      5000;
    # 端口
    server_name 111.231.93.117; # 服务器ip或者域名
    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # 限制最大上传


    # docs
    location /docs  {
        alias  /root/www/sailboat/docs;  # 指向文档路径
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        uwsgi_pass  webserver;
        include     uwsgi_params; # uwsgi服务
    }
}
```

这里可做调整的配置只有 listen 和 location。

listen 代表对外端口，例如设置为 5000 时，浏览器访问的网址为 http://www.xxx.com:5000/

location 代表设定路由，例如：

```
    # docs
    location /docs  {
        alias  /root/www/sailboat/docs;  # 指向文档路径
    }

```
代表用户访问 http://www.xxx/com/docs 时指向的资源为 /root/www/sailboat/docs

为了使配置生效你需要将拷贝到对应的目录，例如: /etc/nginx/conf.d/

> ⚠️ 注意：/etc/nginx/nginx.conf 文件第一行的用户（默认为 nginx）需要设定为当前用户，例如 root。否则启动后引发 permission 相关报错，导致服务无法正常访问。

同样的，Sailboat 已经为你准备好了 uWSGI 配置文件 sailboat/sailboat.ini。

### 第 6 步 启动

首先启动 uWSGI，对应命令如下：

```
$ uwsgi -i /root/www/sailboat.ini &
```
命令执行后便可使用 Crtl+c 组合键退回终端命令行，接着刷新 Nginx 配置：

```
$ nginx -s reload
```
这俩命令执行后便可在浏览器访问 Sailboat 项目了。




# 界面展示

# 使用指引

### 注册

### 登录

### 项目打包

### 项目部署

### 添加一个定时调度

### 查看记录或列表

# 开发故事

## 贡献者名单

## 联系我们
