#! /usr/bin/env python
from math import pow

from solid import circle, cylinder, polygon, color, OpenSCADObject, translate, linear_extrude
from solid.utils import bounding_box, right, Red, Tuple3, euclidify
from euclid3 import Vector2, Vector3, Point2, Point3

from typing import Sequence, Tuple, Union, List, cast

Point23 = Union[Point2, Point3]
Point23List = Union[Point23, Tuple[float, float], Tuple[float, float, float]]
Vec23 = Union[Vector2, Vector3]
FourPoints = Tuple[Point23List, Point23List, Point23List, Point23List]
SEGMENTS = 48

DEFAULT_SUBDIVISIONS = 10
DEFAULT_EXTRUDE_HEIGHT = 1

# =======================
# = CATMULL-ROM SPLINES =
# =======================
def catmull_rom_polygon(points: Sequence[Point23List], 
                        subdivisions: int = DEFAULT_SUBDIVISIONS, 
                        extrude_height: float = DEFAULT_EXTRUDE_HEIGHT, 
                        show_controls: bool =False,
                        center: bool=True) -> OpenSCADObject:
    """
    Return a closed OpenSCAD polygon object through all of `points`, 
    extruded to `extrude_height`. If `show_controls` is True, return red 
    cylinders at each of the specified control points; this makes it easier to
    move determine which points should move to get a desired shape.

    NOTE: if `extrude_height` is 0, this function returns a 2D `polygon()`
    object, which OpenSCAD can only combine with other 2D objects 
    (e.g. `square`, `circle`, but not `cube` or `cylinder`). If `extrude_height`
    is nonzero, the object returned will be 3D and only combine with 3D objects.
    """
    catmull_points = catmull_rom_points(points, subdivisions, close_loop=True)
    shape = polygon(catmull_points)
    if extrude_height > 0:
        shape = linear_extrude(height=extrude_height, center=center)(shape)

    if show_controls:
        shape += control_points(points, extrude_height, center)
    return shape

def catmull_rom_points( points: Sequence[Point23List], 
                        subdivisions:int = 10, 
                        close_loop: bool=False,
                        start_tangent: Vec23 = None,
                        end_tangent: Vec23 = None) -> List[Point23]:
    """
    Return a smooth set of points through `points`, with `subdivision` points 
    between each pair of control points. 
    
    If `close_loop` is False, `start_tangent` and `end_tangent` can specify 
    tangents at the open ends of the returned curve. If not supplied, tangents 
    will be colinear with first and last supplied segments

    Credit due: Largely taken from C# code at: 
    https://www.habrador.com/tutorials/interpolation/1-catmull-rom-splines/
    retrieved 20190712
    """
    catmull_points: List[Point23] = []
    cat_points: List[Point23] = []
    # points_list = cast(List[Point23], points)

    points_list = list([euclidify(p, Point2) for p in points])

    if close_loop:
        cat_points = [points_list[-1]] + points_list + [points_list[0]] 
    else:
        # Use supplied tangents or just continue the ends of the supplied points
        start_tangent = start_tangent or (points_list[1] - points_list[0])
        end_tangent = end_tangent or (points_list[-2] - points_list[-1])
        cat_points = [points_list[0]+ start_tangent] + points_list + [points_list[-1] + end_tangent]

    last_point_range = len(cat_points) - 2 if close_loop else len(cat_points) - 3

    for i in range(0, last_point_range):
        include_last = True if i == last_point_range - 1 else False
        controls = cat_points[i:i+4]
        # If we're closing a loop, controls needs to wrap around the end of the array
        points_needed = 4 - len(controls)
        if points_needed > 0:
            controls += cat_points[0:points_needed]
        controls_tuple = cast(FourPoints, controls)
        catmull_points += _catmull_rom_segment(controls_tuple, subdivisions, include_last)

    return catmull_points

def _catmull_rom_segment(controls: FourPoints, 
                         subdivisions: int, 
                         include_last=False) -> List[Point23]: 
    """
    Returns `subdivisions` Points between the 2nd & 3rd elements of `controls`,
    on a quadratic curve that passes through all 4 control points.
    If `include_last` is True, return `subdivisions` + 1 points, the last being
    controls[2]. 

    No reason to call this unless you're trying to do something very specific
    """
    pos: Point23 = None
    positions: List[Point23] = []

    num_points = subdivisions
    if include_last:
        num_points += 1

    p0, p1, p2, p3 = [euclidify(p, Point2) for p in controls]
    a = 2 * p1
    b = p2 - p0
    c = 2* p0 - 5*p1 + 4*p2 - p3
    d = -p0 + 3*p1 - 3*p2 + p3

    for i in range(num_points):
        t = i/subdivisions
        pos = 0.5 * (a + (b * t) + (c * t * t) + (d * t * t * t))
        positions.append(Point2(*pos))
    return positions

# ==================
# = BEZIER SPLINES =
# ==================
# Ported from William A. Adams' Bezier OpenSCAD code at: 
# https://www.thingiverse.com/thing:8443

def bezier_polygon( controls: FourPoints, 
                    subdivisions:int = DEFAULT_SUBDIVISIONS, 
                    extrude_height:float = DEFAULT_EXTRUDE_HEIGHT,
                    show_controls: bool = False,
                    center: bool = True) -> OpenSCADObject:
    points = bezier_points(controls, subdivisions)
    shape = polygon(points)
    if extrude_height != 0:
        shape = linear_extrude(extrude_height, center=center)(shape)

    if show_controls:
        control_objs = control_points(controls, extrude_height=extrude_height, center=center)
        shape += control_objs
    
    return shape

def bezier_points(controls: FourPoints, 
                  subdivisions: int = DEFAULT_SUBDIVISIONS,
                  include_last: bool = True) -> List[Point2]:
    """
    Returns a list of `subdivisions` (+ 1, if `include_last` is True) points
    on the cubic bezier curve defined by `controls`. The curve passes through 
    controls[0] and controls[3]

    If `include_last` is True, the last point returned will be controls[3]; if
    False, (useful for linking several curves together), controls[3] won't be included

    Ported from William A. Adams' Bezier OpenSCAD code at: 
    https://www.thingiverse.com/thing:8443
    """
    # TODO: enable a smooth curve through arbitrarily many points, as described at:
    # https://www.algosome.com/articles/continuous-bezier-curve-line.html

    points: List[Point2] = []
    last_elt = 1 if include_last else 0
    for i in range(subdivisions + last_elt):
        u = i/subdivisions
        points.append(_point_along_bez4(*controls, u))
    return points

def _point_along_bez4(p0: Point23List, p1: Point23List, p2: Point23List, p3: Point23List, u:float) -> Point2:
    p0 = euclidify(p0)
    p1 = euclidify(p1)
    p2 = euclidify(p2)
    p3 = euclidify(p3)

    x = _bez03(u)*p0.x + _bez13(u)*p1.x + _bez23(u)*p2.x + _bez33(u)*p3.x
    y = _bez03(u)*p0.y + _bez13(u)*p1.y + _bez23(u)*p2.y + _bez33(u)*p3.y
    return Point2(x,y)

def _bez03(u:float) -> float:
    return pow((1-u), 3)

def _bez13(u:float) -> float:
    return 3*u*(pow((1-u),2))

def _bez23(u:float) -> float:
    return 3*(pow(u,2))*(1-u)

def _bez33(u:float) -> float:
    return pow(u,3)

# ===========
# = HELPERS =
# ===========
def control_points(points: Sequence[Point23], extrude_height:float=0, center:bool=True, points_color:Tuple3=Red) -> OpenSCADObject:
    """
    Return a list of red cylinders/circles (depending on `extrude_height`) at
    a supplied set of 2D points. Useful for visualizing and tweaking a curve's 
    control points
    """
    # Figure out how big the circles/cylinders should be based on the spread of points
    min_bb, max_bb = bounding_box(points)
    outline_w = max_bb[0] - min_bb[0]
    outline_h = max_bb[1] - min_bb[1]
    r = min(outline_w, outline_h) / 20 # 
    if extrude_height == 0:
        c = circle(r=r)
    else:
        h = extrude_height * 1.1
        c = cylinder(r=r, h=h, center=center)
    controls = color(points_color)([translate([p.x, p.y])(c) for p in points])
    return controls
