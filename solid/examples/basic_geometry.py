#! /usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division
import os
import sys
import re

from solid import *
from solid.utils import *

SEGMENTS = 48


def basic_geometry():
    # SolidPython code can look a lot like OpenSCAD code.  It also has
    # some syntactic sugar built in that can make it look more pythonic.
    # Here are two identical pieces of geometry, one left and one right.

    # left_piece uses standard OpenSCAD grammar (note the commas between
    # block elements; OpenSCAD doesn't require this)
    left_piece =  union()(
                        translate([-15, 0, 0])(
                            cube([10, 5, 3], center=True)
                        ),
                        translate([-10, 0, 0])(
                            difference()(
                                cylinder(r=5, h=15, center=True),
                                cylinder(r=4, h=16, center=True)
                            )
                        )
                    )
    
    # Right piece uses a more Pythonic grammar.  + (plus) is equivalent to union(), 
    # - (minus) is equivalent to difference() and * (star) is equivalent to intersection
    # solid.utils also defines up(), down(), left(), right(), forward(), and back()
    # for common transforms.
    right_piece = right(15)(cube([10, 5, 3], center=True))
    cyl = cylinder(r=5, h=15, center=True) - cylinder(r=4, h=16, center=True)
    right_piece += right(10)(cyl)

    return union()(left_piece, right_piece)

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir
    file_out = os.path.join(out_dir, 'basic_geometry.scad')

    a = basic_geometry()

    print("%(__file__)s: SCAD file written to: \n%(file_out)s" % vars())

    # Adding the file_header argument as shown allows you to change
    # the detail of arcs by changing the SEGMENTS variable.  This can
    # be expensive when making lots of small curves, but is otherwise
    # useful.
    scad_render_to_file(a, file_out, file_header='$fn = %s;' % SEGMENTS)
