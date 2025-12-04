# Retrieves a secret from AWS Secrets Manager using the ARN
import boto3
import json
import base64

def get_secret(client: boto3.client, secret_arn: str) -> dict:
    """
    Retrieves a secret from AWS Secrets Manager using the ARN

    Args:
        client: The boto3 client to use
        secret_arn: The ARN of the secret to retrieve

    Returns:
        dict: The secret
    """
    
    try:
        response = client.get_secret_value(SecretId=secret_arn)
    except Exception as e:
        raise e

    # Decrypts secret using the associated KMS key
    if 'SecretString' in response:
      return json.loads(response['SecretString'])
    elif 'SecretBinary' in response:
      return base64.b64decode(response['SecretBinary']).decode('utf-8')
    else:
      raise ValueError(f"Secret {secret_arn} is not a valid secret")