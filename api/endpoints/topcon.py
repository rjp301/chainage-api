from fastapi import APIRouter
from ..utils.prisma import prisma

router = APIRouter(prefix="/topcon")

@router.get("/{run_id}")
async def get_run(run_id: int):
  run = await prisma.topconrun.find_unique(
    where={ "id": run_id },
    include={ "data_pts": True, "data_rng": True }
  )
  return run


@router.get("/download/{run_id}")
async def download_run(run_id: int):
  return { "run_id": run_id }

