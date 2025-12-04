import pytest
import json
import boto3
from notifications.utils.secrets import get_secret
from unittest.mock import MagicMock


def test_get_secret():
    secret_arn = 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test/test'
    
    # Create a mock client and mock the get_secret_value method
    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {
        'SecretString': json.dumps({'test': 'test'})
    }
    
    secret = get_secret(mock_client, secret_arn)
    assert secret == {'test': 'test'}
    assert mock_client.get_secret_value.call_count == 1
    assert mock_client.get_secret_value.call_args[1]['SecretId'] == secret_arn