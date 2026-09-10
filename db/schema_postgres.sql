-- Elderly Online Training System — PostgreSQL DDL (Phase 6 deployment port)
-- Idempotent: applied on first connection (CREATE ... IF NOT EXISTS).
-- Split on ';' by db/database.py after stripping full-line '--' comments:
-- no ';' inside string literals; '--' comments only. (Consequence: no
-- DO $$...$$ guard blocks — they contain internal semicolons; migrations
-- must be plain splitter-safe statements.)
--
-- password_hash / consent_* / sessions are the FINAL schema shape,
-- ACTIVATED by the Step-2 auth hardening — nullable and inert until
-- then (authored now to avoid a second migration on a not-yet-deployed DB).
--
-- Phase 7 (localization, 7.4): users.locale — additive, nullable.
-- Phase 8 (first-run guidance): users.ui_hints — additive, nullable.
-- Phase 9 (retention): users.baseline — additive, nullable; and the
-- FIRST TYPE-WIDENING: rest_assessments.sls_left_sec / sls_right_sec
-- INTEGER -> REAL. Rationale: both the baseline and the weekly forms
-- collect 0.5-step values (#7's motor-precision grid) — int() truncation
-- silently discarded the halves; the Phase 9 chart compares baseline
-- (JSONB, exact) with weekly values and exposed the loss. 0.5-grid
-- values are binary-exact in REAL; existing int values convert losslessly
-- (12 -> 12.0). Existing DBs: one-time tiny-table rewrite via the ALTERs
-- below; fresh DBs get REAL from CREATE; re-running the ALTER on an
-- already-REAL column is a no-op (same type — no rewrite).

CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY,
  username TEXT NOT NULL,
  age INTEGER NOT NULL CHECK (age BETWEEN 18 AND 110),
  sex TEXT CHECK (sex IN ('M','F','U')) DEFAULT 'U',
  sarc_f_score INTEGER,
  calf_score INTEGER,
  balance_score INTEGER,
  chair_stand_score INTEGER,
  red_flags TEXT DEFAULT '',
  total_score INTEGER,
  level TEXT CHECK (level IN ('Level 0','Level 1','Level 2','Level 3','Level 4')),
  current_cycle INTEGER NOT NULL DEFAULT 1,
  password_hash TEXT,
  consent_version TEXT,
  consent_accepted_at TIMESTAMPTZ,
  locale TEXT,
  ui_hints JSONB,
  baseline JSONB
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS locale TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS ui_hints JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS baseline JSONB;

CREATE TABLE IF NOT EXISTS training_progress (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL CHECK (week BETWEEN 0 AND 4),
  day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 7),
  exercise_ids TEXT NOT NULL,
  rpe_scores TEXT,
  UNIQUE (user_email, cycle, week, day)
);

CREATE TABLE IF NOT EXISTS weekly_plan (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL,
  exercise_ids TEXT NOT NULL,
  UNIQUE (user_email, cycle, week)
);

CREATE TABLE IF NOT EXISTS rest_assessments (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL,
  memory_recall_count INTEGER,
  reflection TEXT,
  sit_to_stand_15s_cycles INTEGER,
  sls_left_sec REAL,
  sls_right_sec REAL,
  UNIQUE (user_email, cycle, week)
);

CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);

-- Phase 9 type widening (int -> real) for existing DBs; no-op when
-- already REAL (same type — no rewrite). Splitter-safe: one statement,
-- no internal semicolons.
ALTER TABLE rest_assessments ALTER COLUMN sls_left_sec TYPE real;
ALTER TABLE rest_assessments ALTER COLUMN sls_right_sec TYPE real;

CREATE INDEX IF NOT EXISTS idx_progress_user
  ON training_progress (user_email, cycle);
CREATE INDEX IF NOT EXISTS idx_plan_user
  ON weekly_plan (user_email, cycle);
CREATE INDEX IF NOT EXISTS idx_rest_user
  ON rest_assessments (user_email, cycle);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions (expires_at);