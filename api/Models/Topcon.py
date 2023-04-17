# import matplotlib.pyplot as plt
import shapefile
from ..utils.ACAD import Point,Polyline

from .Centerline import Centerline

from dataclasses import dataclass
import pandas as pd
import geopandas as gpd

from fastapi import File

@dataclass
class Topcon:
  slope: float
  width_bot: float
  file_ditch: File
  file_ground: File
  CL: Centerline

  def __post_init__(self):
    self.rover_import()
    self.ditch_import()
    self.volume_calc()

  def rover_import(self):
    columns = ["NUM","Y","X","Z","DESC"]
    data = pd.read_csv(self.file_ground.file,header=None)
    data.columns = columns
    data["GEOMETRY"] = [Point(row["X"],row["Y"],row["Z"]) for _,row in data.iterrows()]
    data["geometry"] = gpd.points_from_xy(data.X,data.Y,data.Z)
    data = gpd.GeoDataFrame(data,crs=self.CL.crs)
    data["CHAINAGE"] = data.geometry.apply(self.CL.find_KP)
    self.data_pts = data.sort_values("CHAINAGE").reset_index(drop=True)

  def ditch_import(self):
    with shapefile.Reader(self.file_ditch.filename) as shp:
      shapes = shp.shapes()
      points = shapes[0].points
      z_coords = shapes[0].z
      vertices = [Point(i[0],i[1],z) for i,z in zip(points,z_coords)]
      self.ditch = Polyline(vertices)

  def volume_calc(self):
    for index,row in self.data_pts.iterrows():
      pt = row["GEOMETRY"]
      
      try: depth = pt.z - self.ditch.elevation_at_pt(pt)
      except: continue

      width_top = depth/self.slope*2 + self.width_bot if self.slope > 0 else self.width_bot
      self.data_pts.at[index,"DEPTH"] = depth
      self.data_pts.at[index,"SLOPE"] = self.slope
      self.data_pts.at[index,"WIDTH_BOT"] = self.width_bot
      self.data_pts.at[index,"WIDTH_TOP"] = width_top
      self.data_pts.at[index,"AREA"] = self.width_bot*depth + (width_top - self.width_bot)/2*depth

    # data_pts = data_pts.drop(["geometry"],axis=1)
    print(self.data_pts,"\n")

    # Filter points for those that have a depth
    data_pts_copy = self.data_pts.copy().dropna().reset_index(drop=True)
    
    # Create string describing scope of volume info
    self.KP_min = min(data_pts_copy.CHAINAGE)
    self.KP_max = max(data_pts_copy.CHAINAGE)
    self.KP_rng = f"{self.CL.format_KP(self.KP_min)} to {self.CL.format_KP(self.KP_max)}"
    
    # Create dataframe of volumes for sections
    self.data_rng = pd.DataFrame()

    self.data_rng["KP_beg"] = data_pts_copy["CHAINAGE"].tolist()[:-1]
    self.data_rng["KP_end"] = data_pts_copy["CHAINAGE"].tolist()[1:]
    self.data_rng["AREA_beg"] = data_pts_copy["AREA"].tolist()[:-1]
    self.data_rng["AREA_end"] = data_pts_copy["AREA"].tolist()[1:]

    self.data_rng["AREA_avg"] = (self.data_rng.AREA_beg + self.data_rng.AREA_end) / 2
    self.data_rng["LENGTH"] = self.data_rng.KP_end - self.data_rng.KP_beg
    self.data_rng["VOLUME"] = self.data_rng.LENGTH * self.data_rng.AREA_avg
    
    self.data_rng = self.data_pts.drop("geometry",axis=1)
    
    print(self.data_rng,"\n")


  def result(self):
    return {
      "data_pts": self.data_pts.to_dict("records"),
      "data_rng": self.data_rng.to_dict("records"),
      "KP_rng": self.data_rng,
    }
  
  def save(self):
    return {

    }