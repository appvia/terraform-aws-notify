# Notifications PRD

## Overview

This document defines the product requirements and target architecture for a **centralized notifications framework** in a multi-account AWS Organizations environment. Member accounts generate events from diverse AWS sources (for example Security Hub, GuardDuty, CloudWatch, AWS Budgets, and AWS Cost Anomaly Detection). Those events are collected and forwarded into a **routing plane** in the security account, where policy decides **who** should be notified—central teams, owning application teams, or both—and **how** messages reach them.

Approved Slack and Microsoft Teams delivery is implemented using centrally managed chat integrations, configured and governed only from the central account. The objective is a predictable, auditable path from org-wide signals to the correct individuals and channels, without fragmenting integrations across member accounts.

## Problem Statement

Today, notification capability exists in multiple places in the platform, but the model is fragmented and account-scoped:

- Landing zone modules provision local SNS-backed notification paths per account and region.
- Team notifications are currently modeled around direct email and webhook delivery.
- Security notifications can be emitted from individual accounts, but there is no clear centralized routing and governance model for multi-team consumption.
- Application teams need access to actionable notifications for their own accounts, while platform and security teams need central visibility and control.

This creates several challenges:

- inconsistent delivery patterns across accounts and services
- weak governance over destination ownership and allowed chat integrations
- difficulty enforcing mandatory central security visibility
- duplication of notification configuration in member accounts
- inability to cleanly support both central and team-specific destinations for the same events

## Vision

Provide a centralized notifications framework in the security account that:

- receives events from landing-zone-managed AWS accounts across key services (security, operations, cost, and related platforms)
- routes notifications by domain, ownership, and severity so the right people and teams see each class of signal
- enforces strong central governance over chat integrations
- always delivers mandatory security notifications to the central security team
- optionally delivers filtered copies of relevant events to approved application team channels
- integrates with account onboarding so team destinations are declared as code, not manually configured

## Goals

- Provide a single, consistent pattern for member accounts to emit and forward notifications from supported sources (including Security Hub, GuardDuty, CloudWatch, budgets, Cost Anomaly Detection, and deployment or platform events as aligned with the landing zone).
- Centralize Slack and Microsoft Teams notification integrations in a single governed AWS account.
- Support both central shared channels and team-specific approved channels.
- Preserve strong central control over destination approval, IAM guardrails, and chat platform access.
- Allow application teams to request notification destinations during account provisioning.
- Reuse existing landing-zone event sources where practical.
- Support at least these domains:
  - security
  - operations
  - deployments
  - cost
- Keep initial scope to notifications only, with no interactive ChatOps commands required.

## Non-Goals

- Full self-service team-managed chat integrations in member accounts
- Broad interactive CLI or remediation actions from chat channels
- Unlimited arbitrary external webhook destinations
- Replacing existing security tooling or SIEM workflows
- Solving all event normalization for all services in phase 1

## Users and Stakeholders

### Primary Users

- Central Security Team
- Platform / Cloud Engineering Team
- Application Teams
- FinOps Team

### Stakeholders

- AWS Organizations administrators
- Landing zone platform maintainers
- Compliance and governance owners
- Incident response and operations teams

## Current State

The current platform already contains notification-related capability:

- Terragrunt account onboarding defines shared defaults and per-account overrides.
- Landing-zone application modules accept `notifications` as input.
- Base landing-zone modules provision SNS-backed notifications.
- Security Hub events are already emitted through EventBridge rules in the member account model.

However, the current model is still primarily account-local and destination-centric rather than centrally governed and policy-driven.

## Desired Outcomes

- Every landing-zone-managed account emits a predictable set of notification events.
- Security findings are always routed to a central security channel.
- Application teams can receive notifications for their own accounts in approved destinations.
- The notification destination for an account is declared in onboarding configuration and reviewed through pull requests.
- The security account owns all centrally configured chat destination integrations (Slack and Teams).
- Routing logic supports duplication where required, for example:
  - central security team receives all critical security findings
  - app team receives relevant copies for their account
- The solution supports both Slack and Teams from day one.

## Functional Requirements

### FR1: Centralized Chat Destination Configuration

The platform must manage all approved Slack and Teams chat destination configuration centrally in the security account (and enforce organization policy/guardrails as required).

### FR2: Approved Destination Registry

The platform must maintain a centrally owned registry of approved Slack and Teams destinations.

### FR3: Account-Level Notification Declaration

Application account onboarding must allow a team to declare notification intent in code, including:

- team ownership
- approved destination alias
- domains to receive
- optional security-copy policy
- optional central-only or team-only preferences for non-mandatory domains

### FR4: Mandatory Central Security Routing

Security notifications must always be routed to a central security destination.

### FR5: Optional Team Copy

The platform must support copying eligible notifications to application team destinations based on account ownership and policy.

### FR6: Domain-Based Routing

Notifications must be routable by at least these domains:

- security
- operations
- deployments
- cost

### FR7: Filtering

The platform must support filtering by at least:

- account
- region
- domain
- severity
- ownership/team alias

### FR8: Strong Governance

Only centrally approved workspaces, tenants, teams, and channels may be used.

### FR9: Notifications Only

Initial implementation must restrict channels to notifications-only behavior.

### FR10: Multi-Account Support

The platform must support landing-zone-managed accounts across AWS Organizations.

## Non-Functional Requirements

- auditable via code review and infrastructure as code
- scalable across many accounts and regions
- minimal per-account operational overhead
- least-privilege IAM and strong guardrails
- resilient to regional event distribution patterns
- extensible to future custom notifications and richer workflows

## High-Level Architecture

### Architectural Principle

Separate event production from destination ownership.

## Recommended Target Architecture

### Security Account

Host the following in the security account:

- approved destination registry
- Slack and Teams channel configurations
- notifications-only IAM roles and guardrails
- AWS Organizations chat applications policies
- central routing resources
- per-domain SNS topics and/or EventBridge routing rules

### Member Accounts

Provision the following in each managed account:

- service-native event emitters where required
- EventBridge rules for selected domains
- a member-account enrichment Lambda that:
  - inspects source payloads
  - reads resource tags and/or configured account/service metadata
  - normalizes and enriches events with routing metadata (for example domain, product/application, environment, ownership/team alias, severity/priority class)
  - forwards enriched events cross-account to the central EventBridge bus

### Routing Pattern

The preferred routing pattern is:

1. member account event is generated
2. a member-account enrichment Lambda normalizes the event and adds routing metadata using source inspection (including tags) and configured account/service metadata
3. the enriched event is forwarded cross-account to the security account EventBridge bus
4. central routing applies policy
5. event is delivered to:
   - mandatory central domain channel
   - optional team destination channel
   - both, where policy requires duplication

## Conceptual Architecture

```text
                                         +----------------------------------+
                                         | GitHub / Terragrunt Onboarding    |
                                         | lz-aws-landing-zones              |
                                         |-----------------------------------|
                                         | account config declares:          |
                                         | - owner/team alias                |
                                         | - approved team destination alias |
                                         | - domains to copy                 |
                                         | - security copy policy            |
                                         +-----------------+----------------+
                                                           |
                                                           v
+---------------------------+                 +------------+-------------+
| Management / CI Pipeline  |                 | Security Account         |
|---------------------------|                 | Central Notifications    |
| applies account landing   |                 |--------------------------|
| zone + central routing    |---------------->| Destination registry     |
| changes from code         |                 | Slack/Teams configs      |
+-------------+-------------+                 | Org chat policies        |
              |                               | Notification IAM role    |
              |                               | EventBridge bus/rules    |
              |                               | SNS topics by domain     |
              |                               +------+---------+---------+
              |                                      |         |
              |                                      |         |
              v                                      |         |
+-------------+-------------+                        |         |
| Member Account            |                        |         |
| Application Landing Zone  |                        |         |
|---------------------------|                        |         |
| Security Hub findings     |                        |         |
| GuardDuty findings        |                        |         |
| CloudWatch alarms         |                        |         |
| Budgets / Cost Anomaly    |                        |         |
| Deploy/app events         |                        |         |
| EventBridge rules         |---invoke--->EnrichLambda         |
| EnrichLambda              |---PutEvents--->CentralEventBus---+
+-------------+-------------+
              |
              v
      (events enriched with:
       account id, owner,
       product, environment,
       region, domain, severity)

                    In Security Account Routing Layer
                    ---------------------------------

         +--------------------+   +--------------------+   +--------------------+
         | SNS topic: security|   | SNS topic: ops     |   | SNS topic: deploy  |
         +---------+----------+   +---------+----------+   +---------+----------+
                   |                        |                          |
                   v                        v                          v

     +---------------------------+   +--------------------------+   +--------------------------+
     | Central Security Channel  |   | Central Ops Channel      |   | Central Platform Channel |
     | mandatory                 |   | mandatory/shared         |   | optional/shared          |
     +---------------------------+   +--------------------------+   +--------------------------+

                   \                    /                  /
                    \                  /                  /
                     \                /                  /
                      v              v                  v

                +--------------------------------------------------+
                | Optional Team Channels                           |
                |--------------------------------------------------|
                | payments-alerts (Slack)                          |
                | payments-alerts (Teams)                          |
                | search-alerts (Slack)                            |
                | etc                                              |
                |                                                  |
                | Only approved aliases; routed by policy:         |
                | - account/team ownership                         |
                | - allowed domains                                |
                | - severity filters                               |
                +--------------------------------------------------+
```

## Security Considerations

- No direct member-account ownership of Slack or Teams integrations
- No unmanaged incoming webhooks in onboarding configuration
- All chat access restricted through organization policy and IAM guardrails
- Mandatory routing for security cannot be disabled by application teams
- Team copies of security events should be filtered to reduce alert fatigue and data sprawl

## Implementation Details

This section documents the selected implementation pattern end-to-end.

At a high level, the flow is:

- **member account → EventBridge rule → enrichment Lambda (tags + metadata) → `events:PutEvents` → central EventBridge bus**

### Infrastructure as Code (module layout)

The IaC should be composed of:

- **One central module** (deployed in the security account) that provisions:
  - the central EventBridge bus and its resource policy
  - central routing rules and downstream delivery targets
  - any central registries/guardrails required for approved destinations
- **One member module** at `modules/notifications` (deployed per member account/region) that provisions:
  - EventBridge rules for selected domains/sources
  - the enrichment Lambda and its IAM permissions
  - configuration-driven metadata storage in **SSM Parameter Store** (for example account/service defaults used by the Lambda)

### Member account onboarding (keep it simple)

Onboarding a member account should be configuration-driven and minimal:

- a single Terraform object input that declares which sources/domains are enabled and any local overrides
- metadata written to SSM Parameter Store (free tier friendly) to avoid hard-coding routing metadata into Lambda code
- the member module wires EventBridge → Lambda and the Lambda publishes into the central bus

### Routing intents via tags (allow-listed)

Member accounts may request additional notification delivery by attaching **routing intent** tags to resources that generate events (for example CloudWatch alarms), but must not specify destination details (Slack channel IDs, email addresses, ServiceNow instance configuration, etc.). Member accounts only emit **route keys**; the central framework maps those keys to approved delivery targets.

- **Tag namespace**: `notify.io/*`
- **Supported tags** (initial set):
  - `notify.io/routes`: route keys (either repeated tags where supported, or a comma-separated list)
  - `notify.io/priority`: `low|normal|high|critical`
  - `notify.io/product`: product identifier
  - `notify.io/service`: service identifier

To keep routing governed and auditable, route keys must be **allow-listed per account**. The allow-list is stored in **SSM Parameter Store** (written by the member module) and validated by the enrichment Lambda before forwarding the event to the central bus. Unknown route keys are dropped (or routed only to mandatory central destinations).

### Cross-Account Permissions (EventBridge PutEvents)

- The **central event bus** in the security account must have a **resource policy** permitting `events:PutEvents` from approved member accounts (preferably constrained using AWS Organizations conditions).
- The **member enrichment Lambda execution role** must allow `events:PutEvents` to the central bus ARN.

### Central Account Routing

1. The central EventBridge bus receives enriched events from member accounts.
2. Central routing rules apply governance and delivery policy (mandatory central security routing, optional team copies, filtering).
3. Notifications are delivered to approved Slack/Teams destinations via centrally managed chat integrations, and/or to other central targets as required.

### EventBridge

```hcl

module "configuration" {
  account_tags = {
    account = "Hosting"
    owner   = "Engineering"
    service = "Hosting"
  }

  # We receive all cloudwatch alarms - we filter on the following
  # tagging information, and forward appropreiately
  cloudwatch = {
    #
    application = {
      filters = {
        tags = "notify.io"
      }
      tags = {
        priority = "high"
        service  = "payments"
      }
      route = ["slack/hosting_alarms", "slack/payment_team"]
    }
  }

  securityhub = {
    route = ["slack/engineering"]
  }
}
```

EventBridge sources

```
{
  "$or": [{
    "source": ["aws.cloudwatch"],
    "detail-type": ["CloudWatch Alarm State Change"]
  }, {
    "source": ["aws.macie"]
  }, {
    "source": ["aws.access-analyzer"]
  }, {
    "source": ["aws.inspector2"]
  }, {
    "source": ["aws.trustedadvisor"]
  }, {
    "source": ["aws.servicequotas"]
  }, {
    "source": ["aws.securityhub"],
    "detail-type": ["Security Hub Findings - Imported"]
  }, {
    "source": ["aws.guardduty"],
    "detail-type": ["GuardDuty Finding"]
  }, {
    "source": ["aws.health"],
    "detail-type": ["AWS Health Event"]
  }, {
    "source": ["aws.ce"],
    "detail-type": "Anomaly Detected"
  }]
}
```

### Onboarding Experience

Application teams must not create their own chat integrations.

Instead, during account onboarding they declare notification intent such as:

- owning team alias
- approved destination alias
- enabled domains
- security copy preference
- optional severity thresholds where allowed

Example conceptual intent:

```hcl
notifications = {
  team_alias        = "payments"
  destination_alias = "slack-payments-alerts"
  domains           = ["operations", "deployments", "cost"]
  security_copy     = ["HIGH", "CRITICAL"]
}
```

This declaration is reviewed and then materialized by centrally managed infrastructure.

### Member Account Ingress and Enrichment

1. Source AWS services emit events (for example Security Hub, GuardDuty, CloudWatch, Budgets/Cost Anomaly Detection, and approved application/platform events).
2. EventBridge rules (per-domain or per-source) invoke a standard **enrichment Lambda** in the member account.
3. The enrichment Lambda:
   - inspects the source event and extracts stable identifiers
   - reads **resource tags** where applicable
   - applies **configured account/service metadata** (for example from centrally managed onboarding configuration materialized into the member account)
   - produces a normalized/enriched event containing routing metadata such as:
     - domain
     - product/application
     - environment
     - ownership/team alias
     - severity and/or priority class
   - forwards the enriched event to the **central EventBridge bus** in the security account via `events:PutEvents`
