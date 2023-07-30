import sys

sys.path.insert(0, "package")
from io import BytesIO
import boto3
import os
import json
from multipart import MultipartParser


s3_client = boto3.client("s3")
bucketName = str(os.environ["BUCKET_NAME"])


def handle_storing(event, context):
    content_type_header = event["headers"]["Content-Type"]
    boundary = content_type_header.split("boundary=")[1]

    ctype = content_type_header.split(";boundary=")[0]
    print(ctype)

    key = (
        event["body"]
        .split(boundary)[1]
        .split("Content-Type")[0]
        .split("filename=")[1]
        .replace('"', "")
    )
    event_body = bytes(event["body"], "utf-8")

    rfile = BytesIO(event_body)
    parsed_list = MultipartParser(rfile, boundary.encode("utf-8"))
    file_content = parsed_list.parts()[0].value

    response = upload_to_s3(bucketName, key, file_content, ctype)
    return {"statusCode": 200, "body": ""}
    # json.dumps(response)


def upload_to_s3(bucket, key, file, ctype):
    response = s3_client.put_object(
        ACL="public-read", Body=file, Bucket=bucket, Key=key, ContentType=ctype
    )
    return response
