# syntax=docker/dockerfile:1
# Use the '#syntax' to enable advanced features of BuildKit


FROM python:3.13-slim AS builder

RUN mkdir -p /app
WORKDIR /app

ARG MODEL_NAME
ARG SENTENCE_TRANSFORMERS_HOME
ENV MODEL_NAME=${MODEL_NAME}
ENV SENTENCE_TRANSFORMERS_HOME=${SENTENCE_TRANSFORMERS_HOME}

# no .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# no output buffer
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++

RUN pip install --upgrade pip
# RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
# CPU only
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# try copy models file
COPY . .

# download model
# Use --mount=type=secret to safely mount the token
RUN --mount=type=secret,id=hf_token \
    export HUGGINGFACE_HUB_TOKEN=$(cat /run/secrets/hf_token) && \
    export MODEL_NAME=${MODEL_NAME} && \
    export SENTENCE_TRANSFORMERS_HOME=${SENTENCE_TRANSFORMERS_HOME} && \
    python /app/scripts/download-model.py

FROM python:3.13-slim

# supervisor: Manage multiple processes simultaneously
RUN apt-get update && apt-get install -y --no-install-recommends supervisor

RUN mkdir -p /app
WORKDIR /app

RUN useradd -m user && \
    chown -R user /app

ARG MODEL_NAME
ARG SENTENCE_TRANSFORMERS_HOME
ENV MODEL_NAME=${MODEL_NAME}
ENV SENTENCE_TRANSFORMERS_HOME=${SENTENCE_TRANSFORMERS_HOME}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
ENV DOCKER_ENV="True"

# copy
# python lib
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
# model
COPY --from=builder /app/sentence_transformers_models /app/sentence_transformers_models
# code
COPY --chown=user:user . .

# supervisor configuration
COPY --chown=root:root supervisord.conf /etc/supervisor/supervisord.conf

# supervisor log directory
RUN mkdir -p /var/log/supervisor && \
    chown -R user /var/log/supervisor

# collect static
RUN python manage.py collectstatic --noinput

# supervisor needs to run as root
# USER user 

EXPOSE 8000

# CMD [ "gunicorn", "-c", "gunicorn.conf.py", "blog.wsgi:application" ]
CMD [ "supervisord" , "-c", "/etc/supervisor/supervisord.conf" ]


# https://www.docker.com/blog/how-to-dockerize-django-app/
