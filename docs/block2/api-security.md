# AI API security boundary

The certification API uses Django session authentication and Django's CSRF
middleware. Persistent game lookup always filters by both game ID and the
authenticated owner; an unknown or foreign ID returns the same 404 response.
Only a choice already present in server-side saved state is accepted, limiting
free-form prompt injection at this boundary. Request body and choice lengths are
bounded, and a per-user hourly cache quota protects model spend.

Health exposes readiness booleans only. Configuration requires authentication
and returns model names and operational limits, never credentials or prompts.
Metrics use bounded labels and contain no prompt or identity content. Provider
failures return a controlled 503 and existing state is not persisted.

The original browser routes retain CSRF exemptions for compatibility and are
not part of this secured contract. Migrating their JavaScript calls to CSRF
headers and removing every exemption is tracked as remaining application debt.
