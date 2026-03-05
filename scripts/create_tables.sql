-- CECAN Vercel - Crear tablas en Supabase
-- Ejecutar en: https://supabase.com/dashboard/project/ujitdikwkaibdppbzddi/sql/new

CREATE TABLE IF NOT EXISTS journals (
    id          SERIAL PRIMARY KEY,
    issn        VARCHAR(10),
    eissn       VARCHAR(10),
    title       VARCHAR(500) NOT NULL,
    title_abbrev        VARCHAR(200),
    iso_abbrev          VARCHAR(200),
    year                INTEGER,

    -- Métricas de impacto
    impact_factor       FLOAT,
    impact_factor_5yr   FLOAT,
    eigenfactor         FLOAT,
    article_influence   FLOAT,
    immediacy_index     FLOAT,
    norm_eigenfactor    FLOAT,

    -- Rankings
    quartile_rank           VARCHAR(5),
    jif_percentile          FLOAT,
    category_ranking        VARCHAR(100),
    categories_code         VARCHAR(200),
    categories_description  TEXT,
    edition                 VARCHAR(20),

    -- Editorial
    publisher_name  VARCHAR(500),
    country         VARCHAR(100),
    address         TEXT,

    -- Citas
    total_cites     INTEGER,
    cited_half_life FLOAT,

    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_journals_issn  ON journals(issn);
CREATE INDEX IF NOT EXISTS ix_journals_eissn ON journals(eissn);

CREATE TABLE IF NOT EXISTS publications (
    id      SERIAL PRIMARY KEY,
    title   VARCHAR(1000),
    doi     VARCHAR(300) UNIQUE,
    abstract TEXT,
    year    INTEGER,
    volume  VARCHAR(50),
    issue   VARCHAR(50),
    pages   VARCHAR(100),

    -- Archivo PDF
    pdf_filename        VARCHAR(500),
    pdf_storage_path    VARCHAR(1000),

    -- Revista vinculada
    journal_id          INTEGER REFERENCES journals(id),
    journal_issn_raw    VARCHAR(10),

    -- Métricas snapshot
    impact_factor_snapshot  FLOAT,
    quartile_snapshot       VARCHAR(5),
    jif_percentile_snapshot FLOAT,

    -- Estado
    status                  VARCHAR(50) DEFAULT 'uploaded',
    doi_extraction_method   VARCHAR(50),
    openalex_data           TEXT,

    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);
