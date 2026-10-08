# zjleblanc.eda

Event-Driven Ansible (EDA) source plugins maintained by [zjleblanc](https://github.com/zjleblanc).

## Plugins

| Plugin | FQCN | Description |
| --- | --- | --- |
| `dd_poll` | `zjleblanc.eda.dd_poll` | Polls the Datadog Events API (v2, Service Access Token auth) and emits new events |

See [`docs/datadog_eda_polling_integration.md`](https://github.com/zjleblanc/ansible-eda-demos/blob/main/docs/datadog_eda_polling_integration.md) in the parent repository for full setup and usage instructions, including Datadog-side and AAP-side configuration.

## Requirements

- `ansible-core >= 2.14`
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

## License

GPL-2.0-or-later
