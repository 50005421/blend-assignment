import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8012"

st.set_page_config(page_title="Bend Insights AI", layout="wide")
st.title("Blend Assistant")

#get table-name from api
def get_ingested_tables():
    try:
        response = requests.post(f"{API_URL}/get_ingested_table")
        if response.status_code == 200:
            data = response.json()
            return data.get("tables", [])
        else:
            st.error(f"Error fetching tables: {response.text}")
            return []
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return []

# --- Sidebar: Configuration & Ingestion ---
with st.sidebar:
    existing_tables = get_ingested_tables()
    if existing_tables:
        st.markdown("**Existing Tables:**")
        st.markdown("\n".join([f"- {t}" for t in existing_tables]))

    st.divider()

    st.header("📂 Data Ingestion")
    uploaded_file = st.file_uploader("Upload Sales CSV", type=["csv"])

    if uploaded_file:
        table_name = uploaded_file.name.split(".")[0].lower()
        table_name = table_name.replace(' ', '_')
        table_name = st.text_input("Table Name", table_name)
        st.info(f"Proposed Table Name: **{table_name}**")
        if st.button("Upload & Ingest"):
            with st.spinner("Ingesting data into Database..."):
                files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                data = {"table_name": table_name}

                try:
                    response = requests.post(f"{API_URL}/ingest", files=files, data=data)

                    if response.status_code == 200:
                        res_json = response.json()
                        st.success(res_json["message"])
                        st.session_state['ingested_columns'] = res_json.get("columns", [])
                        st.session_state['ingested_table'] = table_name
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    # Metadata Description Form (Shows after successful ingestion)
    if 'ingested_columns' in st.session_state and st.session_state['ingested_columns']:
        st.info("ℹ️ Help the AI understand your columns:")

        with st.form("metadata_form"):
            descriptions = {}
            cols = st.session_state['ingested_columns']

            for col in cols:
                descriptions[col] = st.text_input(f"Description for '{col}'", placeholder=f"What is {col}?")

            submitted = st.form_submit_button("Save Context")

            if submitted:
                # Filter out empty descriptions
                valid_descriptions = {k: v for k, v in descriptions.items() if v.strip()}

                if valid_descriptions:
                    payload = {
                        "table_name": st.session_state['ingested_table'],
                        "descriptions": valid_descriptions
                    }
                    try:
                        res = requests.post(f"{API_URL}/metadata", json=payload)
                        if res.status_code == 200:
                            st.success("Metadata saved successfully!")
                            # Clear state to hide form
                            del st.session_state['ingested_columns']
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save metadata: {e}")

# --- Main Chat Interface ---

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Optional: Show SQL/Data if available in history (stored as extra fields)
        if "sql" in message:
            with st.expander("View SQL"):
                st.code(message["sql"], language="sql")
        if "data" in message:
            with st.expander("View Raw Data"):
                st.text(message["data"])

# Chat Input
if prompt := st.chat_input("Ask a question about your sales data..."):
    # 1. Add User Message to History
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history_log = []
    for msg in st.session_state.messages[-6:]:
        if msg["role"] == "user":
            history_log.append(f"User: {msg['content']}")
        elif msg["role"] == "assistant":
            sql = msg.get("sql")
            if sql:
                history_log.append(f"Assistant SQL: {sql}")
            else:
                history_log.append(f"Assistant: {msg['content']}")

    # 2. Call API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                payload = {"question": prompt,
                           "chat_history": history_log
                           }
                response = requests.post(f"{API_URL}/chat", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer")
                    sql = data.get("sql_query")
                    raw_data = data.get("data")

                    st.markdown(answer)

                    # Show debug artifacts
                    if sql:
                        with st.expander("🔍 View Generated SQL"):
                            st.code(sql, language="sql")
                    if raw_data:
                        with st.expander("📊 View Retrieved Data"):
                            st.text(raw_data)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sql": sql,
                        "data": raw_data
                    })
                else:
                    error_msg = f"Error {response.status_code}: {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except Exception as e:
                st.error(f"API Connection Error: {e}")