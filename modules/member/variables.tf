# ---------------------------------------------------------------------------------------------------------------------
# REQUIRED VARIABLES
# ---------------------------------------------------------------------------------------------------------------------

variable "central_event_bus_arn" {
  description = "ARN of the central EventBridge bus in the security account that this member account forwards enriched events to. Must be in the same region as this module deployment."
  type        = string

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:events:[a-z0-9-]+:[0-9]{12}:event-bus/.+$", var.central_event_bus_arn))
    error_message = "central_event_bus_arn must be a valid EventBridge event bus ARN, e.g. arn:aws:events:eu-west-1:111122223333:event-bus/notify-io-central"
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# ACCOUNT DEFAULTS
# ---------------------------------------------------------------------------------------------------------------------

variable "account_defaults" {
  description = "Stable metadata applied to every enriched event forwarded from this account. Used by central routing and the audit trail to identify ownership without inspecting individual events."
  type = object({
    team_alias  = string
    product     = string
    environment = string
    owner_email = string
  })

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.account_defaults.team_alias))
    error_message = "account_defaults.team_alias must be lowercase alphanumeric with hyphens, e.g. 'hosting' or 'payments-platform'"
  }

  validation {
    condition     = contains(["dev", "staging", "prod", "sandbox", "shared"], var.account_defaults.environment)
    error_message = "account_defaults.environment must be one of: dev, staging, prod, sandbox, shared"
  }

  validation {
    condition     = can(regex("^.+@.+$", var.account_defaults.owner_email))
    error_message = "account_defaults.owner_email must be a valid email address"
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------------------------------------------------

variable "sources" {
  description = "Controls which AWS event sources are enabled for this member account. Each source maps to an EventBridge rule and/or ingestion adapter provisioned by the member module."
  type = object({
    cloudwatch_alarms = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    securityhub       = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    guardduty         = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    macie             = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    access_analyzer   = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    inspector2        = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    health            = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    trusted_advisor   = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    service_quotas    = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    cost_anomaly      = optional(object({ enabled = optional(bool, false) }), { enabled = false })
    budgets           = optional(object({ enabled = optional(bool, false) }), { enabled = false })
  })
  default = {}
}

# ---------------------------------------------------------------------------------------------------------------------
# ROUTING
# ---------------------------------------------------------------------------------------------------------------------

variable "routing" {
  description = <<-EOT
    Per-source routing intent overrides. Route values are free-form logical keys (e.g. "team.hosting",
    "central.finops") that are resolved to approved delivery destinations by the central registry.
    Keys that do not exist in the central allow-list fall back to the operations channel rather than
    being dropped. Destination details (channel IDs, webhook URLs) must never appear here.
  EOT
  type = object({
    securityhub = optional(object({
      additional_routes = optional(list(string), [])
      # Additional team-copy routes for non-mandatory delivery.
      # Note: domain=security and mandatory central routing are always applied by the
      # central rules layer regardless of what is declared here.
    }), { additional_routes = [] })

    cloudwatch_alarms = optional(object({
      default_routes = optional(list(string), [])
      # Default route keys used when no notify.io/* tags are present on the alarm resource.
      # Tag-based routes on the resource take precedence over this default.
    }), { default_routes = [] })

    macie = optional(object({
      additional_routes = optional(list(string), [])
    }), { additional_routes = [] })

    access_analyzer = optional(object({
      additional_routes = optional(list(string), [])
    }), { additional_routes = [] })

    inspector2 = optional(object({
      additional_routes = optional(list(string), [])
    }), { additional_routes = [] })

    guardduty = optional(object({
      additional_routes = optional(list(string), [])
    }), { additional_routes = [] })

    health = optional(object({
      default_routes = optional(list(string), [])
    }), { default_routes = [] })

    trusted_advisor = optional(object({
      default_routes = optional(list(string), [])
    }), { default_routes = [] })

    service_quotas = optional(object({
      default_routes = optional(list(string), [])
    }), { default_routes = [] })

    cost_anomaly = optional(object({
      default_routes = optional(list(string), [])
      severity_floor = optional(string, "MEDIUM")
      # Minimum severity to forward. Events below this floor are not forwarded.
      # Valid values: INFO, LOW, MEDIUM, HIGH, CRITICAL
    }), { default_routes = [], severity_floor = "MEDIUM" })

    budgets = optional(object({
      default_routes = optional(list(string), [])
    }), { default_routes = [] })
  })
  default = {}

  validation {
    condition = contains(
      ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
      var.routing.cost_anomaly.severity_floor
    )
    error_message = "routing.cost_anomaly.severity_floor must be one of: INFO, LOW, MEDIUM, HIGH, CRITICAL"
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# LAMBDA CONFIGURATION
# ---------------------------------------------------------------------------------------------------------------------

variable "lambda_log_level" {
  description = "Log level for the enrichment Lambda function"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.lambda_log_level)
    error_message = "lambda_log_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
  }
}

variable "lambda_memory_size" {
  description = "Memory in MB for the enrichment Lambda function"
  type        = number
  default     = 128

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "lambda_memory_size must be between 128 and 10240 MB"
  }
}

variable "lambda_timeout" {
  description = "Timeout in seconds for the enrichment Lambda function"
  type        = number
  default     = 30

  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "lambda_timeout must be between 1 and 900 seconds"
  }
}

variable "lambda_runtime" {
  description = "Python runtime for the enrichment Lambda function"
  type        = string
  default     = "python3.13"
}

variable "lambda_role_permissions_boundary" {
  description = "ARN of a permissions boundary policy to attach to the enrichment Lambda IAM role. Required in environments where all IAM roles must have a boundary."
  type        = string
  default     = null
}

# ---------------------------------------------------------------------------------------------------------------------
# OBSERVABILITY
# ---------------------------------------------------------------------------------------------------------------------

variable "cloudwatch_log_group_retention" {
  description = "Retention in days for the enrichment Lambda CloudWatch log group"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.cloudwatch_log_group_retention)
    error_message = "cloudwatch_log_group_retention must be a valid CloudWatch retention value in days"
  }
}

variable "cloudwatch_log_group_kms_key_id" {
  description = "KMS key ARN to encrypt the enrichment Lambda CloudWatch log group. Defaults to no encryption if not provided."
  type        = string
  default     = null
}

# ---------------------------------------------------------------------------------------------------------------------
# TAGGING
# ---------------------------------------------------------------------------------------------------------------------

variable "tags" {
  description = "Tags to apply to all resources provisioned by this module"
  type        = map(string)
  default     = {}
}
