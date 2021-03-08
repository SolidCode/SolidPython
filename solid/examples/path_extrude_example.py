#! /usr/bin/env python3
from solid.solidpython import OpenSCADObject
import sys
from math import cos, radians, sin, pi, tau
from pathlib import Path

from euclid3 import Point2, Point3

from solid import scad_render_to_file, text, translate
from solid.utils import extrude_along_path, right


from typing import Set, Sequence, List, Callable, Optional, Union, Iterable

SEGMENTS = 48


def sinusoidal_ring(rad=25, segments=SEGMENTS):
    outline = []
    for i in range(segments):
        angle = radians(i * 360 / segments)
        scaled_rad = (1 + 0.18*cos(angle*5)) * rad
        x = scaled_rad * cos(angle)
        y = scaled_rad * sin(angle)
        z = 0
        # Or stir it up and add an oscillation in z as well
        # z = 3 * sin(angle * 6)
        outline.append(Point3(x, y, z))
    return outline


def star(num_points=5, outer_rad=15, dip_factor=0.5):
    star_pts = []
    for i in range(2 * num_points):
        rad = outer_rad - i % 2 * dip_factor * outer_rad
        angle = radians(360 / (2 * num_points) * i)
        star_pts.append(Point3(rad * cos(angle), rad * sin(angle), 0))
    return star_pts

def circle_points(rad: float = 15, num_points: int = SEGMENTS) -> List[Point2]:
    angles = [tau/num_points * i for i in range(num_points)] 
    points = list([Point2(rad*cos(a), rad*sin(a)) for a in angles])
    return points

def extrude_example():
    # Note the incorrect triangulation at the two ends of the path.  This
    # is because star isn't convex, and the triangulation algorithm for
    # the two end caps only works for convex shapes.
    path_rad = 50
    shape = star(num_points=5)
    path = sinusoidal_ring(rad=path_rad, segments=240)

    # # If scale_factors aren't included, they'll default to
    # # no scaling at each step along path.  Here, let's
    # # make the shape twice as big at beginning and end of the path
    # scales = [1] * len(path)
    # n = len(path)
    # scales = [1 + 0.5*sin(i*6*pi/n) for i in range(n)]
    # scales[0] = 2
    # scales[-1] = 2

    extruded = extrude_along_path( shape_pts=shape, path_pts=path)
    # Label
    extruded += translate([-path_rad/2, 2*path_rad])(text('Basic Extrude'))
    return extruded
        
def extrude_example_xy_scaling() -> OpenSCADObject:
    num_points = SEGMENTS
    path_rad = 50
    circle = circle_points(15)
    path = circle_points(rad = path_rad)

    # angle: from 0 to 6*Pi
    angles = list((i/(num_points - 1)*tau*3 for i in range(len(path))))


    # If scale_factors aren't included, they'll default to
    # no scaling at each step along path.
    no_scale_obj = translate([-path_rad / 2, 2 * path_rad])(text('No Scale'))
    no_scale_obj += extrude_along_path(circle, path)

    # With a 1-D scale factor, an extrusion grows and shrinks uniformly
    x_scales = [(1 + cos(a)/2) for a in angles]
    x_obj = translate([-path_rad / 2, 2 * path_rad])(text('1D Scale'))
    x_obj += extrude_along_path(circle, path, scale_factors=x_scales)

    # With a 2D scale factor, a shape's X & Y dimensions can scale 
    # independently, leading to more interesting shapes
    # X & Y scales vary between 0.5 & 1.5
    xy_scales = [Point2( 1 + cos(a)/2, 1 + sin(a)/2) for a in angles]
    xy_obj = translate([-path_rad / 2, 2 * path_rad])( text('2D Scale'))
    xy_obj += extrude_along_path(circle, path, scale_factors=xy_scales)

    obj = no_scale_obj + right(3*path_rad)(x_obj) + right(6 * path_rad)(xy_obj)
    return obj

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent

    basic_extrude = extrude_example()
    scaled_extrusions = extrude_example_xy_scaling()
    a = basic_extrude + translate([0,-250])(scaled_extrusions)
    file_out = scad_render_to_file(a,  out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{file_out}")
