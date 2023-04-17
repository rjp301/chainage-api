from fastapi import UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi import APIRouter

import json
import shutil
import shapefile
import openpyxl
import tempfile

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from typing import Dict, List
from pathlib import Path

router = APIRouter()

def create_excel_workbook(file_path, worksheet_data):
  wb = openpyxl.Workbook()
  for sheet_name, sheet_data in worksheet_data.items():
    sheet = wb.create_sheet(sheet_name)
    for row_idx, row_data in enumerate(sheet_data):
      for col_idx, col_data in enumerate(row_data):
        sheet.cell(row=row_idx+1, column=col_idx+1, value=col_data)
  wb.save(file_path)
  return wb

async def get_temp_dir():
  fname = tempfile.NamedTemporaryFile(suffix=".xlsx")
  try:
    yield fname.name
  finally:
    del fname


@router.post("/json-to-excel")
async def json_to_excel(data: dict, fname=Depends(get_temp_dir)):
  filename = data["filename"] + ".xlsx"
  worksheet_data = data["worksheets"]
 
  create_excel_workbook(fname, worksheet_data)
  return FileResponse(fname, 
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
    filename=filename
  )


@router.post("/shapefile-to-geojson")
async def shapefile_to_geojson(file: UploadFile = File(...)):
  with tempfile.TemporaryDirectory() as temp_dir:
    # Save uploaded file to temporary directory
    file_path = Path(temp_dir) / file.filename
    with file_path.open("wb") as buffer:
      shutil.copyfileobj(file.file, buffer)

    # Check if the uploaded file is a valid shapefile
    try:
      sf = shapefile.Reader(str(file_path))
    except shapefile.ShapefileException:
      raise HTTPException(status_code=400, detail="Uploaded file is not a valid Shapefile")

    # Extract the shapefile's fields and features
    fields = [f[0] for f in sf.fields[1:]]
    features = []
    for sr in sf.shapeRecords():
      geom = sr.shape.__geo_interface__
      atr = dict(zip(fields, sr.record))
      features.append(dict(geometry=geom, properties=atr))

    # Convert features to GeoJSON using the geojson package
    geojson_data = json.dumps(dict(type="FeatureCollection", features=features))

  return geojson_data
