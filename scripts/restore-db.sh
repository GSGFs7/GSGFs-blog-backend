#!/usr/bin/bash

source .env

BACKUP_FILE="$1"

docker exec -i blog-postgres psql \
    -U "${DATABASE_USER}" \
    -d "${DATABASE_NAME}" \
    < "${BACKUP_FILE}"

if [ $? -eq 0 ];then
	echo "success"
else
	echo "failed"
	exit 1
fi
