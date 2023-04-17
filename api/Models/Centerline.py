from dataclasses import dataclass
from shapely.ops import linemerge,substring
from shapely.geometry import LineString,Point
from centerline.format_KP import format_KP

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import geopandas as gpd
import math
import os

def round_up(num,divisor): return num + divisor - (num%divisor)
def round_down(num,divisor): return num - (num%divisor)

@dataclass
class Centerline:
  line_data: gpd.GeoDataFrame
  points: gpd.GeoDataFrame
  footprint: gpd.GeoDataFrame = None

  gen_offset: bool = False
  crs: str = "EPSG:26910"

  def __post_init__(self):
    assert self.value_col in self.points.columns, "value_col must be a field in points file"
    
    self.points = (self.points
      .to_crs(self.crs)
      .sort_values(self.value_col)
      .reset_index(drop=True)
      )
    self.points[self.value_col] = self.points[self.value_col].astype(float)
    # self.points.to_csv("test.csv")

    self.line = (self.line_data
      .to_crs(self.crs)
      .geometry
      .unary_union
      )
    self.line = linemerge(self.line) if self.line.geom_type == "MultiLineString" else self.line

    if self.footprint is not None:
      self.footprint = self.footprint.to_crs(self.crs)

    self.KP_min = self.points[self.value_col].min()
    self.KP_max = self.points[self.value_col].max()

    if self.gen_offset:
      self.offset = self.line.parallel_offset(self.line.length/2000,"left")

  def __repr__(self):
    return f"Centerline: {format_KP(self.KP_min)} - {format_KP(self.KP_max)} [{self.name}]"

  def move_to_ln(self,node):
    return self.line.interpolate(self.line.project(node))

  def splice(self,p1,p2):
    p1_proj = self.line.project(p1)
    p2_proj = self.line.project(p2)
    projs = (p1_proj,p2_proj)
    return substring(self.line,min(projs),max(projs))

  def dist_to_ln(self,node,signed=True):
    moved = self.move_to_ln(node)
    distance = moved.distance(node)
    if not signed: return distance
    assert self.offset, "Parallel line must be instantiated"
    moved_offset = self.offset.interpolate(self.line.project(node))
    line_offset = LineString([node,moved_offset])
    return distance if line_offset.intersects(self.line) else -distance

  def find_KP(self,node:Point):
    node_mvd = self.move_to_ln(node)
    nearest = self.points.sindex.nearest(geometry=node)[1]
    nearest = self.points.iloc[nearest]

    k1 = nearest.iloc[0][self.value_col]
    p1 = self.line.project(nearest.iloc[0].geometry)
    p = self.line.project(node_mvd)

    nearest_i = nearest.index[0]
    next_kp_i = nearest_i + 1 if p > p1 else nearest_i - 1
    next_kp = self.points.iloc[next_kp_i]

    k2 = next_kp[self.value_col]
    p2 = self.line.project(next_kp.geometry)

    k = k1 + (p - p1) * (k2 - k1) / (p2 - p1)
    return k

  def perp_angle(self,node):
    assert self.offset, "Must generate offset at instantiation to find perpindicular angle"
    moved_pt = self.move_to_ln(node)
    offset_pt = self.offset.interpolate(self.offset.project(node))
    return math.degrees(math.atan2(offset_pt.y - moved_pt.y,offset_pt.x - moved_pt.x))

  def from_KP(self,KP):
    # assert KP <= self.KP_max, f"{format_KP(KP)} is greater than max of {format_KP(self.KP_max)}"
    # assert KP >= self.KP_min, f"{format_KP(KP)} is less than min of {format_KP(self.KP_min)}"

    if KP > self.KP_max:
      print(f"{format_KP(KP)} is greater than {format_KP(self.KP_max)}")
      return None
      
    if KP < self.KP_min: 
      print(f"{format_KP(KP)} is less than {format_KP(self.KP_min)}")
      return None

    temp = self.points.iloc[(self.points[self.value_col] - KP).abs().argsort()[:2]]
    k1 = temp.iloc[0][self.value_col]
    k2 = temp.iloc[1][self.value_col]

    if k1 == KP or k1 == k2: return temp.iloc[0].geometry
    
    p1 = self.line.project(temp.iloc[0].geometry)
    p2 = self.line.project(temp.iloc[1].geometry)

    p = p1 + (KP - k1) * (p2 - p1) / (k2 - k1)
    return self.line.interpolate(p)

  def splice_KP(self,KP_beg,KP_end,crop=True):
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
      result.append(substring(self.line,p1,p2))

    return gpd.GeoSeries(result,crs=self.crs)

  def hollow_fp(self):
    assert self.footprint is not None, "Footprint file must be imported"
    hollow = self.footprint.copy()
    hollow.geometry = hollow.buffer(0.01)
    hollow = hollow.dissolve()
    self.hollow = hollow.iloc[0].geometry.buffer(-0.01)
    return self.hollow

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

  def plot(self,ax):
    self.points.plot(ax=ax,color="k",marker="^")
    self.line_data.plot(ax=ax,color='r')