from fastapi import APIRouter
from ..utils.prisma import prisma
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/centerline")

class CenterlineMarker(BaseModel):
  value: float
  x: float
  y: float

class Centerline(BaseModel):
  userId: int
  name: str
  description: str = ""
  line: str
  markers: List[CenterlineMarker]

@router.get("/")
async def all_centerlines():
  return await prisma.centerline.find_many()

@router.get("/{centerline_id}")
async def get_centerline(centerline_id:int):
  return await prisma.centerline.find_unique(
    where={"id":centerline_id},
    include={"markers": True}
  )

@router.post("/")
async def create_centerline(centerline:Centerline):
  return await prisma.centerline.create(
    data={
      "userId": centerline.userId,
      "name": centerline.name,
      "description": centerline.description,
      "line": centerline.line,
      "markers": {
        "create": [{"value":marker.value, "x":marker.x, "y":marker.y} for marker in centerline.markers]
      }
    },
    include={"markers":True}
  )

@router.delete("/{centerline_id}")
async def delete_centerline(centerline_id:int):
  return await prisma.centerline.delete(where={"id":centerline_id})

@router.put("/{centerline_id}")
async def update_centerline(centerline_id:int,centerline:Centerline):
  return await prisma.centerline.update(data=centerline,where={"id":centerline_id})
