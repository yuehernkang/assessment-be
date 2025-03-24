import json
import boto3
import time
import uuid
from decimal import Decimal
# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "BeStack-InventoryCFCBEC24-1AFGTO0FT9LS"  # Change this to your actual table name
table = dynamodb.Table(TABLE_NAME)
def decimal_to_str(obj):
    """Helper function to convert Decimal to string for JSON serialization."""
    if isinstance(obj, Decimal):
        return str(obj)  # Convert to string
    if isinstance(obj, dict):
        return {k: decimal_to_str(v) for k, v in obj.items()}  # Recursively process dict
    if isinstance(obj, list):
        return [decimal_to_str(i) for i in obj]  # Recursively process lists
    return obj

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        name = body.get("name")
        category = body.get("category")
        price = body.get("price")

        if not name or not category or price is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: name, category, or price"})
            }

        try:
            price_str = f"{Decimal(price):.2f}"
        except Exception:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid price format"})
            }

        pk = name  
        sk = "ITEM"  
        updated_at = int(time.time())
        response = table.update_item(
            Key={"pk": pk, "sk": sk},
            UpdateExpression="SET price = :price, updated_at = :updated_at, id = :id, category = :category",
            ExpressionAttributeValues={
                ":price": price_str,
                ":updated_at": updated_at,
                ":id": str(uuid.uuid4()),
                ":category": category
            },
            ReturnValues="ALL_NEW"  # Returns the updated item
        )
        updated_item = response.get("Attributes", {})
        updated_item_clean = decimal_to_str(updated_item)
        item_id = updated_item_clean.get("id", "")
        return {
            "id": item_id  
        }


    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
