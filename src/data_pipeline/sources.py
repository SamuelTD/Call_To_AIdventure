from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .schemas import RawMonster, SourceName


def load_json_source(
    path: Path,
    source: SourceName,
    *,
    source_url: str | None = None,
) -> list[RawMonster]:
    content = path.read_text(encoding="utf-8")
    if path.suffix.casefold() in {".jsonl", ".ndjson"}:
        payload = [json.loads(line) for line in content.splitlines() if line.strip()]
    else:
        payload = json.loads(content)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array")
    file_collected_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    records = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            item = {"invalid_value": item}
        record_payload = item.get("payload", item)
        if not isinstance(record_payload, dict):
            record_payload = {"invalid_value": record_payload}
        name = str(record_payload.get("name") or "").strip()
        source_record_id = str(item.get("source_record_id") or name or f"row-{index + 1}")
        collected_at = item.get("collected_at") or file_collected_at
        records.append(
            RawMonster(
                source=source,
                source_record_id=source_record_id,
                source_url=item.get("source_url") or source_url,
                collected_at=collected_at,
                payload={
                    key: value
                    for key, value in record_payload.items()
                    if key not in {"source", "source_record_id", "source_url", "collected_at"}
                },
            )
        )
    return records
