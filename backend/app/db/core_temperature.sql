-- Manual CORE temperature entries. Deliberately a table of its own (never a column of readings):
-- skin and core are different measurements and must never be mixed. Nothing in the rules engine reads this table.
-- IF NOT EXISTS so an older database picks it up on start without being rebuilt.
CREATE TABLE IF NOT EXISTS core_temperatures (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  astronaut_id TEXT NOT NULL,
  ts           TEXT NOT NULL,          -- when it was measured, ISO UTC (2026-11-14T09:30:00Z)
  core_temp_c  REAL NOT NULL,
  method       TEXT NOT NULL,          -- oral | tympanic | temporal | axillary | rectal | other
  note         TEXT,
  recorded_at  TEXT NOT NULL           -- when it was entered, ISO UTC
);
CREATE INDEX IF NOT EXISTS idx_core_astro_ts ON core_temperatures (astronaut_id, ts);
