#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from solid import circle, cylinder, polygon, color, OpenSCADObject, translate, linear_extrude
from solid.utils import bounding_box, right, Red
from euclid3 import Vector2, Vector3, Point2, Point3

from typing import Sequence, Tuple, Union, List

Point23 = Union[Point2, Point3]
Vec23 = Union[Vector2, Vector3]
FourPoints = Tuple[Point23, Point23, Point23, Point23]
SEGMENTS = 48

def catmull_rom_polygon(points: Sequence[Point23], 
                        subdivisions: int = 10, 
                        extrude_height: int = 1, 
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

def catmull_rom_points( points: Sequence[Point23], 
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

    if close_loop:
        cat_points = [points[-1]] + points + [points[0]] 
    else:
        # Use supplied tangents or just continue the ends of the supplied points
        start_tangent = start_tangent or (points[1] - points[0])
        end_tangent = end_tangent or (points[-2] - points[-1])
        cat_points = [points[0]+ start_tangent] + points + [points[-1] + end_tangent]

    last_point_range = len(cat_points) - 2 if close_loop else len(cat_points) - 3

    for i in range(0, last_point_range):
        include_last = True if i == last_point_range - 1 else False
        controls = cat_points[i:i+4]
        # If we're closing a loop, controls needs to wrap around the end of the array
        overflow = i+4 - len(cat_points)
        if overflow > 0:
            controls += cat_points[0:overflow]
        catmull_points += _catmull_rom_segment(controls, subdivisions, include_last)

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

    p0, p1, p2, p3 = controls
    a = 2 * p1
    b = p2 - p0
    c = 2* p0 - 5*p1 + 4*p2 - p3
    d = -p0 + 3*p1 - 3*p2 + p3

    for i in range(num_points):
        t = i/subdivisions
        pos = 0.5 * (a + (b * t) + (c * t * t) + (d * t * t * t))
        positions.append(pos)
    return positions

def control_points(points: Sequence[Point23], extrude_height:float=0, center:bool=True) -> OpenSCADObject:
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
    controls = color(Red)([translate([p.x, p.y])(c) for p in points])
    return controls