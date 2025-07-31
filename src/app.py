import streamlit as st
from agent import run_agent

st.set_page_config(page_title="Emergency Contact Agent", page_icon="🚑")
st.title("Emergency Contact Agent")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


user_input = st.chat_input("Type your emergency or question...")

if user_input:
    conversation = st.session_state.chat_history + [("user", user_input)]
    with st.spinner("Agent is responding..."):
        chat_turns = run_agent(user_input, conversation)
    for sender, msg in chat_turns[len(st.session_state.chat_history):]:
        st.session_state.chat_history.append((sender, msg))

for sender, msg in st.session_state.chat_history:
    if sender == "user":
        st.chat_message("user").write(msg)
    else:
        st.chat_message("assistant").write(msg)