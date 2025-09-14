#!/usr/bin/env python


import os
import sys

import django

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)  # Search path for modules

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog.settings")
    django.setup()

    # ModuleNotFoundError: No module named 'api'
    from api.models import Post

    posts = Post.objects.all()
    for post in posts:
        try:
            post.save()
        except Exception as e:
            print(f"Error processing article '{post.title}': {e}")
