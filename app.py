"""Streamlit entrypoint. Run: python -m streamlit run app.py"""
import streamlit as st
from src.config import Settings
from src.errors import IncidentMindError
from src.agent.incident_agent import IncidentAgent
from src.agent.reasoning import Reasoner
from src.memory.hindsight_memory import HindsightMemory
from src.ui import dashboard, demo_view, incident_view, memory_view, postmortem_view

st.set_page_config(page_title="IncidentMind · Organizational incident memory", page_icon="◈", layout="wide")
st.markdown("""<style>
.block-container {max-width: 1240px; padding-top: 2.5rem;}
h1 {letter-spacing: -0.035em; line-height: 1.12;}
h2,h3 {letter-spacing: -0.02em;}
[data-testid="stSidebar"] {border-right: 1px solid #233044;}
[data-testid="stMetricValue"] {color: #43DAC5;}
div[data-testid="stExpander"] {border-color: #273549;}
</style>""", unsafe_allow_html=True)
try:
    settings = Settings.from_env()
except IncidentMindError as exc:
    st.error(str(exc))
    st.stop()
memory = HindsightMemory(settings)
agent = IncidentAgent(memory, Reasoner(settings))
st.session_state.setdefault("drafts", {})
with st.sidebar:
    st.markdown("## ◈ IncidentMind")
    st.caption("Every incident becomes knowledge\nfor the next incident.")
    st.divider()
    # Separate widget key lets page actions change the selected destination safely.
    options = ["Dashboard", "New Incident", "Incidents", "Memory", "Post-Mortem", "Demo"]
    if "nav" in st.session_state:
        st.session_state["navigation_widget"] = st.session_state.pop("nav")
    page = st.radio("Workspace", options, key="navigation_widget")
    st.divider()
    st.caption("MEMORY PROVIDER")
    st.write("Hindsight")
    st.caption(f"Bank: {settings.bank_id}")
    problems = []
    for validate in [settings.validate_memory, settings.validate_llm]:
        try:
            validate()
        except IncidentMindError as exc:
            problems.append(str(exc))
    if problems:
        st.warning("Configuration needed")
        with st.expander("Setup details"):
            for problem in problems:
                st.write(problem)
            st.code("cp .env.example .env", language="bash")
            st.caption("Configure .env on the server, then rerun the app. Never paste keys into chat or commit them.")
    else:
        st.caption("Configured · connectivity not yet checked")
    if st.button("Check Hindsight connection"):
        try:
            with st.spinner("Checking bank access…"):
                memory.check_connection()
            st.success("Hindsight bank reachable")
        except IncidentMindError as exc:
            st.error(str(exc))
    st.caption("Single-organization prototype\nActive drafts last for this session.")

if page == "Dashboard":
    dashboard.render(memory)
elif page == "New Incident":
    incident_view.render_new(agent)
elif page == "Incidents":
    incident_view.render_history(memory)
elif page == "Memory":
    memory_view.render(memory)
elif page == "Post-Mortem":
    postmortem_view.render(memory)
elif page == "Demo":
    demo_view.render(memory)
