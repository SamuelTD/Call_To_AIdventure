# Dataset API access and security decisions

The certification API is read-only. Monster collection and detail endpoints are
public because they expose non-personal reference data already used by the
public game. Ingestion summaries require an authenticated Django session and a
staff account because manifests can contain operational source information.

The API uses parameterized SQL, allow-listed ordering fields, bounded pagination
(maximum 100 records), typed numeric filters and a consistent error envelope.
There are no certification write endpoints, so CSRF is not applicable to this
surface. Existing game write endpoints are outside this dataset API and should
be migrated away from their historical CSRF exemptions as a separate regression-
tested security change.

The development server has no distributed rate limiter. Production deployment
must apply per-IP limits at the reverse proxy: a proposed starting policy is 60
dataset requests per minute with a short burst allowance. A multi-instance
application-level limit would require shared state such as Redis. This control
is documented rather than simulated with process-local memory, which would not
provide meaningful production protection.

Interactive documentation is available at `/api/v1/docs/`; its rendering assets
come from the public unpkg CDN. The underlying OpenAPI contract remains locally
available at `/api/v1/openapi.yaml` when the CDN is unavailable.
