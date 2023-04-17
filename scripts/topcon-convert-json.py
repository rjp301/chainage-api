import pandas as pd
import os,shutil
import json
import shapefile

from shapely.geometry import LineString,Point
from centerline import format_KP


def clear_folder(folder):
  for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
      if os.path.isfile(file_path) or os.path.islink(file_path):
        os.unlink(file_path)
      elif os.path.isdir(file_path):
        shutil.rmtree(file_path)
    except Exception as e:
      print('Failed to delete %s. Reason: %s' % (file_path, e))

def ditch_import(fname):
  with shapefile.Reader(fname) as shp:
    shapes = shp.shapes()
    points = shapes[0].points
    z_coords = shapes[0].z
    vertices = [Point(i[0],i[1],z) for i,z in zip(points,z_coords)]
    return LineString(vertices).wkt

output_folder = "/Users/riley/Desktop/topcon_runs"
path = "/Users/riley/Projects/pipeline-applets/topcon/runs"
runs = os.listdir(path)
runs.sort()

clear_folder(output_folder)

for index,run in enumerate(runs):
  result = {}
  
  files = os.listdir(os.path.join(path,run))

  excel = [i for i in files if ".xlsx" in i and "~" not in i]
  if not excel: continue
  excel = pd.ExcelFile(os.path.join(path,run,excel[0]))

  pnt_rename = {
    "NUM":"num",
    "Y":"y",
    "X":"x",
    "Z":"z",
    "DESC":"desc",
    "GEOMETRY":"geometry",
    "CHAINAGE":"chainage",
    "DEPTH":"depth",
    "SLOPE":"slope",
    "WIDTH_BOT":"width_bot",
    "WIDTH_TOP":"width_top",
    "AREA":"area"
  }

  rng_rename = {
    "AREA_beg":"area_beg",
    "AREA_end":"area_end",
    "AREA_avg":"area_avg",
    "LENGTH":"length",
    "VOLUME":"volume",
  }

  pnt_data = (excel
    .parse("point_data")
    .rename(pnt_rename,axis=1)
  )
  result["width_bot"] = max(pnt_data["width_bot"].dropna())
  result["slope"] = max(pnt_data["slope"].dropna())
  result["data_pts"] = (pnt_data
    .to_dict(orient="records")
  )

  rng_data = (excel
    .parse("range_data")
    .rename(rng_rename,axis=1)
  )
  # print(rng_data)
  result["total_volume"] = sum(rng_data["volume"])
  result["data_rng"] = (rng_data
    .to_dict(orient="records")
  )

  KP_beg = min(rng_data["KP_beg"])
  KP_end = max(rng_data["KP_end"])

  result["KP"] = {
    "beg": KP_beg,
    "end": KP_end,
    "str": f"{format_KP(KP_beg)} to {format_KP(KP_end)}"
  }

  print(run)
  # print(files)
  shp = [i for i in files if ".shp" in i][0]
  result["ditch_profile"] = ditch_import(os.path.join(path,run,shp))


  # print(result)
  fname = os.path.join(output_folder,f"run_{index:04d}.json")
  with open(fname,"w") as file:
    text = json.dumps(result)
    text = text.replace("NaN","null")
    file.write(text)
