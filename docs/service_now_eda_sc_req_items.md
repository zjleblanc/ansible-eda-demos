# Using ServiceNow Business with Event-Driven Ansible

This guide explains how the Ansible playbook in [`integrations/service_now_business_rule.yml`](../integrations/service_now_business_rule.yml) configures ServiceNow to POST JSON to an Ansible Automation Platform (AAP) **external event stream**, and how [`rulebooks/sc_req_items.yml`](../rulebooks/sc_req_items.yml) consumes those events—including the **Create Label** pattern that tags work in AAP and re-enters the rulebook so the right downstream rule can run.

## End-to-end flow

1. A user submits or updates a **Requested Item** (`sc_req_item`) in the Service Catalog.
2. A ServiceNow **business rule** (advanced script) runs **after** insert/update/delete and calls a **REST message** that `POST`s a JSON body to your AAP event stream URL.
3. **Event-Driven Ansible** receives the HTTP payload as an event (in this repo’s rulebook, via a webhook source while developing; in production, bind the same rulebook to the **Event Stream** in AAP).
4. Rules in `sc_req_items.yml` match on catalog item, modification count, and (for the Terraform path) whether the event was already processed by the label job.

## Prerequisites (AAP)

1. Create an **external event stream** in AAP (EDA) and note:
   - **POST URL** — used as `aap_event_stream` (the playbook sets this on the REST message endpoint).
   - **Bearer token** (or equivalent secret) — used as `aap_event_stream_token` for the `Authorization` header.

2. Deploy the rulebook (or activation) that uses `rulebooks/sc_req_items.yml`, pointed at that event stream.

3. Ensure the **job templates** and **workflow templates** referenced in the rulebook exist in AAP under the **Autodotes** organization (or change the rulebook to match your environment).

## Configure ServiceNow with the Ansible playbook

The playbook uses the `zjleblanc.servicenow.records` role to upsert Table API records idempotently. Define variables (for example in an inventory, `vars` file, or `-e` on the command line):

| Variable | Purpose |
|----------|---------|
| `aap_event_stream` | Full HTTPS URL of the AAP external event stream POST endpoint. |
| `aap_event_stream_token` | Secret passed as `Authorization: Bearer …` on outbound requests from ServiceNow. |
| `sys_user_id` | ServiceNow **sys_user** `sys_id` used in the business rule **filter** (`requested_for=<user>^EQ`) so only that user’s catalog requests trigger the rule (useful for demos and limiting blast radius). |

Optional overrides:

| Variable | Default | Purpose |
|----------|---------|---------|
| `sn_rest_message_name` | `Zach LeBlanc - EDA` | REST message name; must match the script (see below). |
| `sn_rest_message_fn_name` | `POST` | REST message HTTP method function name. |
| `sn_business_rule_name` | `Zach LeBlanc - Service Catalog Requests` | Business rule display name. |
| `sn_business_rule_desc` | (see playbook) | Description on the business rule. |

Run the playbook (example):

```bash
ansible-playbook integrations/service_now_business_rule.yml \
  -e 'aap_event_stream=https://<aap-host>/eda-event-streams/api/eda/v1/external_event_stream/<uuid>/post/' \
  -e 'aap_event_stream_token=<token>' \
  -e 'sys_user_id=<requested_for_user_sys_id>'
```

Tags: tasks are tagged `rest` if you want `ansible-playbook … --tags rest`.

### What the playbook creates in ServiceNow

1. **`sys_rest_message`** — REST message named `sn_rest_message_name`, endpoint `aap_event_stream`, authentication type **no authentication** on the message (credentials are supplied via headers on the function; see next).

2. **`sys_rest_message_headers`** on that message:
   - `Authorization`: `Bearer {{ aap_event_stream_token }}`
   - `Content-Type`: `application/json`

3. **`sys_rest_message_fn`** — HTTP **POST** function inheriting parent auth, same endpoint.

4. **`sys_script` (business rule)** on table **`sc_req_item`** with:
   - **When**: `after`
   - **Advanced**: `true` (script runs)
   - **Insert / Update / Delete**: all enabled
   - **Filter condition**: `requested_for={{ sys_user_id }}^EQ`
   - **Script**: rendered from [`integrations/invoke_rest_message.js.j2`](../integrations/invoke_rest_message.js.j2)

### Business rule script behavior

The template builds a JSON object from the current `sc_req_item` row:

- Iterates fields from the record (skips the raw `variables` field on the row; variables are handled separately).
- For most fields, uses the **internal** value; for **boolean** and **journal_input**, uses **display** values when present.
- Builds `payload.variables` as a map of **variable name → value** from the catalog item’s questions.

It then executes:

```javascript
var request = new sn_ws.RESTMessageV2(REST_MESSAGE_NAME, "{{ sn_rest_message_fn_name }}");
request.setRequestBody(JSON.stringify(payload));
request.setTimeout(1000);
request.execute();
```

So the body AAP receives is a flat Service Catalog request snapshot plus a `variables` object—what the rulebook refers to as `event.payload` (exact nesting depends on how the webhook/event stream wraps the POST body; conditions in the rulebook use `event.payload.…`).

## Receiving events in `rulebooks/sc_req_items.yml`

The rulebook **source** is an `ansible.eda.webhook` listener on port `5003` for local testing. In AAP, you normally attach the same rules file to an **activation** backed by the **external event stream** you configured above, so ServiceNow’s POSTs become EDA events without running a raw webhook on `0.0.0.0`.

### Rules at a glance

| Rule | Idea |
|------|------|
| **Create Label** | First pass for a specific catalog item: run **AAP // Create Label** with `post_events: true` so a follow-up event can carry `labeled_event`. |
| **Provision VM** / **Decommission VM** | Other catalog items (`cat_item` sys_ids): run AWS workflows on first modification (`sys_mod_count == '1'`). |
| **Deploy and Configure VM - Ansible + Terraform** | Runs after labeling: matches on `event.labeled_event` and uses `aap_label` as a **job label** on the workflow. |
| **Catch 'em All** | Debug fallback (`1 == 1`). |

Catalog item and field sys_ids in the rulebook are **environment-specific**; replace them if your ServiceNow instance uses different items.

## How **Create Label** works (label in AAP + second pass)

Some automations need an **Automation Controller label** that identifies the requested item (for example, so a workflow can be limited to instances labeled with that RITM). Doing that inside the first webhook event is awkward because the label does not exist until a controller job runs. This rulebook uses a **two-phase** pattern:

### Phase 1 — incoming ServiceNow event

The **Create Label** rule runs only when **all** of the following hold:

- `event.labeled_event` is **not** defined — so this is the “raw” ServiceNow event, not the follow-up from the label job.
- `event.payload.cat_item` equals the Terraform-related catalog item sys id (`3dfcbfc687633e106a094046cebb3507` in the sample rulebook).
- `event.payload.sys_mod_count == '1'` — typically the first version of the record after submit (tune if your process updates the item multiple times).

**Action:** `run_job_template` for **AAP // Create Label** with:

- `post_events: true` — when the job finishes, EDA emits another event into the same rulebook so downstream rules can run without another ServiceNow POST.
- `job_args.extra_vars` passing `organization`, `label` (RITM number from `event.payload.number`), and `payload` (full Service Catalog payload for the job to use).

The **AAP // Create Label** job template (defined in AAP, not in this repo) should:

1. Create (or ensure) a **controller label** whose name matches the requested item number (or your chosen convention).
2. With `post_events: true`, publish a follow-up event whose structure includes **`labeled_event`**: the original catalog fields **plus** something like **`aap_label`** so workflows can pass `labels: ["{{ event.labeled_event['aap_label'] }}"]`.

Exact mechanics depend on your job playbook (for example `set_stats`, FQCNs, or patterns your team uses for EDA job completion events). The **contract** the rulebook expects is: after the job, an event exists where **`event.labeled_event`** mirrors the Service Catalog payload fields the downstream rule references (`cat_item`, `sys_mod_count`, `variables`, `number`, `sys_id`, `sys_created_by`, `aap_label`, etc.).

### Phase 2 — labeled event drives the right workflow

The rule **Deploy and Configure VM - Ansible + Terraform** matches:

```text
event.labeled_event.cat_item == '<same cat item sys id>' and event.labeled_event.sys_mod_count == '1'
```

It runs the **Terraform // HCP // Azure Deploy and Configure Workflow** with:

- `labels: ["{{ event.labeled_event['aap_label'] }}"]` so the workflow is scoped to the label created in phase 1.
- Extra vars derived from `event.labeled_event` (SSH key, VM size, ServiceNow task metadata, etc.).

**Provision VM** and **Decommission VM** rules instead key only on **different** `cat_item` values on the **first** event (`event.payload…` only), so they do not depend on `labeled_event`—only the Terraform catalog item uses the label-and-republish split.

### Why split Create Label and Deploy?

- **Separation of concerns**: one job establishes controller-side labeling; the workflow consumes that label and heavy infrastructure logic stays in a workflow template.
- **Correct ordering**: the rule engine sees the labeled event only after the label job succeeds (`post_events`), avoiding races where a workflow might start before the label exists.
- **Routing**: the first event is handled exclusively by **Create Label** (for that `cat_item`); the second event is handled by the Terraform rule because `labeled_event` is present and matches—so each pass has a clear condition and you avoid double-firing the same rule on one logical “user request” if you tune `sys_mod_count` and conditions carefully.

## Manual configuration (without Ansible)

If you prefer the UI:

1. Create a **REST message** with endpoint = your event stream URL; add headers **Authorization** (`Bearer <token>`) and **Content-Type** (`application/json`); add a **POST** method.
2. Create an **on After** business rule on **`Requested Item`** (`sc_req_item`), advanced, with the same insert/update/delete and filter as in the playbook.
3. Paste the script from `invoke_rest_message.js.j2` (with `REST_MESSAGE_NAME` and the method name literal strings matching your REST message and method).

## References

- Playbook: [`integrations/service_now_business_rule.yml`](../integrations/service_now_business_rule.yml)
- Script template: [`integrations/invoke_rest_message.js.j2`](../integrations/invoke_rest_message.js.j2)
- Rulebook: [`rulebooks/sc_req_items.yml`](../rulebooks/sc_req_items.yml)
