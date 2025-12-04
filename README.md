<!-- markdownlint-disable -->

<a href="https://www.appvia.io/"><img src="https://github.com/appvia/terraform-aws-notify/blob/main/docs/appvia_banner.jpg?raw=true" alt="Appvia Banner"/></a><br/><p align="right"> <a href="https://registry.terraform.io/modules/appvia/notify/aws/latest"><img src="https://img.shields.io/static/v1?label=APPVIA&message=Terraform%20Registry&color=191970&style=for-the-badge" alt="Terraform Registry"/></a></a> <a href="https://github.com/appvia/terraform-aws-notify/releases/latest"><img src="https://img.shields.io/github/release/appvia/terraform-aws-notify.svg?style=for-the-badge&color=006400" alt="Latest Release"/></a> <a href="https://appvia-community.slack.com/join/shared_invite/zt-1s7i7xy85-T155drryqU56emm09ojMVA#/shared-invite/email"><img src="https://img.shields.io/badge/Slack-Join%20Community-purple?style=for-the-badge&logo=slack" alt="Slack Community"/></a> <a href="https://github.com/appvia/terraform-aws-notify/graphs/contributors"><img src="https://img.shields.io/github/contributors/appvia/terraform-aws-notify.svg?style=for-the-badge&color=FF8C00" alt="Contributors"/></a>

<!-- markdownlint-restore -->
<!--
  ***** CAUTION: DO NOT EDIT ABOVE THIS LINE ******
-->

![Github Actions](https://github.com/appvia/terraform-aws-notifications/actions/workflows/terraform.yml/badge.svg)

# Terraform AWS Notify

## Description

The purpose of this module is to provide a building block for processing and delivering notifications, sourced from SNS and forwarded to one or more endpoints (email, slack, teams and or custom subscribers).

## Usage

```hcl
module "notifications" {
  source = "../.."

  # creates the SNS topic of the given name, and allows CloudWatch service to post to topic
  allowed_aws_services = [
    "budgets.amazonaws.com",
    "cloudwatch.amazonaws.com",
    "cloudtrail.amazonaws.com",
    "events.amazonaws.com",
  ]
  create_sns_topic = false
  sns_topic_name   = "lza-cloudaccess-notifications"

  # consistent tags applied across all resources
  tags = {
    Environment = "Test"
    Owner       = "DevOps"
  }

  slack = {
    # slack webhook URL
    webhook_url = "https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXX/XXXXXXXXXXXXXXXX"
  }

  # list of email address that will be subscribed
  email = {
    addresses = []
  }
}
```

## Update Documentation

The `terraform-docs` utility is used to generate this README. Follow the below steps to update:

1. Make changes to the `.terraform-docs.yml` file
2. Fetch the `terraform-docs` binary (<https://terraform-docs.io/user-guide/installation/>)
3. Run `terraform-docs markdown table --output-file ${PWD}/README.md --output-mode inject .`

## Development

### Python Code Structure

The Lambda function code is located in `assets/notifications/` and follows a modular architecture:

```
assets/notifications/
├── lambda_function.py          # Main Lambda entry point
├── events/                      # Event parsing and normalization
│   ├── event_parser.py         # Main parser that routes events to specific parsers
│   ├── event_type.py           # Event type definitions and enums
│   ├── normalized_event.py    # Normalized event data structure
│   └── parsers/                # Event-specific parsers
│       ├── base.py             # Abstract base parser
│       ├── cloudwatch.py       # CloudWatch alarm parser
│       ├── securityhub.py      # Security Hub findings parser
│       ├── guardduty.py        # GuardDuty findings parser
│       ├── kms.py              # KMS key deletion parser
│       └── default.py          # Default parser for unknown events
├── formatters/                 # Message formatting for different platforms
│   ├── base_formatter.py       # Abstract base formatter
│   ├── slack_formatter.py      # Slack message formatting
│   └── teams_formatter.py      # Microsoft Teams message formatting
├── senders/                    # Message sending to different platforms
│   ├── base_sender.py          # Abstract base sender
│   ├── slack_sender.py         # Slack webhook sender
│   └── teams_sender.py         # Teams webhook sender
├── utils/                      # Utility functions
│   ├── secrets.py              # AWS Secrets Manager integration
│   └── strings.py              # String utility functions
└── tests/                      # Test files
    ├── test_lambda_function.py # Integration tests for Lambda handler
    └── [module]/tests/         # Unit tests for each module
```

### Architecture Overview

The code follows a pipeline architecture:

1. **Event Reception**: The `lambda_handler` receives AWS events (typically from SNS)
2. **Event Parsing**: The `EventParser` identifies the event type and uses the appropriate parser to normalize it into a `NormalizedEvent`
3. **Message Formatting**: A platform-specific formatter (Slack or Teams) converts the normalized event into a formatted message
4. **Message Sending**: A platform-specific sender delivers the message to the target webhook

This design allows for easy extension:

- Add new event types by creating a new parser in `events/parsers/`
- Add new platforms by implementing `BaseFormatter` and `MessageSender` subclasses
- Modify formatting logic without affecting parsing or sending logic

### Setting Up Development Environment

1. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

### Running Tests

Tests are organized to mirror the code structure. To run all tests:

```bash
# Using make (recommended)
make test-python

# Or directly with pytest
pytest assets/notifications/ -v
```

To run specific test files or modules:

```bash
# Run tests for a specific module
pytest assets/notifications/events/tests/ -v
pytest assets/notifications/formatters/tests/ -v
pytest assets/notifications/utils/tests/ -v

# Run a specific test file
pytest assets/notifications/tests/test_lambda_function.py -v

# Run a specific test
pytest assets/notifications/utils/tests/test_secrets.py::test_get_secret -v
```

The test suite includes:

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test the full Lambda handler with mocked HTTP servers
- **Mocking**: Uses `unittest.mock` for AWS services and `pytest-httpserver` for webhook testing

### Test Requirements

The test suite requires the following dependencies (listed in `requirements.txt`):

- `pytest>=7.0.0` - Testing framework
- `pytest-httpserver>=1.0.0` - HTTP server for testing webhooks
- `werkzeug>=2.0.0` - Dependency for pytest-httpserver
- `boto3>=1.26.0` - AWS SDK (used in code and tests)

## Maintenance

Frequently (quartley at least) check and upgrade:

1. Python runtime - [python_runtime](./modules/notify/variables.tf)
2. AWS PowerTools Lambda Layer for python ARN: [powertools_layer_arn_suffix](./modules/notify/variables.tf)

## Acknowledgements

- [notify-teams](https://github.com/teamclairvoyant/terraform-aws-notify-teams/releases/tag/v4.12.0.6) - distributed under Apache 2.0 license; obligations met under this GNU V3 license
- [terraform-aws-notify-slack](https://github.com/terraform-aws-modules/terraform-aws-notify-slack/releases/tag/v6.4.0) - distributed under Apache 2.0 license; obligations met under this GNU V3 license

<!-- BEGIN_TF_DOCS -->
## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 6.0.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_sns_topic_name"></a> [sns\_topic\_name](#input\_sns\_topic\_name) | The name of the source sns topic where events are published | `string` | n/a | yes |
| <a name="input_allowed_aws_principals"></a> [allowed\_aws\_principals](#input\_allowed\_aws\_principals) | Optional, list of AWS accounts able to publish via the SNS topic (when creating topic) e.g 123456789012 | `list(string)` | `[]` | no |
| <a name="input_allowed_aws_services"></a> [allowed\_aws\_services](#input\_allowed\_aws\_services) | Optional, list of AWS services able to publish via the SNS topic (when creating topic) e.g cloudwatch.amazonaws.com | `list(string)` | `[]` | no |
| <a name="input_cloudwatch_log_group_class"></a> [cloudwatch\_log\_group\_class](#input\_cloudwatch\_log\_group\_class) | The class of the CloudWatch log group | `string` | `"STANDARD"` | no |
| <a name="input_cloudwatch_log_group_kms_key_id"></a> [cloudwatch\_log\_group\_kms\_key\_id](#input\_cloudwatch\_log\_group\_kms\_key\_id) | The KMS key id to use for encrypting the cloudwatch log group (default is none) | `string` | `null` | no |
| <a name="input_cloudwatch_log_group_retention"></a> [cloudwatch\_log\_group\_retention](#input\_cloudwatch\_log\_group\_retention) | The retention period for the cloudwatch log group (for lambda function logs) in days | `number` | `14` | no |
| <a name="input_create_sns_topic"></a> [create\_sns\_topic](#input\_create\_sns\_topic) | Whether to create an SNS topic for notifications | `bool` | `false` | no |
| <a name="input_email"></a> [email](#input\_email) | The configuration for Email notifications | <pre>object({<br/>    addresses = optional(list(string))<br/>    # The email addresses to send notifications to<br/>  })</pre> | `null` | no |
| <a name="input_ephemeral_storage_size"></a> [ephemeral\_storage\_size](#input\_ephemeral\_storage\_size) | Amount of ephemeral storage (/tmp) in MB your Lambda Function can use at runtime | `number` | `512` | no |
| <a name="input_function_name"></a> [function\_name](#input\_function\_name) | Name of the Lambda function | `string` | `"lz-notifications"` | no |
| <a name="input_lambda_log_level"></a> [lambda\_log\_level](#input\_lambda\_log\_level) | The log level for the Lambda function | `string` | `"INFO"` | no |
| <a name="input_lambda_role_description"></a> [lambda\_role\_description](#input\_lambda\_role\_description) | Description of the IAM role for the Lambda function | `string` | `"Used by the notifications lambda to forward alarms on to slack or teams"` | no |
| <a name="input_lambda_role_name"></a> [lambda\_role\_name](#input\_lambda\_role\_name) | Name of the IAM role for the Lambda function | `string` | `null` | no |
| <a name="input_lambda_role_permissions_boundary"></a> [lambda\_role\_permissions\_boundary](#input\_lambda\_role\_permissions\_boundary) | ARN of the permissions boundary to be used on the Lambda IAM role | `string` | `null` | no |
| <a name="input_lambda_runtime"></a> [lambda\_runtime](#input\_lambda\_runtime) | The runtime to use for the Lambda function | `string` | `"python3.13"` | no |
| <a name="input_memory_size"></a> [memory\_size](#input\_memory\_size) | Amount of memory in MB your Lambda Function can use at runtime | `number` | `128` | no |
| <a name="input_slack"></a> [slack](#input\_slack) | The configuration for Slack notifications | <pre>object({<br/>    lambda_name = optional(string, "slack-notify")<br/>    # The name of the lambda function to create<br/>    lambda_description = optional(string, "Lambda function to send slack notifications")<br/>    # An optional secret name in secrets manager to use for the slack configuration<br/>    webhook_url = optional(string)<br/>    # An optional ARN for a secret in secrets manager containing the webhook url details<br/>    webhook_arn = optional(string, null)<br/>  })</pre> | `null` | no |
| <a name="input_sns_topic_policy"></a> [sns\_topic\_policy](#input\_sns\_topic\_policy) | The policy to attach to the sns topic, else we default to account root | `string` | `null` | no |
| <a name="input_subscribers"></a> [subscribers](#input\_subscribers) | Optional list of custom subscribers to the SNS topic | <pre>map(object({<br/>    protocol = string<br/>    # The protocol to use. The possible values for this are: sqs, sms, lambda, application. (http or https are partially supported, see below).<br/>    endpoint = string<br/>    # The endpoint to send data to, the contents will vary with the protocol. (see below for more information)<br/>    endpoint_auto_confirms = bool<br/>    # Boolean indicating whether the end point is capable of auto confirming subscription e.g., PagerDuty (default is false)<br/>    raw_message_delivery = bool<br/>    # Boolean indicating whether or not to enable raw message delivery (the original message is directly passed, not wrapped in JSON with the original message in the message property) (default is false)<br/>  }))</pre> | `{}` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags to apply to all resources | `map(string)` | `{}` | no |
| <a name="input_teams"></a> [teams](#input\_teams) | The configuration for teams notifications | <pre>object({<br/>    lambda_name = optional(string, "teams-notify")<br/>    # The name of the lambda function to create<br/>    lambda_description = optional(string, "Lambda function to send teams notifications")<br/>    # An optional secret name in secrets manager to use for the slack configuration<br/>    webhook_url = optional(string)<br/>    # An optional ARN for a secret in secrets manager containing the webhook url details<br/>    webhook_arn = optional(string, null)<br/>  })</pre> | `null` | no |
| <a name="input_timeout"></a> [timeout](#input\_timeout) | The amount of time your Lambda Function has to run in seconds | `number` | `30` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | The ARN of the Lambda function |
| <a name="output_lambda_function_invoke_arn"></a> [lambda\_function\_invoke\_arn](#output\_lambda\_function\_invoke\_arn) | The invoke ARN of the Lambda function |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | The name of the Lambda function |
| <a name="output_lambda_function_role_arn"></a> [lambda\_function\_role\_arn](#output\_lambda\_function\_role\_arn) | The ARN of the IAM role created for the Lambda function |
| <a name="output_sns_topic_arn"></a> [sns\_topic\_arn](#output\_sns\_topic\_arn) | The ARN of the SNS topic |
<!-- END_TF_DOCS -->
