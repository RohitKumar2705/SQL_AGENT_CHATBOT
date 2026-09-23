from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # must happen before app.agent is imported (it reads env vars)

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from .agent import ask_agent  # noqa: E402

app = FastAPI(title="SQL Agent Chatbot")

STATIC_DIR = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    question = request.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="message must not be empty")
    try:
        reply = ask_agent(question)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e
    return ChatResponse(reply=reply)


# Serve the static frontend last, so it doesn't shadow the /api/* routes above.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
