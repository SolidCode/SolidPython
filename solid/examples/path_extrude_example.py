#! /usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division
import os
import sys
import re

# Assumes SolidPython is in site-packages or elsewhwere in sys.path
from solid import *
from solid.utils import *

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
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir
    file_out = os.path.join(out_dir, 'path_extrude_example.scad')

    a = extrude_example()

    print("%(__file__)s: SCAD file written to: \n%(file_out)s" % vars())
    scad_render_to_file(a, file_out, include_orig_code=True)
