import json
import psycopg
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from app.schemas import ChatRequest
from app.agent.graph import build_graph, connection_pool, DB_URI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.rag.retriever import retrieve

agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent

    setup_conn = await psycopg.AsyncConnection.connect(DB_URI, autocommit=True)
    try:
        checkpointer = AsyncPostgresSaver(setup_conn)
        await checkpointer.setup()
    finally:
        await setup_conn.close()

    await connection_pool.open()
    agent = build_graph(AsyncPostgresSaver(connection_pool))
    print("🚀 InGPT ready (Memory + Streaming Fixed)")
    yield
    await connection_pool.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.session_id}}

    context_text = ""
    if len(req.question.strip().split()) > 1:
        try:
            context_text, _ = retrieve(req.question)
        except:
            context_text = "No relevant company documents found."

    initial_state = {
        "messages": [HumanMessage(content=req.question)],
        "context": context_text
    }

    async def event_generator():
        async for chunk in agent.astream(initial_state, config, stream_mode="updates"):
            for _, output in chunk.items():
                if "messages" in output:
                    msg = output["messages"][-1]
                    text = msg[1] if isinstance(msg, tuple) else msg.content

                    # 🔒 PRESERVE NEWLINES
                    safe_text = text.replace("\n", "\\n")

                    yield f"data: {json.dumps({'chunk': safe_text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    try:
        state = await agent.aget_state(config)
        messages = []

        if state and "messages" in state.values:
            for msg in state.values["messages"]:
                role = "user" if msg.type == "human" else "assistant"
                messages.append({"role": role, "content": msg.content})

        return {"messages": messages}
    except:
        return {"messages": []}
