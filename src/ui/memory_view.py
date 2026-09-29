import streamlit as st
from src.errors import IncidentMindError
from src.ui.common import incident_details


def render(memory):
    st.title("Memory inspector")
    st.write("Trace every historical claim back to an actual incident in Hindsight.")
    a = st.session_state.get("analysis")
    if not a:
        st.info("Analyze an incident to inspect context-specific memory and the lessons it contributed.")
    else:
        st.metric("Relevant historical incidents", len(a.historical_incidents))
        st.caption("These are retrieved sources selected for relevance, not the total size of the memory bank.")
        for i in a.historical_incidents:
            with st.expander(f"{i.incident_id} · {i.root_cause}"):
                incident_details(i)
                st.write("**Post-mortem lesson:**", i.postmortem)
        if a.enhanced.evidence_used:
            st.subheader("Patterns and their influence · AI interpretation")
            for e in a.enhanced.evidence_used:
                st.write(f"**{e.incident_id}:** {e.influence}")
        with st.expander("Raw recalled facts · audit trace"):
            st.json(a.retrieved_facts)
    recent = st.session_state.get("last_learned")
    if recent:
        st.success(f"Recent learning: {recent.incident_id} · {recent.outcome}")
        st.write(recent.postmortem)
    with st.form("source_lookup"):
        incident_id = st.text_input("Inspect a stored incident ID", placeholder="INC-SEED-1001")
        submitted = st.form_submit_button("Read Hindsight source")
    if submitted:
        if not incident_id.strip():
            st.warning("Enter an incident ID.")
        else:
            try:
                with st.spinner("Reading Hindsight source…"):
                    incident_details(memory.retrieve_incident_knowledge(incident_id.strip()))
            except IncidentMindError as exc:
                st.error(str(exc))
