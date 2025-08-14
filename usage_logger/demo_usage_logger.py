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
      Implementation of the UsageLogger interface that merely spits out
      usage stats to the logger.
    """
    async def log_usage(self, token_dict: Dict[str, Any], request_metadata: Dict[str, Any]):
        """
          Logs the token usage for external capture.
 
        :param token_dict: A dictionary that describes overall token usage for a completed request.
 
                For each class of LLM (more or less equivalent to an LLM provider), there will
                be one key whose value is a dictionary with some other keys:
 
                Relevant keys include:
                    "completion_tokens" - Integer number of tokens generated in response to LLM input
                    "prompt_tokens" - Integer number of tokens that provide input to an LLM
                    "time_taken_in_seconds" - Float describing the total wall-clock time taken for the request.
                    "total_cost" -  An estimation of the cost in USD of the request.
                                    This number is to be taken with a grain of salt, as these estimations
                                    can come from model costs from libraries instead of directly from
                                    providers.
                    "total_tokens" - Total tokens used for the request.
 
                More keys can appear, but should not be counted on.
                The ones listed above contain potentially salient information for usage logging purposes.
 
        :param request_metadata: A dictionary of filtered request metadata whose keys contain
                identifying information for the usage log.
        """
        print("Logging usage to DynamoDB...")
        print(f"Token usage: {token_dict}")

        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        self.table_name = 'usage-logs'  # Change to your table name
        self.table = self.dynamodb.Table(self.table_name)

        try:
            # Extract request_id and user_id from metadata
            request_id = request_metadata.get('request_id', 'unknown')
            user_id = request_metadata.get('user_id', 'unknown')
            
            # Create composite sort key
            sort_key = f"{user_id}#{request_id}"
            
            # Prepare item for DynamoDB
            item = {
                'PK': user_id,  # PK
                'SK': f"{user_id}#{request_id}",  # SK
                'token_usage': json.dumps(token_dict),
                'request_metadata': json.dumps(request_metadata),
                'user_id': user_id,
            'total_tokens': token_dict.get('total_tokens', 0),
            'prompt_tokens': token_dict.get('prompt_tokens', 0),
            'completion_tokens': token_dict.get('completion_tokens', 0),
            'successful_requests': token_dict.get('successful_requests', 0),
            'total_cost': str(token_dict.get('total_cost', 0.0)),  # Decimal as string
            'time_taken_in_seconds': str(token_dict.get('time_taken_in_seconds', 0.0)),
            'caveats': token_dict.get('caveats', [])
            }
            
            # Write to DynamoDB
            self.table.put_item(Item=item)
            
            print(f"Successfully logged usage for request {request_id}")
            
        except ClientError as e:
            print(f"Error logging to DynamoDB: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
