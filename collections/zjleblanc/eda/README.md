# zjleblanc.eda

Event-Driven Ansible (EDA) source plugins maintained by [zjleblanc](https://github.com/zjleblanc).

## Plugins

| Plugin | FQCN | Description |
| --- | --- | --- |
| `dd_poll` | `zjleblanc.eda.dd_poll` | Polls the Datadog Events API (v2, Service Access Token auth) and emits new events |

See [`docs/datadog_eda_polling_integration.md`](../../../docs/datadog_eda_polling_integration.md) in the parent repository for full setup and usage instructions, including Datadog-side and AAP-side configuration.

## Requirements

- `ansible-core >= 2.16`
- Python dependency: `aiohttp` (see `requirements.txt`) -- installed automatically when this collection is built into a decision environment.

## Installation

```bash
ansible-galaxy collection install zjleblanc.eda
```

For Ansible Automation Platform, add this collection to the `galaxy` dependencies of your decision environment definition so it is available to rulebook activations:

```yaml
# execution-environment.yml
dependencies:
  galaxy:
    collections:
      - name: zjleblanc.eda
```

## Versioning

This collection's version is bumped and published to Ansible Galaxy
automatically by a GitHub Actions pipeline whenever a change under this
directory is pushed to `main`. The bump level (`major`/`minor`/`patch`) is
derived from commit message prefixes (`major:`, `minor:`, `patch:`, with
`feat:`/`fix:` accepted as aliases of `minor:`/`patch:`).

See [`docs/collection_release_pipeline.md`](../../../docs/collection_release_pipeline.md)
in the parent repository for the full commit message convention, pipeline
behavior, and required secrets.

## License

GPL-2.0-or-later
