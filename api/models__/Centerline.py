import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import geopandas as gpd
import shapely.wkt
import shapely.geometry
import shapely.ops
import pyproj

def round_up(num,divisor): return num + divisor - (num%divisor)
def round_down(num,divisor): return num - (num%divisor)

def format_KP(number,comma=False) -> str:
  """Formats chainage number as '#+###' e.g. 34032.43 to 34+032"""
  if type(number) == int or float:
    post_plus = number % 1000
    pre_plus = (number - post_plus)/1000
    return f"{pre_plus:,.0f}+{post_plus:03.0f}" if comma else f"{pre_plus:.0f}+{post_plus:03.0f}"
  return number

class Centerline:
  def __init__(self,prisma_obj) -> None:
    self.id: int = prisma_obj.id
    self.name: str = prisma_obj.name
    self.description: str = prisma_obj.description
    self.crs: str = prisma_obj.crs

    self.line: shapely.geometry.LineString = shapely.wkt.loads(prisma_obj.line)
    
    markers_df = pd.DataFrame.from_records([i.__dict__ for i in prisma_obj.markers])
    self.markers: gpd.GeoDataFrame = gpd.GeoDataFrame(
      data=markers_df,
      geometry=gpd.points_from_xy(markers_df["x"],markers_df["y"]),
      crs=self.crs,
    )

    self.KP_min: float = min(self.markers["value"])
    self.KP_max: float = max(self.markers["value"])
  
  def __repr__(self):
    return f"Centerline: {format_KP(self.KP_min)} - {format_KP(self.KP_max)} [{self.name}]"
  
  def to_crs(self,target_crs):
    current = pyproj.CRS(self.crs)
    target = pyproj.CRS(target_crs)
    project = pyproj.Transformer.from_crs(current,target,always_xy=True).transform
    
    self.line = shapely.ops.transform(project,self.line)
    self.markers = self.markers.to_crs(target_crs)
    self.crs = target_crs

    return self

  def move_to_ln(self, node:shapely.geometry.Point) -> shapely.geometry.Point:
    return self.line.interpolate(self.line.project(node))
  
  def splice(self, p1:shapely.geometry.Point, p2:shapely.geometry.Point) -> shapely.geometry.LineString | shapely.geometry.Point:
    p1_proj = self.line.project(p1)
    p2_proj = self.line.project(p2)
    projs = (p1_proj,p2_proj)
    return shapely.ops.substring(self.line,min(projs),max(projs))
  
  def dist_to_ln(self,node,signed=True) -> float:
    moved = self.move_to_ln(node)
    distance = moved.distance(node)
    if not signed: return distance

    if not hasattr(self,"offset"):
      self.offset = self.line.parallel_offset(self.line.length/2000,"left")

    moved_offset = self.offset.interpolate(self.line.project(node))
    line_offset = shapely.geometry.LineString([node,moved_offset])
    return distance if line_offset.intersects(self.line) else -distance
  
  def find_KP(self,node:shapely.geometry.Point) -> float:
    node_mvd = self.move_to_ln(node)
    nearest = self.markers.sindex.nearest(geometry=node)[1]
    nearest = self.markers.iloc[nearest]

    k1 = nearest.iloc[0]["value"]
    p1 = self.line.project(nearest.iloc[0].geometry)
    p = self.line.project(node_mvd)

    nearest_i = nearest.index[0]
    next_kp_i = nearest_i + 1 if p > p1 else nearest_i - 1
    next_kp = self.markers.iloc[next_kp_i]

    k2 = next_kp["value"]
    p2 = self.line.project(next_kp.geometry)

    k = k1 + (p - p1) * (k2 - k1) / (p2 - p1)
    return k

  def from_KP(self, KP:float) -> shapely.geometry.Point | None:
    # assert KP <= self.KP_max, f"{format_KP(KP)} is greater than max of {format_KP(self.KP_max)}"
    # assert KP >= self.KP_min, f"{format_KP(KP)} is less than min of {format_KP(self.KP_min)}"

    if KP > self.KP_max:
      print(f"{format_KP(KP)} is greater than {format_KP(self.KP_max)}")
      return None
      
    if KP < self.KP_min: 
      print(f"{format_KP(KP)} is less than {format_KP(self.KP_min)}")
      return None

    temp = self.markers.iloc[(self.markers["value"] - KP).abs().argsort()[:2]]
    k1 = temp.iloc[0]["value"]
    k2 = temp.iloc[1]["value"]

    if k1 == KP or k1 == k2: return temp.iloc[0].geometry
    
    p1 = self.line.project(temp.iloc[0].geometry)
    p2 = self.line.project(temp.iloc[1].geometry)

    p = p1 + (KP - k1) * (p2 - p1) / (k2 - k1)
    return self.line.interpolate(p)

  def splice_KP(self, KP_beg:float, KP_end:float, crop=True) -> shapely.geometry.LineString | None:
    """Returns linestring between the two KP values"""
    if crop:
      KP_beg = max(min(KP_beg,KP_end),self.KP_min)
      KP_end = min(max(KP_beg,KP_end),self.KP_max)

    pt_beg = self.from_KP(KP_beg)
    pt_end = self.from_KP(KP_end)
    if pt_end and pt_beg: return self.splice(pt_beg,pt_end)
    return None

  def equal_segments(self,ideal_seg_length):
    cl_length = self.line.length
    num_segs = round(cl_length/ideal_seg_length)
    actual_seg_length = cl_length / num_segs

    result = []
    for i in range(num_segs):
      p1 = i * actual_seg_length
      p2 = (i + 1) * actual_seg_length
      result.append(shapely.ops.substring(self.line,p1,p2))

    return gpd.GeoSeries(result,crs=self.crs)

  def reg_chainages(self,divisor):
    chainages = []
    KP_beg = round_up(self.KP_min,divisor)
    KP_end = round_down(self.KP_max,divisor)

    if self.KP_min < KP_beg: chainages.append(self.KP_min)
    i = KP_beg
    while i <= KP_end:
      chainages.append(i)
      i += divisor
    if self.KP_max > KP_end: chainages.append(self.KP_max)
    return chainages