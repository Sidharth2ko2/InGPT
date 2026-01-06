from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.agent.nodes import ask_node, checklist_node, draft_node

DB_URI = "postgresql://postgres:root@localhost:5432/ingpt_db"

connection_pool = AsyncConnectionPool(
    conninfo=DB_URI,
    max_size=20,
    open=False,
    kwargs={
        "autocommit": True,
        "row_factory": dict_row
    }
)

def build_graph(checkpointer):
    workflow = StateGraph(MessagesState)

    workflow.add_node("ask", ask_node)
    workflow.add_node("checklist", checklist_node)
    workflow.add_node("draft", draft_node)

    workflow.set_entry_point("ask")

    # ❗ NO forced END — memory persists
    return workflow.compile(checkpointer=checkpointer)
