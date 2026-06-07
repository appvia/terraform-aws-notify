output "enrichment_lambda_arn" {
  description = "ARN of the enrichment Lambda function"
  value       = module.notifications.enrichment_lambda_arn
}

output "dlq_arn" {
  description = "ARN of the enrichment Lambda Dead Letter Queue"
  value       = module.notifications.dlq_arn
}
