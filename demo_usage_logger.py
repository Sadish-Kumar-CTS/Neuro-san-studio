# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT

import json
from typing import Any
from typing import Dict
import boto3
from botocore.exceptions import ClientError

from neuro_san.interfaces.usage_logger import UsageLogger


class DemoUsageLogger(UsageLogger):
    """
    Implementation of the UsageLogger interface that logs usage stats to DynamoDB.
    """

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = 'usage-logs'  # Change to your table name
        self.table = self.dynamodb.Table(self.table_name)

    async def log_usage(self, token_dict: Dict[str, Any], request_metadata: Dict[str, Any]):
        """
        Logs the token usage to DynamoDB.
        """
        try:
            # Extract request_id and user_id from metadata
            request_id = request_metadata.get('request_id', 'unknown')
            user_id = request_metadata.get('user_id', 'unknown')
            
            # Create composite sort key
            sort_key = f"{user_id}#{request_id}"
            
            # Prepare item for DynamoDB
            item = {
                'requestid': request_id,  # PK
                'userid_requestid': sort_key,  # SK
                'token_usage': json.dumps(token_dict),
                'request_metadata': json.dumps(request_metadata)
            }
            
            # Write to DynamoDB
            self.table.put_item(Item=item)
            
            print(f"Successfully logged usage for request {request_id}")
            
        except ClientError as e:
            print(f"Error logging to DynamoDB: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
