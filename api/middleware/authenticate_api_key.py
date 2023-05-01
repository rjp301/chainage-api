from fastapi import Request, Response
from fastapi.responses import JSONResponse

from starlette.middleware.base import BaseHTTPMiddleware

from api.utils.prisma import prisma

unprotected_routes = set([("POST", "/api/user/")])


async def get_user_from_api_key(api_key: str):
    return await prisma.user.find_unique(where={"api_key": api_key})


class AuthenticateApiKey(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        url = request.url.path
        method = request.method
        if (method, url) in unprotected_routes:
            print("unprotected route")
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=403,
                content={"msg": "Must include API Key in X-API-Key header"},
            )

        user = await get_user_from_api_key(api_key)
        if user is None:
            return JSONResponse(status_code=401, content={"msg": "Invalid API Key"})

        response = await call_next(request)
        response.state.user = user
        return response
