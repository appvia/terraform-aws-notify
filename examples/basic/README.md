# Email example using appvia notifications

Create a `tfvars` local file with variables for:
```
email_addresses = ["<your mail1@address1.domain>"]
sns_topic_name  = "your new sns topic name!"
```

Then:
```
terraform init
AWS_PROFILE=<profile name> terraform apply --var-file=./<your vars>.tfvars
```

And to delete:
```
AWS_PROFILE=<profile name> terraform destroy --var-file=./<your vars>.tfvars
```

<!-- BEGIN_TF_DOCS -->
## Providers

No providers.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_slack_webhook_url"></a> [slack\_webhook\_url](#input\_slack\_webhook\_url) | The Slack webhook URL to send notifications to | `string` | `"https://hooks.slack.com/services/XXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_sns_topic_arn"></a> [sns\_topic\_arn](#output\_sns\_topic\_arn) | The ARN of the SNS topic |
<!-- END_TF_DOCS -->