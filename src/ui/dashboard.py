from collections import Counter
import streamlit as st
from src.errors import IncidentMindError


def render(memory):
    st.caption("ORGANIZATIONAL MEMORY / INCIDENT RESPONSE")
    st.title("Every incident becomes knowledge\nfor the next incident.")
    st.write("Recall what worked. Avoid what failed. Turn the resolution into your team's next advantage.")
    drafts = list(st.session_state.get("drafts", {}).values())
    st.metric("Active incidents · this session", sum(i.outcome == "Active" for i in drafts))
    st.markdown("### Your response workflow")
    cols = st.columns(3)
    for col, title, desc in zip(cols,
            ["01 / Recall", "02 / Respond", "03 / Learn"],
            ["Match current symptoms to past incidents in Hindsight.",
             "Review evidence and recommended actions with your engineer.",
             "Record the real outcome so the next incident starts smarter."]):
        with col, st.container(border=True):
            st.subheader(title)
            st.write(desc)
    if st.button("Refresh memory overview", type="primary"):
        st.session_state.pop("overview", None)
        try:
            with st.spinner("Reading the most recent Hindsight records…"):
                st.session_state["overview"] = memory.history(limit=20)
        except IncidentMindError as exc:
            st.error(str(exc))
    overview = st.session_state.get("overview")
    if overview is None:
        st.info("Refresh to load real memory metrics, or start with Demo. No synthetic metrics are displayed.")
        return
    records, total = overview
    resolved = [i for i in records if i.outcome == "Resolved"]
    a, b, c = st.columns(3)
    a.metric("Stored incident records · total", total)
    b.metric("Resolved · loaded records", len(resolved))
    c.metric("Avg. resolution · loaded resolved", f"{sum(i.resolution_time for i in resolved)/len(resolved):.1f} min" if resolved else "—")
    st.caption(f"Overview covers up to 20 recently updated records, not all-time resolution statistics. Loaded {len(records)}.")
    st.subheader("Recent incidents")
    st.dataframe([{"Incident": i.incident_id, "Service": i.service, "Severity": i.severity,
                   "Outcome": i.outcome, "Root cause": i.root_cause} for i in records], hide_index=True, width="stretch")
    st.subheader("Runbooks recalled across loaded outcomes")
    counts = Counter(i.runbook for i in records if i.runbook)
    if counts:
        st.dataframe([{"Runbook": k, "Recorded uses": v} for k, v in counts.most_common()], hide_index=True)
