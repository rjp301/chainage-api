from api.utils.prisma import prisma
from api.endpoints import topcon,centerline

from fastapi import FastAPI,APIRouter

api = APIRouter(prefix="/api")
api.include_router(topcon.router)
api.include_router(centerline.router)

app = FastAPI(
    debug=True,
    title="Pipeline Applets",
    description="Collection of functions and data useful for constructing pipelines"
)
app.include_router(api)

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