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

### FR11: Unrouted Fallback (No Silent Drop)

Events that arrive at the central bus and do not match any team route key, or that carry unknown/invalid routing metadata, must not be silently dropped. They must be delivered to a dedicated central `unrouted` destination for triage, with the original payload and the reason for fallback (`unknown_route_key`, `missing_metadata`, `allow_list_miss`, `schema_violation`, etc.) attached. Security-classified events must additionally route to the mandatory central security destination regardless of fallback state.

### FR12: Payload Redaction Before Chat Delivery

Events delivered to Slack or Teams must pass through a central redaction step that strips or templates fields known to carry sensitive content (resource ARNs containing account-internal references, raw IPs where not required, principal/user identifiers, secrets accidentally embedded in alarm descriptions). The unredacted payload is archived in a central S3 bucket with KMS encryption for incident response.

### FR13: Versioned Enriched Event Schema

The enriched cross-account event must conform to a versioned schema (`notify.io.v1.Event`) registered in EventBridge Schema Registry in the security account. Every enriched event must carry `schemaVersion` and central rules must pattern-match against schema version so future evolution does not break existing routes.

### FR14: Per-Region Central Bus

The central routing plane is deployed once per active region. Member accounts forward events to the central bus in the same region. There is no inter-region forwarding inside the framework; regional independence is preserved for blast radius, latency, and EventBridge quota reasons.

## Non-Functional Requirements

- auditable via code review and infrastructure as code
- scalable across many accounts and regions
- minimal per-account operational overhead
- least-privilege IAM and strong guardrails
- resilient to regional event distribution patterns
- extensible to future custom notifications and richer workflows
- every routing decision must be auditable: structured logs capturing `(eventId, sourceAccount, derivedDomain, matchedRoutes, deliveredDestinations, ruleId, schemaVersion)` retained for at least 90 days
- recoverable: the central bus archives all received events with replay capability for at least 30 days
- safely degradable: ingestion failures, schema violations, and unknown routes surface to an `unrouted` destination rather than being lost

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

### Baseline controls

- No direct member-account ownership of Slack or Teams integrations
- No unmanaged incoming webhooks in onboarding configuration
- All chat access restricted through organization policy and IAM guardrails
- Mandatory routing for security cannot be disabled by application teams
- Team copies of security events should be filtered to reduce alert fatigue and data sprawl

### Trust boundary controls

Because enrichment runs in the member account and member-account compromise is a credible threat, the central routing layer must treat member-supplied routing metadata as **advisory**, not authoritative, wherever a routing decision has security implications:

1. **Central bus resource policy.** `events:PutEvents` is allowed only when `aws:PrincipalOrgID` matches the organization ID **and** `aws:SourceAccount` is in the centrally maintained allow-list of onboarded accounts. `Principal: *` is never used without both conditions.
2. **Account-identity cross-check.** Central rules drop and alarm on any event where the enriched `detail.account` does not equal `aws:SourceAccount`. This blocks a compromised member Lambda from spoofing another account's identity in the enriched payload.
3. **Authoritative security domain.** Central rules derive `domain=security` directly from `source` and `detail-type` (e.g. `aws.securityhub`, `aws.guardduty`, `aws.macie`, `aws.access-analyzer`, `aws.inspector2`) and ignore any member-supplied `domain` field for routing-sensitive decisions. The member-supplied `domain` is metadata only. Mandatory security routing therefore cannot be bypassed by tampering with the enriched event.
4. **Authoritative severity for security.** For security-domain events the central severity is derived from the source payload (SecurityHub `Severity.Label`, GuardDuty `severity`, Inspector `severity`) rather than from member-supplied enrichment. This prevents downgrade attacks where a compromised enrichment Lambda relabels a `CRITICAL` finding as `LOW`.
5. **Centrally owned allow-list.** The route-key allow-list and onboarded-account list in SSM Parameter Store are written exclusively by the central pipeline's cross-account role. An SCP denies write on `notify.io/*` parameters to any other principal. The member module reads but never writes the allow-list.
6. **Tag policies.** AWS Organizations Tag Policies constrain `notify.io/priority` to `low|normal|high|critical` and reject unknown keys under the `notify.io/` namespace. An SCP additionally denies `*:TagResource`/`*:UntagResource` on `notify.io/*` keys for non-platform principals. Without these, free-text tags will silently corrupt routing within months.
7. **Encryption at rest.** All SNS topics, EventBridge bus archives, Lambda log groups, and S3 archive buckets use customer-managed KMS keys (not `aws/sns`, `aws/lambda`). Key policies grant decrypt only to the routing principals that need it.
8. **Notifications-only chat IAM.** The AWS Chatbot channel-configuration role used by Slack/Teams integrations has an explicit deny on `lambda:Invoke*`, `ssm:StartSession`, `ssm:Start*`, `ec2:*`, `iam:*`, `s3:GetObject` outside an allow-list of routing buckets, and any `Run*`/`Execute*`/`Create*` action. FR9 ("notifications only") is enforced by IAM, not by configuration intent.
9. **Payload redaction and archival.** A central redaction step (Lambda or EventBridge Pipes filter) is applied before chat delivery to strip resource ARNs that leak internal account naming, raw IPs, principal/user identifiers, and any field matching common secret patterns. The unredacted payload is archived in S3 with KMS for incident response (see FR12).
10. **Routing-decision audit trail.** Every routing decision is emitted as a structured log record `(eventId, sourceAccount, derivedDomain, derivedSeverity, matchedRoutes, deliveredDestinations, ruleId, schemaVersion, redactionApplied)`. Logs go to a CloudWatch log group and are forwarded to the central S3 audit bucket. This is the evidence trail used to prove FR4 (mandatory security routing) was not bypassed during an incident.
11. **Replay/flood protection.** Per-source-account CloudWatch alarms on `PutEvents` rate detect a compromised member Lambda spamming the central bus. The central bus archive doubles as replay protection: duplicate `eventId`s within a configurable window are deduplicated by the central rules layer.
12. **Idempotency keys.** Enriched events carry an `eventId` derived from the source identifier (SecurityHub finding ID, alarm ARN + state-change timestamp, etc.) so retries and replays do not double-page on-call.

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

To keep routing governed and auditable, route keys must be **allow-listed per account**. The allow-list is stored in **SSM Parameter Store**, written **only by the central pipeline** (see Security Considerations §5), and read by the member enrichment Lambda for validation before forwarding the event to the central bus.

Unknown or invalid route keys must **not** be silently dropped. The handling is:

- If any route key is unknown, the event is still forwarded to the central bus with `routingStatus=allow_list_miss` and the offending keys recorded in `routingDiagnostics.unknownRouteKeys`. Central routing delivers the event to the `unrouted` destination (see FR11) so the misconfiguration surfaces to operations.
- If the event's authoritative domain (derived centrally) is `security`, the mandatory central security destination still receives the event regardless of route-key validity. Security routing cannot be defeated by tag tampering or allow-list misses.
- Events that fail schema validation (`schemaVersion` missing, payload does not match `notify.io.v1.Event`) are routed to `unrouted` with `routingStatus=schema_violation` and an alarm fires.

### Cross-Account Permissions (EventBridge PutEvents)

- The **central event bus** in the security account must have a **resource policy** permitting `events:PutEvents` only when:
  - `aws:PrincipalOrgID` equals the organization ID, **and**
  - `aws:SourceAccount` is in the centrally maintained allow-list of onboarded accounts (rendered into the policy by the central pipeline).
  `Principal: *` is never used without both conditions. The policy is recomputed and re-applied by the central pipeline whenever the onboarded-account list changes.
- The **member enrichment Lambda execution role** must allow `events:PutEvents` to the central bus ARN and nothing else for that statement. The role has no other cross-account permissions.
- Central rules drop and alarm on any event where `detail.account != aws:SourceAccount` (account-identity cross-check, Security Considerations §2).

### Central Account Routing

1. The central EventBridge bus receives enriched events from member accounts.
2. Central routing rules apply governance and delivery policy (mandatory central security routing, optional team copies, filtering).
3. Notifications are delivered to approved Slack/Teams destinations via centrally managed chat integrations, and/or to other central targets as required.

### Member Module Configuration (per-account)

The member module accepts a single object input split into three concerns: stable account-level metadata, the set of sources to enable, and the per-source routing intent. Destination details (channel IDs, webhooks, email lists) are never specified here — only logical route keys that the central registry resolves.

```hcl
module "notifications" {
  source = "github.com/appvia/terraform-aws-notify//modules/notifications"

  # Stable metadata applied to every enriched event from this account.
  # Used by central routing and the audit trail.
  account_defaults = {
    team_alias  = "hosting"
    product     = "platform-hosting"
    environment = "prod"
    owner_email = "hosting-oncall@example.com"
  }

  # Central bus this member account forwards into. Must be in the same
  # region as this module deployment (see Per-Region Deployment Model).
  central_event_bus_arn = "arn:aws:events:eu-west-1:111122223333:event-bus/notify-io-central"

  # Which AWS sources this account ingests. Booleans only here —
  # all routing decisions live in the central rules layer.
  sources = {
    cloudwatch_alarms = { enabled = true }
    securityhub       = { enabled = true }
    guardduty         = { enabled = true }
    macie             = { enabled = true }
    access_analyzer   = { enabled = true }
    inspector2        = { enabled = true }
    health            = { enabled = true }
    trusted_advisor   = { enabled = true }
    service_quotas    = { enabled = true }
    cost_anomaly      = { enabled = true } # native EventBridge (IMMEDIATE freq)
    budgets           = { enabled = true } # via SNS bridge — see Ingestion Adapters
  }

  # Per-source overrides for default routing intent. The route values
  # are logical keys; they are resolved to channels by the central
  # registry (see FR2). They must appear in the per-account allow-list
  # in SSM (see Allow-List Governance).
  routing = {
    securityhub = {
      # Domain is *advisory* here — central rules derive domain=security
      # authoritatively from source/detail-type. This block only adds
      # additional team-copy routes for non-mandatory delivery.
      additional_routes = ["team.hosting"]
    }
    cloudwatch_alarms = {
      # Alarms carry their routing on the resource via notify.io/* tags.
      # This block is the default if no tags are present.
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

  tags = var.tags
}
```

The intent declared above is reviewed by pull request, materialized by the central pipeline into the member account, and used by the enrichment Lambda. Note specifically: there is no `slack/...` or `teams/...` string anywhere in member configuration. Logical route keys (`team.hosting`, `central.finops`, `central.sec`) are the only routing primitive teams interact with.

### EventBridge Sources Pattern

The member module installs a single EventBridge rule on the default bus that captures all natively-emitted sources of interest and forwards them to the enrichment Lambda. Non-native sources (AWS Budgets threshold notifications, CAD `DAILY`/`WEEKLY` summaries) are handled by their dedicated ingestion adapters and never appear in this pattern.

```json
{
  "$or": [
    { "source": ["aws.cloudwatch"], "detail-type": ["CloudWatch Alarm State Change"] },
    { "source": ["aws.macie"] },
    { "source": ["aws.access-analyzer"] },
    { "source": ["aws.inspector2"] },
    { "source": ["aws.trustedadvisor"] },
    { "source": ["aws.servicequotas"] },
    { "source": ["aws.securityhub"], "detail-type": ["Security Hub Findings - Imported"] },
    { "source": ["aws.guardduty"], "detail-type": ["GuardDuty Finding"] },
    { "source": ["aws.health"], "detail-type": ["AWS Health Event"] },
    { "source": ["aws.ce"], "detail-type": ["Anomaly Detected"] }
  ]
}
```

Notes:

- `aws.ce` / `Anomaly Detected` events are only emitted for `IMMEDIATE`-frequency CAD subscriptions. The member module creates the CAD subscription as part of onboarding `cost_anomaly`; without that subscription nothing reaches the bus.
- `aws.budgets` is deliberately **excluded** from this pattern. The only EventBridge events from `aws.budgets` are CloudTrail-derived API calls (e.g. `CreateBudget`), which are administrative, not user-facing alerts. The actual budget-breach notifications enter the framework via the Budgets SNS bridge (see Ingestion Adapters) and arrive at the central bus with `source=appvia.budgets`.
- `aws.health` events are regional; for organization-wide aggregation, enable Health Organizational View in the Org management account and consume the aggregated events there in addition to per-account.

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
   - produces a normalized/enriched event conforming to the `notify.io.v1.Event` schema (see Event Schema and Versioning), containing:
     - `schemaVersion`
     - `eventId` (idempotency key derived from the source event)
     - `account` (must equal `aws:SourceAccount` at the central bus)
     - `region`
     - `domain` (advisory; central rules derive authoritatively for `security`)
     - `severity` (advisory; central rules derive authoritatively for `security`)
     - `product`, `service`, `environment`, `team_alias` (from `account_defaults` and `notify.io/*` tags)
     - `routeKeys` (from `notify.io/routes` tag, intersected with the allow-list)
     - `routingStatus` (`ok` / `allow_list_miss` / `missing_metadata`)
     - `routingDiagnostics` (e.g. `unknownRouteKeys`)
     - `sourcePayload` (the original event for downstream consumers and the archive)
   - forwards the enriched event to the **central EventBridge bus** in the security account via `events:PutEvents`

### Ingestion Adapters for Non-EventBridge-Native Sources

Not every source the spec lists emits directly to EventBridge. The member module provides per-source ingestion adapters where needed. As of the current AWS surface area:

| Source                       | Native EventBridge?                                                 | Adapter in member module                                                |
|------------------------------|---------------------------------------------------------------------|-------------------------------------------------------------------------|
| Security Hub                 | Yes (`aws.securityhub`)                                             | None — direct rule                                                      |
| GuardDuty                    | Yes (`aws.guardduty`)                                               | None — direct rule                                                      |
| Macie                        | Yes (`aws.macie`)                                                   | None — direct rule                                                      |
| IAM Access Analyzer          | Yes (`aws.access-analyzer`)                                         | None — direct rule                                                      |
| Inspector 2                  | Yes (`aws.inspector2`)                                              | None — direct rule                                                      |
| CloudWatch Alarm state       | Yes (`aws.cloudwatch`)                                              | None — direct rule                                                      |
| AWS Health                   | Yes (`aws.health`) — per-region                                     | None for member events; Org-wide aggregation requires Health Organizational View enabled at the Org management account |
| Trusted Advisor              | Yes (`aws.trustedadvisor`) — Business/Enterprise Support only       | None — direct rule (only emits where the support plan permits)          |
| Service Quotas               | Yes (`aws.servicequotas`)                                           | None — direct rule                                                      |
| Cost Anomaly Detection       | **Partial** — `aws.ce` / `Anomaly Detected` only for `IMMEDIATE` subscription frequency. `DAILY`/`WEEKLY` summaries are email-only and not exposed to EventBridge | Member module creates an `IMMEDIATE`-frequency CAD subscription pointing at the central bus (or a member-account SNS topic that bridges). DAILY/WEEKLY summaries remain email-only and out of scope of EventBridge routing. |
| AWS Budgets                  | **No** — only CloudTrail-derived API events (`detail-type: "AWS API Call via CloudTrail"`) reach EventBridge. Actual threshold-breach notifications are not native EventBridge events | Member module creates a per-account SNS topic for Budgets notifications; an SNS-subscribed Lambda wraps each Budgets message as a `notify.io.v1.Event` with `source=appvia.budgets` (synthetic namespace to distinguish from CloudTrail-derived `aws.budgets`) and PutEvents into the central bus. Topic policy restricts publish to `budgets.amazonaws.com` with `aws:SourceAccount` condition. |

The synthetic `appvia.*` source namespace is reserved for adapter-wrapped events so central rules can distinguish "real" AWS-native events from adapter-bridged ones. Central rules match adapter sources by `source` prefix.

### Per-Region Deployment Model

EventBridge buses are regional. The framework deploys one central bus **per active region**. Member accounts in region X forward to the central bus in region X. There is no inter-region forwarding inside the framework. Rationale:

- regional blast radius: an outage or quota exhaustion in one region does not affect routing in others
- latency: cross-region PutEvents is measurable additional latency for high-volume sources like CloudWatch alarms
- EventBridge quotas: default `PutEvents` quota is per-region per-account; spreading the load across regions naturally raises headroom
- compliance: some workloads require event data to remain in-region

Per-region resources:

- one central event bus, resource policy keyed on `aws:PrincipalOrgID` + per-region allow-list
- one bus archive (30+ days, KMS-encrypted)
- the central routing rules, redaction Lambda/Pipe, and per-domain SNS topics
- region-local copies of Chatbot channel configurations where Chatbot supports the region; for unsupported regions, route via SNS cross-region to the nearest supported region for Chatbot delivery only (downstream of routing decisions, so the trust boundary is preserved)

Member accounts run the member module once per active region. The member module pins `central_event_bus_arn` to the same-region central bus.

### Reliability: DLQ, Archive, Replay

Every cross-account or cross-service hop has explicit failure handling:

- **Member enrichment Lambda**: configured with a dedicated DLQ (SQS, KMS-encrypted). Failures to PutEvents to the central bus land in the DLQ. CloudWatch alarm fires on `ApproximateNumberOfMessagesVisible > 0` sustained for 5 minutes.
- **Central bus archive**: every event received by the central bus is archived to a managed EventBridge archive with retention of at least 30 days. Archives are KMS-encrypted.
- **Replay**: operators can replay archived events to a named rule for forensics or for re-routing after a central-rule fix. Replay is gated by an IAM role assumable only by the central platform team.
- **Central rule targets**: every rule target (SNS topic, Lambda, Chatbot) has a target-level DLQ. Targets with no DLQ are forbidden by a central guardrail check.
- **Idempotency**: each enriched event carries `eventId` derived deterministically from the source event (e.g. SecurityHub finding `Id`, alarm ARN + `StateChangeTime`). Central routing deduplicates on `eventId` within a 1-hour rolling window using a small DynamoDB table.
- **Quota observability**: per-region CloudWatch alarms on EventBridge `PutEvents` throttles, SNS `NumberOfNotificationsFailed`, and Lambda `Throttles` surface quota pressure before it causes drops.

### Event Schema and Versioning

The enriched cross-account event must conform to a versioned schema registered in EventBridge Schema Registry in the security account. Initial schema: `notify.io.v1.Event`.

- Every enriched event carries `schemaVersion: "v1"` at the top level.
- Central routing rules pattern-match on `schemaVersion` so a future `v2` can be deployed alongside `v1` without breaking existing routes.
- The schema is published from the central module via `aws_schemas_schema`. Member modules consume a generated typed SDK (or a JSON Schema validator) so the enrichment Lambda fails fast on malformed events.
- Schema-violating events delivered to the central bus are routed to `unrouted` with `routingStatus=schema_violation` and the schema-registry deviation report attached.

Skeleton (JSON Schema, abbreviated):

```json
{
  "$id": "https://appvia.io/schemas/notify.io.v1.Event.json",
  "type": "object",
  "required": ["schemaVersion", "eventId", "account", "region", "source", "sourcePayload"],
  "properties": {
    "schemaVersion": { "const": "v1" },
    "eventId": { "type": "string", "minLength": 1 },
    "account": { "type": "string", "pattern": "^[0-9]{12}$" },
    "region": { "type": "string" },
    "source": { "type": "string" },
    "domain": { "enum": ["security", "operations", "deployments", "cost", "unknown"] },
    "severity": { "enum": ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"] },
    "product": { "type": "string" },
    "service": { "type": "string" },
    "environment": { "type": "string" },
    "teamAlias": { "type": "string" },
    "routeKeys": { "type": "array", "items": { "type": "string" } },
    "routingStatus": { "enum": ["ok", "allow_list_miss", "missing_metadata", "schema_violation"] },
    "routingDiagnostics": { "type": "object" },
    "sourcePayload": { "type": "object" }
  }
}
```

### Allow-List Governance

The route-key allow-list and the onboarded-account list are configuration that controls *who can ask to be paged for what*. Both live in SSM Parameter Store but are owned end-to-end by the central pipeline, not by member accounts:

- The central pipeline assumes a cross-account role (`AppviaNotifyCentralWriter`) in each member account whose only permission is `ssm:PutParameter`/`ssm:DeleteParameter`/`ssm:AddTagsToResource` scoped to `arn:aws:ssm:*:*:parameter/notify.io/*`.
- An SCP applied to the Workloads OU denies `ssm:PutParameter` on `/notify.io/*` for any principal other than `AppviaNotifyCentralWriter`. Members cannot self-grant route keys.
- The member module's read role can only `ssm:GetParameter` / `ssm:GetParametersByPath` under `/notify.io/`.
- The central pipeline tags every parameter it writes with `notify.io/managed-by=central` and `notify.io/source-pr=<pr-url>` for traceability.
- Allow-list changes are pull-request-reviewed in the central onboarding repository; merge triggers the central pipeline which writes the updated allow-list into each affected member account.

### Redaction Before Chat Delivery

Slack and Teams are not security tools. A central redaction step sits between the routing rules and the Chatbot targets:

- Implemented as a Lambda (or EventBridge Pipes enrichment step) on the central side, fed from the per-domain SNS topics, with the Chatbot integration consuming the redacted output.
- Redaction rules applied:
  - resource ARN templating: replace account ID with team alias (`arn:aws:s3:::123456789012-payments-data` → `arn:aws:s3:::<payments>-data`)
  - raw IPv4/IPv6 addresses outside RFC1918 stripped or hashed where not material to the alert
  - principal/user identifiers (`userIdentity.userName`, `userIdentity.arn`) reduced to role-only
  - common secret patterns (AKIA*, ASIA*, github_pat_*, eyJ* JWT-shaped, hex blobs > 32 chars) blanket-masked as `[redacted-secret-pattern]`
- The pre-redaction payload is archived to a central S3 bucket (KMS, Object Lock optional) for incident response. Access to the bucket is via break-glass role with audit logging.
- The redaction step itself emits a `notify.io.v1.RedactionApplied` record into the audit log for every event so the audit trail records what was masked.

### Enrichment Implementation Notes

The enrichment step *could* be implemented with EventBridge Pipes (zero-Lambda for many cases), but:

- **EventBridge Pipes input transformers cannot read cross-account.** A Pipe in the member account can transform the event payload but cannot read tags or SSM parameters from the central account at transform time; a Pipe in the central account cannot read tags from the source member account. For the member-side enrichment described in this spec (tag inspection + SSM allow-list lookup against parameters held in the same account), Pipes is viable if the enrichment EnrichmentStep is a Lambda in the same account. The Pipes runtime then provides batching, retries, and filtering primitives.
- The framework uses **EventBridge Pipes with a Lambda enrichment step** in the member account where the source supports Pipes (SQS, Kinesis, DynamoDB Streams). For EventBridge-rule-driven sources (Security Hub, GuardDuty, CloudWatch Alarms, Cost Anomaly Detection), the member module continues to use EventBridge rules → Lambda → PutEvents because Pipes cannot consume directly from an event bus.
- The central-side redaction step is a natural fit for EventBridge Pipes (SNS → Pipes with enrichment Lambda → Chatbot). All of its data is in-account.

In both shapes, the Lambda code is the same module (`notifications.handler`) — what differs is which runtime drives it.
