#!/usr/bin/bash

docker save django:latest | zstd -c -T0 -16 > 'django.tar.zst'
