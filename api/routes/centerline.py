from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from ..utils.prisma import prisma
from pydantic import BaseModel
from typing import Annotated

from .auth import manager

import geopandas as gpd
import shapely.ops

router = APIRouter(prefix="/centerline")

@router.get("/")
async def all_centerlines(user=Depends(manager)):
  return await prisma.centerline.find_many(where={"userId":user.id})

@router.get("/{centerline_id}")
async def get_centerline(centerline_id:int,user=Depends(manager)):
  result = await prisma.centerline.find_unique(
    where={"id":centerline_id},
    include={"markers": True}
  )
  if result.userId != user.id:
    raise HTTPException(status_code=401,detail="Not authorized to access item") 
  return result

@router.post("/")
async def create_centerline(
  name: Annotated[str,Form()],
  description: Annotated[str,Form()],
  marker_value_col: Annotated[str,Form()],
  shp_line: UploadFile = File(...),
  shp_markers: UploadFile = File(...),
  shp_footprint: UploadFile = File(...),
  user=Depends(manager),
):
  
  EPSG_4326 = "EPSG:4326"

  line = gpd.read_file(shp_line.file).to_crs(EPSG_4326).geometry.unary_union
  line = shapely.ops.linemerge(line) if line.geom_type == "MultiLineString" else line
  line = line.wkt

  df_markers = gpd.read_file(shp_markers.file).to_crs(EPSG_4326).sort_values(marker_value_col)
  markers = [{
    "value":float(row[marker_value_col]),
    "x": row.geometry.x,
    "y": row.geometry.y,
    } for _,row in df_markers.iterrows()]

  return await prisma.centerline.create(
    data={
      "userId": user.id,
      "name": name,
      "description": description,
      "line": line,
      "crs": EPSG_4326,
      "markers": {
        "create": markers
      }
    },
    include={"markers":True}
  )

@router.delete("/{centerline_id}")
async def delete_centerline(centerline_id:int,user=Depends(manager)):
  return await prisma.centerline.delete(where={"id":centerline_id})