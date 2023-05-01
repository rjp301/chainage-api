import math
import numpy as np

from dataclasses import dataclass
from typing import List

from .quadtree import *

@dataclass
class Point:
  x: float
  y: float
  z: float = 0
  label: any = None
  
  def __repr__(self):
    if self.z == 0: return f"POINT({self.x:.3f} {self.y:.3f})"
    else: return f"POINT({self.x:.3f} {self.y:.3f} {self.z:.3f})"

  def __key(self):
    return (self.x, self.y, self.z)

  def __hash__(self):
    return hash(self.__key())

  def __eq__(self,other):
    if not isinstance(other,Point): return NotImplemented
    precision = 5
    c1 = round(self.x,precision) == round(other.x,precision)
    c2 = round(self.y,precision) == round(other.y,precision)
    return c1 and c2
  
  def move(self,dx=0,dy=0,dz=0):
    self.x += dx
    self.y += dy
    self.z += dz

  def copy(self,dx=0,dy=0,dz=0):
    return Point(self.x + dx,self.y + dy,self.z + dz,label=self.label)

  def copy_polar(self,d,theta):
    dx = d*math.cos(math.radians(theta))
    dy = d*math.sin(math.radians(theta))
    return Point(self.x + dx,self.y + dy,self.z,label=self.label)

  def pt_to_pt(self,node) -> float:
    delta_x = self.x - node.x
    delta_y = self.y - node.y
    return math.sqrt(delta_x**2 + delta_y**2)

  def nearest(self,nodes):
    return min(nodes, key=lambda i: self.pt_to_pt(i))

@dataclass
class Line:
  p1: Point
  p2: Point

  def __repr__(self):
    return f"LINESTRING({self.p1.x:.3f} {self.p1.y:.3f}, {self.p2.x:.3f} {self.p2.y:.3f})"

  def length(self) -> float:
    return self.p1.pt_to_pt(self.p2)
  
  def angle(self) -> float:
    """Angle from the positive horizontal axis in degrees"""
    dist_x = self.p2.x - self.p1.x
    dist_y = self.p2.y - self.p1.y
    angle = math.atan2(dist_y,dist_x)
    angle = math.degrees(angle)
    return angle

  def reverse(self):
    self.p1,self.p2 = self.p2,self.p1
    return self
  
  def equation_abc(self) -> float:
    # Ax + By + C = 0
    A = self.p1.y - self.p2.y
    B = self.p2.x - self.p1.x
    C = self.p1.x * self.p2.y - self.p2.x * self.p1.y
    return A,B,C
  
  def equation_mb(self) -> float:
    # y = mx + b
    m = (self.p2.y - self.p1.y) / (self.p2.x - self.p1.x)
    b = self.p1.y - m*self.p1.x
    return m,b

  def which_side(self,node) -> int:
    d = (node.x - self.p1.x)*(self.p2.y - self.p1.y) - (node.y - self.p1.y)*(self.p2.x - self.p1.x)
    if d < 0: return -1
    if d > 0: return 1
    if d == 0: return 0

  def dist_to_pt(self,node,signed=False) -> float:
    A,B,C = self.equation_abc()
    num = abs(A*node.x + B*node.y + C)
    num = num*self.which_side(node) if signed else num
    den = math.sqrt(A**2 + B**2)
    return 0 if den == 0 else num/den
  
  def on_line(self,node):
    """Determine if a point is coincident with the line segment"""
    cross_product = (node.y - self.p1.y) * (self.p2.x - self.p1.x) - (node.x - self.p1.x) * (self.p2.y - self.p1.y)
    if abs(cross_product) > 1e-3: return False

    dot_product = (node.x - self.p1.x) * (self.p2.x - self.p1.x) + (node.y - self.p1.y) * (self.p2.y - self.p1.y)
    if dot_product < 0: return False

    squared_length = (self.p2.x - self.p1.x) * (self.p2.x - self.p1.x) + (self.p2.y - self.p1.y) * (self.p2.y - self.p1.y)
    if dot_product > squared_length: return False

    return True
 
  def move_to_ln(self,node):
    if self.on_line(node): return node
    
    A,B,C = self.equation_abc()
    x = (B*(B*node.x - A*node.y) - A*C) / (A**2 + B**2)
    y = (A*(-B*node.x + A*node.y) - B*C) / (A**2 + B**2)
    
    return Point(x,y,node.z) 

  def along(self,dt):
    """Returns the coordinates of a point a certain distance along the length of the line"""
    # https://math.stackexchange.com/questions/175896/finding-a-point-along-a-line-a-certain-distance-away-from-another-point
    # assert dt >= 0, "Distance must be positive"
    d = self.length()
    t = dt/d
    x = (1-t)*self.p1.x + t*self.p2.x
    y = (1-t)*self.p1.y + t*self.p2.y
    return Point(x,y)

  def middle(self):
    return self.along(self.length/2)

  def pt_along(self,node):
    """Returns the length along the line to a point. Starting at P1"""
    new_node = self.move_to_ln(node)
    return new_node.pt_to_pt(self.p1)

  def intersects(self,other,within=True):
    assert isinstance(other,Line), "Other must be a line"
    
    x1,x2 = float(self.p1.x),float(self.p2.x)
    x3,x4 = float(other.p1.x),float(other.p2.x)
    y1,y2 = float(self.p1.y),float(self.p2.y)
    y3,y4 = float(other.p1.y),float(other.p2.y)

    den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    
    try:
      t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4))/den
      u = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3))/den
    except: return None

    if (t > 1 or t < 0) and within: return None
    if (u > 1 or u < 0) and within: return None

    Px = self.p1.x + t*(self.p2.x - self.p1.x)
    Py = self.p1.y + t*(self.p2.y - self.p1.y)

    return Point(Px,Py)

  def intersects_pl(self,other):
    assert isinstance(other,Polyline), "Other must be a polyline"
    intersections = [self.intersects(i) for i in other.segments]
    return [i for i in intersections if i]

  def offset(self,dist):
    angle = self.angle() + 90
    return Line(self.p1.copy_polar(dist,angle),self.p2.copy_polar(dist,angle))

@dataclass
class Polyline:
  vertices: List[Point]
  KPs: List[Point] = None

  def __post_init__(self):
    assert len(self.vertices) > 1, "Need vertices to make a Polyline"
    self.vertices = list(dict.fromkeys(self.vertices))
    self.segments = [Line(self.vertices[i-1],v) for i,v in enumerate(self.vertices) if i > 0]
    
    self.qtree = QuadTree(find_boundary(self.vertices))
    self.q_radius = max(i.length() for i in self.segments)
    for i in self.vertices: self.qtree.insert(i)
    
    if self.KPs:
      # self.KPs = sorted(self.KPs,key=lambda i: i.label)
      self.qtree_KP = QuadTree(find_boundary(self.KPs))
      for i in self.KPs: self.qtree_KP.insert(i)

  def __repr__(self):
    points = [f"{i.x} {i.y} {i.z}" for i in self.vertices]
    return f"LINESTRING({', '.join(points)})"

  def nearest_vertex(self,node,radius=None):
    radius = self.q_radius if not radius else radius
    points = []
    self.qtree.query_radius(node,radius,points)
    if not points:
      raise ValueError(f"No vertices within a {radius:.2f} radius of {node}")
    return node.nearest(points)

  def remove_vertex(self,index):
    new_vertices = self.vertices.copy()
    del new_vertices[index]
    return Polyline(new_vertices,self.KPs)

  def insert_vertex(self,index,node):
    new_vertices = self.vertices.copy()
    new_vertices.insert(index,node)
    return Polyline(new_vertices,self.KPs)

  def length(self):
    return sum(seg.length() for seg in self.segments)

  def move_to_ln(self,node,radius=None):
    """Returns the coordinates of node if it were moved to be coincident with the line along the shortest possible path"""
    # Determine nearest vertex to the node
    nearest_pt = self.nearest_vertex(node,radius=radius)
    nearest_pt_dist = nearest_pt.pt_to_pt(node)

    # Sort segments by distance to node
    for segment,distance in sorted(zip(self.segments,[i.dist_to_pt(node) for i in self.segments]), key=lambda i: i[1]):
      # If a vertex is the nearest part of the polyline to the node, return vertex
      if distance >= nearest_pt_dist: return nearest_pt
      
      # Move pt to line segment and see if on line
      moved_pt = segment.move_to_ln(node)
      if segment.on_line(moved_pt):
        return moved_pt

    return nearest_pt

  def reverse(self):
    new_vertices = self.vertices
    new_vertices.reverse()
    return Polyline(new_vertices)

  def which_segment(self,node,radius=None):
    """Returns the line segment in the polyline which is both closest to the given point and which the point can be moved perpindicularly to be coincident with"""
    new_pt = self.move_to_ln(node,radius=radius)
    return next((i for i in self.segments if i.on_line(new_pt)),False)

  def along(self,dt):
    """Returns a point at a certain distance along the polyline"""
    assert dt <= self.length(), "Distance must be less than polyline length"
    assert dt >= 0, "Distance must be positive"
    length = 0
    for segment in self.segments:
      length += segment.length()
      if length >= dt:
        return segment.along(dt - (length - segment.length()))
  
  def on_line(self,node):
    """Determine if node is coincident with Polyline"""
    segment = self.which_segment(node)
    if segment: return segment.on_line(node)
    return False

  def dist_to_ln(self,node,signed=False):
    segment = self.which_segment(node)
    distance = segment.dist_to_pt(node)
    if signed: distance = distance * segment.which_side(node)
    return distance

  def which_side(self,node):
    segment = self.which_segment(node)
    return segment.which_side(node)

  def pt_along(self,node,radius=None):
    """Returns distance from the start of the Polyline to a point when moving along it"""
    segment = self.which_segment(node,radius=radius)
    index = self.segments.index(segment)
    length = sum([seg.length() for seg in self.segments[:index]])
    length += segment.pt_along(node)
    return length

  def pt_to_pt_along(self,p1,p2):
    """Returns the distance between two points when moving along the Polyline"""
    d1 = self.pt_along(p1)
    d2 = self.pt_along(p2)
    return abs(d1 - d2)

  def splice(self,p1,p2,radius=None):
    assert isinstance(p1,Point), "p1 not a point"
    assert isinstance(p2,Point), "p2 not a point"

    p1.segment = self.which_segment(p1,radius=radius)
    p2.segment = self.which_segment(p2,radius=radius)

    p1.moved = p1.segment.move_to_ln(p1)
    p2.moved = p2.segment.move_to_ln(p2)

    # if p1.moved == p2.moved: return None

    p1.index = self.segments.index(p1.segment)
    p2.index = self.segments.index(p2.segment)

    if p1.index <= p2.index: pt_beg,pt_end = p1,p2
    else: pt_end,pt_beg = p1,p2

    vertices = []
    vertices.append(pt_beg.moved)
    index = pt_beg.index

    while index < pt_end.index:
      vertices.append(self.segments[index].p2)
      index += 1

    vertices.append(pt_end.moved)
    return Polyline(vertices)

  def avg_angle(self):
    """Flawed"""
    tans = [math.tan(math.radians(i.angle())) for i in self.segments]
    avg = sum(tans)/len(tans)
    return math.degrees(math.atan(avg))

  def find_KP(self,node,radius=1000):
    """Returns the exact chainage of a point near the Polyline"""
    assert isinstance(node,Point), "Node must be a Point"

    points = []
    self.qtree_KP.query_radius(node,radius,points) # Determine the nearest KP point
    if points:
      nearest_KP = node.nearest(points)
    else:
      print(f"Point is further than {radius}m from CL")
      return None
    
    along_pt = self.pt_along(node,radius=radius)
    along_KP = self.pt_along(nearest_KP,radius=radius)
    diff = along_pt - along_KP # Find the distance between the nearest KP and the node
    chainage = nearest_KP.label + diff # Add the distance to the nearest KP
    return chainage

  def from_KP(self,chainage,extend=False,radius=1000):
    """Returns a point on the Polyline at the given chainage"""
    max_KP = max(i.label for i in self.KPs)
    min_KP = min(i.label for i in self.KPs)

    assert type(chainage) == float or int, "KP must be a number"

    if chainage > max_KP or chainage < min_KP:
      if extend == False:
        print(f"{format_KP(chainage)} not in project")
        return None
      elif chainage < min_KP:
        old_line = self.segments[0]
        length = old_line.length() + abs(chainage - min_KP)
        return self.vertices[1].copy_polar(-length,old_line.angle())
      elif chainage > max_KP:
        old_line = self.segments[-1]
        length = old_line.length() + abs(chainage - max_KP)
        return self.vertices[-2].copy_polar(length,old_line.angle())
  
    nearest_KP = min(self.KPs, key=lambda x: abs(x.label-chainage))
    nearest_i = self.KPs.index(nearest_KP)
    
    if nearest_KP.label < chainage or nearest_KP.label == min_KP:
      lower_KP = nearest_KP
      upper_KP = self.KPs[nearest_i + 1]
    else:
      lower_KP = self.KPs[nearest_i - 1]
      upper_KP = nearest_KP

    for entry in self.KPs:
      if entry.label == chainage:
        return entry
    
    # Create a polyline between the upper and lower bounding points
    # Determine the point as a percentage of the distance between the bounds

    temp_pl = self.splice(lower_KP,upper_KP,radius=radius)

    KP_div = abs(upper_KP.label - lower_KP.label)
    length = temp_pl.length()
    delta = chainage - lower_KP.label
    node = temp_pl.along(delta / KP_div * length)
    node.label = chainage

    return node

  def perp_angle(self,node):
    if node in self.vertices:
      index = self.vertices.index(node)
      if node == self.vertices[0]: return self.segments[0].angle() + 90
      if node == self.vertices[-1]: return self.segments[0].angle() + 90
      s1 = self.segments[index-1]
      s2 = self.segments[index]
      angle3 = avg_lines([s1,s2]).angle() + 90
      return angle3
    return self.which_segment(node).angle() + 90    

  def intersects_pl(self,other):
    inter = []
    for segment in self.segments:
      intersections = [segment.intersects(i) for i in other.segments]
      intersections = [i for i in intersections if i]
      intersections.sort(key=lambda i: segment.pt_along(i))
      inter += intersections
    return inter
  
  def offset_simple(self,dist):
    if dist == 0: return self
    offset_lines = [i.offset(dist) for i in self.segments]
    return join_lines(offset_lines)

  def offset(self,dist):
    if dist == 0: return self
    offset = self.offset_simple(dist)

    inter = [offset.vertices[0]]
    inter += offset.intersects_pl(offset)
    inter += [offset.vertices[-1]]

    inter_self = [i for i in inter if i not in offset.vertices]
    overlaps = []
    for i in inter_self:
      i1 = inter.index(i)
      i2 = inter.index(i,i1+1)
      overlap = (i1,i2)
      if overlap not in overlaps: overlaps.append(overlap)

    overlaps = [i for i in overlaps if not any((i[0] > j[0] and i[1] < j[1]) for j in overlaps)]
    inter = [i for index,i in enumerate(inter) if not any((index >= j[0] and index < j[1]) for j in overlaps)]
    return Polyline(inter)

  def lin_divide(self,num_div):
    alongs = np.linspace(0,self.length(),num_div)
    return [self.along(i) for i in alongs]

  def splice_KP(self,KP_beg,KP_end):
    pt_beg = self.from_KP(KP_beg,True)
    pt_end = self.from_KP(KP_end,True)
    new_KPs = [i for i in self.KPs if (i.label <= KP_end and i.label >= KP_beg)]
    new_vertices = self.splice(pt_beg,pt_end).vertices
    return Polyline(new_vertices,new_KPs)

  def elevation_at_pt(self,node):
    segment = self.which_segment(node)
    new_node = segment.move_to_ln(node)
    if not segment.on_line(new_node): return None
    
    tot_length = segment.length()
    pt_length = segment.pt_along(node)
    tot_vert = segment.p2.z - segment.p1.z
    pt_vert = pt_length * tot_vert / tot_length
    
    return pt_vert + segment.p1.z

def avg_points(nodes):
  x = [i.x for i in nodes]
  y = [i.y for i in nodes]
  return Point(sum(x)/len(x),sum(y)/len(y))

def avg_lines(lines):
  p1 = [i.p1 for i in lines]
  p2 = [i.p2 for i in lines]
  return Line(avg_points(p1),avg_points(p2))

def join_lines(lines) -> Polyline:
  pts = []
  pts.append(lines[0].p1)
  for i in range(1,len(lines)):
    intersection = lines[i-1].intersects(lines[i],within=False)
    pts.append(intersection)
  pts.append(lines[-1].p2)
  return Polyline(pts)

def pts_to_pl(pts,thresh) -> Polyline:
  # Assumes that points are already ordered correctly
  polylines = []
  current = [pts.pop(0)]
  while pts:
    if pts[0].pt_to_pt(current[-1]) < thresh:
      current.append(pts.pop(0))
    else:
      polylines.append(current)
      current = [pts.pop(0)]
  polylines.append(current)
  polylines = [Polyline(vertices=i) for i in polylines if len(i) > 1]
  return polylines