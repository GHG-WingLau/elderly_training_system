Phase 6, post Step 3. State at authoring: 249 tests green on Postgres(Docker local), password auth + consent v1.1 + logout + remember-me(?t= token) live, debug stripped in production, narration + illustrationslive, support footer on every page.

0 · Prerequisites
 GitHub repo pushed (public — recorded decision; secrets NEVERcommitted; .gitignore verified per DEPLOYMENT §repo-prep)
 Docker Postgres suite green: pytest (conftest defaultsDATABASE_URL to the local compose service) — expect 253
 psycopg.__version__ matches the requirements.txt pin (3.3.5)
1 · Neon
Create a project (region nearest your beta users). Note thepooled connection string (host contains -pooler) for themain branch — production.
Create a branch beta-test (disposable). Note its pooled string.
Pre-deploy suite run against the branch — NEVER against main:TEST_DB_CONFIRM_REMOTE=1 DATABASE_URL=<beta-test pooled string> pytest(the env override exists precisely for a disposable branch; the guardrefuses non-local hosts without it). Expect 253 green. Delete/recreatethe branch afterwards at will.
Autosuspend note: Neon free tier suspends idle computes; the pooledstring keeps first-query latency sub-second after wakeup.
2 · Streamlit Community Cloud
New app → repo / branch main / Main file path: app.py.
Python version: 3.12 (matches the pinned dev runtime).
Advanced → Secrets — paste:database_url = ""Do NOT add dev_tools (its absence is what strips ?debug inproduction — Step 3 decision).
requirements.txt is picked up automatically (streamlit, jsonschema,pytest, psycopg[binary]==3.3.5; edge-tts correctly absent).
First boot: init_db() applies schema_postgres.sql idempotentlyon first connection — verify in the Neon console that the fivetables + indexes exist.
3 · Deployed-URL smoke (the permanent QA lines, on production)
 Register a throwaway account end-to-end: consent checkbox →wizard → hub. Verify the users row in Neon (password_hash,consent_version v1.1, consent_accepted_at).
 Full workout day: breathing (ring animates, auto-stops atprescribed cycles) → exercises (illustrations, narration plays,per-card prescription line) → RPE → summary; training_progressrow in Neon.
 Transitions snap to top (console: one [scroll-reset] line each).
 Support footer: tap the address image on a REAL phone → mail appopens, subject prefilled.
 Remember-me: login → reload → still on hub; bookmark → reopenbookmark → hub. Logout → reload → login page; sessions row gone.
 Device matrix 320/375/414px: no clipped buttons/players; audioplayer 48px; wrapped labels fine.
 Console expectation: the st.iframe sandbox warning appears 2–3×per page — KNOWN-BENIGN platform noise (DECISIONS record). OnlyNEW messages matter.
4 · Beta operations
Invite list first (do not publicize the URL); each user registerswith consent. Instruct: "bookmark the app after your first login"(the hub tip reinforces this).
Feedback channel: Sheepandfish.fit@gmail.com — check daily duringbeta; the footer makes it one tap for users.
Data review: Neon console SQL against main (accepted review path).Useful: consent audit (email, consent_version, consent_accepted_at),engagement (completed days per user), adverse signals (weeklyaverage RPE ≥ 4.0 streaks — the regression logic also handles thisin-app).
Debug controls: unavailable in production by design. For QA traversalof production data, use the Neon console reads (never writes).
5 · Rollback
App: Cloud → redeploy previous commit (app history is per-commit).
Data: Neon → restore point (branch restore) — coordinate with usersif data loss occurs; beta scope makes this acceptable.
6 · Known beta limitations (recorded, accepted)
Bare-URL open requires one login (token rides the URL; bookmark /home-screen / reload-with-full-URL all persist) — bookmark guidanceis the mitigation; P4 (auto-rerun probe) declined for beta.
Token visible in URL/bookmarks; shared link = live session untilexpiry/logout; logout is the invalidation path.
A bookmark made before a later logout holds a dead token (onere-login + re-bookmark recovers).
No email verification on accounts (supervised beta, invite list).