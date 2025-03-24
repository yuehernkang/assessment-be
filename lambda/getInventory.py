import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

TABLE_NAME = "BeStack-InventoryCFCBEC24-1AFGTO0FT9LS"
INDEX_NAME = "skIndex" 

# Remove hardcoded resource creation and make it injectable for testing
def get_table():
    dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
    return dynamodb.Table(TABLE_NAME)

def decimal_to_str(obj):
    """Convert Decimal values to strings for JSON serialization."""
    if isinstance(obj, Decimal):
        return str(obj)  # Convert Decimal to string
    if isinstance(obj, dict):
        return {k: decimal_to_str(v) for k, v in obj.items()}  # Recursively process dict
    if isinstance(obj, list):
        return [decimal_to_str(i) for i in obj]  # Recursively process lists
    return obj

def calculate_total_price(items):
    """Calculate the total price from a list of items."""
    total_price = sum(Decimal(item.get('price', '0')) for item in items)
    return f"{total_price:.2f}"

def lambda_handler(event, context):
    query_params = event.get("queryStringParameters", {})
    table = get_table()

    try:
        if not query_params:
            print('0')
            response = table.query(
                IndexName=INDEX_NAME,
                KeyConditionExpression=Key("sk").eq("ITEM")
            )
        else:
            print('1')
            dt_from = int(query_params.get('dt_from', 0))
            dt_to = int(query_params.get('dt_to', 0))
            print(dt_to, dt_from)
            category = query_params.get('category')
            
            if dt_from and dt_to:
                if category:
                    #Got date and category
                    print('3')
                    response = table.query(
                        IndexName="dateIndex",
                        KeyConditionExpression=Key("sk").eq("ITEM") & Key("updated_at").between(dt_from, dt_to),
                        FilterExpression="category = :category",
                        ExpressionAttributeValues={
                            ':category': category
                        }
                    )
                else:
                    #Got date but no category
                    print('4')
                    response = table.query(
                        IndexName="dateIndex",
                        KeyConditionExpression=Key("sk").eq("ITEM") & Key("updated_at").between(dt_from, dt_to)
                    )
            else:
                print('5')
                if category:
                    # No date but got category
                    response = table.query(
                        IndexName=INDEX_NAME,
                        KeyConditionExpression=Key("sk").eq("ITEM"),
                        FilterExpression="category = :category",
                        ExpressionAttributeValues={
                            ':category': category
                        }
                    )
                else:
                    response = table.query(
                        IndexName=INDEX_NAME,
                        KeyConditionExpression=Key("sk").eq("ITEM"),
                    )

        items = response.get("Items", [])
        items_clean = decimal_to_str(items)
        total_price_str = calculate_total_price(items)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "items": items_clean,
                "total_price": total_price_str
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
