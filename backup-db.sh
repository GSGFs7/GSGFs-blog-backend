#!/usr/bin/bash

source .env

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_${TIMESTAMP}.dump"

mkdir -p ${BACKUP_DIR}

docker exec blog-db pg_dump -U ${DATABASE_USERNAME} ${DATABASE_NAME} > ${BACKUP_FILE}
