#! /usr/bin/env python3
import sys
from math import cos, radians, sin

from euclid3 import Point3

from solid import scad_render_to_file
from solid.utils import extrude_along_path

SEGMENTS = 48


def sinusoidal_ring(rad=25, segments=SEGMENTS):
    outline = []
    for i in range(segments):
        angle = i * 360 / segments
        x = rad * cos(radians(angle))
        y = rad * sin(radians(angle))
        z = 2 * sin(radians(angle * 6))
        outline.append(Point3(x, y, z))
    return outline


def star(num_points=5, outer_rad=15, dip_factor=0.5):
    star_pts = []
    for i in range(2 * num_points):
        rad = outer_rad - i % 2 * dip_factor * outer_rad
        angle = radians(360 / (2 * num_points) * i)
        star_pts.append(Point3(rad * cos(angle), rad * sin(angle), 0))
    return star_pts


def extrude_example():
    # Note the incorrect triangulation at the two ends of the path.  This
    # is because star isn't convex, and the triangulation algorithm for
    # the two end caps only works for convex shapes.
    shape = star(num_points=5)
    path = sinusoidal_ring(rad=50)

    # If scale_factors aren't included, they'll default to
    # no scaling at each step along path.  Here, let's
    # make the shape twice as big at beginning and end of the path
    scales = [1] * len(path)
    scales[0] = 2
    scales[-1] = 2

    extruded = extrude_along_path(shape_pts=shape, path_pts=path, scale_factors=scales)

    return extruded


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    a = extrude_example()
    file_out = scad_render_to_file(a, out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{file_out}")
