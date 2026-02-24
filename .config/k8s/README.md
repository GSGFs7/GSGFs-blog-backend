使用 k3s 部署的配置

需要用到 `Dockerfile.*` 这些文件来构建镜像

步骤:

0. 安装并配置 k3s

1. 配置环境变量

   ```bash
   # 复制 .env 并填写相关内容
   cp .env.example .env
   ```

2. 构建镜像并导入到 k3s

   ```bash
   ./script/k3s-build.sh
   ```

   这将得到这三个镜像：
   - `localhost/blog-django:latest`
   - `localhost/blog-celery-worker:latest`
   - `localhost/blog-celery-beat:latest`

3. 部署到 k3s

   ```bash
   ./script/k3s-deploy.sh
   # 或者使用开发环境配置
   ./script/k3s-deploy.sh dev
   ```
