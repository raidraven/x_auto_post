from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from middleware.line_auth import verify_line_token
from services.claude_service import chat_stream

router = APIRouter(prefix="/api/chat", tags=["chat"])


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    mood_score: str = "未記録"
    current_goal: str = "未設定"


@router.post("")
async def chat(
    body: ChatRequest,
    request: Request,
    _: str = Depends(verify_line_token),
):
    display_name = getattr(request.state, "display_name", "あなた")
    messages_dict = [m.model_dump() for m in body.messages]

    async def generate():
        async for chunk in chat_stream(
            messages=messages_dict,
            user_name=display_name,
            mood_score=body.mood_score,
            current_goal=body.current_goal,
        ):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")
