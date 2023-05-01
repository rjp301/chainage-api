from fastapi import HTTPException, Request, Response
from dotenv import load_dotenv

from starlette.middleware.base import BaseHTTPMiddleware

import os

load_dotenv()
API_KEY = os.getenv("API_KEY")


class AuthenticateApiKey(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        api_key = request.headers.get("X-API-Key")
        if api_key != API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API Key")
        response = await call_next(request)
        return response
