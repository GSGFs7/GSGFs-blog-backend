# GSGFs-blog-backend

使用 `Django` 和 `Django-ninja` 构建的个人网站后端.

## 运行

> [!NOTE]  
> Django 自带的后台在 `/not-admin` 而不是 `/admin`

`python`版本: `3.14`, 推荐使用 uv 作为包管理器

_Windows 用户在运行 `./xxx.py` 这类命令时可能需要在前面加上 `python`, 例如 `./manage.py runserver`
应该改为 `python ./manage.py runserver`_

1. 安装所需依赖

   ```bash
   uv sync
   ```

2. 激活 Python 虚拟环境 (以 `Linux` 为例)

   ```bash
   source .venv/bin/activate
   ```

3. 将 `.env.example` 复制一份为 `.env` 并填写需要的环境变量

   尖括号中的内容是必填项, 可以使用 `openssl rand -base64 40` 生成所需的随机字符

4. 启动数据库和 Redis

   ```bash
   docker compose up -d "blog-db" "blog-redis"
   ```

5. 由于搜索功能依赖向量化处理, 需要下载用于生成向量的嵌入模型

   ```bash
   ./scripts/download-model.py
   ```

6. 迁移数据库

   ```bash
   ./manage.py makemigrations && ./manage.py migrate
   ```

7. 创建一个管理员用户 (用于登陆后台)

   ```bash
   ./manage.py createsuperuser
   ```

8. 运行开发服务器

   ```bash
   ./manage.py runserver
   ```

## 目录

```text
.
├── api/            # Django app
│   ├── backends/   # Django 后端
│   ├── migrations/ # 数据库迁移
│   ├── routers/    # 路由
│   ├── tests/      # 测试
│   ├── admin.py    # Django admin 设置
│   ├── apps.py     # Django app 设置
│   ├── models.py   # Django ORM
│   ├── schemas.py  # schema 定义
│   ├── signals.py  # Django 信号处理
│   ├── task.py     # celery 任务
│   └── urls.py     # URL 汇总
├── blog/           # Django project
├── scripts/        # 辅助脚本
├── templates/      # Django 模板
└── manage.py       # Django cli
```

## 接口文档

`django-ninja` 自带 `swagger-UI`, 启动后访问 `/api/docs`

## 小工具

统一放在 `scripts` 文件夹中

- `backup-db.sh`: 一个简单备份数据库脚本(配合`cron`使用)
- `download-model.py`: 下载模型
- `export.sh`: 导出 docker 镜像
- `upload.py`: 上传文件至 R2 对象存储
- `regenerate_embeddings.py`: 重新生成文章向量

## 开源协议

MIT
