import boto3
import uuid
import os
from decimal import Decimal
from datetime import datetime

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb", region_name=str(os.environ["REGION_NAME"]))
dynamodb_client = boto3.client("dynamodb")
statistics_table = dynamodb.Table(str(os.environ["STATISTICS_TABLE"]))
air_pollution_table = dynamodb.Table(str(os.environ["OPEN_DATA_TABLE"]))


def handle_processing(event, context):
    decoded_data, stations, components = fetch_data(event=event)
    statistics = init_statistics_dict(stations=stations, components=components)

    try:
        first = True
        for row in decoded_data:
            if first:
                first = False
            else:
                row_data = row.split(";")
                date_time = row_data[0]
                station_id, component_id, value = extract_row(row_data=row_data)

                # air_pollution_table.put_item(
                #     Item={
                #         "id": str(uuid.uuid4()),
                #         "station_id": station_id,
                #         "component_id": component_id,
                #         "date_time": date_time,
                #         "value": value,
                #     }
                # )

                if (station_id, component_id) not in statistics:
                    # print("Tuple is missing in statistics...")
                    # print("Tuple -> ", (station_id, component_id))
                    continue

                stats_values = statistics[(station_id, component_id)]
                statistics[(station_id, component_id)] = process(
                    stats_values=stats_values, value=value
                )

        year = extract_year(date_time)

        print("Finished inserting into " + str(os.environ["OPEN_DATA_TABLE"]) + "...")
        save_statistics(statistics, year)
    except (
        dynamodb_client.exceptions.ResourceNotFoundException
    ) as table_not_found_exception:
        return "ERROR: Unable to locate DynamoDB some of the tables..."

    return {"statusCode": 200, "body": "Processing data finished successfully..."}


def extract_year(dt_string):
    dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
    return dt.year


def save_statistics(statistics, year):
    print("Statistics len -> ", len(statistics))
    for key, value in statistics.items():
        statistics_table.put_item(
            Item={
                "id": str(uuid.uuid4()),
                "station_id": key[0],
                "component_id": key[1],
                "year": str(year),
                "max_value": Decimal(str(value["max"])),
                "min_value": Decimal(str(value["min"]))
                if value["min"] is not None
                else "None",
                "avg_value": Decimal(str(value["avg"])),
            }
        )
    print("Finished inserting into " + str(os.environ["STATISTICS_TABLE"]) + "...")


def process(stats_values, value):
    value = round(float(value), 2)
    stats_values["count"] += 1
    stats_values["val_sum"] += value
    stats_values["avg"] = round(stats_values["val_sum"] / stats_values["count"], 2)

    if stats_values["max"] < value:
        stats_values["max"] = value
    if stats_values["min"] is None or stats_values["min"] > value:
        stats_values["min"] = value

    return stats_values


def extract_row(row_data):
    value = row_data[3]
    station_id = row_data[1]
    component_id = row_data[2]
    return station_id, component_id, value


def fetch_data(event):
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    file = s3_client.get_object(Bucket=bucket_name, Key=key)
    data = boundary_wrapper = file["Body"].read().decode("utf-8")
    boundary = boundary_wrapper.split("\r\nContent-Disposition: form-data;")[0]
    decoded_data = (
        data.split(boundary)[1].split("Content-Type: text/csv")[1].split("\r\n")
    )
    decoded_data = [item for item in decoded_data if item]

    stations = dynamodb.Table("station").scan()["Items"]
    components = dynamodb.Table("component").scan()["Items"]

    return decoded_data, stations, components


def init_statistics_dict(stations, components):
    statistics = {}
    for station in stations:
        for component in components:
            statistics |= {
                (str(int(station["id"])), str(int(component["id"]))): {
                    "max": 0,
                    "min": None,
                    "avg": 0.0,
                    "val_sum": 0.0,
                    "count": 0,
                }
            }
    return statistics
