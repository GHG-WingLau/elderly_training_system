All Streamlit code MUST use these keys (set in app.py). Do not introducenew session keys without documenting here.

Base
Key	Type	Purpose
authenticated	bool	User has logged in (testing-phase auth)
user_email	str|None	Logged-in user's email (PK)
user	dict|None	Full users row (mirrors DB)
current_state	str	Current state-machine state (v4.1 §3.4)
session_flags	dict	In-workout flags
debug	bool	?debug=true present in URL
Rules:

A day/week/cycle advance is computed from the DB (latesttraining_progress / rest_assessments row), NEVER from session state alone.
Every successful write transitions current_state via the state machine.
session_flags is reset on WORKOUT_SUMMARY → DAILY_HUB.
Phase 2 — onboarding wizard
| onboarding_step | int (0–4) | Current wizard step || onboarding_data | dict | Accumulated partial results across steps || pending_level | str|None | Level awaiting confirmation on step 4 || pending_total | int|None | Total score awaiting confirmation |

Routing rule: after login, app.py sets current_state = "ONBOARDING_SARC_F"if user.level is null, else "DAILY_HUB". On wizard confirm, the wizard setscurrent_state = "DAILY_HUB" and clears the onboarding keys.

Phase 3 — workout loop
| session_flags.last_rpe | str|None | RPE string from the just-submitted workout || session_flags.last_daily | list|None | Card IDs from the just-submitted workout |

Rule: session_flags is reset to {} on WORKOUT_SUMMARY → DAILY_HUB. RPEwidget keys are position-tagged (rpe_{cycle}{week}{day}_{cid}) so valuesnever leak across days.

Phase 4 — regression
| regression_ack | bool | Day 7 acknowledgment checkbox when a level regression is due |

Rule: after any set_user_level / advance_cycle write, refreshst.session_state["user"] from the DB before the next render.

Phase 5 — debug
| debug_override | dict|None | {"cycle","week","day"} when a QA override is applied |

Phase 6 — post-MVP UI/UX changes
| prev_fingerprint | tuple (bool, str, int|None) | Scroll-reset gate: (authenticated, current_state, onboarding_step) snapshot from the last completed render || breathing_started | dict[str, bool] | BREATHING_SESSION: practice codes whose metronome ring is running |

Rules:

prev_fingerprint: maintained only by app.py, updated after each completedrender; renders aborted by st.rerun() skip the update (comparison happenson the next settled render); views must never write it; debug_override isdeliberately excluded from the fingerprint.
breathing_started: written only by breathing_view Start/Stop handlers;pruned to today's scheduled codes on every BREATHING_SESSION render;popped on transition to EXERCISE_SESSION; no other view reads or writes it.

Logout (daily_hub btn_logout → utils.auth.clear_session_state): resetsauthenticated/user_email/user/current_state/session_flags to the app.pyboot defaults and pops breathing_started, regression_ack,onboarding_step, onboarding_data, prev_fingerprint. No view may clearauth keys directly — clear_session_state is the single logout path(Step 2b adds DB session-token deletion inside it).

Remember me (Step 2b, mechanism (a)): login checkbox REMEMBER_LABEL("Keep me logged in on this device (30 days)", key login_remember,default ON) creates a 30-day sessions token placed in the URL as?t= (st.query_params — the only Python-readable client-sidepersistence on 1.62). app.py main() calls utils.auth.try_restore_session()when unauthenticated: valid token → auth state restored (then normalrouting); dead token → param removed. Logout (clear_session_state) isthe single path: deletes the token row, removes ?t=, wipes auth + flowkeys. Trade-offs accepted: token visible in URL/bookmarks (bookmark =stay logged in); a shared link leaks a live session until expiry orlogout.

no new session keys (the tip reads st.query_params, stateless; the debug gate writes the existing debug key).

