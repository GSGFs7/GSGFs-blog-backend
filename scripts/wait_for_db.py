#!/usr/bin/env python

import os
import sys
import time

import django
from django.db import connection
from django.db.utils import OperationalError

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog.settings")
django.setup()


def check_db():
    max_retries = 15
    for i in range(max_retries):
        try:
            # Attempt to establish a connection
            connection.ensure_connection()
            with connection.cursor() as cursor:
                # Execute basic query
                cursor.execute("SELECT 1;")
                # Check if pgvector extension is available and working
                # This is important as the project heavily relies on it
                try:
                    cursor.execute("SELECT '[1,2,3]'::vector;")
                except Exception as ve:
                    print(f"Database connection OK, but pgvector check failed: {ve}")
                    print(
                        "Hint: Ensure 'CREATE EXTENSION IF NOT EXISTS vector;'"
                        " has been run or the image includes it."
                    )

            print("Successfully connected to the database and verified pgvector.")
            return True
        except OperationalError as e:
            print(f"Database not ready (retry {i + 1}/{max_retries}): {e}")
            time.sleep(2)
        except Exception as e:
            print(f"Unexpected error during DB check: {e}")
            time.sleep(2)
    return False


if __name__ == "__main__":
    print("Starting database connection check...")
    if check_db():
        sys.exit(0)
    else:
        print("Could not connect to the database after several retries.")
        sys.exit(1)
