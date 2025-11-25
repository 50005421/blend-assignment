from langchain_core.prompts import ChatPromptTemplate
import concurrent.futures
from api.configuration.llm_factory import LLMFactory
from api.service.db_layer import PostgresManager

db = PostgresManager()


def query_resolution_agent(state):
    print(f"🤖 [Resolution Agent] Generating SQL for: {state['question']}")

    llm = LLMFactory.get_llm()

    # Format history for prompt
    history = state.get('chat_history', [])
    history_context = "\n".join(history) if history else "No previous context."

    prompt = ChatPromptTemplate.from_template(
        """You are a PostgreSQL expert. Write a SQL query to answer the user's question.
        
         - if conversation history provides relevant context, use it to inform your SQL generation.
        
        DATABASE SCHEMA:
        {schema}
        
        CONVERSATION HISTORY (Context for follow-up questions):
        {history}
        
        FEW EXAMPLES (Use these as a guide for syntax):
        {rag_examples}
        
        PREVIOUS ERROR (If any - fix this):
        {error}
        
        QUESTION: {question}
        
        Return ONLY the SQL query. No markdown, no backticks."""
    )

    chain = prompt | llm
    response = chain.invoke({
        "schema": state['schema_context'],
        "history": history_context,
        "rag_examples": state['rag_examples'],
        "error": state.get("error", ""),
        "question": state['question']
    })

    clean_sql = response.content.strip().replace("```sql", "").replace("```", "")

    return {
        "sql_query": clean_sql,
        "retry_count": state.get("retry_count", 0) + 1
    }

def data_extraction_agent(state):
    print(f"Extraction Agent || Executing: {state['sql_query']}")

    result = db.execute_query(state['sql_query'])

    if result["success"]:
        return {"query_result": result["data"], "error": None}
    else:
        return {"query_result": None, "error": result["error"]}


def validation_agent(state):
    print("Validation Agent || Checking results...")

    if state['error']:
        print(f"Validation Failed: Error - {state['error']}")
        return {"validation_status": "invalid"}

    if state['query_result'] == "No results found.":
        if state['retry_count'] < 2:
            print("Validation Failed: Empty result, retrying...")
            return {"validation_status": "invalid", "error": "Query returned no data. Check case sensitivity or logic."}

    print("Validation Passed")
    return {"validation_status": "valid"}

def recursive_summarize(llm, full_data_str: str, chunk_size: int = 1000):
    print(f"Recursive Summarizer || Data is large (>1000 rows). Switching to Map-Reduce mode...")
    lines = full_data_str.strip().split('\n')
    if len(lines) < 3:
        return "Data too short to summarize."
    headers = "\n".join(lines[:2])
    data_rows = lines[2:]
    chunks = [data_rows[i:i + chunk_size] for i in range(0, len(data_rows), chunk_size)]
    print(f"📊 Split {len(data_rows)} rows into {len(chunks)} chunks (Chunk Size: {chunk_size}).")
    map_prompt = ChatPromptTemplate.from_template(
        """Analyze this specific subset of data rows. 
        Focus on identifying key trends, anomalies, or high values in this chunk.
        DATA SUBSET:
        {header}
        {rows}
        
        Briefly summarize findings for this chunk:"""
    )
    map_chain = map_prompt | llm

    def process_single_chunk(chunk_data):
        idx, chunk_lines = chunk_data
        chunk_text = "\n".join(chunk_lines)
        try:
            res = map_chain.invoke({"header": headers, "rows": chunk_text})
            return res.content
        except Exception as e:
            return f"Error processing chunk {idx}: {str(e)}"
    print(f"Recursive Summarizer || Spinning up 20 threads for parallel processing...")
    chunk_args = [(i, chunk) for i, chunk in enumerate(chunks)]
    intermediate_summaries = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(process_single_chunk, chunk_args)
        intermediate_summaries = list(results)

    print(f"Recursive Summarizer || All {len(chunks)} chunks processed.")

    print("Recursive Summarizer || Reducing intermediate summaries...")
    combined_summaries = "\n- ".join(intermediate_summaries)

    reduce_prompt = ChatPromptTemplate.from_template(
        """Here are summaries from different parts of a large dataset. 
        Synthesize them into a single, cohesive business answer.
        
        INTERMEDIATE FINDINGS:
        - {combined_summaries}
        
        Final Answer:"""
    )

    reduce_chain = reduce_prompt | llm
    final_res = reduce_chain.invoke({"combined_summaries": combined_summaries})
    return final_res.content

def summarization_agent(state):
    print("Summarizer || Analyzing data size...")
    llm = LLMFactory.get_llm()
    data_str = state['query_result']
    lines = data_str.strip().split('\n')
    line_count = len(lines) - 2 if len(lines) > 2 else 0

    print(f"Retrieved {line_count} rows.")

    if line_count > 1000:
        final_answer = recursive_summarize(llm, data_str, chunk_size=1000)
    else:
        print("Data fits in context. Using standard summarization.")
        prompt = ChatPromptTemplate.from_template(
            """User Question: {question}
            SQL Used: {sql_query}
            Data Retrieved: 
            {query_result}
            
            Provide a clear, business-friendly answer based on the data."""
        )
        chain = prompt | llm
        res = chain.invoke(state)
        final_answer = res.content

    return {"final_answer": final_answer}