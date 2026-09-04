-- Q1: final application dataset, with quality filters and deterministic order.
SELECT m.id, m.name, m.armor, m.HP, m.challenge_rating, m.description
FROM monsters AS m
WHERE m.HP > 0
  AND m.armor >= 0
  AND (m.challenge_rating IS NULL OR m.challenge_rating BETWEEN 0 AND 100)
ORDER BY m.name COLLATE NOCASE;

-- Q2: lineage of each canonical record across collection sources.
SELECT m.name, s.source, s.source_record_id, s.source_url,
       s.collected_at, s.selected, s.ingestion_run_id
FROM monsters AS m
JOIN monster_sources AS s ON s.monster_id = m.id
WHERE m.id = :monster_id
ORDER BY s.selected DESC, s.source;

-- Q3: quality summary for an ingestion run.
SELECT r.id, r.collected_count, r.accepted_count, r.rejected_count,
       r.merged_count, r.conflict_count,
       COUNT(DISTINCT s.source) AS distinct_sources
FROM ingestion_runs AS r
LEFT JOIN monster_sources AS s ON s.ingestion_run_id = r.id
WHERE r.id = :run_id
GROUP BY r.id;

-- Q4: dataset grouped by challenge rating for API and report analysis.
SELECT challenge_rating, COUNT(*) AS monster_count,
       ROUND(AVG(HP), 2) AS average_hp,
       ROUND(AVG(armor), 2) AS average_armor
FROM monsters
WHERE challenge_rating IS NOT NULL
GROUP BY challenge_rating
ORDER BY challenge_rating;
