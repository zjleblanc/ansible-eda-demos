# ansible-eda-demos

Demo rulebooks, playbooks, and integrations for **Event-Driven Ansible** (EDA) on Ansible Automation Platform.

Events from observability platforms and ITSMs flow into EDA rulebooks, which match conditions and launch AAP job or workflow templates to remediate issues and provision infrastructure automatically.

## Table of contents

- [Repository layout](#repository-layout)
- [Event streams and source plugins](#event-streams-and-source-plugins)
  - [What are event streams?](#what-are-event-streams)
  - [Why event streams replace source plugins](#why-event-streams-replace-source-plugins)
  - [How event streams replace sources in a rulebook](#how-event-streams-replace-sources-in-a-rulebook)
  - [Legacy source plugin examples](#legacy-source-plugin-examples)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Example Downstream Playbooks](#example-downstream-playbooks)
- [Use Cases](#use-cases)

## Repository layout

```
rulebooks/          EDA rulebooks (event sources, conditions, actions)
playbooks/          Remediation and ITSM playbooks launched by rulebooks
  filter_plugins/   Custom Jinja filters (Dynatrace, ServiceNow helpers)
  tasks/            Shared task files (ServiceNow comments, attachments, state)
integrations/       ServiceNow business rule and REST message setup
files/              Sample event payloads for testing
docs/               How-to guides and screenshots
vars/               Variable files for demo rulebooks
legacy/             Legacy source-plugin and polling rulebook examples
```

## Event streams and source plugins

### What are event streams?

Event streams are a simplified event routing feature introduced in AAP 2.5. They provide a managed, server-side webhook endpoint built into the EDA controller that can receive events from any external system — Dynatrace, Datadog, ServiceNow, GitHub, and others — without requiring a vendor-specific source plugin.

When you create an event stream in the EDA controller, it generates a unique URL. You configure your remote system (observability platform, ITSM, etc.) to POST webhook payloads to that URL. The EDA controller handles authentication, header filtering, and forwarding the events to one or more rulebook activations.

### Why event streams replace source plugins

Earlier versions of EDA relied on **vendor-specific source plugins** to ingest events. Each integration required its own Ansible collection containing a custom source plugin (e.g. `dynatrace.event_driven_ansible.dt_webhook`). These plugins ran inside the rulebook activation process and were responsible for binding to a port, managing the connection, handling authentication, and parsing vendor-specific payload envelopes.

This approach had several drawbacks:

- **Plugin maintenance** — every vendor integration required a dedicated collection that had to be installed in the decision environment and kept up to date.
- **Credential exposure** — API tokens and secrets were passed as source plugin arguments in the rulebook, making them visible in the project source.
- **Payload coupling** — vendor plugins often wrapped the raw payload in an extra envelope (e.g. `event.payload.eventData.name` instead of `event.payload.name`), so switching plugins meant rewriting all conditions.
- **Scaling limits** — each activation opened its own listener; there was no way to share a single inbound endpoint across multiple rulebook activations.

Event streams solve all of these problems. Authentication is configured once in the EDA controller using event stream credentials (HMAC, Basic, Token, OAuth2, ECDSA). The raw webhook payload arrives directly at `event.payload`, so conditions are written against the vendor's native schema. A single event stream endpoint can feed multiple activations, and no vendor collection needs to be installed.

### How event streams replace sources in a rulebook

Rulebooks that target event streams still declare a source entry, but it serves only as a **placeholder** that gets swapped out at activation time.

```yaml
sources:
  # will be replaced by Event Stream
  - name: Example Event Source
    ansible.eda.webhook:
      host: 0.0.0.0
      port: 5010
```

When you create a rulebook activation in the EDA controller, you map each source to an event stream through the **Event streams** mapping UI. The controller replaces the source type, source name, and arguments with its internal `ansible.eda.pg_listener` source backed by the event stream. Filters, rules, conditions, and actions are all unaffected — only the source entry is swapped.

### Legacy source plugin examples

The `legacy/` directory holds reference rulebooks from earlier AAP versions that use vendor-specific source plugins or polling instead of event streams:

| Legacy rulebook | Source plugin | Notes |
|-----------------|--------------|-------|
| `dynatrace_webhook.yml` | `dynatrace.event_driven_ansible.dt_webhook` | AAP ≤ 2.4; payloads nested under `event.payload.eventData` |
| `remediate_disk_usage_nr.yml` | `ansible.eda.webhook` | New Relic webhook (no vendor plugin, but pre-event-stream pattern) |
| `remediate_linux.yml` | `ansible.eda.webhook` | Linux remediation demo webhook |
| `zabbix.yml` | `ansible.eda.webhook` | Zabbix event webhook |
| `dynatrace_problems.yml` | `dynatrace.event_driven_ansible.dt_esa_api` | Polled the Dynatrace Problems API on a 30-second interval |
| `snow_tables.yml` | `cloin.eda.snow_records` | Polled ServiceNow `sc_req_item` and `incident` tables every second |

## Prerequisites

- Ansible Automation Platform with an EDA controller
- Credentials configured in AAP for ServiceNow, AWS, Dynatrace, etc. (not stored in this repo)

## Usage

Import this project into AAP, then create an EDA rulebook activation pointing at the desired rulebook. The rulebook's `run_job_template` or `run_workflow_template` actions reference job templates that must already exist in the **Autodotes** organization.

For local testing with `ansible-rulebook`:

```bash
ansible-rulebook --rulebook rulebooks/demo_webhook.yml -i inventory -S SOURCE_ARGS
```

## Example Downstream Playbooks

| Playbook | Purpose |
|----------|---------|
| `resolve_problem.yml` | Close a Dynatrace problem and its ServiceNow incident with attachments |
| `remediate_memory_usage.yml` | Kill high-memory processes from an allowlist, update ServiceNow |
| `remediate_onagent.yml` | Reboot EC2 instance to restore a Dynatrace OneAgent |
| `rollback_nginx_site.yml` | Restore a demo nginx site; escalate to ServiceNow if threshold exceeded |
| `no_op.yml` | Debug dump of `ansible_eda` variables |

## Use Cases

- [ServiceNow catalog integration](docs/service_now_eda_sc_req_items.md)
- [Disk space remediation lab](docs/expand_disk_space.md)
- [Resolve Dynatrace problem demo](docs/resolve_problem.md)
- [Datadog + EDA integration](docs/datadog_eda_integration.md)
