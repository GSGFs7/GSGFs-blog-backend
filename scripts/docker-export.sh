#!/usr/bin/bash

docker save django:latest | zstd -c -T0 -12 > 'django.tar.zst'
