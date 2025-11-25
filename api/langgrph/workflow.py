from langgraph.graph import StateGraph, END

from api.langgrph.agents import query_resolution_agent, data_extraction_agent, validation_agent, summarization_agent
from api.langgrph.state import AgentState


def validation_router(state):
    if state['validation_status'] == 'valid':
        return "summarizer"
    if state['retry_count'] > 3:
        return "summarizer"
    return "resolution"


workflow = StateGraph(AgentState)


workflow.add_node("resolution", query_resolution_agent)
workflow.add_node("extraction", data_extraction_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("summarizer", summarization_agent)


workflow.set_entry_point("resolution")
workflow.add_edge("resolution", "extraction")
workflow.add_edge("extraction", "validation")


workflow.add_conditional_edges(
    "validation",
    validation_router,
    {
        "summarizer": "summarizer",
        "resolution": "resolution"
    }
)

workflow.add_edge("summarizer", END)

agent_app = workflow.compile()