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

-- body_temp_c holds WEARABLE SKIN temperature (the contract field name is frozen).
-- Core temperature is manual and confirmatory; it will live in its own table, never here.
CREATE TABLE readings (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  astronaut_id         TEXT NOT NULL,
  ts                   TEXT NOT NULL,          -- ISO UTC, e.g. 2026-11-14T08:00:00Z
  heart_rate_bpm       REAL,
  spo2_pct             REAL,
  sleep_hours          REAL,
  body_temp_c          REAL,
  -- quality and context (Ammara, Section 2). Poor readings are stored but never used.
  hr_quality           TEXT    DEFAULT 'good', -- good | poor
  spo2_quality         TEXT    DEFAULT 'good', -- good | poor
  sleep_source         TEXT    DEFAULT 'wearable', -- wearable | manual
  temp_sensor_location TEXT    DEFAULT 'wrist',
  temp_device_id       TEXT    DEFAULT 'wearable-01',
  temp_contact_quality TEXT    DEFAULT 'good', -- good | poor
  temp_dropout         INTEGER DEFAULT 0,      -- 1 = sensor dropout in the preceding period
  UNIQUE (astronaut_id, ts)
);
CREATE INDEX idx_readings_astro_ts ON readings (astronaut_id, ts);

-- One row per alert on every day (history), so charts can show markers.
CREATE TABLE alerts (
  id                 TEXT NOT NULL,            -- a1, a2, ... most severe first, then newest first
  astronaut_id       TEXT NOT NULL,
  position           INTEGER NOT NULL,
  rule_id            TEXT NOT NULL,            -- HR-01 ... DATA-02
  rule               TEXT NOT NULL,
  severity           TEXT NOT NULL,            -- notice | watch | attention
  category           TEXT NOT NULL,            -- physiological | data_quality | setup
  metric             TEXT NOT NULL,
  value              REAL,
  unit               TEXT,
  baseline           REAL,
  delta              REAL,
  baseline_status    TEXT NOT NULL,            -- established | not_established
  ts                 TEXT NOT NULL,
  message            TEXT NOT NULL,
  next_step          TEXT,
  source             TEXT,
  data_quality       TEXT NOT NULL,            -- good | poor | insufficient
  temp_type          TEXT,                     -- skin (TEMP-01 only)
  sensor_location    TEXT,
  device             TEXT,
  measurement_method TEXT,
  PRIMARY KEY (astronaut_id, id)
);
CREATE INDEX idx_alerts_astro_ts ON alerts (astronaut_id, ts);
