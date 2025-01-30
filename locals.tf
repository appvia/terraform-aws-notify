
locals {
  ## The current account id
  account_id = data.aws_caller_identity.current.account_id
  ## The current region
  region = data.aws_region.current.name
  ## Indicates if we are enabling emails notifications
  enable_email = var.email != null ? true : false

  ## Expected sns topic arn, assuming we are not creating the sns topic
  expected_sns_topic_arn = format("arn:aws:sns:%s:%s:%s", local.region, local.account_id, var.sns_topic_name)
  ## Is the arn of the sns topic to use
  sns_topic_arn = var.create_sns_topic ? module.sns[0].topic_arn : local.expected_sns_topic_arn
  ## Is the SNS topic policy to use
  sns_topic_policy = var.sns_topic_policy != null ? var.sns_topic_policy : data.aws_iam_policy_document.current.json
}
