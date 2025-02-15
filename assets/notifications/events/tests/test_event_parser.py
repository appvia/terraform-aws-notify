from datetime import datetime
from notifications.events import EventParser, NormalizedEvent, EventType
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
                
    def test_parse_cloudwatch_eventbridge_alarm(self):
        alarm_message = {
            "version": "0",
            "id": "c4c1c1c9-6542-e61b-6ef0-8c4d36933a92",
            "detail-type": "CloudWatch Alarm State Change",
            "source": "aws.cloudwatch",
            "account": "123456789012",
            "time": "2019-10-02T17:04:40Z",
            "region": "us-east-1",
            "resources": [
                "arn:aws:cloudwatch:us-east-1:123456789012:alarm:ServerCpuTooHigh"
            ],
            "detail": {
                "alarmName": "ServerCpuTooHigh",
                "configuration": {
                    "description": "Goes into alarm when server CPU utilization is too high!",
                    "metrics": [
                        {
                            "id": "30b6c6b2-a864-43a2-4877-c09a1afc3b87",
                            "metricStat": {
                                "metric": {
                                "dimensions": {
                                    "InstanceId": "i-12345678901234567"
                                },
                                "name": "CPUUtilization",
                                "namespace": "AWS/EC2"
                                },
                                "period": 300,
                                "stat": "Average"
                            },
                            "returnData": "true"
                        }
                    ]
                },
                "previousState": {
                    "reason": "Threshold Crossed: 1 out of the last 1 datapoints [0.0666851903306472 (01/10/19 13:46:00)] was not greater than the threshold (50.0) (minimum 1 datapoint for ALARM -> OK transition).",
                    "reasonData": "{\"version\":\"1.0\",\"queryDate\":\"2019-10-01T13:56:40.985+0000\",\"startDate\":\"2019-10-01T13:46:00.000+0000\",\"statistic\":\"Average\",\"period\":300,\"recentDatapoints\":[0.0666851903306472],\"threshold\":50.0}",
                    "timestamp": "2019-10-01T13:56:40.987+0000",
                    "value": "OK"
                },
                "state": {
                    "reason": "Threshold Crossed: 1 out of the last 1 datapoints [99.50160229693434 (02/10/19 16:59:00)] was greater than the threshold (50.0) (minimum 1 datapoint for OK -> ALARM transition).",
                    "reasonData": "{\"version\":\"1.0\",\"queryDate\":\"2019-10-02T17:04:40.985+0000\",\"startDate\":\"2019-10-02T16:59:00.000+0000\",\"statistic\":\"Average\",\"period\":300,\"recentDatapoints\":[99.50160229693434],\"threshold\":50.0}",
                    "timestamp": "2019-10-02T17:04:40.989+0000",
                    "value": "ALARM"
                }
            }
        }

        test_event = self.get_sns_event(alarm_message)
        result = self.parser.parse_event(test_event)

        assert isinstance(result, NormalizedEvent)
        assert result.event_type == EventType.CLOUDWATCH
        assert result.severity == "critical"
        assert result.title == "ServerCpuTooHigh"
        assert result.region == "us-east-1"
        assert result.description == "Goes into alarm when server CPU utilization is too high!"
        assert result.source == "CloudWatch"
        assert result.details["resources"] == ["arn:aws:cloudwatch:us-east-1:123456789012:alarm:ServerCpuTooHigh"]
        assert result.details["reason"] == "Threshold Crossed: 1 out of the last 1 datapoints [99.50160229693434 (02/10/19 16:59:00)] was greater than the threshold (50.0) (minimum 1 datapoint for OK -> ALARM transition)."
        assert result.details["current_state"] == "ALARM"

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
        
        print("result", result)

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
                    "Id": "arn:aws:securityhub:us-east-1:111122223333:subscription/aws-foundational-security-best-practices/v/1.0.0/EC2.1/finding/a1b2c3d4-5678-90ab-cdef-EXAMPLE11111",
                    "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
                    "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/EC2.1",
                    "AwsAccountId": "111122223333",
                    "Types": [
                        "Software and Configuration Checks/Industry and Regulatory Standards/AWS-Foundational-Security-Best-Practices"
                    ],
                    "Severity": {
                        "Label": "MEDIUM"
                    },
                    "Title": "EC2 instances should have IMDSv2 enabled",
                    "Description": "This AWS control checks whether your EC2 instance metadata version is configured with Instance Metadata Service Version 2 (IMDSv2).",
                    "CreatedAt": "2020-08-06T02:18:23.995Z",
                    "UpdatedAt": "2020-08-06T02:18:23.995Z",
                    "Remediation": {
                        "Recommendation": {
                            "Text": "For directions on how to fix this issue, please consult the AWS Security Hub Foundational Security Best Practices documentation."
                        }
                    },
                    "Resources": [{
                        "Type": "AwsS3Bucket",
                        "Id": "arn:aws:s3:::example-bucket",
                        "Partition": "aws",
                        "Region": "us-east-1",
                        "Details": {
                            "AwsS3Bucket": {
                                "OwnerId": "111122223333",
                                "CreatedAt": "2023-01-01T00:00:00.000Z",
                                "ServerSideEncryptionConfiguration": {
                                    "Rules": [{
                                        "ApplyServerSideEncryptionByDefault": {
                                            "SSEAlgorithm": "None"
                                        }
                                    }]
                                }
                            }
                        }
                    }],
                    "Workflow": {
                        "Status": "NEW"
                    }
                }]
            },
        }

        test_event = self.get_sns_event(security_finding)
        result = self.parser.parse_event(test_event)

        assert isinstance(result, NormalizedEvent)
        assert result.event_type == EventType.SECURITY_HUB
        assert result.severity == "medium"
        assert result.title == "EC2 instances should have IMDSv2 enabled"
        assert result.description == "This AWS control checks whether your EC2 instance metadata version is configured with Instance Metadata Service Version 2 (IMDSv2)."
        assert result.source == "SecurityHub"
        assert result.details["remediation"] == "For directions on how to fix this issue, please consult the AWS Security Hub Foundational Security Best Practices documentation."
        assert result.details["status"] == "NEW"
        assert result.details["resources"] == [{
            "type": "AwsS3Bucket",
            "region": "us-east-1",
            "resource_id": "arn:aws:s3:::example-bucket",
        }]
        

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
                            "blocked": False,
                        },
                    },
                },
                "resource": {
                    "resourceType": "Instance",
                    "instanceDetails": {
                        "instanceId": "i-1234567890abcdef0",
                        "instanceType": "t2.micro",
                        "launchTime": "2024-01-01T00:00:00Z",
                        "instanceState": "running",
                    },
                },
            },
        }

        test_event = self.get_sns_event(guardduty_finding)
        result = self.parser.parse_event(test_event)

        assert isinstance(result, NormalizedEvent)
        assert result.event_type == EventType.GUARDDUTY
        assert result.severity == "critical"  # Based on severity 8.0
        assert result.title == "Suspicious Activity"
        assert result.description == "Potential security threat"
        assert result.source == "GuardDuty"
        assert result.details["resource_type"] == "Instance"
        assert result.details["region"] == "us-west-2"

    def test_parse_unknown_event(self):
        """Test handling of an unknown event type"""
        unknown_message = {
            "Subject": "Unknown Event Type",
            "Message": json.dumps({"some": "data"}),
        }
        test_event = self.get_sns_event(unknown_message)

        with pytest.raises(ValueError, match="Unknown event type"):
            self.parser.parse_event(test_event)
