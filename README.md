# GSGFs-blog-backend

## 如何运行

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

## 开源协议

MIT
