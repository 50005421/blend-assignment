from typing import TypedDict, Optional, List


class AgentState(TypedDict):
    question: str
    schema_context: str
    rag_examples: str
    sql_query: str
    query_result: Optional[str]
    error: Optional[str]
    validation_status: str
    retry_count: int
    final_answer: str
    chat_history: List[str]