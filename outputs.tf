output "sns_topic_arn" {
  description = "The ARN of the SNS topic"
  value       = local.sns_topic_arn
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = try(module.lambda_function[0].lambda_function_arn, null)
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = try(module.lambda_function[0].lambda_function_name, null)
}

output "lambda_function_invoke_arn" {
  description = "The invoke ARN of the Lambda function"
  value       = try(module.lambda_function[0].lambda_function_invoke_arn, null)
}

output "lambda_function_role_arn" {
  description = "The ARN of the IAM role created for the Lambda function"
  value       = try(module.lambda_function[0].lambda_role_arn, null)
}
