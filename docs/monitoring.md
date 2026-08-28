# Local Monitoring

The development monitoring stack contains Prometheus and Grafana. Django runs
on the host and exposes automatic framework metrics plus application-specific
game and LLM metrics at `/metrics`.

## Start the stack

Start Django on an address reachable from the Prometheus container:

```bash
uv run python src/django/manage.py runserver 0.0.0.0:8000
```

In a second terminal, start Prometheus and Grafana:

```bash
docker compose -f compose.monitoring.yml up -d
```

Open the services:

- Django metrics: <http://localhost:8000/metrics>
- Prometheus: <http://localhost:9090>
- Prometheus targets: <http://localhost:9090/targets>
- Grafana: <http://localhost:3000>

Grafana's local-development credentials default to `admin` / `admin`. Override
them before starting Compose when needed:

```bash
GRAFANA_ADMIN_USER=admin GRAFANA_ADMIN_PASSWORD=replace-me \
  docker compose -f compose.monitoring.yml up -d
```

The Prometheus data source and the **Call To AIdventure Overview** dashboard are
provisioned automatically.

## Verify collection

The Prometheus target named `call-to-aidventure-django` should be `UP`. Useful
queries include:

```promql
up{job="call-to-aidventure-django"}
```

```promql
sum(increase(aidventure_games_started_total[1h])) by (adventure)
```

```promql
histogram_quantile(
  0.95,
  sum(rate(aidventure_llm_request_duration_seconds_bucket[5m])) by (le, operation)
)
```

```promql
sum(rate(aidventure_llm_requests_total[5m])) by (operation, status)
```

```promql
histogram_quantile(
  0.95,
  sum(rate(aidventure_story_turn_ready_duration_seconds_bucket[5m]))
    by (le, adventure)
)
```

To inspect the application metrics directly:

```bash
curl -s http://localhost:8000/metrics | rg 'aidventure_'
```

## Metrics and privacy

Custom metrics are defined in `src/observability/metrics.py`. Labels are limited
to controlled values such as adventure IDs, combat actions, outcome modes, and
LLM operation names. Do not add prompts, story text, choices, usernames, session
IDs, exception messages, or other unbounded/private values as labels.

The LLM duration histogram includes retry delays, so it represents the latency
experienced by the game. `aidventure_llm_attempts_total` counts provider calls,
while `aidventure_llm_requests_total` counts logical operations.

`aidventure_story_turn_ready_duration_seconds` is measured in the browser from
submitting a choice with **Next** until the next set of story choices is rendered
and usable. It includes server processing, LLM calls, network transit, and browser
work. Combat transitions, endings, and failed turns are excluded.

## Stop or reset

Stop the containers while keeping collected data:

```bash
docker compose -f compose.monitoring.yml down
```

Delete Prometheus and Grafana volumes only when a full local reset is intended:

```bash
docker compose -f compose.monitoring.yml down --volumes
```

## Production notes

This stack is intended for local development. Before deployment:

- use strong externally managed Grafana credentials;
- keep `/metrics`, Prometheus, and Grafana on a private network or protect them
  with an authenticated reverse proxy;
- revisit data retention and persistent volume backups;
- change the Prometheus scrape target from `host.docker.internal` to the actual
  Django service name;
- review multi-process metric collection if Django runs under multiple workers.
