from tempfile import NamedTemporaryFile
from fastapi.responses import FileResponse
from fastapi import Depends, APIRouter, Request

from typing import List, Dict, Optional
from pydantic import BaseModel

import pandas as pd

router = APIRouter(prefix="/convert")


async def get_temp_dir():
    fname = NamedTemporaryFile(suffix=".xlsx")
    try:
        yield fname.name
    finally:
        del fname


class Sheet(BaseModel):
    sheetname: Optional[str] = None
    records: List[Dict]


class XlsxData(BaseModel):
    filename: Optional[str] = "workbook"
    sheets: List[Sheet]


@router.post("/xlsx")
async def convert_xlsx(data: XlsxData, temp_file=Depends(get_temp_dir)):
    filename = data.filename
    filename = filename if filename.endswith(".xlsx") else filename + ".xlsx"

    with pd.ExcelWriter(temp_file) as writer:
        for sheet in data.sheets:
            df = pd.DataFrame.from_records(sheet.records)
            df.to_excel(writer, sheet_name=sheet.sheetname, index=False)

    return FileResponse(
        temp_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )
