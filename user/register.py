import json
import boto3
import botocore.exceptions
import os

cognito_idp_client = boto3.client('cognito-idp')
user_pool_id = str(os.environ['USER_POOL_ID'])
client_id = str(os.environ['CLIENT_ID'])

def handle_registration(event, context):
    
    # for field in ["email", "password", "name"]:
    #     if not event.get(field):
    #         return {
    #             "statusCode": 400,
    #             "message" : "{field} is not present."
    #         }
    
    event_body = event['body']
    try:
        email = event_body['email']
        password = event_body['password']
        name = event_body['name']
        
        response = cognito_idp_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
            {
                'Name': "name",
                'Value': name
            },
            {
                'Name': "email",
                'Value': email
            }
            ],
            MessageAction= 'SUPPRESS',
        )
        
        if response['User'] :
            cognito_idp_client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Password=password,
                Username=email,
                Permanent=True
            )
    
    except cognito_idp_client.exceptions.UsernameExistsException as e:
        return {
                "statusCode": 400,
                "message" : "Username already exists",
            }
        
        
    except cognito_idp_client.exceptions.InvalidPasswordException as e:
        return {
                "statusCode": 400,
                "message" : "Password should have Caps,\
                          Special chars, Numbers",
            }
        
    except cognito_idp_client.exceptions.UserLambdaValidationException as e:
        return {
                "statusCode": 400,
                "message" : "Username already exists",
            }
    
    except Exception as e:
            return {
                "statusCode": 500,
                "message" : str(e),
            }
    
    return {
            "statusCode": 200,
            "isBase64Encoded": False,
            "headers": {},
            "content-type": "application/json",
            "body": json.dumps(event['body'])
    }
    