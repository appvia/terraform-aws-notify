
## Find the current AWS account ID
data "aws_caller_identity" "current" {}

## Find the current AWS region
data "aws_region" "current" {}

## Provision an SNS IAM policy allowing the account root
data "aws_iam_policy_document" "current" {
  statement {
    sid    = "AllowAccountRoot"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = [format("arn:aws:iam::%s:root", local.account_id)]
    }
    actions = [
      "sns:Publish"
    ]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = local.allowed_aws_services

    content {
      sid    = "AllowService${statement.value.name}"
      effect = "Allow"
      principals {
        type        = "Service"
        identifiers = [statement.value.service]
      }
      actions = [
        "sns:Publish"
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.allowed_aws_principals

    content {
      sid    = "AllowPrincipal${index(var.allowed_aws_principals, statement.value)}"
      effect = "Allow"
      principals {
        type        = "AWS"
        identifiers = [statement.value]
      }
      actions = [
        "sns:Publish"
      ]
      resources = ["*"]
    }
  }
}
