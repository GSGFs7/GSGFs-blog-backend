#!/usr/bin/bash

docker buildx build -t django . &&
    docker save django:latest | zstd -c -T0 --ultra -20 >'django.tar.zst'
