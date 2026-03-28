import os
import httpx
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

LINE_VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"


async def verify_line_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """LINEのIDトークンを検証してline_user_idを返す"""
    id_token = credentials.credentials
    channel_id = os.environ.get("LINE_CHANNEL_ID", "")

    # 開発環境ではバイパス
    if os.environ.get("APP_ENV") == "development" and id_token == "dev-token":
        request.state.line_user_id = "dev-user-001"
        request.state.display_name = "テストユーザー"
        return "dev-user-001"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            LINE_VERIFY_URL,
            data={"id_token": id_token, "client_id": channel_id},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid LINE token")

    payload = resp.json()
    line_user_id: str = payload.get("sub", "")
    display_name: str = payload.get("name", "あなた")

    if not line_user_id:
        raise HTTPException(status_code=401, detail="Cannot extract user ID")

    request.state.line_user_id = line_user_id
    request.state.display_name = display_name
    return line_user_id
