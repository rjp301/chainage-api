from fastapi import APIRouter
from ..utils.prisma import prisma
from pydantic import BaseModel

import json

router = APIRouter(prefix="/centerline")

class Centerline(BaseModel):
  name: str
  description: str = ""
  line: dict
  markers: dict
  marker_value: str
  footprint: dict | None = None

@router.get("/")
async def all_centerlines():
  return await prisma.centerline.find_many()

@router.get("/{centerline_id}")
async def get_centerline(centerline_id:int):
  return await prisma.centerline.find_unique(where={"id":centerline_id})

@router.post("/")
async def create_centerline(centerline:Centerline):
  return await prisma.centerline.create(centerline)

@router.delete("/{centerline_id}")
async def delete_centerline(centerline_id:int):
  return await prisma.centerline.delete(where={"id":centerline_id})

@router.put("/{centerline_id}")
async def update_centerline(centerline_id:int,centerline:Centerline):
  return await prisma.centerline.update(data=centerline,where={"id":centerline_id})
