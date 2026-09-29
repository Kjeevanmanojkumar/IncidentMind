import streamlit as st
from pydantic import ValidationError
from src.agent.incident_agent import IncidentAgent
from src.errors import IncidentMindError
from src.models.incident import Incident
from src.ui.common import incident_details, lines, show_analysis


def render_new(agent: IncidentAgent):
    st.title("New incident")
    st.write("Start with what you know. Recall how your team solved it before.")
    st.caption("Remove credentials and personal information from logs before submission; incident data is sent to your configured providers.")
    demo = st.session_state.get("demo_input", {})
    generation = st.session_state.get("form_generation", 0)
    with st.form(f"new_incident_{generation}"):
        a, b = st.columns([3, 1])
        service = a.text_input("Service", value=demo.get("service", ""), max_chars=100)
        severity = b.selectbox("Severity", ["SEV-1", "SEV-2", "SEV-3", "SEV-4"])
        description = st.text_area("Incident description", value=demo.get("description", ""), max_chars=4000)
        error = st.text_input("Error message", value=demo.get("error_message", ""), max_chars=4000)
        symptoms = st.text_area("Symptoms · one per line", value="\n".join(demo.get("symptoms", [])), max_chars=8000)
        logs = st.text_area("Relevant logs", value=demo.get("logs", ""), max_chars=12000)
        change = st.text_input("Recent deployment / change", value=demo.get("recent_change", ""), max_chars=4000)
        submitted = st.form_submit_button("Analyze Incident", type="primary")
    if submitted:
        st.session_state.pop("analysis", None)
        try:
            i = Incident(service=service, severity=severity, description=description,
                error_message=error, symptoms=lines(symptoms), logs=logs, recent_change=change)
            st.session_state.setdefault("drafts", {})[i.incident_id] = i
            st.session_state["current_id"] = i.incident_id
            with st.status("Analyzing incident…", expanded=True) as status:
                result = agent.analyze(i, status.write)
                st.session_state["analysis"] = result
                status.update(label="Response brief ready", state="complete", expanded=False)
        except ValidationError:
            st.error("Enter a service name (letters, digits, dots, underscores or hyphens), a description and valid field lengths.")
        except IncidentMindError as exc:
            st.error(str(exc))
            st.info("Your valid incident remains available under Post-Mortem. No recommendation has been marked successful.")
    if st.session_state.get("analysis"):
        show_analysis(st.session_state.analysis)
        if st.button("Record actual outcome →"):
            st.session_state["nav"] = "Post-Mortem"
            st.rerun()


def render_history(memory):
    st.title("Incident history")
    st.caption("Recorded outcomes are loaded directly from Hindsight. Active drafts exist only in this browser session.")
    for i in st.session_state.get("drafts", {}).values():
        if i.outcome == "Active":
            with st.expander(f"Active draft · {i.incident_id} · {i.service}"):
                incident_details(i)
    page = st.number_input("History page", min_value=1, step=1, value=1)
    try:
        with st.spinner("Reading Hindsight source documents…"):
            records, total = memory.history(offset=(page - 1) * 20)
        st.caption(f"{total} stored records · 20 per page")
        if not records:
            st.info("No stored incident records on this page. Seed the Demo bank or record an actual outcome.")
        for i in records:
            with st.expander(f"{i.severity} · {i.service} · {i.incident_id} · {i.outcome}"):
                incident_details(i)
    except IncidentMindError as exc:
        st.error(str(exc))
