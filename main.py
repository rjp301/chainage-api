from api.utils.prisma import prisma
from api.endpoints import convert

from fastapi import FastAPI

app = FastAPI()
app.include_router(convert.router, prefix="/api")

@app.on_event("startup")
async def startup():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()

@app.get("/")
def read_root():
    return {"version": "1.0.0"}
