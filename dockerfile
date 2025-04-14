# 构建环境
FROM python:3.13.3-alpine AS builder

RUN mkdir -p /app
WORKDIR /app

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

RUN apk add --no-cache gcc python3-dev musl-dev linux-headers

# 安装软件包
RUN pip install --upgrade pip
# RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 最终环境
FROM python:3.13.3-alpine

RUN adduser -D -H -h /app user && \
    mkdir /app && \
    chown -R user /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
ENV DOCKER_ENV="True"

# 复制环境
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 复制代码
COPY --chown=user:user . .

# 收集静态文件
RUN python manage.py collectstatic --noinput

USER user

EXPOSE 8000

CMD [ "gunicorn", "-c", "gunicorn.conf.py", "blog.wsgi:application" ]


# https://www.docker.com/blog/how-to-dockerize-django-app/