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

        try:
            # Use environment variables for AWS credentials
            dynamodb = boto3.resource('dynamodb')
            table_name = 'usage-logs'  # Change to your table name
            table = dynamodb.Table(table_name)
            
            # Extract request_id and user_id from metadata
            request_id = request_metadata.get('request_id', 'unknown')
            user_id = request_metadata.get('user_id', 'unknown')
            
            # Extract token data from nested structure
            total_tokens = 0
            prompt_tokens = 0
            completion_tokens = 0
            total_cost = 0.0
            time_taken = 0.0
            
            # token_dict often has nested provider data
            for provider, data in token_dict.items():
                if isinstance(data, dict):
                    total_tokens += data.get('total_tokens', 0)
                    prompt_tokens += data.get('prompt_tokens', 0)
                    completion_tokens += data.get('completion_tokens', 0)
                    total_cost += data.get('total_cost', 0.0)
                    time_taken += data.get('time_taken_in_seconds', 0.0)
            
            # Prepare item for DynamoDB
            item = {
                'PK': user_id,
                'SK': f"{user_id}#{request_id}",
                'request_id': request_id,
                'user_id': user_id,
                'total_tokens': total_tokens,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_cost': str(total_cost),
                'time_taken_in_seconds': str(time_taken),
                'token_usage': json.dumps(token_dict),
                'request_metadata': json.dumps(request_metadata)
            }
            
            # Write to DynamoDB
            table.put_item(Item=item)
            
            print(f"Successfully logged usage for request {request_id}")
            
        except ClientError as e:
            print(f"Error logging to DynamoDB: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
