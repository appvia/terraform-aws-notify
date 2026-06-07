# terraform-aws-notify — Member Module

This module is deployed **once per active region in each member (application) account**. It provisions the event capture and enrichment pipeline that normalises AWS service events and forwards them as structured `notify.io.v1.Event` payloads to the central EventBridge bus in the security account.

## What this module does

- Installs EventBridge rules on the account default bus for each enabled source (`securityhub`, `guardduty`, `cloudwatch_alarms`, etc.)
- Deploys an enrichment Lambda that reads resource tags and account metadata, normalises the event, and calls `events:PutEvents` on the central bus
- Provides a Dead Letter Queue (DLQ) and CloudWatch alarm for enrichment failures
- Writes routing metadata to SSM Parameter Store under `/notify.io/` (managed by the central pipeline; this module reads only)

## What this module does NOT do

- It does not create Slack channels, Teams tenants, or any chat integration
- It does not contain destination details — only logical route keys (e.g. `team.hosting`)
- It does not write to SSM Parameter Store — the central pipeline owns that namespace

## Usage

```hcl
module "notifications" {
  source = "github.com/appvia/terraform-aws-notify//modules/member"

  central_event_bus_arn = "arn:aws:events:eu-west-1:111122223333:event-bus/notify-io-central"

  account_defaults = {
    team_alias  = "hosting"
    product     = "platform-hosting"
    environment = "prod"
    owner_email = "hosting-oncall@example.com"
  }

  sources = {
    securityhub       = { enabled = true }
    guardduty         = { enabled = true }
    cloudwatch_alarms = { enabled = true }
    cost_anomaly      = { enabled = true }
    budgets           = { enabled = true }
  }

  routing = {
    securityhub = {
      additional_routes = ["team.hosting"]
    }
    cloudwatch_alarms = {
      default_routes = ["team.hosting"]
    }
    budgets = {
      default_routes = ["team.hosting", "central.finops"]
    }
    cost_anomaly = {
      default_routes = ["central.finops"]
      severity_floor = "MEDIUM"
    }
  }

  tags = var.tags
}
```

## Route keys

Route keys (e.g. `team.hosting`, `central.finops`, `central.sec`) are logical identifiers that the central routing registry maps to approved chat destinations. They are allow-listed per account by the central pipeline. Unknown route keys fall back to the central operations channel rather than being dropped.

<!-- BEGIN_TF_DOCS -->
## Providers

No providers.

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_account_defaults"></a> [account\_defaults](#input\_account\_defaults) | Stable metadata applied to every enriched event forwarded from this account. Used by central routing and the audit trail to identify ownership without inspecting individual events. | <pre>object({<br/>    team_alias  = string<br/>    product     = string<br/>    environment = string<br/>    owner_email = string<br/>  })</pre> | n/a | yes |
| <a name="input_central_event_bus_arn"></a> [central\_event\_bus\_arn](#input\_central\_event\_bus\_arn) | ARN of the central EventBridge bus in the security account that this member account forwards enriched events to. Must be in the same region as this module deployment. | `string` | n/a | yes |
| <a name="input_cloudwatch_log_group_kms_key_id"></a> [cloudwatch\_log\_group\_kms\_key\_id](#input\_cloudwatch\_log\_group\_kms\_key\_id) | KMS key ARN to encrypt the enrichment Lambda CloudWatch log group. Defaults to no encryption if not provided. | `string` | `null` | no |
| <a name="input_cloudwatch_log_group_retention"></a> [cloudwatch\_log\_group\_retention](#input\_cloudwatch\_log\_group\_retention) | Retention in days for the enrichment Lambda CloudWatch log group | `number` | `30` | no |
| <a name="input_lambda_log_level"></a> [lambda\_log\_level](#input\_lambda\_log\_level) | Log level for the enrichment Lambda function | `string` | `"INFO"` | no |
| <a name="input_lambda_memory_size"></a> [lambda\_memory\_size](#input\_lambda\_memory\_size) | Memory in MB for the enrichment Lambda function | `number` | `128` | no |
| <a name="input_lambda_role_permissions_boundary"></a> [lambda\_role\_permissions\_boundary](#input\_lambda\_role\_permissions\_boundary) | ARN of a permissions boundary policy to attach to the enrichment Lambda IAM role. Required in environments where all IAM roles must have a boundary. | `string` | `null` | no |
| <a name="input_lambda_runtime"></a> [lambda\_runtime](#input\_lambda\_runtime) | Python runtime for the enrichment Lambda function | `string` | `"python3.13"` | no |
| <a name="input_lambda_timeout"></a> [lambda\_timeout](#input\_lambda\_timeout) | Timeout in seconds for the enrichment Lambda function | `number` | `30` | no |
| <a name="input_routing"></a> [routing](#input\_routing) | Per-source routing intent overrides. Route values are free-form logical keys (e.g. "team.hosting",<br/>"central.finops") that are resolved to approved delivery destinations by the central registry.<br/>Keys that do not exist in the central allow-list fall back to the operations channel rather than<br/>being dropped. Destination details (channel IDs, webhook URLs) must never appear here. | <pre>object({<br/>    securityhub = optional(object({<br/>      additional_routes = optional(list(string), [])<br/>      # Additional team-copy routes for non-mandatory delivery.<br/>      # Note: domain=security and mandatory central routing are always applied by the<br/>      # central rules layer regardless of what is declared here.<br/>    }), { additional_routes = [] })<br/><br/>    cloudwatch_alarms = optional(object({<br/>      default_routes = optional(list(string), [])<br/>      # Default route keys used when no notify.io/* tags are present on the alarm resource.<br/>      # Tag-based routes on the resource take precedence over this default.<br/>    }), { default_routes = [] })<br/><br/>    macie = optional(object({<br/>      additional_routes = optional(list(string), [])<br/>    }), { additional_routes = [] })<br/><br/>    access_analyzer = optional(object({<br/>      additional_routes = optional(list(string), [])<br/>    }), { additional_routes = [] })<br/><br/>    inspector2 = optional(object({<br/>      additional_routes = optional(list(string), [])<br/>    }), { additional_routes = [] })<br/><br/>    guardduty = optional(object({<br/>      additional_routes = optional(list(string), [])<br/>    }), { additional_routes = [] })<br/><br/>    health = optional(object({<br/>      default_routes = optional(list(string), [])<br/>    }), { default_routes = [] })<br/><br/>    trusted_advisor = optional(object({<br/>      default_routes = optional(list(string), [])<br/>    }), { default_routes = [] })<br/><br/>    service_quotas = optional(object({<br/>      default_routes = optional(list(string), [])<br/>    }), { default_routes = [] })<br/><br/>    cost_anomaly = optional(object({<br/>      default_routes = optional(list(string), [])<br/>      severity_floor = optional(string, "MEDIUM")<br/>      # Minimum severity to forward. Events below this floor are not forwarded.<br/>      # Valid values: INFO, LOW, MEDIUM, HIGH, CRITICAL<br/>    }), { default_routes = [], severity_floor = "MEDIUM" })<br/><br/>    budgets = optional(object({<br/>      default_routes = optional(list(string), [])<br/>    }), { default_routes = [] })<br/>  })</pre> | `{}` | no |
| <a name="input_sources"></a> [sources](#input\_sources) | Controls which AWS event sources are enabled for this member account. Each source maps to an EventBridge rule and/or ingestion adapter provisioned by the member module. | <pre>object({<br/>    cloudwatch_alarms = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    securityhub       = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    guardduty         = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    macie             = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    access_analyzer   = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    inspector2        = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    health            = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    trusted_advisor   = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    service_quotas    = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    cost_anomaly      = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>    budgets           = optional(object({ enabled = optional(bool, false) }), { enabled = false })<br/>  })</pre> | `{}` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags to apply to all resources provisioned by this module | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_dlq_arn"></a> [dlq\_arn](#output\_dlq\_arn) | ARN of the Dead Letter Queue that receives events when the enrichment Lambda fails to forward to the central bus |
| <a name="output_dlq_url"></a> [dlq\_url](#output\_dlq\_url) | URL of the Dead Letter Queue |
| <a name="output_enrichment_lambda_arn"></a> [enrichment\_lambda\_arn](#output\_enrichment\_lambda\_arn) | ARN of the enrichment Lambda function that forwards enriched events to the central bus |
| <a name="output_enrichment_lambda_name"></a> [enrichment\_lambda\_name](#output\_enrichment\_lambda\_name) | Name of the enrichment Lambda function |
| <a name="output_enrichment_lambda_role_arn"></a> [enrichment\_lambda\_role\_arn](#output\_enrichment\_lambda\_role\_arn) | ARN of the IAM role used by the enrichment Lambda |
| <a name="output_eventbridge_rule_arns"></a> [eventbridge\_rule\_arns](#output\_eventbridge\_rule\_arns) | Map of source name to EventBridge rule ARN for each enabled source |
<!-- END_TF_DOCS -->
