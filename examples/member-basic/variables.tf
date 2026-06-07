variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-1"
}

variable "central_event_bus_arn" {
  description = "ARN of the central EventBridge bus in the security account"
  type        = string
}
