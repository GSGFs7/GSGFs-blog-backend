# GSGFs-blog-backend

使用`Django`和`Django-ninja`构建的个人网站后端.

## 运行

> [!NOTE]
> Django 自带的后台在 `/not-admin` 而不是 `/admin`

`python`版本: `3.13`, 推荐使用 uv 作为包管理器

1. 创建一个`python`虚拟环境

   ```bash
   uv venv
   ```

2. 激活此虚拟环境(以`Linux`为例)

   ```bash
   source .venv/bin/activate
   ```

3. 安装库

   ```bash
   uv pip install -r requirements.txt
   ```

4. 将`.env.example`复制一份为`.env`并填写需要的环境变量

   如果不填写数据库部分则会使用不需要额外配置的`sqlite3`作为数据库  
   尖括号中的内容是必填项, 可以使用 `openssl rand -base64 33` 生成所需的随机字符

5. 迁移数据库

   ```bash
   ./manage.py makemigrations && ./manage.py migrate
   ```

6. 创建一个管理员用户 (用于登陆后台)

   ```
   ./manage.py createsuperuser
   ```

7. 运行开发服务器

   ```bash
   ./manage.py runserver
   ```

## 小工具

- `backup-db.sh`: 一个简单备份数据库脚本(配合`cron`使用)
- `export.sh`: 导出 docker 镜像
- `upload.py`: 上传文件至 R2 对象存储

## 开源协议

MIT
