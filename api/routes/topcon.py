from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from ..utils.prisma import prisma
from ..models.Topcon import Topcon
from ..models.Centerline import Centerline
from typing import Annotated
from tempfile import NamedTemporaryFile

import pandas as pd

router = APIRouter(prefix="/topcon")


@router.post("/")
async def run_topcon(
    request: Request,
    width_bot: Annotated[float, Form()],
    slope: Annotated[float, Form()],
    centerline_id: Annotated[int, Form()],
    data_crs: Annotated[str, Form()],
    ground_csv: UploadFile = File(...),
    ditch_shp: UploadFile = File(...),
):
    print(request)
    centerline = Centerline(
        await prisma.centerline.find_unique(
            where={"id": centerline_id}, include={"markers": True}
        )
    )

    topcon = Topcon(
        slope=slope,
        width_bot=width_bot,
        CL=centerline.to_crs(data_crs),
        file_ground=ground_csv,
        file_ditch=ditch_shp,
    )

    return await prisma.topconrun.create(
        data=topcon.__dict__(),
        include={"data_pts": True, "data_rng": True},
    )


@router.get("/")
async def all_topcon_runs(request: Request):
    return await prisma.topconrun.find_many()


@router.get("/{run_id}")
async def get_run(run_id: int):
    run = await prisma.topconrun.find_unique(
        where={"id": run_id}, include={"data_pts": True, "data_rng": True}
    )
    return run


@router.delete("/{run_id}")
async def delete_run(run_id: int):
    return await prisma.topconrun.delete(where={"id": run_id})


async def get_temp_dir():
    fname = NamedTemporaryFile(suffix=".xlsx")
    try:
        yield fname.name
    finally:
        del fname


@router.get("/{run_id}/download")
async def download_run(run_id: int, temp_file=Depends(get_temp_dir)):
    run = await get_run(run_id)

    pts_cols = [
        "num",
        "x",
        "y",
        "z",
        "desc",
        "geometry",
        "chainage",
        "slope",
        "width_bot",
        "width_top",
        "area",
    ]
    pts_rename = {i: i.upper() for i in pts_cols}

    rng_cols = [
        "KP_beg",
        "KP_end",
        "area_beg",
        "area_end",
        "area_avg",
        "length",
        "volume",
    ]
    rng_rename = {i: i.upper() for i in rng_cols}

    pts_dict = [i.__dict__ for i in run.data_pts]
    pts_excel = pd.DataFrame.from_records(pts_dict)[pts_cols].rename(pts_rename, axis=1)

    rng_dict = [i.__dict__ for i in run.data_rng]
    rng_excel = pd.DataFrame.from_records(rng_dict)[rng_cols].rename(rng_rename, axis=1)

    filename = f"Ditch Volume - {run.KP_rng}.xlsx"

    with pd.ExcelWriter(temp_file) as writer:
        pts_excel.to_excel(writer, sheet_name="point_data", index=False)
        rng_excel.to_excel(writer, sheet_name="range_data", index=False)

    return FileResponse(
        temp_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )
