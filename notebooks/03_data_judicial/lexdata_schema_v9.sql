
-- LexData v9 — Schema PostgreSQL
-- Ejecutar: psql -U postgres -d lexdata -f lexdata_schema_v9.sql

CREATE SCHEMA IF NOT EXISTS lexdata;

CREATE TABLE IF NOT EXISTS lexdata.ivf_municipios (
    id                        SERIAL PRIMARY KEY,
    municipio                 TEXT NOT NULL,
    anio                      INTEGER,
    vif_total                 NUMERIC DEFAULT 0,
    alimentos_familia_total   NUMERIC DEFAULT 0,
    medidas_proteccion_total  NUMERIC DEFAULT 0,
    inasistencia_total        NUMERIC DEFAULT 0,
    ivf_score_bruto           NUMERIC,
    ivf_score_ponderado       NUMERIC,
    ivf_tasa_100k             NUMERIC,
    nivel_riesgo              TEXT,
    poblacion                 INTEGER,
    alerta                    BOOLEAN DEFAULT FALSE,
    created_at                TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lexdata.hechos_vif (
    id           SERIAL PRIMARY KEY,
    municipio    TEXT,
    departamento TEXT,
    anio         INTEGER,
    cantidad     NUMERIC DEFAULT 1,
    tipo_ciclo   TEXT DEFAULT'VIF',
    fuente       TEXT,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lexdata.inasistencia_alimentaria (
    id           SERIAL PRIMARY KEY,
    municipio    TEXT,
    departamento TEXT,
    anio         INTEGER,
    cantidad     NUMERIC DEFAULT 1,
    tipo_ciclo   TEXT DEFAULT'INASISTENCIA',
    fuente       TEXT,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lexdata.medidas_icbf (
    id           SERIAL PRIMARY KEY,
    municipio    TEXT,
    departamento TEXT,
    anio         INTEGER,
    cantidad     NUMERIC DEFAULT 1,
    tipo_ciclo   TEXT DEFAULT'MEDIDAS_PROTECCION',
    fuente       TEXT,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lexdata.procesos_alimentos (
    id           SERIAL PRIMARY KEY,
    municipio    TEXT,
    departamento TEXT,
    anio         INTEGER,
    cantidad     NUMERIC DEFAULT 1,
    tipo_ciclo   TEXT DEFAULT'ALIMENTOS',
    fuente       TEXT,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ivf_municipio ON lexdata.ivf_municipios(municipio);
CREATE INDEX IF NOT EXISTS idx_ivf_anio      ON lexdata.ivf_municipios(anio);
CREATE INDEX IF NOT EXISTS idx_ivf_alerta    ON lexdata.ivf_municipios(alerta);
