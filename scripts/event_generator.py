#!/usr/bin/env python3

import argparse
import json
import sys
import boto3


class TestEventGenerator:
    """
    Helper class to generate sample AWS event payloads for testing
    """

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

    def get_security_hub_event(self):
        """Helper to return a sample Security Hub event payload"""
        return {
            "version": "0",
            "id": "CWE-2",
            "detail-type": "Security Hub Findings - Imported",
            "source": "aws.securityhub",
            "account": "111122223333",
            "time": "2019-04-11T21:52:17Z",
            "region": "us-east-1",
            "detail": {
                "findings": [
                    {
                        "SchemaVersion": "2018-10-08",
                        "Id": "arn:aws:securityhub:us-east-1:111122223333:subscription/aws-foundational-security-best-practices/v/1.0.0/EC2.1/finding/a1b2c3d4-5678-90ab-cdef-EXAMPLE11111",
                        "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
                        "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/EC2.1",
                        "AwsAccountId": "111122223333",
                        "Types": [
                            "Software and Configuration Checks/Industry and Regulatory Standards/AWS-Foundational-Security-Best-Practices"
                        ],
                        "Severity": {"Label": "MEDIUM"},
                        "Title": "EC2 instances should have IMDSv2 enabled",
                        "Description": "This AWS control checks whether your EC2 instance metadata version is configured with Instance Metadata Service Version 2 (IMDSv2).",
                        "CreatedAt": "2020-08-06T02:18:23.995Z",
                        "UpdatedAt": "2020-08-06T02:18:23.995Z",
                        "Remediation": {
                            "Recommendation": {
                                "Text": "For directions on how to fix this issue, please consult the AWS Security Hub Foundational Security Best Practices documentation."
                            }
                        },
                    }
                ]
            },
        }

    def get_security_hub_resource_event(self):
        """Helper to return a sample Security Hub event payload with resource details"""
        return {
            "version": "0",
            "id": "CWE-3",
            "detail-type": "Security Hub Findings - Imported",
            "source": "aws.securityhub",
            "account": "111122223333",
            "time": "2023-04-11T21:52:17Z",
            "region": "us-east-1",
            "detail": {
                "findings": [
                    {
                        "SchemaVersion": "2018-10-08",
                        "Id": "arn:aws:securityhub:us-east-1:111122223333:subscription/aws-foundational-security-best-practices/v/1.0.0/S3.1/finding/b1b2c3d4-5678-90ab-cdef-EXAMPLE22222",
                        "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
                        "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/S3.1",
                        "AwsAccountId": "111122223333",
                        "Types": [
                            "Software and Configuration Checks/Industry and Regulatory Standards/AWS-Foundational-Security-Best-Practices"
                        ],
                        "Resources": [
                            {
                                "Type": "AwsS3Bucket",
                                "Id": "arn:aws:s3:::example-bucket",
                                "Partition": "aws",
                                "Region": "us-east-1",
                                "Details": {
                                    "AwsS3Bucket": {
                                        "OwnerId": "111122223333",
                                        "CreatedAt": "2023-01-01T00:00:00.000Z",
                                        "ServerSideEncryptionConfiguration": {
                                            "Rules": [
                                                {
                                                    "ApplyServerSideEncryptionByDefault": {
                                                        "SSEAlgorithm": "None"
                                                    }
                                                }
                                            ]
                                        },
                                    }
                                },
                            }
                        ],
                        "Severity": {"Label": "HIGH"},
                        "Title": "S3 Bucket should have server-side encryption enabled",
                        "Description": "This AWS control checks whether S3 bucket has server-side encryption enabled.",
                        "CreatedAt": "2023-04-11T21:52:17.995Z",
                        "UpdatedAt": "2023-04-11T21:52:17.995Z",
                        "Remediation": {
                            "Recommendation": {
                                "Text": "Enable server-side encryption for the S3 bucket using AWS KMS keys (SSE-KMS) or S3-managed keys (SSE-S3).",
                                "Url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html",
                            }
                        },
                    }
                ]
            },
        }

    def get_budget_event(self):
        """Helper to return a sample AWS Budget event payload"""
        return {
            "version": "0",
            "id": "cwe-event-id",
            "detail-type": "Budget Threshold Exceeded",
            "source": "aws.budgets",
            "account": "111122223333",
            "time": "2023-12-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "budgetName": "Example Budget",
                "budgetType": "COST",
                "accountId": "111122223333",
                "budgetLimit": {"amount": "1000", "unit": "USD"},
                "actualSpend": {"amount": "1100", "unit": "USD"},
                "timePeriod": {
                    "start": "2023-12-01T00:00:00Z",
                    "end": "2023-12-31T23:59:59Z",
                },
                "thresholdExceeded": "110%",
                "notification": {
                    "notificationType": "ACTUAL",
                    "comparisonOperator": "GREATER_THAN",
                    "threshold": 100,
                },
            },
        }

    def get_cloudwatch_eventbridge_alarm(self):
        """Helper to return a sample CloudWatch EventBridge alarm event payload"""
        return {
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
                                    "dimensions": {"InstanceId": "i-12345678901234567"},
                                    "name": "CPUUtilization",
                                    "namespace": "AWS/EC2",
                                },
                                "period": 300,
                                "stat": "Average",
                            },
                            "returnData": "true",
                        }
                    ],
                },
                "previousState": {
                    "reason": "Threshold Crossed: 1 out of the last 1 datapoints [0.0666851903306472 (01/10/19 13:46:00)] was not greater than the threshold (50.0) (minimum 1 datapoint for ALARM -> OK transition).",
                    "reasonData": '{"version":"1.0","queryDate":"2019-10-01T13:56:40.985+0000","startDate":"2019-10-01T13:46:00.000+0000","statistic":"Average","period":300,"recentDatapoints":[0.0666851903306472],"threshold":50.0}',
                    "timestamp": "2019-10-01T13:56:40.987+0000",
                    "value": "OK",
                },
                "state": {
                    "reason": "Threshold Crossed: 1 out of the last 1 datapoints [99.50160229693434 (02/10/19 16:59:00)] was greater than the threshold (50.0) (minimum 1 datapoint for OK -> ALARM transition).",
                    "reasonData": '{"version":"1.0","queryDate":"2019-10-02T17:04:40.985+0000","startDate":"2019-10-02T16:59:00.000+0000","statistic":"Average","period":300,"recentDatapoints":[99.50160229693434],"threshold":50.0}',
                    "timestamp": "2019-10-02T17:04:40.989+0000",
                    "value": "ALARM",
                },
            },
        }

    def get_cloudwatch_event(self):
        """Helper to return a sample CloudWatch alarm event payload"""
        return {
            "AlarmName": "Test Alarm",
            "AlarmDescription": "Test Description",
            "NewStateValue": "ALARM",
            "OldStateValue": "OK",
            "StateChangeTime": "2024-01-01T00:00:00Z",
            "Region": "us-west-2",
            "NewStateReason": "Threshold Crossed",
        }
        
    def get_kms_deletion_event(self):
        """Helper to return a sample KMS deletion event payload"""
        return {
            "version": "0",
            "id": "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
            "detail-type": "KMS CMK Deletion",
            "source": "aws.kms",
            "account": "123456789012",
            "time": "2016-08-08T01:23:45Z",
            "region": "us-east-1",
            "resources": ["arn:aws:kms:us-east-1:123456789012:key/2812ba3e-1a61-4575-956c-80fe03ed4e56"],
            "detail": {
                "key-id": "2812ba3e-1a61-4575-956c-80fe03ed4e56"
            }
        }

    def get_cost_anomaly_event(self):
        """Helper to return a sample AWS Cost Anomaly event payload"""
        return {
            "version": "0",
            "id": "cwe-event-id",
            "detail-type": "Cost Anomaly Detection Alert",
            "source": "aws.ce",
            "account": "111122223333",
            "time": "2023-12-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "anomalyId": "f4c29b31-a968-4338-a276-12345678abcd",
                "monitorArn": "arn:aws:ce::111122223333:anomalymonitor/f4c29b31-a968-4338-a276-12345678abcd",
                "rootCauses": [
                    {
                        "service": "Amazon EC2",
                        "region": "us-east-1",
                        "linkedAccount": "111122223333",
                        "usageType": "BoxUsage:t3.micro",
                    }
                ],
                "impact": {"maxImpact": 100.00, "totalImpact": 100.00},
                "anomalyStartDate": "2023-12-01T00:00:00Z",
                "anomalyEndDate": "2023-12-01T23:59:59Z",
                "anomalyDetails": {
                    "totalActualSpend": 200.00,
                    "totalExpectedSpend": 100.00,
                    "totalImpact": 100.00,
                    "totalImpactPercentage": 100.00,
                },
            },
        }

    def get_guardduty_event(self):
        """Helper to return a sample GuardDuty finding event payload"""
        return {
            "version": "0",
            "id": "cd2d702e-ab31-411b-9344-793ce56b1bc7",
            "detail-type": "GuardDuty Finding",
            "source": "aws.guardduty",
            "account": "111122223333",
            "time": "2023-12-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "schemaVersion": "2.0",
                "accountId": "111122223333",
                "region": "us-east-1",
                "partition": "aws",
                "id": "sample-id-123",
                "arn": "arn:aws:guardduty:us-east-1:111122223333:detector/123456/finding/sample-id-123",
                "type": "UnauthorizedAccess:EC2/SSHBruteForce",
                "resource": {
                    "resourceType": "Instance",
                    "instanceDetails": {
                        "instanceId": "i-99999999",
                        "instanceType": "t2.micro",
                        "launchTime": "2023-12-01T00:00:00Z",
                        "instanceState": "running",
                        "availabilityZone": "us-east-1a",
                        "imageId": "ami-99999999",
                        "imageDescription": "Amazon Linux 2",
                    },
                },
                "severity": 5,
                "createdAt": "2023-12-01T00:00:00Z",
                "updatedAt": "2023-12-01T00:00:00Z",
                "title": "SSH brute force attacks against i-99999999",
                "description": "EC2 instance i-99999999 is being probed for SSH weaknesses",
                "service": {
                    "serviceName": "guardduty",
                    "detectorId": "123456",
                    "action": {
                        "actionType": "NETWORK_CONNECTION",
                        "networkConnectionAction": {
                            "connectionDirection": "INBOUND",
                            "protocol": "TCP",
                            "blocked": "false",
                        },
                    },
                    "resourceRole": "TARGET",
                    "additionalInfo": {
                        "threatName": "SSHBruteForce",
                        "threatListName": "ProofPoint",
                    },
                    "count": 1,
                },
            },
        }


def main():
    """
    Main function to parse command line arguments and generate events
    """

    generator = TestEventGenerator()

    event_map = {
        "security_hub": generator.get_security_hub_event,
        "security_hub_resource": generator.get_security_hub_resource_event,
        "budget": generator.get_budget_event,
        "cloudwatch": generator.get_cloudwatch_event,
        "cloudwatch_eventbridge": generator.get_cloudwatch_eventbridge_alarm,
        "cost_anomaly": generator.get_cost_anomaly_event,
        "guardduty": generator.get_guardduty_event,
    }

    events_list = "\nAvailable events:\n  " + "\n  ".join(event_map.keys())

    parser = argparse.ArgumentParser(
        description="Process events with optional topics",
        epilog=events_list,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Add required positional argument for event name
    parser.add_argument("event_name", help="Name of the event to process")

    # Add optional topic argument with both short and long form
    parser.add_argument(
        "-t", "--topic", help="Specify the AWS SNS name for the event", default=None
    )

    args = parser.parse_args()

    # Now you can use:
    # args.event_name - for the event name
    # args.topic - for the topic (will be None if not provided)

    if args.event_name not in event_map:
        print(f"Unknown event type: {args.event_name}")
        print("Available event types:")
        print("  security_hub - Generate Security Hub event")
        print("  security_hub_resource - Generate Security Hub event with resource")
        print("  budget - Generate AWS Budget event")
        print("  cloudwatch - Generate CloudWatch alarm event")
        print("  cloudwatch_eventbridge - Generate CloudWatch EventBridge alarm event")
        print("  cost_anomaly - Generate Cost Anomaly event")
        print("  guardduty - Generate GuardDuty finding event")
        sys.exit(1)

    event = event_map[args.event_name]()

    if args.topic:
        try:
            sns = boto3.client("sns")
            # Get the topic ARN by name
            topics = sns.list_topics()["Topics"]
            topic_arn = next(
                (
                    topic["TopicArn"]
                    for topic in topics
                    if topic["TopicArn"].split(":")[-1] == args.topic
                ),
                None,
            )

            if not topic_arn:
                print(f"SNS topic '{args.topic}' not found")
                sys.exit(1)

            # Publish the event to SNS
            response = sns.publish(
                TopicArn=topic_arn, Message=json.dumps(event, indent=2)
            )
            print(f"Successfully published to SNS topic: {args.topic}")
            print(f"MessageId: {response['MessageId']}")
        except Exception as e:
            print(f"Error publishing to SNS: {str(e)}")
            sys.exit(1)
    else:
        print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()
