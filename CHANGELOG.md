# Changelog

## 2026-08-20 — Update Dynatrace EDA demo to support OpenFlake

### Added
- OpenFlake remediation rule to `dynatrace_event_stream.yml` to trigger specialized AWS workflows for flake-branded hosts

### Changed
- Refined generic disk remediation rule in `dynatrace_event_stream.yml` to use case-insensitive matching
- Cleaned up arrow documentation assets by removing unused icon groups

## 2026-08-20 — Add Datadog documentation

### Added
- Comprehensive guide for Datadog EDA integration, including webhook configuration and monitor setup
- Supporting screenshots and logo assets for Datadog integration documentation

## 2026-08-17 — Variablize and refine OpenFlake provisioning in ServiceNow rulebook

### Added
- Enabled OpenFlake Decommission VM rule in `sc_req_items.yml`

### Changed
- Variablized catalog item IDs for OpenFlake provisioning and decommissioning
- Updated `sys_mod_count` triggers to 0 to match OpenFlake's initial record creation events

## 2026-08-16 — Consolidate legacy rulebooks under legacy/

### Changed
- Renamed `archive/` to `legacy/` and updated README references to use legacy terminology
- Moved Dynatrace webhook, New Relic disk remediation, Linux remediation, and Zabbix rulebooks from `rulebooks/` into `legacy/` alongside the former archive polling examples

## 2026-08-16 — Add OpenFlake VM provisioning to ServiceNow rulebook

### Added
- OpenFlake Provision VM rule that triggers AWS // Provisioning Workflow // OpenFlake on matching catalog items
- Commented placeholder for a future OpenFlake Decommission VM rule

### Changed
- Renamed the ServiceNow requested-items rulebook and event source to cover Standard and OpenFlake paths

## 2026-08-16 — Explain event streams and legacy source plugin architecture

### Changed
- Replaced event source table in README with a full explanation of event streams, how they improve on vendor-specific source plugins, how source entries are swapped at activation time, and which rulebooks are legacy examples

## 2026-08-16 — Add project documentation and changelog

### Added
- Comprehensive README with repository layout, playbook reference, prerequisites, and usage instructions
- CHANGELOG.md to track project changes
