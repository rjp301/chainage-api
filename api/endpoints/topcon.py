from fastapi import APIRouter, UploadFile, File, Form
from ..utils.prisma import prisma
from ..utils.volume_calc import volume_calc
from pydantic import BaseModel
from typing import Annotated

router = APIRouter(prefix="/topcon")

class TopconInfo(BaseModel):
  width_bot: float
  slope: float

@router.post("/")
async def run_topcon(
  width_bot: Annotated[float,Form()],
  slope: Annotated[float,Form()],
  centerlineId: Annotated[int,Form()],
  ground_csv: UploadFile = File(...),
  ditch_shp: UploadFile = File(...),
):
  
  result = volume_calc(
    slope=slope,
    width_bot=width_bot,
    ground_csv=ground_csv.file,
    ditch_shp=ditch_shp.filename
  )

  # Perform topcon calculation here including calculating KP of points
  # Transform ditch_shp
  # Transform ground_csv
  # Calculate height and area for each point
  # Convert points to ranges
  # Calculate volumes for each range
  # Save all pertinent info to db
  # Return data_pts and data_rng and KP string

  return result


@router.get("/")
async def all_topcon_runs():
  return await prisma.topconrun.find_many()


@router.get("/{run_id}")
async def get_run(run_id: int):
  run = await prisma.topconrun.find_unique(where={ "id": run_id })
  data_rng = await prisma.topcondatarng.find_unique(where={"runId": run_id})
  data_pts = await prisma.topcondatapts.find_unique(where={"runId": run_id})
  return {"info": run, "data_pts": data_pts, "data_rng": data_rng}


@router.get("/download/{run_id}")
async def download_run(run_id: int):
  return { "run_id": run_id }

