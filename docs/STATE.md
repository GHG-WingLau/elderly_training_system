docs/STATE.md
All Streamlit code MUST use these keys (set in app.py). Do not introducenew session keys without documenting here.

Base keys
Key	Type	Purpose
authenticated	bool	User has logged in
user_email	str|None	Logged-in user's email (PK)
user	dict|None	Full users row (mirrors DB)
current_state	str	Current state-machine state (v4.1 §3.4)
session_flags	dict	In-workout flags
debug	bool	?debug=true present in URL
Rules:

A day/week/cycle advance is computed from the DB (latesttraining_progress / rest_assessments row), NEVER from session statealone.
Every successful write transitions current_state via the statemachine.
session_flags is reset on WORKOUT_SUMMARY → DAILY_HUB.
Phase 2 — onboarding wizard
Key	Type	Purpose
onboarding_step	int (0–4)	Current wizard step
onboarding_data	dict	Accumulated partial results across steps
pending_level	str|None	Level awaiting confirmation on step 4
pending_total	int|None	Total score awaiting confirmation
Routing rule: after login, app.py sets current_state ="ONBOARDING_SARC_F" if user.level is null, else "DAILY_HUB". On wizardconfirm, the wizard sets current_state = "DAILY_HUB" and clears theonboarding keys.

Phase 3 — workout loop
Key	Type	Purpose
session_flags.last_rpe	str|None	RPE string from the just-submitted workout
session_flags.last_daily	list|None	Card IDs from the just-submitted workout
Rule: session_flags is reset to {} on WORKOUT_SUMMARY → DAILY_HUB. RPEwidget keys are position-tagged (rpe_{cycle}{week}{day}_{cid}) sovalues never leak across days.

Phase 4 — regression
Key	Type	Purpose
regression_ack	bool	Day 7 acknowledgment checkbox when a level regression is due
Rule: after any set_user_level / advance_cycle write, refreshst.session_state["user"] from the DB before the next render.

Phase 5 — debug
Key	Type	Purpose
debug_override	dict|None	{"cycle","week","day"} when a QA override is applied
Phase 6 — post-MVP UI/UX changes
Key	Type	Purpose
prev_fingerprint	tuple (bool, str, int|None)	Scroll-reset gate: (authenticated, current_state, onboarding_step) snapshot from the last completed render
breathing_started	dict[str, bool]	BREATHING_SESSION: practice codes whose metronome ring is running
Rules:

prev_fingerprint: maintained only by app.py, updated after eachcompleted render; renders aborted by st.rerun() skip the update(comparison happens on the next settled render); views must neverwrite it; debug_override is deliberately excluded from thefingerprint.
breathing_started: written only by breathing_view Start/Stophandlers; pruned to today's scheduled codes on everyBREATHING_SESSION render; popped on transition to EXERCISE_SESSION;no other view reads or writes it.
Logout (daily_hub btn_logout → utils.auth.clear_session_state): resetsauthenticated/user_email/user/current_state/session_flags to the app.pyboot defaults and pops breathing_started, regression_ack,onboarding_step, onboarding_data, prev_fingerprint. No view may clearauth keys directly — clear_session_state is the single logout path(Step 2b adds DB session-token deletion inside it).

Remember me (Step 2b, mechanism (a)): login checkbox REMEMBER_LABEL("Keep me logged in on this device (30 days)", key login_remember,default ON) creates a 30-day session token placed in the URL as ?t=(st.query_params — the only Python-readable client-side persistence on1.62). app.py main() calls utils.auth.try_restore_session() whenunauthenticated: valid token → auth state restored (then normalrouting); dead token → param removed. Logout (clear_session_state) isthe single path: deletes the token row, removes ?t=, wipes auth + flowkeys. Trade-offs accepted: token visible in URL/bookmarks (bookmark =stay logged in); a shared link leaks a live session until expiry orlogout.

No new session keys (the tip reads st.query_params, stateless; thedebug gate writes the existing debug key).

Phase 7 — localization
Key	Type	Purpose
locale	str	Active UI locale ("en" default | "zh-HK" | "zh-TW")
Rules:

Resolved by utils.locale.boot_resolve_locale() in app.py main() everypass (idempotent), AFTER try_restore_session, BEFORE any render:?lang= (validated against SUPPORTED_LOCALES) > session value >users.locale (authenticated only) > "en".
The session key is written ONLY for explicit resolutions (URL paramor profile adoption) — never for the default: a pre-auth "en" passmust not pin the session against a non-en profile after login.
The picker (auth page + daily hub; SUPPORTED_LOCALES ships all threelocales) is the only writer of the session key: it setssession_state["locale"], st.query_params["lang"] (the ?t= writepattern), and — when authenticated — persists viaqueries.set_user_locale (single write path; session user dictrefreshed).
Picker WIDGET key is locale-tagged (f"locale_picker_{current}") — theRPE position-tagged-key precedent: Streamlit persists widget state bykey and ignores index on remount, so an untagged key desynced thedisplayed value from the session locale after profile adoption(caught by test_boot_resolves_profile_locale_into_picker).
Picker LABEL is a FIXED bilingual wayfinding string ("Select yourpreferred language / 請選擇你的語言"), identical in every locale — theswitcher must be findable before the user understands the UI language(accessibility decision); display names remain per-locale autonyms.
clear_session_state does NOT reset locale (UI preference, not authstate); logout removes ?t= only — ?lang= stays.
Views read st.session_state["locale"] (or utils.locale.get_locale());no view reads ?lang= directly. Data loaders and utils.strings resolvevia utils.locale.safe_locale() (bare-mode-safe; no session context →"en"). Per-locale caches are process-lifetime — dev-server restartafter data edits.
A zh registration records consent_version "v1.1-zh-HK"/"v1.1-zh-TW"(§7.8) and users.locale (decision (a)) at create_user; the wizardpreference selectbox is index-mapped to Level {i} (stored levelvalues never localize; display names come fromutils.strings.level_display, keyed by the stored EN values).
Tab title: set_page_config localizes from ?lang= at FIRST load only(set_page_config applies once per page load; a mid-session switchre-titles on the next reload — documented trade-off).