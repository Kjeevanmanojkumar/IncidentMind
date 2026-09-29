import streamlit as st
from pydantic import ValidationError
from src.errors import IncidentMindError
from src.models.incident import PostMortem
from src.services.incident_service import IncidentService
from src.ui.common import lines


def render(memory):
    st.title("Post-mortem → new memory")
    st.write("Record what actually happened. Your confirmed outcome becomes evidence for the next incident.")
    drafts = st.session_state.get("drafts", {})
    active = [key for key, i in drafts.items() if i.outcome == "Active"]
    if not active:
        st.info("Create an incident first. Resolved session records remain visible in Incident history.")
        if st.session_state.get("last_learned"):
            st.success(f"Memory Updated · {st.session_state.last_learned.incident_id}")
        return
    current = st.session_state.get("current_id")
    selected = st.selectbox("Incident", active, index=active.index(current) if current in active else 0,
        format_func=lambda k: f"{k} · {drafts[k].service}")
    i = drafts[selected]
    st.caption(i.description)
    with st.form("postmortem_" + selected):
        root = st.text_area("Actual root cause", max_chars=4000)
        steps = st.text_area("Resolution steps / actions attempted · one per line", max_chars=12000)
        failed = st.text_area("Failed approaches · one per line", max_chars=12000)
        runbook = st.text_input("Runbook used · optional", max_chars=1000)
        a, b = st.columns(2)
        outcome = a.selectbox("Outcome", ["Resolved", "Mitigated", "Unresolved"])
        duration = b.number_input("Time to recorded outcome · minutes", min_value=0.0, max_value=525600.0, value=8.0)
        notes = st.text_area("Post-mortem notes / prevention learning", max_chars=4000)
        submitted = st.form_submit_button("Save outcome to Hindsight", type="primary")
    if submitted:
        try:
            post = PostMortem(root_cause=root, resolution_steps=lines(steps), failed_approaches=lines(failed),
                runbook=runbook, outcome=outcome, resolution_time=duration, postmortem=notes)
            with st.status("Storing actual outcome in Hindsight…") as status:
                saved = IncidentService(memory).resolve(i, post)
                drafts[selected] = saved
                st.session_state["last_learned"] = saved
                st.session_state.pop("overview", None)
                status.update(label="Memory Updated", state="complete")
            st.success(f"✓ Incident {saved.outcome.lower()} · ✓ Root cause stored · ✓ Actions and outcome stored · ✓ Post-mortem stored · ✓ Hindsight memory updated")
            if runbook:
                st.success("✓ Runbook stored")
            st.info("Open Demo and load a similar future incident to verify recall of this new learning.")
        except ValidationError:
            st.error("Enter the actual root cause, at least one step, and post-mortem notes. Each step must be under 1,000 characters.")
        except IncidentMindError as exc:
            st.error(str(exc))
            st.warning("Memory update is not confirmed. The draft and form remain available. Retry with the same incident ID.")
