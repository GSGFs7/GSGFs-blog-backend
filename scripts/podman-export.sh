#!/usr/bin/bash

podman save django:latest | zstd -c -T0 -12 > 'django.tar.zst'
