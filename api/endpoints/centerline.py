from fastapi import APIRouter, UploadFile, File, Form
from ..utils.prisma import prisma
from pydantic import BaseModel
from typing import Annotated

import geopandas as gpd
import shapely.ops

router = APIRouter(prefix="/centerline")

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
async def create_centerline(
  name: Annotated[str,Form()],
  description: Annotated[str,Form()],
  marker_value_col: Annotated[str,Form()],
  shp_line: UploadFile = File(...),
  shp_markers: UploadFile = File(...),
  shp_footprint: UploadFile = File(...),
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
      "userId": 1,
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
async def delete_centerline(centerline_id:int):
  return await prisma.centerline.delete(where={"id":centerline_id})