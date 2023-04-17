# import matplotlib.pyplot as plt
import shapefile
from ..utils.ACAD import Point,Polyline
from centerline import import_CL,format_KP

import pandas as pd
import geopandas as gpd

def rover_import(fname):
  CL = import_CL()
  columns = ["NUM","Y","X","Z","DESC"]

  data = pd.read_csv(fname,header=None)
  data.columns = columns
  data["GEOMETRY"] = [Point(row["X"],row["Y"],row["Z"]) for _,row in data.iterrows()]
  data["geometry"] = gpd.points_from_xy(data.X,data.Y,data.Z)
  data = gpd.GeoDataFrame(data,crs=CL.crs)
  data["CHAINAGE"] = data.geometry.apply(CL.find_KP)
  return data.sort_values("CHAINAGE").reset_index(drop=True)

def ditch_import(fname):
  with shapefile.Reader(fname) as shp:
    shapes = shp.shapes()
    points = shapes[0].points
    z_coords = shapes[0].z
    vertices = [Point(i[0],i[1],z) for i,z in zip(points,z_coords)]
    return Polyline(vertices)

def get_KP_range(data_pts:pd.DataFrame):
  KP_min = min(data_pts.CHAINAGE)
  KP_max = max(data_pts.CHAINAGE)
  return f"{format_KP(KP_min)} to {format_KP(KP_max)}"

def volume_calc(slope,width_bot,ground_csv,ditch_shp):

  data_pts = rover_import(ground_csv)
  ditch = ditch_import(ditch_shp)
  
  for index,row in data_pts.iterrows():
    pt = row["GEOMETRY"]
    
    try: depth = pt.z - ditch.elevation_at_pt(pt)
    except: continue

    width_top = depth/slope*2 + width_bot if slope > 0 else width_bot
    data_pts.at[index,"DEPTH"] = depth
    data_pts.at[index,"SLOPE"] = slope
    data_pts.at[index,"WIDTH_BOT"] = width_bot
    data_pts.at[index,"WIDTH_TOP"] = width_top
    data_pts.at[index,"AREA"] = width_bot*depth + (width_top - width_bot)/2*depth

  # data_pts = data_pts.drop(["geometry"],axis=1)
  print(data_pts,"\n")

  # Filter points for those that have a depth
  data_pts_copy = data_pts.copy().dropna().reset_index(drop=True)
  
  # Create string describing scope of volume info
  KP_min = min(data_pts_copy.CHAINAGE)
  KP_max = max(data_pts_copy.CHAINAGE)
  KP_range = f"{format_KP(KP_min)} to {format_KP(KP_max)}"
  
  # Create dataframe of volumes for sections
  data_rng = pd.DataFrame()

  data_rng["KP_beg"] = data_pts_copy["CHAINAGE"].tolist()[:-1]
  data_rng["KP_end"] = data_pts_copy["CHAINAGE"].tolist()[1:]
  data_rng["AREA_beg"] = data_pts_copy["AREA"].tolist()[:-1]
  data_rng["AREA_end"] = data_pts_copy["AREA"].tolist()[1:]

  data_rng["AREA_avg"] = (data_rng.AREA_beg + data_rng.AREA_end) / 2
  data_rng["LENGTH"] = data_rng.KP_end - data_rng.KP_beg
  data_rng["VOLUME"] = data_rng.LENGTH * data_rng.AREA_avg

  print(data_rng,"\n")

  return {
    "data_pts": data_pts.drop("geometry",axis=1).to_dict("records"),
    "data_rng": data_rng.to_dict("records"),
    "KP_str": KP_range,
    "KP_beg": KP_min,
    "KP_end": KP_max,
  }

