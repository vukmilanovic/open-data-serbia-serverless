import boto3
import json
import os

s3_client = boto3.client("s3")
bucketName = str(os.environ["BUCKET_NAME"])


def handle_url(event, context):
    params = event["queryStringParameters"]

    presigned_url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": params["bucket_name"], "Key": params["file_key"]},
        ExpiresIn=params["expiry_time"],
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": json.dumps(presigned_url),
    }
