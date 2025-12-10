#!/usr/bin/bash

source .env

BACKUP_FILE="$1"

docker exec -i blog-db psql \
    -U "${DATABASE_USERNAME}" \
    -d "${DATABASE_NAME}" \
    < "${BACKUP_FILE}"

if [ $? -eq 0 ];then
	echo "success"
else
	echo "failed"
	exit 1
fi
