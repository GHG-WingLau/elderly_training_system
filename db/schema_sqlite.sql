-- Elderly Online Training System — SQLite DDL (v4.1)
PRAGMA foreign_keys = ON;

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
  level TEXT CHECK (level IN
    ('Level 0','Level 1','Level 2','Level 3','Level 4')),
  current_cycle INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS training_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL CHECK (week BETWEEN 0 AND 4),
  day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 7),
  exercise_ids TEXT NOT NULL,
  rpe_scores TEXT,
  UNIQUE (user_email, cycle, week, day)
);

CREATE TABLE IF NOT EXISTS weekly_plan (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL,
  exercise_ids TEXT NOT NULL,
  UNIQUE (user_email, cycle, week)
);

CREATE TABLE IF NOT EXISTS rest_assessments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL,
  memory_recall_count INTEGER,
  reflection TEXT,
  sit_to_stand_15s_cycles INTEGER,
  sls_left_sec INTEGER,
  sls_right_sec INTEGER,
  UNIQUE (user_email, cycle, week)
);