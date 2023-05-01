from api.utils.prisma import prisma
from api.routes import topcon, centerline

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware

from api.middleware.authenticate_api_key import AuthenticateApiKey

api = APIRouter(prefix="/api")
api.include_router(centerline.router)
api.include_router(topcon.router)


app = FastAPI(
    debug=True,
    title="Pipeline Applets",
    description="Collection of functions and data, useful for constructing pipelines",
)
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthenticateApiKey)


@app.on_event("startup")
async def startup():
    await prisma.connect()


@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()


@app.get("/")
def read_root():
    return {"version": "1.0.0"}


@app.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    return url_list
