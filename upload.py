#!/usr/bin/env python


# 用于将本地的文件上传至r2的脚本, 如果需要上传远程文件可以先使用rclone挂载到本地的某个文件夹下再上传.


import argparse
import datetime
import json
import os
import shutil
import sys
from typing import Optional

import boto3
import dotenv
from botocore.exceptions import ClientError

dotenv.load_dotenv(".env")

# Config
# R2_TOKEN = os.environ.get("R2_TOKEN")  # The token given by CF is not used
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")

# Initializing the R2 Client
r2_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)


def list_buckets() -> None:
    """List all buckets"""
    for bucket in r2_client.list_buckets()["Buckets"]:
        print(f"{bucket['Name']}")


def upload_file(file_name: str, bucket: str, object_name: Optional[str] = None) -> bool:
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If no `object_name` is given, the file name is used.
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        r2_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        print(f"Error: {file_name} upload failed. {e}")
        return False
    return True


def upload_directory(dir_path: str, bucket: str, prefix: str = "") -> None:
    """Recursively upload all files in a folder

    :param dir_path: Directory to upload
    :param bucket: Bucket to upload
    """

    def load_cache() -> dict:
        """Reuse recent results

        :return: A dictionary containing all file names, the value of the key is `True`.
        """
        try:
            res = {}
            with open("uploaded.json", "r", encoding="utf-8") as f:
                already_existing_file = json.load(f)
            for file in already_existing_file:
                res[file["Key"]] = True
            return res
        except:
            return {}

    total_files = 0
    uploaded_files = 0
    already_existing_file = load_cache()

    # Iterate through all files in a directory
    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            # Restore file path
            local_path = os.path.join(root, filename)

            # Process object name
            relative_path = os.path.relpath(local_path, dir_path)
            # For Windows users, use / instead of \
            r2_object_name = os.path.join(prefix, relative_path).replace("\\", "/")

            print(r2_object_name)
            print(already_existing_file)
            if already_existing_file.get(r2_object_name):
                print(f"跳过重复文件: {local_path}")
                continue

            # Upload files
            print(f"正在上传: {local_path} -> ({bucket}){r2_object_name}")
            total_files += 1
            if upload_file(local_path, bucket, r2_object_name):
                uploaded_files += 1

    print("-" * shutil.get_terminal_size().columns)
    print(f"上传完成: 总共 {total_files} 个文件, 成功上传 {uploaded_files} 个")
    return


def list_object(bucket: str, prefix: str = "", delimiter: str = "") -> None:
    """List all object in an bucket

    :param bucket: The name of bucket
    :param prefix: Only list objects starting with this prefix (optional)
    :param delimiter: Separator for grouping (optional)
    """

    def write_list_object(files):
        """Persisting data in a JSON file"""

        # Overriding JSON serialization of `datetime`
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, datetime.datetime):
                    return o.strftime("%Y-%m-%d %H:%M:%S")
                return super().default(o)

        try:
            with open("uploaded.json", "w", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        files,
                        cls=DateTimeEncoder,
                        indent=2,
                        ensure_ascii=False,
                    )
                )
        except Exception as e:
            print(f"写入文件错误: {e}")

    try:
        paginator = r2_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=bucket,
            Prefix=prefix,
            Delimiter=delimiter,
        )

        files = []
        print(f'存储桶 "{bucket}" 中的文件:')
        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    size_mb = obj["Size"] / (1024 * 1024)
                    print(f'  {obj["Key"]} ({size_mb:.2f} MB)')
                    files.append(
                        {
                            "Key": obj["Key"],
                            "LastModified": obj["LastModified"],
                            "ETag": obj["ETag"],
                            "Size": obj["Size"],
                            "StorageClass": obj["StorageClass"],
                        }
                    )
        write_list_object(files)
    except ClientError as e:
        print(f"Error: 列出 '{bucket}' 中的文件失败. {e}")


def print_usage() -> None:
    """Print instructions"""

    print(f"用法: {sys.argv[0]} [命令]")
    print("可用命令")
    print("  upload <dir> <bucket> [prefix] - 上传文件夹内所有文件至存储桶")
    print("  list <bucket>                  - 列出所有文件")
    print("  list_bucket                    - 列出所有存储桶")
    print("  --zh                           - 显示此帮助信息")


def parse_argument() -> argparse.Namespace:
    """Parsing user input parameters"""

    # Why English? Because argparse is English.
    parser = argparse.ArgumentParser(
        description="R2 object storage file uploader",
        epilog="使用--zh参数查看中文帮助",
    )
    subparser = parser.add_subparsers(dest="command", description="Available commands")

    # upload command
    upload_parser = subparser.add_parser(
        "upload",
        aliases=["u"],
        help="Upload all files in the directory to R2",
    )
    upload_parser.add_argument(
        "dir_path",
        help="The directory where the file is located",
    )
    upload_parser.add_argument(
        "bucket",
        help="The bucket where the upload will be made",
    )
    upload_parser.add_argument(
        "prefix",
        nargs="?",
        default="",
        help="Object prefix in the bucket",
    )

    # list bucket command
    subparser.add_parser(
        "list_bucket",
        aliases=["b"],
        help="List all buckets available for upload",
    )

    # list command
    list_parser = subparser.add_parser(
        "list",
        aliases=["l"],
        help="List all files in a bucket",
    )
    list_parser.add_argument(
        "bucket",
        help="The name of the bucket to be uploaded",
    )
    list_parser.add_argument(
        "prefix",
        nargs="?",
        default="",
        help="List only files with this prefix",
    )
    list_parser.add_argument(
        "delimiter",
        nargs="?",
        default="",
        help="Delimiter of the files",
    )

    # global
    parser.add_argument(
        "--zh",
        action="store_true",
        help="Show Chinese output",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()


def main():
    """Main function"""

    args = parse_argument()

    if args.command == "upload":
        upload_directory(args.dir_path, args.bucket, args.prefix)
    elif args.command == "list_bucket":
        list_buckets()
    elif args.command == "list":
        list_object(args.bucket, args.prefix, args.delimiter)
    else:
        print_usage()


if __name__ == "__main__":
    main()
