# Changelog

## 2026-10-08 — Add automated collection semver release pipeline

### Added
- GitHub Actions workflow `.github/workflows/collection-release.yml` that bumps, builds, and publishes the `zjleblanc.eda` collection to Ansible Galaxy on pushes to `main` that touch `collections/zjleblanc/eda/`
- Version-bump script `.github/scripts/bump_collection_version.py` implementing commit-prefix-based semver (`major:`/`minor:`/`patch:`, with `feat:`/`fix:` accepted as aliases)
- Guide `docs/collection_release_pipeline.md` covering the pipeline flow, commit message convention, and required `GALAXY_API_TOKEN` secret setup

### Changed
- Added a "Versioning" section to `collections/zjleblanc/eda/README.md` linking to the new release pipeline documentation

## 2026-10-08 — Add Datadog Events API polling integration

### Added
- New local collection `zjleblanc.eda` containing the `dd_poll` source plugin for polling the Datadog Events API v2 with Service Access Token authentication
- Demo rulebook `rulebooks/datadog_event_poll.yml` illustrating the polling pattern without an inbound event stream
- Comprehensive setup guide `docs/datadog_eda_polling_integration.md` for egress-only environments where AAP initiates the connection to Datadog

### Changed
- Updated `README.md` to document the new `collections/` directory and cross-link the polling use case
- Refined `docs/datadog_eda_integration.md` to reference the polling alternative for environments that cannot allow inbound webhook traffic

## 2026-08-25 — Add Datadog OAuth2 JWT event stream guide

### Added
- New guide `docs/datadog_eda_integration_oauth.md` covering Datadog Event Streams using the OAuth2 JWT credential type, with Okta as the worked Identity Provider example
- Okta Authorization Server, EDA credential/event stream, and Datadog OAuth2 webhook configuration steps, plus a testing/validation and troubleshooting section

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
