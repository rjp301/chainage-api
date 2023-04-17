from fastapi import UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi import APIRouter

import json
import shutil
import shapefile

from tempfile import TemporaryDirectory
from tempfile import NamedTemporaryFile

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from typing import Dict, List
from pathlib import Path

router = APIRouter()

@router.post("/json-to-excel")
async def json_to_excel(data: Dict[str, List[Dict[str, str]]]):
  # Validate the JSON payload
  if not isinstance(data, dict):
    raise HTTPException(status_code=400, detail="Invalid JSON payload: expected a dictionary")

  for ws_name, rows in data.items():
    if not isinstance(ws_name, str):
      raise HTTPException(status_code=400, detail=f"Invalid worksheet name: {ws_name}")

    if not isinstance(rows, list):
      raise HTTPException(status_code=400, detail=f"Invalid data rows for worksheet {ws_name}: expected a list")

    if not all(isinstance(row, dict) for row in rows):
      raise HTTPException(status_code=400, detail=f"Invalid data rows for worksheet {ws_name}: expected a list of dictionaries")

  # Create a new Excel workbook
  wb = Workbook()

  # Loop through each worksheet in the JSON payload
  for ws_name, rows in data.items():
    # Create a new worksheet in the workbook
    ws = wb.create_sheet(title=ws_name)

    # Add the column headers to the first row of the worksheet
    headers = rows[0].keys()
    for col_num, header in enumerate(headers, 1):
      col_letter = get_column_letter(col_num)
      ws[f"{col_letter}1"] = header

    # Add the data rows to the worksheet
    for row_num, row_data in enumerate(rows, 2):
      for col_num, cell_data in enumerate(row_data.values(), 1):
        col_letter = get_column_letter(col_num)
        ws[f"{col_letter}{row_num}"] = cell_data

  # Write the workbook to a temporary file
  with NamedTemporaryFile(delete=True) as tmp:
    wb.save(tmp.name)
    tmp.seek(0)

    # Return the temporary file as a StreamingResponse with the appropriate content type
    return StreamingResponse(tmp, 
      media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
      headers={"Content-Disposition": "attachment; filename=export.xlsx"}
    )


@router.post("/shapefile-to-geojson")
async def shapefile_to_geojson(file: UploadFile = File(...)):
  with TemporaryDirectory() as temp_dir:
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
