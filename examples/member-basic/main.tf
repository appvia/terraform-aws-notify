# Example: member module — hosting team, production account
#
# This example shows a realistic onboarding of a member account for the
# "hosting" platform team. It enables the core security and operational
# sources and declares logical route keys for team and central destinations.
#
# No Slack channel IDs, webhook URLs, or Teams tenant identifiers appear here.
# Those are owned entirely by the central module in the security account.

module "notifications" {
  source = "../../modules/member"

  central_event_bus_arn = var.central_event_bus_arn

  account_defaults = {
    team_alias  = "hosting"
    product     = "platform-hosting"
    environment = "prod"
    owner_email = "hosting-oncall@example.com"
  }

  sources = {
    securityhub       = { enabled = true }
    guardduty         = { enabled = true }
    cloudwatch_alarms = { enabled = true }
    cost_anomaly      = { enabled = true }
    budgets           = { enabled = true }
  }

  routing = {
    securityhub = {
      # domain=security and mandatory central routing are always applied by the
      # central rules layer. This adds an optional team-copy route.
      additional_routes = ["team.hosting"]
    }
    cloudwatch_alarms = {
      # Default routes when no notify.io/* tags are present on the alarm resource.
      # Tag-based routes on the resource take precedence.
      default_routes = ["team.hosting"]
    }
    budgets = {
      default_routes = ["team.hosting", "central.finops"]
    }
    cost_anomaly = {
      default_routes = ["central.finops"]
      severity_floor = "MEDIUM"
    }
  }

  tags = {
    Environment = "prod"
    Team        = "hosting"
    ManagedBy   = "terraform"
  }
}
