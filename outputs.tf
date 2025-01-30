output "sns_topic_arn" {
  description = "The ARN of the SNS topic"
  value       = local.sns_topic_arn
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = module.lambda_function.lambda_function_arn
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = module.lambda_function.lambda_function_name
}

output "lambda_function_invoke_arn" {
  description = "The invoke ARN of the Lambda function"
  value       = module.lambda_function.lambda_function_invoke_arn
}

output "lambda_function_role_arn" {
  description = "The ARN of the IAM role created for the Lambda function"
  value       = module.lambda_function.lambda_role_arn
}
