# Blend Insights Assistant

An autonomous, multi-agent system designed to query large-scale retail
datasets using natural language. It features a scalable
architecture with PostgreSQL, LangGraph, FastAPI, and Streamlit.

------------------------------------------------------------------------

## **Architecture**

-   **Frontend:** Streamlit (Port 8501)
-   **Backend:** FastAPI (Port 8000)
-   **Database:** PostgreSQL (Structured Data)
-   **Vector Store:** FAISS + Ollama (RAG for SQL Examples)
-   **Orchestration:** LangGraph (Stateful Agent Loops)

------------------------------------------------------------------------

## **Prerequisites**

-   Python 3.12
-   PostgreSQL Database installed and running
-   Ollama installed (for local embeddings)
    -   Download from: https://ollama.com
    -   Run command: `ollama pull embaddinggamma`

------------------------------------------------------------------------

## **Installation & Setup**

### **1. Extract zip & Install Dependencies**

``` bash
cd blend-assistant
pip install -r requirements.txt
```

### **2. Configuration**

Open `configuration.py` and update: - Azure API Keys - `DB_CREDENTIALS`
(Host, User, Password) to match your local PostgreSQL instance

### **3. Initialize Database**

Ensure PostgreSQL is running and create a database named
`blend_retails`.

The application will automatically create tables during data ingestion.

------------------------------------------------------------------------

## **How to Run**

Use two terminals: one for backend and one for frontend.

### **Terminal 1: Start the Backend API**

Handles agents, LangGraph logic, and database connections.

``` bash
uvicorn fastapi_server:app --reload
```

API Docs available at:

    http://localhost:8000/docs

### **Terminal 2: Start the UI**

Launches the chat interface.

``` bash
cd streamlit_ui
streamlit run assignment.py
```

UI available at:

    http://localhost:8501

------------------------------------------------------------------------

## **Usage Guide**

### **Model**

Uses Azure OpenAI by default.

### **1. Ingest Data**

-   Go to **Data Ingestion** in the sidebar
-   Upload your CSV file
-   Provide a table name (e.g., `transactions`)
-   Click **Upload & Ingest**

### **2. Add Metadata (Important)**

After upload, you will be prompted to describe the columns.

Example: - Column: `amt_1` → "Gross Sales Revenue"

This improves SQL accuracy and AI understanding.

### **3. Chat**

Ask questions such as: - *"What is the total revenue by region?"* -
*"Show me the top 5 products."*

You can view: - Generated SQL - Raw data

Both are displayed in expandable tabs.

------------------------------------------------------------------------

## **Advanced Features**

### **Map-Reduce Summarization**

For queries returning more than 1000 rows, the system automatically
switches to parallel processing to summarize data in chunks.

### **Context Awareness**

Chat history is maintained, allowing follow-up questions like: - *"What
about for the South region?"*

### **Self-Correction**

If generated SQL fails, the Validation Agent detects and forces an
automatic retry.

-----------------------------------------------------------------------
