from typing import Optional, Dict
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[list[str]] = []

class MetadataRequest(BaseModel):
    table_name: str
    descriptions: Dict[str, str]

class QueryResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    data: Optional[str] = None