## Provision the SNS topic for the budgets
module "sns" {
  count   = var.create_sns_topic ? 1 : 0
  source  = "terraform-aws-modules/sns/aws"
  version = "7.0.0"

  name                          = var.sns_topic_name
  source_topic_policy_documents = [local.sns_topic_policy]
  tags                          = var.tags
}

## Provision any email notifications if required
resource "aws_sns_topic_subscription" "email" {
  for_each = local.enable_email ? toset(var.email.addresses) : toset([])

  topic_arn = local.sns_topic_arn
  protocol  = "email"
  endpoint  = each.value

  depends_on = [module.sns]
}

## Provision the sns topic subscriptions if required
resource "aws_sns_topic_subscription" "subscribers" {
  for_each = var.subscribers

  confirmation_timeout_in_minutes = 1
  endpoint                        = each.value.endpoint
  endpoint_auto_confirms          = each.value.endpoint_auto_confirms
  protocol                        = each.value.protocol
  raw_message_delivery            = each.value.raw_message_delivery
  topic_arn                       = local.sns_topic_arn

  depends_on = [module.sns]
}

## Add Lambda subscription to SNS topic
resource "aws_sns_topic_subscription" "lambda" {
  count     = local.enable_notifications ? 1 : 0
  topic_arn = local.sns_topic_arn
  protocol  = "lambda"
  endpoint  = module.lambda_function[0].lambda_function_arn

  depends_on = [module.sns, module.lambda_function]
}

## Add permission for SNS to invoke Lambda
resource "aws_lambda_permission" "sns" {
  count         = local.enable_notifications ? 1 : 0
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_function[0].lambda_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = local.sns_topic_arn

  depends_on = [module.lambda_function]
}

module "lambda_function" {
  count   = local.enable_notifications ? 1 : 0
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.1.2"

  description    = "Lambda function to process AWS events and send notifications to Slack/Teams"
  tags           = var.tags
  create_package = true

  # Lambda settings
  architectures          = ["arm64"]
  ephemeral_storage_size = var.ephemeral_storage_size
  function_name          = var.function_name
  function_tags          = var.tags
  handler                = "notifications.lambda_function.lambda_handler"
  memory_size            = var.memory_size
  runtime                = var.lambda_runtime
  timeout                = var.timeout

  # Policy settings
  attach_policy_statements           = true
  attach_cloudwatch_logs_policy      = true
  attach_create_log_group_permission = true
  attach_tracing_policy              = true

  # IAM settings
  create_role               = true
  role_description          = var.lambda_role_description
  role_tags                 = var.tags
  role_name                 = local.lambda_role_name
  role_permissions_boundary = var.lambda_role_permissions_boundary

  # Cloudwatch settings
  use_existing_cloudwatch_log_group = false
  cloudwatch_logs_retention_in_days = var.cloudwatch_log_group_retention
  cloudwatch_logs_log_group_class   = var.cloudwatch_log_group_class
  cloudwatch_logs_tags              = var.tags
  cloudwatch_logs_kms_key_id        = var.cloudwatch_log_group_kms_key_id

  policy_statements = merge(
    {
      sns = {
        sid       = "AllowSTS"
        effect    = "Allow"
        actions   = ["sts:GetCallerIdentity"]
        resources = ["*"]
      }
      kms = {
        sid    = "AllowKMSDecrypt"
        effect = "Allow"
        actions = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        resources = ["*"]
      }
    },
    try(var.slack.webhook_arn, null) != null ? {
      secrets_manager = {
        sid       = "AllowSlackSecretsManagerAccess"
        actions   = ["secretsmanager:GetSecretValue"]
        resources = [var.slack.webhook_arn]
        effect    = "Allow"
      }
    } : {},
    try(var.teams.webhook_arn, null) != null ? {
      secrets_manager = {
        sid       = "AllowTeamsSecretsManagerAccess"
        actions   = ["secretsmanager:GetSecretValue"]
        resources = [var.teams.webhook_arn]
        effect    = "Allow"
      }
    } : {},
  )

  source_path = [
    {
      path     = "${path.module}/assets/"
      patterns = ["!tests/*", "!.*\\__pycache__/.*", "!.*\\.pyc$"]
    }
  ]

  # Environment variables
  environment_variables = merge(
    var.slack != null ? {
      NOTIFICATION_PLATFORM = "slack"
      WEBHOOK_URL           = try(var.slack.webhook_url, null)
      WEBHOOK_ARN           = try(var.slack.webhook_arn, null)
    } : {},
    var.teams != null ? {
      NOTIFICATION_PLATFORM = "teams"
      WEBHOOK_URL           = try(var.teams.webhook_url, null)
      WEBHOOK_ARN           = try(var.teams.webhook_arn, null)
    } : {},
    {
      LOG_LEVEL = try(var.lambda_log_level, null)
    }
  )
}
