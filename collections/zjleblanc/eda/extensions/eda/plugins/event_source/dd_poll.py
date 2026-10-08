"""dd_poll.py.

An Event-Driven Ansible source plugin that polls the Datadog Events API for
new events and emits them onto the ansible-rulebook event queue.

This is a locally-maintained, security-hardened source plugin with the
following design choices:
  * Defaults to the Datadog v2 Events API with bearer-token authentication
    (a Service Access Token or Personal Access Token), which Datadog now
    recommends over static API key / Application key pairs.
  * Secrets are read from environment variables (DD_BEARER_TOKEN, or the
    legacy DD_API_KEY / DD_APP_KEY) by default, so no credential ever needs
    to be written into rulebook YAML or AAP survey/extra_vars. In an AAP
    rulebook activation, set these as environment variables sourced from a
    credential, not as plugin arguments.
  * Retains a deprecated v1 API fallback (api_key + app_key) only for
    environments that have not yet migrated to a Service Access Token.
"""

DOCUMENTATION = r"""
---
module: dd_poll
short_description: Poll the Datadog Events API for new events
description:
  - Polls the Datadog Events API on a fixed interval and emits newly observed
    events onto the ansible-rulebook event queue.
  - Authenticates to the Datadog v2 Events API using a bearer token -- a
    Datadog Service Access Token (SAT, prefixed C(ddsat_)) or Personal Access
    Token (PAT, prefixed C(ddpat_)). This is Datadog's current recommended
    authentication model for automation.
  - Falls back to the deprecated v1 Events API (static C(api_key) +
    C(app_key)) only when a bearer token is not supplied, for environments
    that have not yet migrated to a Service Access Token. New integrations
    should not use this mode.
version_added: "1.0.0"
author: "Zach LeBlanc (@zjleblanc)"
options:
  token:
    description:
      - Datadog bearer token (Service Access Token or Personal Access Token)
        used to authenticate to the Datadog v2 Events API.
      - Can also be supplied via the C(DD_BEARER_TOKEN) environment variable.
        Prefer the environment variable so the token never appears in the
        rulebook or an AAP job's extra_vars -- inject it into the rulebook
        activation's environment from an AAP credential.
      - Required unless the deprecated C(api_key) / C(app_key) pair is
        supplied instead.
    type: str
    required: false
  api_key:
    description:
      - Deprecated. Legacy Datadog API key, used together with C(app_key)
        to call the v1 Events API when a bearer C(token) is not supplied.
      - Can also be supplied via the C(DD_API_KEY) environment variable.
      - Datadog has marked Application Keys as a legacy authentication
        method; migrate to a Service Access Token and C(token) instead.
    type: str
    required: false
  app_key:
    description:
      - Deprecated. Legacy Datadog Application key, used together with
        C(api_key) to call the v1 Events API.
      - Can also be supplied via the C(DD_APP_KEY) environment variable.
    type: str
    required: false
  site:
    description:
      - The Datadog site to query, for example C(datadoghq.com),
        C(datadoghq.eu), C(us3.datadoghq.com), C(us5.datadoghq.com),
        C(ap1.datadoghq.com), or C(ddog-gov.com).
      - May also be a fully-qualified API URL (C(https://...)) if you need
        to point at a non-standard endpoint.
    type: str
    default: "datadoghq.com"
  interval:
    description:
      - Polling interval, in seconds.
    type: int
    default: 10
  lookback_minutes:
    description:
      - On every poll, how many minutes back to search for events. Datadog
        events can take a short time to land in the event stream, so a
        small overlapping lookback window avoids missing events;
        already-emitted event IDs are tracked in-memory and de-duplicated
        so overlapping polls do not emit the same event twice.
    type: int
    default: 5
  sources:
    description:
      - Optional list of Datadog event sources to filter on, for example
        C([nagios, chef]). Maps to the v2 API's C(filter[sources]) parameter.
      - Ignored when falling back to the deprecated v1 API.
    type: list
    elements: str
    required: false
  tags:
    description:
      - Optional list of tags to filter events on, for example
        C(["env:prod", "service:checkout"]). Maps to the v2 API's
        C(filter[tags]) parameter.
      - Ignored when falling back to the deprecated v1 API.
    type: list
    elements: str
    required: false
  priority:
    description:
      - Optional event priority filter.
      - Ignored when falling back to the deprecated v1 API.
    type: str
    choices: ["low", "normal"]
    required: false
notes:
  - >-
    Each emitted event is a flattened dict with the fields Datadog returns
    for the event, typically including C(id), C(title), C(message),
    C(hostname), C(priority), C(status), C(tags), C(source_type_name),
    C(monitor_id), and C(timestamp). Rulebook conditions reference these
    directly off the event root, for example
    C(event.title is match("Free Disk Space Below", ignorecase=true)) --
    there is no C(event.payload) wrapper here, unlike event-stream-sourced
    events.
  - Requires the C(aiohttp) Python package to be installed alongside
    C(ansible-rulebook) (installed automatically when this collection is
    built into a decision environment, via the collection's
    C(requirements.txt)).
  - "Recommended setup: create a Datadog service account, generate a
    Service Access Token scoped to the C(events_read) authorization scope,
    store it as an AAP credential, and inject it into the rulebook
    activation as the C(DD_BEARER_TOKEN) environment variable. See
    C(docs/datadog_eda_polling_integration.md) in this collection's parent
    repository for the full walkthrough."
  - This plugin polls Datadog directly from the rulebook activation process
    and does not require an AAP Event Stream. It is a complementary pattern
    to the webhook / Event Stream approach used elsewhere in this repo --
    see C(rulebooks/datadog_event_stream.yml).
"""

EXAMPLES = r"""
- name: Poll Datadog events using a Service Access Token (recommended)
  hosts: all
  sources:
    - zjleblanc.eda.dd_poll:
        interval: 15
        lookback_minutes: 5
        # token is read from the DD_BEARER_TOKEN environment variable set on
        # the rulebook activation; it is intentionally not set here.
  rules:
    - name: Catch all Datadog events
      condition: event.id is defined
      action:
        debug:

- name: Poll Datadog events, filtered by source/tag/priority
  hosts: all
  sources:
    - zjleblanc.eda.dd_poll:
        interval: 10
        sources:
          - my_apps
        tags:
          - "env:prod"
        priority: normal
  rules:
    - name: Catch all Datadog events
      condition: event.id is defined
      action:
        debug:

- name: Legacy v1 authentication (deprecated -- migrate to a Service Access Token)
  hosts: all
  sources:
    - zjleblanc.eda.dd_poll:
        interval: 10
        # api_key / app_key read from DD_API_KEY / DD_APP_KEY if omitted here
  rules:
    - name: Catch all Datadog events
      condition: event.id is defined
      action:
        debug:
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp

LOGGER = logging.getLogger(__name__)

V2_EVENTS_PATH = "/api/v2/events"
V1_EVENTS_PATH = "/api/v1/events"

# Cap on the in-memory de-dup set so a long-running activation doesn't grow
# its memory footprint unbounded.
MAX_SEEN_EVENTS = 10000


def _site_to_api_host(site: str) -> str:
    """Translate a Datadog "site" value into its API base URL."""
    site = (site or "datadoghq.com").strip()
    if site.startswith("http://") or site.startswith("https://"):
        return site.rstrip("/")
    return f"https://api.{site}"


def _as_list(value: Optional[Any]) -> Optional[List[str]]:
    """Normalize a str-or-list argument into a list, or None if unset."""
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    return list(value)


async def _poll_v2(
    session: aiohttp.ClientSession,
    api_host: str,
    token: str,
    start_ts: int,
    end_ts: int,
    sources: Optional[List[str]],
    tags: Optional[List[str]],
    priority: Optional[str],
) -> Dict[str, Any]:
    """Query the Datadog v2 Events API using bearer-token authentication.

    No credential is ever placed in the URL/query string -- the token is
    sent only in the Authorization header.
    """
    url = f"{api_host}{V2_EVENTS_PATH}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    params: Dict[str, str] = {
        "filter[from]": str(start_ts),
        "filter[to]": str(end_ts),
    }
    if sources:
        params["filter[sources]"] = ",".join(sources)
    if tags:
        params["filter[tags]"] = ",".join(tags)
    if priority:
        params["filter[priority]"] = priority

    async with session.get(url, headers=headers, params=params) as response:
        LOGGER.debug("Datadog v2 events poll HTTP status: %s", response.status)
        response.raise_for_status()
        return await response.json()


async def _poll_v1(
    session: aiohttp.ClientSession,
    api_host: str,
    api_key: str,
    app_key: str,
    start_ts: int,
    end_ts: int,
) -> Dict[str, Any]:
    """Query the deprecated Datadog v1 Events API with a static key pair.

    Deprecated: Datadog has marked Application Keys as a legacy
    authentication method. Prefer a Service Access Token with the v2 API.
    """
    url = f"{api_host}{V1_EVENTS_PATH}"
    params = {
        "start": str(start_ts),
        "end": str(end_ts),
        "api_key": api_key,
        "application_key": app_key,
    }
    async with session.get(url, params=params) as response:
        LOGGER.debug("Datadog v1 events poll HTTP status: %s", response.status)
        response.raise_for_status()
        return await response.json()


def _normalize_events(payload: Dict[str, Any], v2: bool) -> List[Dict[str, Any]]:
    """Flatten the v1/v2 response shapes into a common list of event dicts.

    The v2 Events API nests the fields rulebook conditions actually care
    about (title, hostname, priority, status, tags, source_type_name,
    monitor_id, ...) two levels deep:

        data[] -> attributes -> attributes -> {title, hostname, ...}

    with a slimmer summary (message/tags/timestamp) one level up. This
    flattens both levels into a single dict per event, so rulebook
    conditions can use e.g. ``event.title`` / ``event.hostname`` directly,
    matching the ergonomics of the v1 API and the webhook/event-stream
    payloads used elsewhere in this repo.
    """
    if v2:
        events = []
        for item in payload.get("data", []) or []:
            outer = item.get("attributes", {}) or {}
            inner = outer.get("attributes", {}) or {}
            event = dict(inner)
            event.setdefault("message", outer.get("message"))
            event.setdefault("tags", outer.get("tags"))
            event.setdefault("timestamp", outer.get("timestamp"))
            event["id"] = item.get("id")
            events.append(event)
        return events
    return payload.get("events", []) or []


def _event_key(event: Dict[str, Any]) -> Tuple[Any, Any]:
    """Build a de-dup key for an event across v1/v2 payload shapes."""
    timestamp = event.get("date_happened") or event.get("timestamp")
    return (event.get("id"), timestamp)


async def main(queue: asyncio.Queue, args: Dict[str, Any]) -> None:
    """Entry point invoked by ansible-rulebook."""
    interval = int(args.get("interval", 10))
    lookback_minutes = int(args.get("lookback_minutes", 5))
    site = args.get("site") or "datadoghq.com"
    api_host = _site_to_api_host(site)

    # Prefer plugin arguments if explicitly set, otherwise fall back to
    # environment variables so secrets stay out of rulebook YAML.
    token = args.get("token") or os.environ.get("DD_BEARER_TOKEN")
    api_key = args.get("api_key") or os.environ.get("DD_API_KEY")
    app_key = args.get("app_key") or os.environ.get("DD_APP_KEY")

    sources = _as_list(args.get("sources"))
    tags = _as_list(args.get("tags"))
    priority = args.get("priority")

    use_v2 = bool(token)

    if not use_v2 and not (api_key and app_key):
        raise ValueError(
            "dd_poll requires either a bearer `token` (DD_BEARER_TOKEN) for "
            "the recommended Datadog v2 Events API, or a legacy `api_key` + "
            "`app_key` pair (DD_API_KEY / DD_APP_KEY) for the deprecated v1 "
            "API. Neither was supplied."
        )

    if not use_v2:
        LOGGER.warning(
            "dd_poll is using the deprecated Datadog v1 Events API with a "
            "static api_key/app_key pair. Migrate to a Service Access Token "
            "and the `token` option (DD_BEARER_TOKEN) -- Datadog has marked "
            "Application Keys as a legacy authentication method."
        )

    seen_events: Set[Tuple[Any, Any]] = set()
    # Events can take a short time to land in Datadog's event stream, so
    # start the first poll with a small lookback window.
    start_time = time.time() - (lookback_minutes * 60)

    async with aiohttp.ClientSession() as session:
        while True:
            end_time = time.time()
            start_ts = int(start_time)
            end_ts = int(end_time)

            try:
                if use_v2:
                    payload = await _poll_v2(
                        session,
                        api_host,
                        token,
                        start_ts,
                        end_ts,
                        sources,
                        tags,
                        priority,
                    )
                else:
                    payload = await _poll_v1(
                        session, api_host, api_key, app_key, start_ts, end_ts
                    )
            except aiohttp.ClientResponseError as exc:
                LOGGER.error("Datadog events poll failed: %s", exc)
                await asyncio.sleep(interval)
                continue
            except aiohttp.ClientError as exc:
                LOGGER.error("Datadog events poll connection error: %s", exc)
                await asyncio.sleep(interval)
                continue

            for event in _normalize_events(payload, use_v2):
                key = _event_key(event)
                if key in seen_events:
                    continue
                seen_events.add(key)
                await queue.put(event)

            if len(seen_events) > MAX_SEEN_EVENTS:
                seen_events.clear()

            await asyncio.sleep(interval)

            # Re-widen the lookback window on every poll so late-arriving
            # events are still caught.
            start_time = time.time() - (lookback_minutes * 60)


if __name__ == "__main__":
    # Standalone smoke-test: `python3 dd_poll.py` with DD_BEARER_TOKEN (or
    # DD_API_KEY/DD_APP_KEY) exported in the environment. Prints events to
    # stdout instead of putting them on an ansible-rulebook queue.
    logging.basicConfig(level=logging.INFO)

    class MockQueue:
        async def put(self, event):
            print(event)

    cli_args = {
        "token": os.environ.get("DD_BEARER_TOKEN"),
        "api_key": os.environ.get("DD_API_KEY"),
        "app_key": os.environ.get("DD_APP_KEY"),
        "site": os.environ.get("DD_SITE", "datadoghq.com"),
        "interval": int(os.environ.get("INTERVAL", "10")),
        "lookback_minutes": int(os.environ.get("LOOKBACK_MINUTES", "5")),
    }
    asyncio.run(main(MockQueue(), cli_args))
