from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Annotated

import geopandas as gpd
import shapely.ops

router = APIRouter(prefix="/centerline")


@router.post("/")
async def process_centerline(
    marker_value_col: Annotated[str, Form()],
    shp_line: UploadFile = File(...),
    shp_markers: UploadFile = File(...),
):
    EPSG_4326 = "EPSG:4326"

    line = gpd.read_file(shp_line.file).to_crs(EPSG_4326).geometry.unary_union
    line = shapely.ops.linemerge(line) if line.geom_type == "MultiLineString" else line
    line = line.wkt

    df_markers = (
        gpd.read_file(shp_markers.file).to_crs(EPSG_4326).sort_values(marker_value_col)
    )
    markers = [
        {
            "value": float(row[marker_value_col]),
            "x": row.geometry.x,
            "y": row.geometry.y,
        }
        for _, row in df_markers.iterrows()
    ]

    return {
        "markers": markers,
        "line": line,
        "crs": EPSG_4326,
    }
