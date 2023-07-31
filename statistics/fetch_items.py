import boto3
from botocore.exceptions import ClientError
import os
import json
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name=str(os.environ["REGION_NAME"]))


def handle_fetching(event, context):
    station_table = dynamodb.Table(str(os.environ["STATION_TABLE"]))
    component_table = dynamodb.Table(str(os.environ["COMPONENT_TABLE"]))

    try:
        stations = station_table.scan()
        components = component_table.scan()
    except ClientError as err:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": err,
        }

    response = {
        "stations": stations,
        "components": components,
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": json.dumps(response, cls=DecimalEncoder),
    }


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)
