import streamlit as st
from src.models.incident import Incident
from src.models.recommendation import Analysis, Recommendation


def lines(text: str):
    return [line.strip() for line in text.splitlines() if line.strip()]


def incident_details(i: Incident):
    st.caption(f"{i.incident_id} · {i.service} · {i.severity} · {i.outcome} · {i.timestamp:%Y-%m-%d %H:%M UTC}")
    st.write(i.description)
    st.write("**Error:**", i.error_message or "Not recorded")
    if i.symptoms:
        st.write("**Symptoms:**", "; ".join(i.symptoms))
    st.write("**Recent change:**", i.recent_change or "Not recorded")
    if i.logs:
        st.code(i.logs, language="text")
    if i.outcome != "Active":
        st.write("**Confirmed root cause:**", i.root_cause)
        st.write("**Steps performed:**")
        for step in i.resolution_steps:
            st.write("• " + step)
        st.write("**Failed approaches:**", "; ".join(i.failed_approaches) or "None recorded")
        st.write("**Runbook used:**", i.runbook or "None recorded")
        st.write("**Outcome:**", i.outcome, " · **Minutes:**", i.resolution_time)
        st.write("**Post-mortem:**", i.postmortem)


def advice(r: Recommendation):
    st.markdown("#### Diagnosis · hypothesis")
    st.write(r.diagnosis)
    st.markdown("#### Recommended actions")
    for n, step in enumerate(r.recommended_actions, 1):
        st.write(f"{n}. {step}")
    st.markdown("#### Why this recommendation")
    st.write(r.why)


def show_analysis(a: Analysis):
    st.subheader("Response brief")
    st.caption(f"{a.incident.incident_id} · {a.incident.service} · {a.incident.severity}")
    left, right = st.columns(2, gap="large")
    with left, st.container(border=True):
        st.markdown("### Without memory")
        st.caption("Current incident only · same model")
        advice(a.baseline)
    with right, st.container(border=True):
        st.markdown("### With Hindsight memory")
        if a.historical_incidents:
            st.success(f"{len(a.historical_incidents)} relevant historical incidents")
        else:
            st.info("No relevant historical incidents were found. This recommendation is based on the current incident only.")
        advice(a.enhanced)
    st.subheader("Historical evidence")
    st.caption("Confirmed source records from Hindsight. AI hypotheses above are not confirmed outcomes.")
    for i in a.historical_incidents:
        with st.expander(f"{i.incident_id} · {i.service} · {i.outcome}"):
            incident_details(i)
            for e in a.enhanced.evidence_used:
                if e.incident_id == i.incident_id:
                    st.write("**Exact source quote:**")
                    st.text(e.quote)
                    st.write("**AI interpretation of its relevance:**", e.influence)
    if a.historical_incidents:
        with st.container(border=True):
            st.markdown("#### Previous root causes, resolutions and runbooks")
            st.dataframe([{"Incident": i.incident_id, "Root cause": i.root_cause,
                "Successful resolution": "; ".join(i.resolution_steps) if i.outcome == "Resolved" else "Not resolved",
                "Failed approaches": "; ".join(i.failed_approaches) or "None recorded",
                "Runbook": i.runbook or "None recorded", "Outcome": i.outcome}
                for i in a.historical_incidents], hide_index=True, width="stretch")
    st.caption("Engineer review required. IncidentMind never executes infrastructure changes.")
