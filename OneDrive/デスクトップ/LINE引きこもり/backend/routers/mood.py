from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from middleware.line_auth import verify_line_token

router = APIRouter(prefix="/api/mood", tags=["mood"])


class MoodRecord(BaseModel):
    score: int       # 1〜5
    note: str = ""   # 一言メモ（任意）


@router.post("")
async def save_mood(
    body: MoodRecord,
    request: Request,
    _: str = Depends(verify_line_token),
):
    # MVP: DBなしでそのまま返す（フロントのlocalStorageで保持）
    return {
        "ok": True,
        "score": body.score,
        "note": body.note,
        "user_id": request.state.line_user_id,
    }
