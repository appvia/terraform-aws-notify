from datetime import datetime
from ..events import EventParser, NormalizedEvent, EventType
import pytest
import json

class TestEventParser:
    def setup_method(self):
        self.parser = EventParser()
        
    def get_sns_event(self, message):
        """Helper to wrap a message in SNS format"""
        return {
            "Records": [
                {
                    "EventSource": "aws:sns",
                    "Sns": {
                        "Message": json.dumps(message),
                    },
                },
            ],
        }

    def test_non_sns_event(self):
        """Test that non-SNS events raise an error"""
        test_events = [
            {},  # Empty event
            {"Records": []},  # Empty records
            {"Records": [{"EventSource": "aws:sqs"}]},  # Wrong source
            {"detail": {"some": "data"}},  # Direct event
        ]
        
        for event in test_events:
            with pytest.raises(ValueError, match="Unknown event source, not aws:sns"):
                self.parser.parse_event(event)

    def test_parse_cloudwatch_alarm(self):
        """Test parsing of CloudWatch Alarm events"""
        alarm_message = {
            "AlarmName": "Test Alarm",
            "AlarmDescription": "Test Description",
            "NewStateValue": "ALARM",
            "OldStateValue": "OK",
            "StateChangeTime": "2024-01-01T00:00:00Z",
            "Region": "us-west-2",
            "NewStateReason": "Threshold Crossed",
        }
        test_event = self.get_sns_event(alarm_message)
        
        result = self.parser.parse_event(test_event)
        
        assert isinstance(result, NormalizedEvent)
        assert result.event_type == EventType.CLOUDWATCH
        assert result.severity == "critical"
        assert result.title == "Test Alarm"
        assert result.description == "Test Description"
        assert result.source == "CloudWatch"
        assert result.details["reason"] == "Threshold Crossed"
        assert result.details["current_state"] == "ALARM"

    def test_parse_security_hub(self):
        """Test parsing of SecurityHub events"""
        security_finding = {
            "version": "0",
            "id": "12345678-1234-1234-1234-123456789012",
            "detail-type": "Security Hub Findings - Imported",
            "source": "aws.securityhub",
            "account": "123456789012",
            "time": "2024-01-01T00:00:00Z",
            "region": "us-west-2",
            "detail": {
                "findings": [{
                    "SchemaVersion": "2018-10-08",
                    "Id": "arn:aws:securityhub:us-west-2:123456789012:finding/12345678-1234-1234-1234-123456789012",
                    "ProductArn": "arn:aws:securityhub:us-west-2::product/aws/securityhub",
                    "Title": "Security Issue",
                    "Description": "Security Description",
                    "Severity": {
                        "Label": "HIGH",
                        "Original": "8.0"
                    },
                    "UpdatedAt": "2024-01-01T00:00:00Z",
                    "Region": "us-west-2",
                    "Resources": [{
                        "Type": "AwsEc2Instance",
                        "Id": "arn:aws:ec2:us-west-2:123456789012:instance/i-1234567890abcdef0"
                    }],
                    "Compliance": {"Status": "FAILED"},
                    "WorkflowState": "NEW",
                    "RecordState": "ACTIVE"
                }]
            }
        }
        
        test_event = self.get_sns_event(security_finding)
        result = self.parser.parse_event(test_event)
        
        assert isinstance(result, NormalizedEvent)
        assert result.event_type == EventType.SECURITY_HUB
        assert result.severity == "high"
        assert result.title == "Security Issue"
        assert result.description == "Security Description"
        assert result.source == "SecurityHub"
        assert result.details["resource"] == "AwsEc2Instance"
        assert result.details["region"] == "us-west-2"
        assert result.details["compliance_status"] == "FAILED"
        
        
#
    def test_parse_cost_anomaly(self):
        """Test parsing of Cost Anomaly events"""
        anomaly_message = {
            "version": "0",
            "id": "12345678-1234-1234-1234-123456789012",
            "detail-type": "Cost Anomaly Detection",
            "source": "aws.ce",
            "account": "123456789012",
            "time": "2024-01-01T00:00:00Z",
            "region": "us-west-2",
            "detail": {
                "anomalyDetails": {
                    "totalImpact": "150.00",
                    "rootCauses": ["Increased EC2 usage"],
                    "anomalyStartTime": "2024-01-01T00:00:00Z",
                    "anomalyEndTime": "2024-01-01T01:00:00Z",
                    "region": "us-west-2",
                    "service": "EC2",
                },
                "monitorArn": "arn:aws:ce::monitor/1"
            }
        }
        test_event = self.get_sns_event(anomaly_message)
        
        result = self.parser.parse_event(test_event)
        
        assert isinstance(result, NormalizedEvent)
        assert result.event_type == EventType.COST_ANOMALY
        assert result.severity == "high"  # Based on $150 impact
        assert "Cost Anomaly: $150.00 Impact Detected" in result.title
        assert result.source == "AWS Cost Anomaly Detection"
        assert result.details["impact"] == 150.00
        assert result.details["service"] == "EC2"
        assert result.details["region"] == "us-west-2" 
        assert result.details["monitor_arn"] == "arn:aws:ce::monitor/1"
        assert result.details["root_causes"] == ["Increased EC2 usage"]

    def test_parse_aws_budgets(self):
        """Test parsing of AWS Budgets events"""
        budget_message = {
            "version": "0",
            "id": "12345678-1234-1234-1234-123456789012",
            "detail-type": "Budget Status Update",
            "source": "aws.budgets",
            "account": "123456789012",
            "time": "2024-01-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "budgetName": "Test Budget",
                "accountId": "123456789012",
                "budgetType": "COST",
                "actualSpend": {"amount": "900.0", "unit": "USD"},
                "budgetLimit": {"amount": "1000.0", "unit": "USD"},
                "thresholdExceeded": 90.0,
                "timeUnit": "MONTHLY",
                "notificationType": "ACTUAL"
            }
        }
        test_event = self.get_sns_event(budget_message)
        result = self.parser.parse_event(test_event)
        
        assert isinstance(result, NormalizedEvent)
        assert result.event_type == EventType.AWS_BUDGETS
        assert result.severity == "high"  # Based on 90% threshold
        assert "90.0% threshold" in result.title
        assert result.source == "AWS Budgets"
        assert result.details["actual_spend"] == 900
        assert result.details["budget_limit"] == 1000

    def test_parse_guardduty(self):
        """Test parsing of GuardDuty events"""
        guardduty_finding = {
            "version": "0",
            "id": "12345678-1234-1234-1234-123456789012",
            "detail-type": "GuardDuty Finding",
            "source": "aws.guardduty",
            "account": "123456789012",
            "time": "2024-01-01T00:00:00Z",
            "region": "us-west-2",
            "detail": {
                "schemaVersion": "2.0",
                "accountId": "123456789012",
                "region": "us-west-2",
                "partition": "aws",
                "id": "finding-id-1",
                "arn": "arn:aws:guardduty:us-west-2:123456789012:detector/12345678/finding/finding-id-1",
                "type": "UnauthorizedAccess:EC2/SSHBruteForce",
                "title": "Suspicious Activity",
                "description": "Potential security threat",
                "severity": 8.0,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
                "service": {
                    "serviceName": "guardduty",
                    "detectorId": "12345678",
                    "action": {
                        "actionType": "NETWORK_CONNECTION",
                        "networkConnectionAction": {
                            "connectionDirection": "INBOUND",
                            "protocol": "TCP",
                            "blocked": False
                        }
                    }
                },
                "resource": {
                    "resourceType": "Instance",
                    "instanceDetails": {
                        "instanceId": "i-1234567890abcdef0",
                        "instanceType": "t2.micro",
                        "launchTime": "2024-01-01T00:00:00Z",
                        "instanceState": "running"
                    }
                }
            }
        }
        
        test_event = self.get_sns_event(guardduty_finding)
        result = self.parser.parse_event(test_event)
        
        assert isinstance(result, NormalizedEvent)
        assert result.event_type == EventType.GUARD_DUTY
        assert result.severity == "high"  # Based on severity 8.0
        assert result.title == "Suspicious Activity"
        assert result.description == "Potential security threat"
        assert result.source == "GuardDuty"
        assert result.details["resource_type"] == "Instance"
        assert result.details["region"] == "us-west-2"

    def test_parse_unknown_event(self):
        """Test handling of an unknown event type"""
        unknown_message = {
            "Subject": "Unknown Event Type",
            "Message": json.dumps({"some": "data"})
        }
        test_event = self.get_sns_event(unknown_message)
        
        with pytest.raises(ValueError, match="Unknown event type"):
            self.parser.parse_event(test_event)
