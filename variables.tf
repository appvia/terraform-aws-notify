variable "allowed_aws_principals" {
  description = "Optional, list of AWS accounts able to publish via the SNS topic (when creating topic) e.g 123456789012"
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for p in var.allowed_aws_principals : can(regex("^[0-9]{6,}$", p))
    ])
    error_message = "List must be a valid set of AWS account ids - only the ID not the iam"
  }
}

variable "allowed_aws_services" {
  description = "Optional, list of AWS services able to publish via the SNS topic (when creating topic) e.g cloudwatch.amazonaws.com"
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for s in var.allowed_aws_services : can(regex(".+.amazonaws.com$", s))
    ])
    error_message = "List must be a valid set of AWS services"
  }
}

variable "cloudwatch_log_group_class" {
  description = "The class of the CloudWatch log group"
  type        = string
  default     = "STANDARD"
}

variable "cloudwatch_log_group_kms_key_id" {
  description = "The KMS key id to use for encrypting the cloudwatch log group (default is none)"
  type        = string
  default     = null
}

variable "cloudwatch_log_group_retention" {
  description = "The retention period for the cloudwatch log group (for lambda function logs) in days"
  type        = number
  default     = 14
}

variable "create_sns_topic" {
  description = "Whether to create an SNS topic for notifications"
  type        = bool
  default     = false
}

variable "email" {
  description = "The configuration for Email notifications"
  type = object({
    addresses = optional(list(string))
    # The email addresses to send notifications to
  })
  default = null

  validation {
    condition = alltrue([
      for e in coalesce(var.email, { addresses = [] }).addresses : can(regex("^.+@.+$", e))
    ])
    error_message = "Invalid email address"
  }
}

variable "ephemeral_storage_size" {
  description = "Amount of ephemeral storage (/tmp) in MB your Lambda Function can use at runtime"
  type        = number
  default     = 512
}

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "lz-notifications"
}

variable "lambda_log_level" {
  description = "The log level for the Lambda function"
  type        = string
  default     = "INFO"
}

variable "lambda_role_description" {
  description = "Description of the IAM role for the Lambda function"
  type        = string
  default     = "IAM role for Lambda function"
}

variable "lambda_role_name" {
  description = "Name of the IAM role for the Lambda function"
  type        = string
  default     = null
}

variable "lambda_role_permissions_boundary" {
  description = "ARN of the permissions boundary to be used on the Lambda IAM role"
  type        = string
  default     = null
}

variable "memory_size" {
  description = "Amount of memory in MB your Lambda Function can use at runtime"
  type        = number
  default     = 128
}

variable "notification_platform" {
  description = "Platform to send notifications to (slack or teams)"
  type        = string
  default     = "slack"
  validation {
    condition     = contains(["slack", "teams"], var.notification_platform)
    error_message = "notification_platform must be either 'slack' or 'teams'"
  }
}

variable "slack" {
  description = "The configuration for Slack notifications"
  type = object({
    lambda_name = optional(string, "slack-notify")
    # The name of the lambda function to create
    lambda_description = optional(string, "Lambda function to send slack notifications")
    # The description for the slack lambda
    secret_name = optional(string)
    # An optional secret name in secrets manager to use for the slack configuration
    webhook_url = optional(string)
    # The webhook url to post to
    filter_policy = optional(string)
    # An optional SNS subscription filter policy to apply
    filter_policy_scope = optional(string)
    # If filter policy provided this is the scope of that policy; either "MessageAttributes" (default) or "MessageBody"
  })
  default = null
}

variable "sns_topic_name" {
  description = "The name of the source sns topic where events are published"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,256}$", var.sns_topic_name))
    error_message = "Invalid SNS topic name"
  }
}

variable "sns_topic_policy" {
  description = "The policy to attach to the sns topic, else we default to account root"
  type        = string
  default     = null
}

variable "subscribers" {
  description = "Optional list of custom subscribers to the SNS topic"
  type = map(object({
    protocol = string
    # The protocol to use. The possible values for this are: sqs, sms, lambda, application. (http or https are partially supported, see below).
    endpoint = string
    # The endpoint to send data to, the contents will vary with the protocol. (see below for more information)
    endpoint_auto_confirms = bool
    # Boolean indicating whether the end point is capable of auto confirming subscription e.g., PagerDuty (default is false)
    raw_message_delivery = bool
    # Boolean indicating whether or not to enable raw message delivery (the original message is directly passed, not wrapped in JSON with the original message in the message property) (default is false)
  }))
  default = {}
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "teams" {
  description = "The configuration for teams notifications"
  type = object({
    lambda_name = optional(string, "teams-notify")
    # The name of the lambda function to create
    lambda_description = optional(string, "Lambda function to send teams notifications")
    # The description for the teams lambda
    secret_name = optional(string)
    # An optional secret name in secrets manager to use for the slack configuration
    webhook_url = optional(string)
    # The webhook url to post to
    filter_policy = optional(string)
    # An optional SNS subscription filter policy to apply
    filter_policy_scope = optional(string)
    # If filter policy provided this is the scope of that policy; either "MessageAttributes" (default) or "MessageBody"
  })
  default = null
}

variable "timeout" {
  description = "The amount of time your Lambda Function has to run in seconds"
  type        = number
  default     = 30
}
