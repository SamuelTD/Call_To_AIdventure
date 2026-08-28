# GDPR processing register and operating procedures

This document is a technical project record, not legal advice. The project
owner must confirm the stated legal bases and retention periods.

| Processing | Data subjects and fields | Purpose | Proposed legal basis | Recipients | Retention |
|---|---|---|---|---|---|
| Account management | Username, email, password hash, login timestamps | Authentication and account access | Contract / requested service | Application operator | Until account deletion or documented inactivity policy |
| Saved games | Account ID, adventure progress, character state, timestamps | Resume and review gameplay | Contract / requested service | User and application operator | Active saves until account deletion; finished saves 365 days |
| Character templates | Account ID, fictional character attributes | Reuse character configuration | Contract / requested service | User and application operator | Until user or account deletion |
| Technical logs | IP/request metadata may occur in server logs | Security and incident diagnosis | Legitimate interests, subject to confirmation | Application operator/host | 30 days proposed |

Monster, adventure and world-lore records are public/reference game content and
are not intended to contain personal data. Rejected pipeline payloads must be
reviewed before sharing as evidence.

## Data-subject procedures

- Access/portability: verify the requester, then run
  `python src/django/manage.py export_user_data USERNAME --output export.json`.
- Rectification: users can replace character templates; account fields can be
  corrected through Django administration after identity verification.
- Erasure: delete the Django user after identity verification. Foreign-key
  cascades delete their saves and templates; this behavior is tested.
- Retention: preview with
  `python src/django/manage.py cleanup_retention --days 365`; execute only after
  review by adding `--apply`.

Exports contain personal data. Store them outside source control, transmit them
securely, confirm delivery, then delete the temporary copy according to the
request procedure.

## Backup and restore

Stop writes or use SQLite's online backup command before copying databases. For
the local demonstration, rebuild public game data from versioned inputs rather
than treating `data.db` as the authoritative backup. Back up the Django database
to encrypted, access-controlled storage and test restoration separately. Never
commit either generated database or a user export.
