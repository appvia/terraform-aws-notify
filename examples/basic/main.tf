#####################################################################################
# Terraform module examples are meant to show an _example_ on how to use a module
# per use-case. The code below should not be copied directly but referenced in order
# to build your own root module that invokes this module, where
#    source = "github.com/appvia/terraform-aws-notifications?ref=main"
#####################################################################################

module "notifications" {
  source = "../.."

  # creates the SNS topic of the given name, and allows CloudWatch service to post to topic
  allowed_aws_services = [
    "budgets.amazonaws.com",
    "cloudwatch.amazonaws.com",
    "cloudtrail.amazonaws.com",
    "events.amazonaws.com",
  ]
  create_sns_topic = true
  lambda_role_name = "lza-notifications-test"
  function_name    = "lza-notifications-test"
  sns_topic_name   = "lza-notifications-test"

  # consistent tags applied across all resources
  tags = {
    Environment = "Test"
    Owner       = "Engineering"
    Product     = "LandingZone"
  }

  slack = {
    # slack webhook URL
    #webhook_url = var.slack_webhook_url
    webhook_arn = "arn:aws:secretsmanager:eu-west-2:390403866963:secret:webhook-test-wN261F"
  }

  # list of email address that will be subscribed
  email = {
    addresses = []
  }
}
