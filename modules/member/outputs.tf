output "enrichment_lambda_arn" {
  description = "ARN of the enrichment Lambda function that forwards enriched events to the central bus"
  value       = null
}

output "enrichment_lambda_name" {
  description = "Name of the enrichment Lambda function"
  value       = null
}

output "enrichment_lambda_role_arn" {
  description = "ARN of the IAM role used by the enrichment Lambda"
  value       = null
}

output "dlq_arn" {
  description = "ARN of the Dead Letter Queue that receives events when the enrichment Lambda fails to forward to the central bus"
  value       = null
}

output "dlq_url" {
  description = "URL of the Dead Letter Queue"
  value       = null
}

output "eventbridge_rule_arns" {
  description = "Map of source name to EventBridge rule ARN for each enabled source"
  value       = {}
}
