-- Recalcula quartile_snapshot y jif_percentile_snapshot en publicaciones existentes.
--
-- Ejecutar en: Supabase Dashboard → SQL Editor
--
-- Prioridad para cuartil:
--   1. category_ranking ya es 'Q1'-'Q4'
--   2. quartile_rank ya es 'Q1'-'Q4'
--   3. Parsear "X/Y" de quartile_rank  (ranking posicional)
--   4. Parsear "X/Y" de category_ranking
--   5. Derivar desde jif_percentile (>=75→Q1, >=50→Q2, >=25→Q3, else Q4)

UPDATE publications p
SET
  quartile_snapshot = CASE
    WHEN j.category_ranking IN ('Q1', 'Q2', 'Q3', 'Q4')
      THEN j.category_ranking

    WHEN j.quartile_rank IN ('Q1', 'Q2', 'Q3', 'Q4')
      THEN j.quartile_rank

    WHEN j.quartile_rank ~ '^\d+/\d+$'
      THEN CASE
        WHEN SPLIT_PART(j.quartile_rank,'/',1)::float
           / SPLIT_PART(j.quartile_rank,'/',2)::float <= 0.25 THEN 'Q1'
        WHEN SPLIT_PART(j.quartile_rank,'/',1)::float
           / SPLIT_PART(j.quartile_rank,'/',2)::float <= 0.50 THEN 'Q2'
        WHEN SPLIT_PART(j.quartile_rank,'/',1)::float
           / SPLIT_PART(j.quartile_rank,'/',2)::float <= 0.75 THEN 'Q3'
        ELSE 'Q4'
      END

    WHEN j.category_ranking ~ '^\d+/\d+$'
      THEN CASE
        WHEN SPLIT_PART(j.category_ranking,'/',1)::float
           / SPLIT_PART(j.category_ranking,'/',2)::float <= 0.25 THEN 'Q1'
        WHEN SPLIT_PART(j.category_ranking,'/',1)::float
           / SPLIT_PART(j.category_ranking,'/',2)::float <= 0.50 THEN 'Q2'
        WHEN SPLIT_PART(j.category_ranking,'/',1)::float
           / SPLIT_PART(j.category_ranking,'/',2)::float <= 0.75 THEN 'Q3'
        ELSE 'Q4'
      END

    WHEN j.jif_percentile IS NOT NULL
      THEN CASE
        WHEN j.jif_percentile >= 75 THEN 'Q1'
        WHEN j.jif_percentile >= 50 THEN 'Q2'
        WHEN j.jif_percentile >= 25 THEN 'Q3'
        ELSE 'Q4'
      END

    ELSE p.quartile_snapshot
  END,

  jif_percentile_snapshot = CASE
    WHEN j.jif_percentile IS NOT NULL
      THEN j.jif_percentile

    WHEN j.quartile_rank ~ '^\d+/\d+$'
      THEN ROUND(
        CAST(
          (1 - SPLIT_PART(j.quartile_rank,'/',1)::float
                / SPLIT_PART(j.quartile_rank,'/',2)::float
          ) * 100 AS NUMERIC
        ), 2
      )

    WHEN j.category_ranking ~ '^\d+/\d+$'
      THEN ROUND(
        CAST(
          (1 - SPLIT_PART(j.category_ranking,'/',1)::float
                / SPLIT_PART(j.category_ranking,'/',2)::float
          ) * 100 AS NUMERIC
        ), 2
      )

    ELSE p.jif_percentile_snapshot
  END

FROM journals j
WHERE p.journal_id = j.id;

-- Verificación rápida post-migración:
-- SELECT status, quartile_snapshot, COUNT(*)
-- FROM publications
-- GROUP BY status, quartile_snapshot
-- ORDER BY status, quartile_snapshot;
