from fastapi import APIRouter, UploadFile, File, Form
from ..utils.prisma import prisma
from ..models.Topcon import Topcon
from ..models.Centerline import Centerline
from pydantic import BaseModel
from typing import Annotated

import json

router = APIRouter(prefix="/topcon")

@router.post("/")
async def run_topcon(
  width_bot: Annotated[float,Form()],
  slope: Annotated[float,Form()],
  centerlineId: Annotated[int,Form()],
  data_crs: Annotated[str,Form()],
  ground_csv: UploadFile = File(...),
  ditch_shp: UploadFile = File(...),
):
  
  centerline = Centerline(await prisma
    .centerline
    .find_unique(
      where={"id":centerlineId},
      include={"markers":True})
  )

  topcon = Topcon(
    slope=slope,
    width_bot=width_bot,
    CL=centerline.to_crs(data_crs),
    file_ground=ground_csv,
    file_ditch=ditch_shp
  )

  with open("test.json","w") as file: json.dump(topcon.save(),file)
  topcon_saved = await prisma.topconrun.create(
    data=topcon.save(),
    include={"data_pts":True,"data_rng":True}
  )
  return topcon_saved


@router.get("/")
async def all_topcon_runs():
  return await prisma.topconrun.find_many()


@router.get("/{run_id}")
async def get_run(run_id: int):
  run = await prisma.topconrun.find_unique(where={ "id": run_id })
  # data_rng = await prisma.topcondatarng.find_unique(where={"runId": run_id})
  # data_pts = await prisma.topcondatapts.find_unique(where={"runId": run_id})
  # return {"info": run, "data_pts": data_pts, "data_rng": data_rng}
  return run

@router.get("/download/{run_id}")
async def download_run(run_id: int):
  return { "run_id": run_id }

