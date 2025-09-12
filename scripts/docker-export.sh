#!/usr/bin/bash

docker save django:latest | zstd -c -T0 --ultra -17 > 'django.tar.zst'
