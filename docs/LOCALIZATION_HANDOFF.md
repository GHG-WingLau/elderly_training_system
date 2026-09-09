Context pack for the localization phase (Cantonese zh-HK + Traditional-Chinese Mandarin)
Handoff date: 2026-09-07, at the close of Phase 6 (post-MVP UI/UX changes#1–#14 + beta deployment). This document is self-contained. Pair it withthe files in §9.

0. How to use this document
Paste into the new chat, as the opening message: (1) this file, (2)docs/DECISIONS.md, (3) docs/STATE.md, (4) the v4.1 reference PDF (§7Errata inside). The rules in §2 are binding, not advisory — every one ofthem was paid for.

1. Where the system stands
Live beta: Streamlit Community Cloud (public GitHub repo) → NeonPostgres MAIN branch = production; "beta-test" branch = disposablesuite-validation target (drop/recreate freely).
263 tests green (local Docker Postgres; full suite also validatedremote on Neon beta-test). Stack: Python 3.12, Streamlit 1.62.0(EXACT pin), psycopg 3.3.5, pytest + AppTest.
Complete feature set: locked onboarding wizard (SARC-F + baseline),24 exercise cards + 5 breathing practices with approved EN clinicalcopy, pure-CSS breathing metronome (start/stop + auto-stop), JPEGillustrations, TTS narration (29 EN mp3s + manifest drift guard),per-card prescription reminders, autoregulation + regression,password auth (PBKDF2-HMAC-SHA256) + consent v1.1 evidence columns +logout + remember-me (?t= URL token, 30-day DB sessions),transition-gated scroll reset, anti-harvest support footer(Sheepandfish.fit@gmail.com), self-healing DB connection (Neonlifecycle), bookmark tip, dev tools stripped in production.
2. Binding operating rules (carried from all prior phases)
components/locked/ (sarc_f_assessment, baseline_timers,onboarding_wizard) — clinical + tech-lead sign-off to modify;LABEL_* constants are part of the test contract.
Clinical values live in data/*.json — never hardcoded, neverinvented. LOCALIZATION EXTENSION: translated clinical/legal copy isNEW clinical content — each locale's copy requires its ownteam-approved source document before it becomes data (the samesign-off channel the EN approvals used).
Tests locate widgets by label (tests/helpers_e2e.py iteration).LOCALIZATION EXTENSION: rendering a label in another locale IS alabel change — matching test selectors (or data-driven label reads)update in the same change.
WCAG 2.1 AA baseline — ≥18px font, ≥48×48px touch targets, AAcontrast — sign-off conditions, not preferences. Holds for CJK(see §7.7).
Pinned dependency set — streamlit==1.62.0 (EXACT; guarded bytests/test_environment.py::test_streamlit_pin_is_exact — Cloudresolved a loose ">=1.62.0" to 1.63.0 once, hence the guard),psycopg[binary]==3.3.5, jsonschema==4.23.0, pytest==8.3.3. No newruntime deps without discussion; edge-tts is dev-only (never inrequirements.txt; tools/generate_audio.py).
Full-file replacements only (never "modify in place"); pytest afterevery change; prototype-first for any platform-dependent mechanism;PASTE any file before replacing it blind (the source chat neverblind-replaced an unseen file — that rule prevented severalregressions).Process corollaries (all learned from real failures): reconcile thecollected test count after every run (a prediction/actual mismatchmeans something was silently added or dropped — it once caught adropped contract test); give newest-written lines the most skepticalreview (three consecutive defect sets lived exclusively there);observation must not perturb the observed state (transient tri-stateoracles: assert the FORBIDDEN value over a window, with a negativecontrol that proves the harness can detect the defect).
3. Streamlit 1.62 platform facts (validated — do NOT re-derive)
st.iframe: the POSITIONAL argument is the validated raw-HTML vehicle(works for script-bearing AND script-free fragments). "srcdoc=" isNOT a parameter — barred from all current and future changes.
st.iframe sandbox: allow-scripts + allow-same-origin, NOallow-top-navigation. Fragments CAN read/write the parent DOM (parentlocalStorage write ✓; parent history.replaceState ✓) but can NEVERforce a parent rerun (synthetic button click ✗) and can NEVERnavigate the top window (SecurityError). Chrome logs a benignsandbox-escape warning per iframe (2–3× per page) — expected consolenoise; only NEW messages matter in QA.
Consequence: values in browser storage cannot reach Python at boot.The only Python-readable client-side channel is st.query_params —readback PROVEN, including inside AppTest (the bookmark-tip tests).This is why remember-me is a ?t= URL token, not localStorage.
st.session_state is WebSocket-session-scoped: full page reload /tab reopen = blank state; internal reruns keep it. Bare-URL openafter reopen therefore costs one login (accepted; the hub shows atargeted bookmark tip when ?t= is present).
st.html: not usable on 1.62. st.components.v1.html: deprecatedupstream, not used. st.markdown(unsafe_allow_html=True) executes noscripts.
st.audio: unmount does NOT stop playback; autoplay fired only on theFIRST mounted player (unreliable) → production pattern isalways-visible players, no autoplay, no session flags; nativecontrol measures 382×40 → lifted to 48px by the audio CSS rule.
st.number_input accepts free-typed off-step values (step affects+/− tapping only).
st.download_button's MIME parameter is mime (mime_type raisesTypeError).
Module-level JSON caches (_bs_cache, _cards_cache, _bi_cache,_consent_cache) are process-lifetime — dev-server restart afterdata edits. AppTest runs fresh processes, unaffected.
4. Deployment / DB facts
Neon: always the POOLED connection string ("-pooler" host) via Cloudsecrets / DATABASE_URL env. Two lifecycle killers: (a) computesuspend + pooled idle drop → OperationalError (SSL closed);(b) idle-in-TRANSACTION termination → SQLSTATE 25P03, whichpsycopg 3.3.5 does NOT map under OperationalError. Both handled indb/database.py (_HealingConnection: reconnect + one retry onDEAD_CONNECTION_ERRORS; safe because every write is asingle-statement UPSERT) AND prevented in db/queries.py (every readends with conn.rollback() — 25P03 unreachable in normal operation).Local Docker Postgres does NOT enforce (b) — remote branch validationis the environment that catches platform DB behavior.
tests/conftest.py defaults DATABASE_URL to the local docker-composePostgres and REFUSES non-local hosts without TEST_DB_CONFIRM_REMOTE=1(the suite TRUNCATES all tables — point it only at a disposablebranch, never main).
Production Cloud secrets: database_url only. dev_tools deliberatelyABSENT → ?debug=true fully inert in production (local opt-in via.streamlit/secrets.toml; see secrets.toml.example).
Cloud auto-downgrades pyarrow 25→24 — platform behavior, ignore.
5. Data-file inventory — the localization worklist
File	Localizable	Never localize
data/exercise_cards.json	title, purpose, instructions, position_cues (24 cards each)	card_id, category, base_level, isometric; image path; audio path (per-locale files change the PATH value)
data/breathing_sequences.json	title, focus, purpose, instruction, safety_text (3 strings)	inhale_s/hold_s/exhale_s/cycles (clinical cadences), code, schedule
data/baseline_instructions.json	intro + per-measure description/instruction (L/R)	—
data/consent.json	everything (legal document — see §7.8)	version is recorded per registration (users.consent_version)
data/scoring_rubrics.json	SARC-F item labels + option text (user-facing)	ALL thresholds and scores — never touched, never translated numerically
data/prescriptions.json	— (numeric only; display strings built in code)	all values
assets/audio/	regenerate per locale: 29 mp3s + manifest	manifest drift-guard semantics (sha256 of source text — must become per-locale)
assets/exercises/	audit JPEGs for embedded EN text	filenames are contract (tests pin them)
Code-side copy: run a grep census first (every st.title / subheader /write / caption / info / warning / error / button /form_submit_button literal across app.py, components/views/,components/locked/ — sign-off required there — utils/auth.py,utils/contact.py; dev_controls is dev-only, skip). Known labelcontracts in tests: breathing button-label pattern(test_breathing_controls), LABEL_* values (test_copy_contract —values pinned, constant names part of the locked contract), supportfooter, E2E _find() by label, REMEMBER_LABEL, and the consent checkboxlabel — which is READ FROM consent.json, the pattern to extend:data-driven label reads survive localization for free.

6. Recommended architecture (decide §7 first)
Locales: {"en", "zh-HK", "zh-TW"} (codes per §7.1).
Data shape: per-locale files (exercise_cards.zh-HK.json …) behind alocale-aware loader mirroring the existing cache pattern (per-localecaches; same dev-server restart rule). Alternative: inline{"en": …} objects in one file — smaller file count, bigger diffs;either defensible; pick once, stay consistent.
Locale selection: session_state["locale"] (new STATE.md key) set bya visible picker (48px target) on the auth page + hub; default "en".Persistence of the PREFERENCE hits the same boot-handoff wall as theauth token (§3): ?lang= rides bookmarks, or re-pick per session —acceptable at beta scale.
Audio: assets/audio/{locale}/{code}.mp3; tools/generate_audio.pygains --lang (per-locale voice + rate; text read from the locale'sJSONs — verbatim by construction, per locale); manifest per locale;tests/test_audio_contract.py iterates locales (drift guard perlanguage).
Tests: default-locale (en) runs keep every existing selector green;a completeness test per locale asserts every key exists, no ENleakage, no DRAFT; label contracts become data-driven where labelslocalize. Optional per-locale E2E smoke later.
7. Decisions to resolve BEFORE coding (team + product)
Exact locales/audiences: zh-HK (Cantonese, HK conventions) andMandarin in Traditional script (zh-TW?) — confirm codes; note HK andTW written Chinese differ in vocabulary even sharing the script.
Translation + sign-off owner per document class (exercise/breathing/baseline clinical copy; SARC-F items; consent/waiver — legal).
Data shape (§6).
Picker placement/default/persistence decision.
Test-strategy sign-off (default-locale runs + completeness tests vsa keys-not-labels refactor of helpers_e2e).
TTS voices per locale (edge-tts candidates: zh-HK-HiuMaanNeural,zh-TW-HsiaoChenNeural — VERIFY availability and pace on the devbox; the EN standard is en-US-AriaNeural at −15%, locked inDECISIONS; per-language rate may need its own tuning + listen).
Typography: CJK font-family stack in styles/custom.css (and thecontact-footer SVG's font-family); the 18px floor HOLDS for CJK,but Chinese glyph density means a 320px re-flow QA pass per locale;consider a line-height bump for CJK.
Consent: localized waiver = a new legal version("v1.1-zh-HK" style strings in users.consent_version); the evidencecolumns are locale-agnostic.
Register: the baseline instructions are clinician-voice ("I willwrap…", "When I say 'go'…") — preserve register in translation.Known EN flags to fix in the same change if the team approves:"endurances" typo; the 31 cm educational figure vs rubricthresholds; "up to 45 or 60 seconds" vs the 120 s input cap.
Illustrations: audit embedded EN text; per-locale art only ifneeded.Support email stays Latin-script in every locale; only the footer'slead line localizes.
8. Sequencing (recommended)
§7 decisions; procure translations (the long pole).
Census + i18n skeleton (locale key, loaders, picker, STATE.md entry)— EN only, no visible change; full suite green (263 → +new tests).
zh-HK end-to-end: data files + UI strings + consent + tests.
zh-TW end-to-end.
Per-locale audio generation + manifest + drift-guard extension.
QA matrix: per locale × device matrix (320/375/414) × the permanentmanual-QA lines (transitions snap + [scroll-reset] console line;metronome animates + auto-stops; narration spot-listen per locale;footer tap on a real device; idle-gap drill on production).
9. Paste checklist for the new chat's opening message
This file; docs/DECISIONS.md (full, current); docs/STATE.md (full);the v4.1 reference PDF. On demand per change: any file the changetouches (the paste rule). Current suite count: 263 — reconcile afterevery run.
10. First questions the new chat should ask
§7.1–7.5 decisions made? Which translated source documents are inhand?
Paste tests/helpers_e2e.py and the first view to change.
Run the code-side string census grep and share the output.
Carried parked items (from DECISIONS; do not let them evaporate):#10 rest-day progression chart; #11 in-app feedback form; P4auto-rerun probe (declined for beta); bookmark-tip dismiss-once;the anti-harvest public-repo acceptance.