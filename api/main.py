import shutil
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from api.langgrph.workflow import agent_app
from api.modal.model import MetadataRequest, QueryResponse, QueryRequest
from api.service.db_layer import PostgresManager
from api.service.vector_layer import RAGManager

app = FastAPI()

db = PostgresManager()
rag = RAGManager()
rag.ingest_examples()

os.makedirs("temp_uploads", exist_ok=True)

@app.post("/ingest")
async def ingest_data(
        table_name: str = Form(...),
        file: UploadFile = File(...)
):
    file_location = f"temp_uploads/{file.filename}"

    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        success, columns = db.ingest_csv(file_location, table_name)
        os.remove(file_location)
        if success:
            return {"status": "success", "columns": columns, "message": f"Table '{table_name}' created."}
        else:
            raise HTTPException(status_code=500, detail="Failed to ingest data into DB.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/metadata")
async def save_metadata(request: MetadataRequest):
    try:
        db.save_column_metadata(request.table_name, request.descriptions)
        return {"status": "success", "message": "Metadata saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    try:
        schema_context = db.get_schema_string()
        rag_context = rag.retrieve_similar_examples(request.question)


        initial_state = {
            "question": request.question,
            "chat_history": request.chat_history[:-1],
            "schema_context": schema_context,
            "rag_examples": rag_context,
            "retry_count": 0,
            "error": None,
            "sql_query": "",
            "query_result": "",
            "validation_status": "",
            "final_answer": ""
        }

        result = agent_app.invoke(initial_state)

        return QueryResponse(
            answer=result.get("final_answer", "No answer generated."),
            sql_query=result.get("sql_query"),
            data=result.get("query_result")
        )

    except Exception as e:
        return QueryResponse(answer=f"System Error: {str(e)}")

@app.post("/get_ingested_table", status_code=200)
def get_ingested_table():
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """

    result = db.execute_query(query)
    if not result.get("success"):
        return {"tables": [], "error": result.get("error")}

    raw_df = result.get("raw_df")

    if raw_df is None or raw_df.empty:
        return {"tables": []}

    table_list = raw_df["table_name"].tolist()
    table_list.remove("column_metadata") if "column_metadata" in table_list else None
    return {"tables": table_list}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
