# GSGFs-blog-backend

个人网站的后端, 使用`Django`和`Django-ninja`构建.

## 运行

`python`版本: `3.13`

1. 创建一个`python`虚拟环境

   ```bash
   python -m venv .venv
   ```

2. 激活此虚拟环境(以`Linux`为例)

   ```bash
   source .venv/bin/activate
   ```

3. 安装库

   ```bash
   pip install -r requirements.txt
   ```

4. 将`.env.example`复制一份为`.env`并填写需要的环境变量(如果不填写数据库部分则会使用不需要额外配置的`sqlite3`作为数据库)

5. 迁移数据库

   ```bash
   ./manage.py makemigrations && ./manage.py migrate
   ```

6. 运行开发服务器

   ```bash
   ./manage.py runserver
   ```

## 部署

`./manage.py runserver`只适合开发环境, 在生产环境中, 请使用`gunicorn`或`uwsgi`等`WSGI`服务器.

- 使用`docker`部署:

  - 手动构建
    构建并导出镜像(以`Linux`为例):

    ```bash
    export.sh
    ```

    将导出的镜像上传到服务器, 然后运行下面的命令载入镜像:

    ```bash
    docker load < django.tar.zst
    ```

    复制`docker-compose.yml`, 注释`django-web`中的`build`部分, 启用`image`部分.  
     创建`.env`文件, 填写需要的环境变量, 然后运行:

    ```bash
    docker-compose up -d
    ```

  - 使用`action`自动构建的镜像
    这些镜像可以在`action`的`artifact`中找到, 下载后使用`docker load`载入即可.

## 小工具

- `backup-db.sh`: 一个简单备份数据库脚本(配合`cron`使用)
- `export.sh`: 导出 docker 镜像
- `upload.py`: 上传文件至 R2 对象存储

## 开源协议

MIT
