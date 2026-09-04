from __future__ import annotations

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .normalize import normalize_or_reject
from .schemas import (
    CanonicalMonster,
    MergedMonster,
    RawMonster,
    RejectedRecord,
    RunManifest,
    SourceName,
    SourceReference,
    utc_now,
)
from .sources import load_json_source
from .storage import replace_dataset


SOURCE_PRECEDENCE = (SourceName.CURATED, SourceName.SCRAPED)


@dataclass(frozen=True)
class PipelineResult:
    manifest: RunManifest
    monsters: list[MergedMonster]
    rejected: list[RejectedRecord]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, default=str, sort_keys=True))
            stream.write("\n")


def _merge(records: list[RawMonster]) -> tuple[list[MergedMonster], list[RejectedRecord], int, int]:
    grouped: dict[str, list[tuple[RawMonster, CanonicalMonster]]] = defaultdict(list)
    rejected: list[RejectedRecord] = []
    accepted = 0
    for raw in records:
        normalized, rejection = normalize_or_reject(raw)
        if rejection:
            rejected.append(rejection)
            continue
        accepted += 1
        grouped[normalized.stable_key].append((raw, normalized))

    precedence = {source: index for index, source in enumerate(SOURCE_PRECEDENCE)}
    merged: list[MergedMonster] = []
    conflicts = 0
    for key in sorted(grouped):
        candidates = sorted(grouped[key], key=lambda pair: precedence[pair[0].source])
        selected_raw, selected = candidates[0]
        comparable = [candidate.model_dump() for _, candidate in candidates]
        if any(candidate != comparable[0] for candidate in comparable[1:]):
            conflicts += 1
        merged.append(
            MergedMonster(
                monster=selected,
                sources=[
                    SourceReference(
                        source=raw.source,
                        source_record_id=raw.source_record_id,
                        source_url=raw.source_url,
                        collected_at=raw.collected_at,
                        selected=raw is selected_raw,
                    )
                    for raw, _ in candidates
                ],
            )
        )
    return merged, rejected, accepted, conflicts


def run_pipeline(
    *,
    curated_path: Path,
    scraped_path: Path,
    output_dir: Path,
    db_path: Path | None = None,
) -> PipelineResult:
    started_at = utc_now()
    run_id = f"{started_at:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    sources = {
        SourceName.SCRAPED: load_json_source(
            scraped_path,
            SourceName.SCRAPED,
            source_url="https://www.aidedd.org/monster/",
        ),
        SourceName.CURATED: load_json_source(curated_path, SourceName.CURATED),
    }
    raw_records = [record for source in SOURCE_PRECEDENCE[::-1] for record in sources[source]]
    monsters, rejected, accepted, conflicts = _merge(raw_records)

    run_dir = output_dir / run_id
    raw_path = run_dir / "raw.jsonl"
    clean_path = run_dir / "cleaned.jsonl"
    rejected_path = run_dir / "rejected.jsonl"
    manifest_path = run_dir / "manifest.json"
    _write_jsonl(raw_path, [record.model_dump(mode="json") for record in raw_records])
    _write_jsonl(clean_path, [record.model_dump(mode="json") for record in monsters])
    _write_jsonl(rejected_path, [record.model_dump(mode="json") for record in rejected])

    manifest = RunManifest(
        run_id=run_id,
        started_at=started_at,
        completed_at=utc_now(),
        source_counts={source.value: len(records) for source, records in sources.items()},
        collected=len(raw_records),
        accepted_source_records=accepted,
        rejected=len(rejected),
        merged=len(monsters),
        conflicts=conflicts,
        output_files={
            "raw": str(raw_path),
            "cleaned": str(clean_path),
            "rejected": str(rejected_path),
            "manifest": str(manifest_path),
        },
    )
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    if db_path is not None:
        replace_dataset(db_path, manifest, monsters, rejected)
    return PipelineResult(manifest=manifest, monsters=monsters, rejected=rejected)
