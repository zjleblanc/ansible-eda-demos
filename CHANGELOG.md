# Changelog

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
