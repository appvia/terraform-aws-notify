# Member Module — Basic Example

Demonstrates onboarding a member account for the "hosting" platform team.

Enables SecurityHub, GuardDuty, CloudWatch alarms, Cost Anomaly Detection,
and Budgets sources. Declares logical route keys for team and FinOps
destinations. No chat credentials appear in this configuration.

<!-- BEGIN_TF_DOCS -->
## Providers

No providers.

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_central_event_bus_arn"></a> [central\_event\_bus\_arn](#input\_central\_event\_bus\_arn) | ARN of the central EventBridge bus in the security account | `string` | n/a | yes |
| <a name="input_region"></a> [region](#input\_region) | AWS region to deploy into | `string` | `"eu-west-1"` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_dlq_arn"></a> [dlq\_arn](#output\_dlq\_arn) | ARN of the enrichment Lambda Dead Letter Queue |
| <a name="output_enrichment_lambda_arn"></a> [enrichment\_lambda\_arn](#output\_enrichment\_lambda\_arn) | ARN of the enrichment Lambda function |
<!-- END_TF_DOCS -->
