#!/usr/bin/bash

./script/docker-build.sh

docker save django:latest | zstd -c -T0 --ultra -20 > 'django.tar.zst'
