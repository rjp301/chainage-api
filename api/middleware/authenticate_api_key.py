from fastapi import Request, Response
from fastapi.responses import JSONResponse

from starlette.middleware.base import BaseHTTPMiddleware

from api.utils.prisma import prisma


class AuthenticateApiKey(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        api_key = request.headers.get("X-API-Key")
        user = await prisma.user.find_unique(where={"api_key": api_key})
        if user == None:
            return JSONResponse(status_code=403, content={"msg": "Invalid API Key"})
        response.state.user = user
        response = await call_next(request)
        return response
