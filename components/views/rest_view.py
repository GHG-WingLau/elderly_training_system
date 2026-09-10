"""Phase 4 — DAY_7_REST view: recovery checks, reflection, auto-regulation.

Phase 7: chrome via utils.strings; level-bearing lines compose
level_display.

Phase 9: why-recheck explainer + baseline reference (tr-driven);
progress presentation under the baseline block; stance values stored
AS-ENTERED into REAL columns (the int()-truncation correction).

Phase 10, chart v3 (verdict: prototype variant G + top legend; F =
sit-to-stand line chart; user-approved):

  • HEADLINE: the st.metric row — latest value per measure with a
    DELTA (stance vs Day 1; sit-to-stand vs the previous review);
    26px values per the existing CSS; labels reuse the localized form
    labels — zero new copy.
  • STANCE: ONE Altair LINE chart (left + right, shared seconds axis)
    — markers, 3.5 stroke, y-domain [0, 1.5 × max(data, norm)] with a
    ZERO floor, the NORM reference rule (dashed, labeled, value read
    from the rubrics — data-driven, never hardcoded; SLS is unisex),
    the legend at the TOP (the verdict's tweak — the one parameter the
    prototype did not exercise; first check on the manual-QA line),
    16px axis/legend labels (the elderly font pass).
  • The x-axis is the FULL JOURNEY: Day 1 + Weeks 0–4, with unmeasured
    weeks as NULL placeholders — the formative-assessment horizon.
  • SIT-TO-STAND: a single-series LINE chart (verdict F), label above,
    weeks-only axis (the 15-second test has no Day-1 point — the
    Step 2 discipline), no norm rule (the rubric's chair-stand norms
    are for the 30-second baseline test — not comparable); rendered
    only once a value exists.
  • AS-ENTERED (decision (a), pinned by test): an entered 0 is data; a
    DB NULL is a gap — never filtered.
  • NO interpretive copy (team-approved — the numbers speak; the rule
    line is data, not commentary).
  • altair + pandas are TRANSITIVE dependencies of the pinned
    streamlit (no new runtime deps); every chart parameter except
    Legend(orient="top") was exercised in the approved prototype.
  • AppTest is blind to chart/metric visuals (the images/audio
    precedent): the data assembly, domain helper, and full-journey
    index are unit-tested; the visual is a permanent manual-QA line.
    
    v10: axis titles — x untitled (Altair was rendering the raw field names 'x'/'value'), y = localized units (rest.y_seconds / rest.y_count).
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from db import queries
from utils.session_logic import get_session_position
from utils.autoregulation_logic import day7_plan
from utils.breathing_logic import get_safety_text
from utils.exercise_logic import format_prescription
from utils.strings import tr, level_display
from utils.hints import HINT_REST, render_hint
from components.locked.sarc_f_assessment import get_rubrics

# EN contract constants — equal the ui_strings EN values (tests import
# WHY_TITLE / BASELINE_TITLE; the chart x-labels are tr-driven since the
# final translation round).
WHY_TITLE = "Why we measure again each week"
WHY_BODY = ("These quick checks let the program follow your progress and "
            "adjust your exercises. Many people see their numbers improve "
            "over the weeks — yours will show you how you are doing.")
BASELINE_TITLE = "Your starting measurements (Day 1)"
BASELINE_SLS = "Single-leg stance — left: {left} sec · right: {right} sec"
BASELINE_REF = "Your Day 1 result: {value} sec"


def _fmt(v) -> str:
    """"—" for missing; compact numbers otherwise (12.5 -> 12.5, 13 -> 13)."""
    return "—" if v is None else f"{v:g}"


def _y_domain(values: list, norm: float | None = None,
              mult: float = 1.5) -> list:
    """[0, mult × max(values, norm)] — the team spec: zero floor (no
    negatives), full scale ~150% of the data, and the norm MUST fit
    when shown. PURE; degenerate cases (no values, or all zeros) fall
    back to a visible [0, 1] scale — never [0, 0]."""
    candidates = [v for v in values if v is not None]
    if norm is not None:
        candidates.append(norm)
    if not candidates:
        return [0, 1.0]
    ymax = mult * max(candidates)
    return [0, ymax] if ymax > 0 else [0, 1.0]


def _stance_data(baseline: dict | None, rows: list):
    """(x_order, left, right) — the FULL journey: Day 1 (when a
    baseline exists) + ALL five weeks, unmeasured weeks as None
    placeholders (the formative horizon). AS-ENTERED."""
    row_by_week = {r["week"]: r for r in rows}
    x_order: list[str] = []
    left: list = []
    right: list = []
    if baseline:
        x_order.append(tr("rest.chart_day1"))
        left.append(baseline.get("sls_left_sec"))
        right.append(baseline.get("sls_right_sec"))
    for w in range(5):
        x_order.append(tr("rest.chart_week").format(n=w))
        r = row_by_week.get(w)
        left.append(r["sls_left_sec"] if r else None)
        right.append(r["sls_right_sec"] if r else None)
    return x_order, left, right


def _stance_frame(x_order: list, left: list, right: list) -> pd.DataFrame:
    rows = []
    for i, x in enumerate(x_order):
        rows.append({"x": x, "measure": tr("rest.sls_left"),
                     "value": left[i]})
        rows.append({"x": x, "measure": tr("rest.sls_right"),
                     "value": right[i]})
    return pd.DataFrame(rows)


def _sts_data(rows: list):
    """(x_order, values) — weeks only (the 15-second test has no Day-1
    point), placeholders for unmeasured weeks."""
    row_by_week = {r["week"]: r for r in rows}
    x_order = [tr("rest.chart_week").format(n=w) for w in range(5)]
    values = [row_by_week[w]["sit_to_stand_15s_cycles"]
              if w in row_by_week else None for w in range(5)]
    return x_order, values


def _progress_metrics(baseline: dict | None, rows: list) -> list:
    """(ui_key, value, delta|None) triples for the headline metric row —
    PURE. Value = the latest review (or the baseline when no review
    exists yet). Delta: stance vs Day 1 (when both values exist);
    sit-to-stand vs the previous review (when both exist)."""
    latest = rows[-1] if rows else None
    prev = rows[-2] if len(rows) > 1 else None
    out: list = []
    for ui_key, key in (("rest.sls_left", "sls_left_sec"),
                        ("rest.sls_right", "sls_right_sec")):
        source = latest if latest is not None else baseline
        value = source.get(key) if source else None
        delta = None
        if latest is not None and baseline:
            cur, base = latest.get(key), baseline.get(key)
            if cur is not None and base is not None:
                delta = cur - base
        out.append((ui_key, value, delta))
    value = latest.get("sit_to_stand_15s_cycles") if latest else None
    delta = None
    if latest is not None and prev is not None:
        cur, old = (latest.get("sit_to_stand_15s_cycles"),
                    prev.get("sit_to_stand_15s_cycles"))
        if cur is not None and old is not None:
            delta = cur - old
    out.append(("rest.sts", value, delta))
    return out


def _render_progress(baseline: dict | None, rows: list) -> None:
    # Headline — big numbers + direction arrows.
    cols = st.columns(3)
    for col, (ui_key, value, delta) in zip(
            cols, _progress_metrics(baseline, rows)):
        with col:
            st.metric(tr(ui_key), _fmt(value), delta=delta)
    # Stance — one line chart, verdict-G settings. v10: axis TITLES —
    # x untitled (the raw field name "x" was rendering), y carries the
    # localized unit; the three layers SHARE the encoding objects so
    # the axis resolution is consistent by construction.
    x_order, left, right = _stance_data(baseline, rows)
    frame = _stance_frame(x_order, left, right)
    norm = get_rubrics()["single_leg_stance_sec"]["unisex"]["normal_min"]
    domain = _y_domain(left + right, norm=norm)
    x_enc = alt.X("x:N", sort=x_order,
                  axis=alt.Axis(labelFontSize=16, title=None))
    y_enc = alt.Y("value:Q", scale=alt.Scale(domain=domain),
                  axis=alt.Axis(labelFontSize=16,
                                title=tr("rest.y_seconds")))
    chart = alt.Chart(frame).mark_line(point=True, strokeWidth=3.5).encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("measure:N", legend=alt.Legend(
            orient="top", labelFontSize=16, title=None))
    )
    rule = alt.Chart(pd.DataFrame({"value": [norm]})).mark_rule(
        strokeDash=[4, 4], color="#777777").encode(y=y_enc)
    ref_label = f"{tr('rest.reference_level')} ({norm:g} s)"
    label = alt.Chart(pd.DataFrame(
        {"value": [norm], "x": [x_order[0]]})).mark_text(
        text=ref_label, align="left", dy=-10, color="#777777",
        fontSize=16).encode(x=x_enc, y=y_enc)
    st.altair_chart((chart + rule + label).properties(height=260),
                    width="stretch")

    # Sit-to-stand — single-series line chart (verdict F), label above;
    # rendered only once a value exists (no Day-1 anchor to show before
    # the first review — the stance chart carries the horizon until then).
    if any(r.get("sit_to_stand_15s_cycles") is not None for r in rows):
        sts_order, sts_values = _sts_data(rows)
        sts_chart = alt.Chart(pd.DataFrame(
            {"x": sts_order, "value": sts_values})).mark_line(
            point=True, strokeWidth=3).encode(
            alt.X("x:N", sort=sts_order,
                  axis=alt.Axis(labelFontSize=16, title=None)),
            alt.Y("value:Q", scale=alt.Scale(domain=_y_domain(sts_values)),
                  axis=alt.Axis(labelFontSize=16,
                                title=tr("rest.y_count")))
            )
        st.caption(tr("rest.sts"))
        st.altair_chart(sts_chart.properties(height=200),
                        width="stretch")


def render_rest_view(user: dict) -> None:
    pos = get_session_position(user["email"])
    if not pos["is_rest_day"] or pos["is_program_complete"]:
        st.session_state["current_state"] = "DAILY_HUB"
        st.rerun()
        return
    week, cycle = pos["week"], pos["cycle"]
    plan = day7_plan(user["email"], cycle, week, user["level"])
    safety = get_safety_text()
    baseline = user.get("baseline")

    st.title(tr("rest.title").format(week=week))
    st.info(f"🪑 {safety['chair_standard']}")
    render_hint(user, HINT_REST)
    st.write(tr("rest.light_movement"))

    if plan["avg_rpe"] is not None:
        st.metric(tr("rest.metric_label"), f"{plan['avg_rpe']:.1f} / 5")
    if week == 0:
        st.caption(tr("rest.induction"))
    elif plan["classification"] == "high":
        st.warning(tr("rest.hard"))
    elif plan["classification"] == "low":
        st.success(tr("rest.easy"))
    else:
        st.info(tr("rest.moderate"))
    if plan["next_week_prescription"] is not None:
        st.write(tr("rest.next_prescription").format(
            prescription=format_prescription(plan["next_week_prescription"])))

    # Regression prompt (mandatory acknowledgment)
    ack_ok = True
    if plan["regression_to"] is not None:
        new_level_value = f"Level {plan['regression_to']}"
        st.warning(tr("rest.regression_warning").format(
            current_level=level_display(user["level"]),
            new_level=level_display(new_level_value)))
        ack_ok = st.checkbox(
            tr("rest.regression_ack").format(n=level_display(new_level_value)),
            key="regression_ack")
    elif plan["hard_streak"]:
        st.warning(tr("rest.hard_streak").format(n=level_display("Level 0")))

    # Phase 9 — why we re-check + the baseline reference.
    st.info(f"**{tr('rest.why_title')}**\n\n{tr('rest.why_body')}")
    if baseline:
        st.write(f"**{tr('rest.baseline_title')}**")
        st.write(tr("rest.baseline_sls").format(
            left=baseline.get("sls_left_sec"),
            right=baseline.get("sls_right_sec")))

    # Phase 9/10 — progress headline + the verdict-G charts.
    rows = queries.get_rest_assessment_history(user["email"], cycle)
    if baseline or rows:
        _render_progress(baseline, rows)

    with st.form("rest_form"):
        recall = st.number_input(tr("rest.recall"), 0, 6, 0, key="rest_recall")
        reflection = st.text_area(tr("rest.reflection"), key="rest_reflection")
        sts = st.number_input(tr("rest.sts"), 0, 30, 0, key="rest_sts")
        sls_l = st.number_input(tr("rest.sls_left"), 0.0, 120.0, 0.0, 0.5,
                                key="rest_sls_l")
        if baseline:
            st.caption(tr("rest.baseline_ref").format(
                value=baseline.get("sls_left_sec")))
        sls_r = st.number_input(tr("rest.sls_right"), 0.0, 120.0, 0.0, 0.5,
                                key="rest_sls_r")
        if baseline:
            st.caption(tr("rest.baseline_ref").format(
                value=baseline.get("sls_right_sec")))
        submitted = st.form_submit_button(tr("rest.submit"), width="stretch",
                                          type="primary")
    if not submitted:
        return
    if not ack_ok:
        st.error(tr("rest.ack_error"))
        return

    queries.upsert_rest_assessment(user["email"], cycle, week, int(recall),
                                   reflection, int(sts), sls_l, sls_r)
    if plan["regression_to"] is not None:
        new_level = f"Level {plan['regression_to']}"
        queries.set_user_level(user["email"], new_level)
        user["level"] = new_level
        st.session_state["user"] = user
    st.session_state.pop("regression_ack", None)
    st.session_state["current_state"] = (
        "PROGRAM_COMPLETE" if week == 4 else "DAILY_HUB")
    st.rerun()