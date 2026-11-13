"""Streamlit client for the ShopAssist API."""

import uuid

import requests
import streamlit as st


API_URL = "http://localhost:8000"

st.set_page_config(page_title="ShopAssist", page_icon="S")
st.title("ShopAssist")

if "session_id" not in st.session_state:
	st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
	st.session_state.messages = []

with st.sidebar:
	st.header("Customer")
	customer_id = st.number_input("Mock customer ID", min_value=1, value=1, step=1)

for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])
		if message.get("tools"):
			with st.expander("Tool calls"):
				st.write(message["tools"])

if prompt := st.chat_input("How can we help?"):
	st.session_state.messages.append({"role": "user", "content": prompt})
	with st.chat_message("user"):
		st.markdown(prompt)
	response = requests.post(
		f"{API_URL}/chat",
		json={
			"session_id": st.session_state.session_id,
			"customer_id": int(customer_id),
			"message": prompt,
		},
		timeout=120,
	)
	response.raise_for_status()
	payload = response.json()
	st.session_state.messages.append(
		{"role": "assistant", "content": payload["reply"], "tools": payload["tools_called"]}
	)
	st.rerun()
