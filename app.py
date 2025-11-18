import streamlit as st
from agent_workflow import AgentWorkflow
import json

st.set_page_config(page_title="EcoGuide AI Demo", page_icon="🌍", layout="centered")

agent = AgentWorkflow()

st.title("🌍 EcoGuide AI — Demo Version")

st.subheader("Enter Trip Details")

name = st.text_input("Your Name", "Traveler")
location = st.text_input("Destination", "Dubai")
days = st.number_input("Days", 1, 30, 3)
travelers = st.number_input("Travelers", 1, 10, 1)
budget = st.number_input("Budget ($)", 100, 10000, 1500)

interests = st.multiselect(
    "Interests",
    ["Beach", "Adventure", "Food", "Shopping", "Nature"],
    ["Adventure"]
)

if st.button("Generate Trip Plan 🚀"):
    with st.spinner("Generating..."):
        query = f"A {days}-day trip to {location} for {travelers} people interested in {interests}"

        rag_data = []  # No RAG in demo
        priorities = {"eco": 7, "budget": 5, "comfort": 6}
        profile = {"name": name, "interests": interests}

        plan = agent.run(
            query=query,
            rag_data=rag_data,
            budget=budget,
            interests=interests,
            days=days,
            location=location,
            travelers=travelers,
            user_profile=profile,
            priorities=priorities
        )

        st.success("Plan generated!")
        st.write(plan["plan"])

        st.subheader("Raw JSON Output")
        st.json(plan)

        st.session_state["plan"] = plan


# -------------------
# Refinement
# -------------------
if "plan" in st.session_state:
    st.subheader("Refine Your Plan")

    feedback = st.text_input("Tell AI what to improve", "")

    if st.button("Update Plan"):
        with st.spinner("Updating..."):
            updated = agent.refine_plan(st.session_state["plan"], feedback)
            st.session_state["plan"] = updated
            st.success("Updated!")
            st.write(updated["plan"])
