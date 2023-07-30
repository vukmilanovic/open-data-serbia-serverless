import boto3
from boto3.dynamodb.conditions import Attr
import json
import os
from botocore.exceptions import ClientError
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name=str(os.environ["REGION_NAME"]))


def handle_data_fetching(event, context):
    open_data_table = dynamodb.Table(str(os.environ["OPEN_DATA_TABLE"]))
    statistics_table = dynamodb.Table(str(os.environ["STATISTICS_TABLE"]))
    station_table = dynamodb.Table(str(os.environ["STATION_TABLE"]))
    component_table = dynamodb.Table(str(os.environ["COMPONENT_TABLE"]))
    params = event["queryStringParameters"]

    scan_template = {
        "FilterExpression": Attr("station_id").eq(params["station_id"])
        & Attr("component_id").eq(params["component_id"]),
    }
    partial_scan_template = {
        "FilterExpression": Attr("station_id").eq(params["station_id"]),
    }

    open_data = []
    statistics_data = []
    station = station_table.get_item(Key={"id": int(params["station_id"])})
    component = {}

    try:
        if StringIsNotNull(params["component_id"]):
            # open_data = fetch(scan_template, open_data_table)
            statistics_data = fetch(scan_template, statistics_table)
            component = component_table.get_item(
                Key={"id": int(params["component_id"])}
            )
        else:
            # open_data = fetch(partial_scan_template, open_data_table)
            statistics_data = fetch(partial_scan_template, statistics_table)
    except ClientError as err:
        raise

    response = {
        "open_data": open_data,
        "statistics_data": statistics_data,
        "component": component,
        "station": station,
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response, cls=DecimalEncoder),
    }


def fetch(scan_template, table):
    data = []
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_template["ExclusiveStartKey"] = start_key
        response = table.scan(**scan_template)
        data.extend(response.get("Items", []))
        start_key = response.get("LastEvaluatedKey", None)
        done = start_key is None
    return data


def StringIsNotNull(value):
    return value is not None and len(value) > 0


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)
