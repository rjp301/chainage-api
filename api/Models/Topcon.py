# import matplotlib.pyplot as plt
from ..utils.ACAD import Point,Polyline
from .Centerline import Centerline,format_KP
from dataclasses import dataclass
from fastapi import UploadFile
from tempfile import NamedTemporaryFile

import shapefile
import pandas as pd
import geopandas as gpd


@dataclass
class Topcon:
  slope: float
  width_bot: float
  file_ditch: UploadFile
  file_ground: UploadFile
  CL: Centerline

  def __post_init__(self):
    self.rover_import()
    self.ditch_import()
    self.volume_calc()
    print("calculations complete")

  def rover_import(self):
    columns = ["num","y","x","z","desc"]
    data = pd.read_csv(self.file_ground.file,header=None)
    data.columns = columns
    data["geom_ACAD"] = [Point(row["x"],row["y"],row["z"]) for _,row in data.iterrows()]
    data["geometry"] = gpd.points_from_xy(data.x,data.y,data.z)
    data = gpd.GeoDataFrame(data,crs=self.CL.crs)
    data["chainage"] = data.geometry.apply(self.CL.find_KP)
    self.data_pts = data.sort_values("chainage").reset_index(drop=True)

  def ditch_import(self):
    with NamedTemporaryFile() as temp_file:
      temp_file.write(self.file_ditch.file.read())
      with shapefile.Reader(shp=temp_file) as shp:
        shapes = shp.shapes()
        points = shapes[0].points
        z_coords = shapes[0].z
        vertices = [Point(i[0],i[1],z) for i,z in zip(points,z_coords)]
        self.ditch = Polyline(vertices)

  def volume_calc(self):
    for index,row in self.data_pts.iterrows():
      pt = row["geom_ACAD"]
      
      try: depth = pt.z - self.ditch.elevation_at_pt(pt)
      except Exception as e:
        continue

      width_top = depth/self.slope*2 + self.width_bot if self.slope > 0 else self.width_bot
      self.data_pts.at[index,"depth"] = depth
      self.data_pts.at[index,"slope"] = self.slope
      self.data_pts.at[index,"width_bot"] = self.width_bot
      self.data_pts.at[index,"width_top"] = width_top
      self.data_pts.at[index,"area"] = self.width_bot*depth + (width_top - self.width_bot)/2*depth

    self.data_pts["geometry"] = [i.wkt for i in self.data_pts["geometry"]]
    self.data_pts = self.data_pts.drop("geom_ACAD",axis=1)
    print(self.data_pts,"\n")

    # Filter points for those that have a depth
    data_pts_copy = self.data_pts.copy().dropna().reset_index(drop=True)
    
    # Create string describing scope of volume info
    self.KP_min = min(data_pts_copy["chainage"])
    self.KP_max = max(data_pts_copy["chainage"])
    self.KP_rng = f"{format_KP(self.KP_min)} to {format_KP(self.KP_max)}"
    
    # Create dataframe of volumes for sections
    self.data_rng = pd.DataFrame()

    self.data_rng["KP_beg"] = data_pts_copy["chainage"].tolist()[:-1]
    self.data_rng["KP_end"] = data_pts_copy["chainage"].tolist()[1:]
    self.data_rng["area_beg"] = data_pts_copy["area"].tolist()[:-1]
    self.data_rng["area_end"] = data_pts_copy["area"].tolist()[1:]

    self.data_rng["area_avg"] = (self.data_rng["area_beg"] + self.data_rng["area_end"]) / 2
    self.data_rng["length"] = self.data_rng["KP_end"] - self.data_rng["KP_beg"]
    self.data_rng["volume"] = self.data_rng["length"] * self.data_rng["area_avg"]
    
    print(self.data_rng,"\n")


  def save(self):
    return {
      "width_bot": self.width_bot,
      "slope": self.slope,
      "ditch_profile": str(self.ditch),
      "total_volume": sum(self.data_rng["volume"]),
      "data_pts": {"create": self.data_pts.to_dict("records")},
      "data_rng": {"create": self.data_rng.to_dict("records")},
      "KP_beg": self.KP_min,
      "KP_end": self.KP_max,
      "KP_rng": self.KP_rng,
      "centerlineId": self.CL.id,
      "userId": 1,
      "data_crs": self.CL.crs,
    }