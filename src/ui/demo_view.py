import streamlit as st
from src.errors import IncidentMindError
from src.services.sample_service import demo_incident, seed


def _load(i):
    st.session_state["demo_input"] = i.model_dump()
    st.session_state["form_generation"] = st.session_state.get("form_generation", 0) + 1
    st.session_state.pop("analysis", None)
    st.session_state["nav"] = "New Incident"
    st.rerun()


def render(memory):
    st.title("The next incident starts smarter")
    st.write("A payment outage. A remembered fix. A new lesson that survives the session.")
    with st.expander("Setup · seed real Hindsight memory", expanded=False):
        st.write("Import 20 synthetic incident records into the configured Hindsight bank. This makes real API calls and may take several minutes. Re-importing uses the same document IDs.")
        st.caption(f"Target bank: {memory.settings.bank_id}. Use a dedicated demo bank.")
        if st.button("Seed 20 historical incidents"):
            try:
                bar = st.progress(0, text="Initializing demo memory bank…")
                count = seed(memory, lambda n, total: bar.progress(n / total, text=f"Stored {n}/{total} historical incidents"))
                st.success(f"Hindsight confirmed {count} stored incidents.")
                st.session_state.pop("overview", None)
            except IncidentMindError as exc:
                st.error(str(exc))
                st.warning("Import may be partial. Retry to upsert the same source records.")
    st.markdown("### 01 / The incident")
    st.code("payment-api · SEV-1\nHTTP 503 increasing · database connection pool exhausted\nv2.8.4 deployed 10 minutes ago", language="text")
    if st.button("Load Demo Incident", type="primary"):
        _load(demo_incident())
    st.markdown("### 02 / The memory advantage")
    st.write("Click Analyze Incident. Compare the current-only response with the Hindsight-backed recommendation. Expand an actual source and inspect its failed fixes and successful runbook.")
    st.markdown("### 03 / Close the loop")
    st.write("After the simulated resolution, enter the real demo outcome in Post-Mortem. For the scripted demo: an unclosed connection in the v2.8.4 exception path; rollback plus rolling restart; add a connection-release regression test.")
    recent = st.session_state.get("last_learned")
    if recent:
        st.success(f"Stored learning: {recent.incident_id}")
        if st.button("Load similar future incident"):
            # This copies incident symptoms for convenience, never resolution knowledge.
            from src.models.incident import Incident
            future = Incident(service=recent.service, severity=recent.severity,
                description=recent.description, error_message=recent.error_message,
                symptoms=recent.symptoms, logs=recent.logs,
                recent_change="A new deployment preceded the recurrence. " + recent.recent_change)
            st.session_state["expected_memory_id"] = recent.incident_id
            _load(future)
    expected = st.session_state.get("expected_memory_id")
    analysis = st.session_state.get("analysis")
    if expected and analysis:
        if expected in {i.incident_id for i in analysis.historical_incidents}:
            st.success(f"Learning loop verified in this session: {expected} was recalled and cited in the future recommendation.")
        else:
            st.warning(f"Learning loop not yet verified: {expected} is not in the current recommendation's evidence. Check indexing, relevance and the configured bank.")
    st.caption("60-second presentation after setup; actual response time depends on Hindsight and the model. No canned recommendations or offline memory substitute.")
