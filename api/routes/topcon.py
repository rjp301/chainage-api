from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from ..models.Centerline import Centerline, format_KP
from ..utils.ACAD import Point, Polyline

from typing import Annotated
from tempfile import NamedTemporaryFile
from numpy import nan

import shapefile
import pandas as pd
import geopandas as gpd

router = APIRouter(prefix="/topcon")


def rover_import(file_ground: UploadFile, CL: Centerline, data_crs: str):
    data = pd.read_csv(file_ground.file, header=None)
    columns = (
        ["num", "y", "x", "z", "desc"]
        if data.at[0, 1] > data.at[0, 2]
        else ["num", "x", "y", "z", "desc"]
    )
    data.columns = columns
    data["geom_ACAD"] = [
        Point(row["x"], row["y"], row["z"]) for _, row in data.iterrows()
    ]
    data["geometry"] = gpd.points_from_xy(data.x, data.y, data.z)
    data = gpd.GeoDataFrame(data, crs=data_crs)
    data["chainage"] = data.geometry.apply(CL.find_KP)
    return data.sort_values("chainage").reset_index(drop=True)


def ditch_import(file_ditch: UploadFile):
    with NamedTemporaryFile() as temp_file:
        temp_file.write(file_ditch.file.read())
        with shapefile.Reader(shp=temp_file) as shp:
            shapes = shp.shapes()
            points = shapes[0].points
            z_coords = shapes[0].z
            vertices = [Point(i[0], i[1], z) for i, z in zip(points, z_coords)]
            return Polyline(vertices)


@router.post("/")
async def run_topcon(
    width_bot: Annotated[float, Form()],
    slope: Annotated[float, Form()],
    centerline: Annotated[str, Form()],
    data_crs: Annotated[str, Form()],
    ground_csv: UploadFile = File(...),
    ditch_shp: UploadFile = File(...),
):
    CL = Centerline(centerline).to_crs(data_crs)

    data_pts = rover_import(ground_csv, CL, data_crs)
    ditch = ditch_import(ditch_shp)

    for index, row in data_pts.iterrows():
        pt = row["geom_ACAD"]

        try:
            depth = pt.z - ditch.elevation_at_pt(pt)
        except Exception as e:
            continue

        width_top = depth / slope * 2 + width_bot if slope > 0 else width_bot
        data_pts.at[index, "depth"] = depth
        data_pts.at[index, "slope"] = slope
        data_pts.at[index, "width_bot"] = width_bot
        data_pts.at[index, "width_top"] = width_top
        data_pts.at[index, "area"] = (
            width_bot * depth + (width_top - width_bot) / 2 * depth
        )

    if "depth" not in data_pts.columns:
        raise HTTPException(
            status_code=500, detail="Could not get the depth of any points"
        )

    data_pts["geometry"] = [i.wkt for i in data_pts["geometry"]]
    data_pts = data_pts.drop("geom_ACAD", axis=1)
    # print(data_pts, "\n")

    # Filter points for those that have a depth
    data_pts_copy = data_pts.copy().dropna().reset_index(drop=True)

    # Create string describing scope of volume info
    KP_min = min(data_pts_copy["chainage"])
    KP_max = max(data_pts_copy["chainage"])
    KP_rng = f"{format_KP(KP_min)} to {format_KP(KP_max)}"

    # Create dataframe of volumes for sections
    data_rng = pd.DataFrame()

    data_rng["KP_beg"] = data_pts_copy["chainage"].tolist()[:-1]
    data_rng["KP_end"] = data_pts_copy["chainage"].tolist()[1:]
    data_rng["area_beg"] = data_pts_copy["area"].tolist()[:-1]
    data_rng["area_end"] = data_pts_copy["area"].tolist()[1:]

    data_rng["area_avg"] = (data_rng["area_beg"] + data_rng["area_end"]) / 2
    data_rng["length"] = data_rng["KP_end"] - data_rng["KP_beg"]
    data_rng["volume"] = data_rng["length"] * data_rng["area_avg"]

    # print(data_rng, "\n")

    return {
        "ditch_profile": str(ditch),
        "total_volume": sum(data_rng["volume"]),
        "data_pts": data_pts.replace({nan: None}).to_dict("records"),
        "data_rng": data_rng.replace({nan: None}).to_dict("records"),
        "KP_beg": KP_min,
        "KP_end": KP_max,
        "KP_rng": KP_rng,
    }
