import json
import boto3
import botocore.exceptions
import os

cognito_idp_client = boto3.client("cognito-idp")
user_pool_id = str(os.environ["USER_POOL_ID"])
client_id = str(os.environ["CLIENT_ID"])


def handle_login(event, context):
    # for field in ["email", "password"]:
    #     if not event.get(field):
    #         return {
    #             "statusCode": 400,
    #             "message" : "{field} is not present."
    #         }

    event_body = json.loads(event["body"])

    try:
        response = cognito_idp_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={
                "USERNAME": event_body["email"],
                "PASSWORD": event_body["password"],
            },
        )

    except botocore.exceptions.ClientError as e:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": e,
        }

    body = {
        "message": "User has successfully logged in!",
        "token": str(response["AuthenticationResult"]["IdToken"]),
    }

    return {
        "statusCode": 200,
        "isBase64Encoded": False,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": json.dumps(body),
    }
