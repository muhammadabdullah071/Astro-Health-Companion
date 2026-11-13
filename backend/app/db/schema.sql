DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS readings;
DROP TABLE IF EXISTS profile;

CREATE TABLE profile (
  id                 TEXT PRIMARY KEY,
  name               TEXT NOT NULL,
  mission            TEXT NOT NULL,
  mission_start_date TEXT NOT NULL,           -- YYYY-MM-DD (UTC)
  data_label         TEXT NOT NULL DEFAULT 'SIMULATED'
);

CREATE TABLE readings (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  astronaut_id   TEXT NOT NULL,
  ts             TEXT NOT NULL,               -- ISO UTC, e.g. 2026-11-14T08:00:00Z
  heart_rate_bpm REAL,
  spo2_pct       REAL,
  sleep_hours    REAL,
  body_temp_c    REAL,
  UNIQUE (astronaut_id, ts)
);
CREATE INDEX idx_readings_astro_ts ON readings (astronaut_id, ts);

CREATE TABLE alerts (
  id           TEXT PRIMARY KEY,              -- a1, a2, ...
  astronaut_id TEXT NOT NULL,
  position     INTEGER NOT NULL,              -- display order (most severe first)
  rule_id      TEXT NOT NULL,
  rule         TEXT NOT NULL,
  severity     TEXT NOT NULL,                 -- notice | watch | attention
  metric       TEXT NOT NULL,
  value        REAL,
  baseline     REAL,
  ts           TEXT NOT NULL,
  message      TEXT NOT NULL,
  next_step    TEXT,
  source       TEXT
);
