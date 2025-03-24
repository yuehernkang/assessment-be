import sys
import os
import json
import unittest
from unittest.mock import patch
import boto3
from moto import mock_aws
from decimal import Decimal
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from lambda_functions.getInventory import lambda_handler  # Fix import path
TABLE_NAME = "BeStack-InventoryCFCBEC24-1AFGTO0FT9LS"

class TestGetInventoryLambda(unittest.TestCase):
    @mock_aws
    def setUp(self):
        self.dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        self.table = self.dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "updated_at", "AttributeType": "N"},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'skIndex',
                    'KeySchema': [
                        {'AttributeName': 'sk', 'KeyType': 'HASH'},
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                },
                {
                    'IndexName': 'dateIndex',
                    'KeySchema': [
                        {'AttributeName': 'sk', 'KeyType': 'HASH'},
                        {'AttributeName': 'updated_at', 'KeyType': 'RANGE'},
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                }
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
        self.table.wait_until_exists()

        # Insert test data
        self.table.put_item(
            Item={
                "pk": "ITEM#1",
                "sk": "ITEM",
                "name": "Test Item 1",
                "price": Decimal("10.99"),
                "category": "electronics",
                "updated_at": 1742400000
            }
        )
        self.table.put_item(
            Item={
                "pk": "ITEM#2",
                "sk": "ITEM",
                "name": "Test Item 2",
                "price": Decimal("20.99"),
                "category": "books",
                "updated_at": 1742450000
            }
        )

    @mock_aws
    def test_get_all_items(self):
        event = {"queryStringParameters": None}
        response = lambda_handler(event, None)
        print("test_get_all_items response:", response)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        print("test_get_all_items body:", body)
        self.assertIn("items", body)
        self.assertIn("total_price", body)
        self.assertEqual(len(body["items"]), 2)
        self.assertEqual(body["total_price"], "31.98")

    @mock_aws
    def test_get_items_by_date_range(self):
        event = {
            "queryStringParameters": {
                "dt_from": "1742400000",
                "dt_to": "1742450000"
            }
        }
        response = lambda_handler(event, None)
        print("test_get_items_by_date_range response:", response)
        print("test_get_items_by_date_range body:", json.loads(response["body"]))
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(len(body["items"]), 2)

    @mock_aws
    def test_get_items_by_category(self):
        event = {
            "queryStringParameters": {
                "dt_from": "1742400000",
                "dt_to": "1742450000",
                "category": "electronics"
            }
        }
        response = lambda_handler(event, None)
        print("test_get_items_by_category response:", response)
        print("test_get_items_by_category body:", json.loads(response["body"]))
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["items"][0]["category"], "electronics")

    @mock_aws
    def test_error_handling(self):
        event = {
            "queryStringParameters": {
                "dt_from": "invalid",
                "dt_to": "invalid"
            }
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        error_body = json.loads(response["body"])
        self.assertIn("error", error_body)
        self.assertIn("invalid literal for int()", error_body["error"])

if __name__ == '__main__':
    unittest.main()
