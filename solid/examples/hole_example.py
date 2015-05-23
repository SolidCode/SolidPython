#! /usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division
import os
import sys
import re

# Assumes SolidPython is in site-packages or elsewhwere in sys.path
from solid import *
from solid.utils import *

SEGMENTS = 120


def pipe_intersection_hole():
    pipe_od = 12
    pipe_id = 10
    seg_length = 30

    outer = cylinder(r=pipe_od, h=seg_length, center=True)
    inner = cylinder(r=pipe_id, h=seg_length + 2, center=True)

    # By declaring that the internal void of pipe_a should
    # explicitly remain empty, the combination of both pipes
    # is empty all the way through.

    # Any OpenSCAD / SolidPython object can be declared a hole(),
    # and after that will always be empty
    pipe_a = outer + hole()(inner)
    # Note that "pipe_a = outer - hole()(inner)" would work identically;
    # inner will always be subtracted now that it's a hole

    pipe_b = rotate(a=90, v=FORWARD_VEC)(pipe_a)
    return pipe_a + pipe_b


def pipe_intersection_no_hole():
    pipe_od = 12
    pipe_id = 10
    seg_length = 30

    outer = cylinder(r=pipe_od, h=seg_length, center=True)
    inner = cylinder(r=pipe_id, h=seg_length + 2, center=True)
    pipe_a = outer - inner

    pipe_b = rotate(a=90, v=FORWARD_VEC)(pipe_a)
    # pipe_a and pipe_b are both hollow, but because
    # their central voids aren't explicitly holes,
    # the union of both pipes has unwanted internal walls

    return pipe_a + pipe_b


def multipart_hole():
    # It's good to be able to keep holes empty, but often we want to put
    # things (bolts, etc.) in them.  The way to do this is to declare the
    # object containing the hole a "part".  Then, the hole will remain
    # empty no matter what you add to the 'part'.  But if you put an object
    # that is NOT part of the 'part' into the hole, it will still appear.

    # On the left (not_part), here's what happens if we try to put an object
    # into an explicit hole:  the object gets erased by the hole.

    # On the right (is_part), we mark the cube-with-hole as a "part",
    # and then insert the same 'bolt' cylinder into it.  The entire
    # bolt rematins.

    b = cube(10, center=True)
    c = cylinder(r=2, h=12, center=True)

    # A cube with an explicit hole
    not_part = b - hole()(c)

    # Mark this cube-with-hole as a separate part from the cylinder
    is_part = part()(not_part.copy())

    # This fits in the holes
    bolt = cylinder(r=1.5, h=14, center=True) + up(8)(cylinder(r=2.5, h=2.5, center=True))

    # The section of the bolt inside not_part disappears.  The section
    # of the bolt inside is_part is still there.
    a = not_part + bolt + right(45)(is_part + bolt)

    return a

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir
    file_out = os.path.join(out_dir, 'hole_example.scad')

    # On the left, pipes with no explicit holes, which can give
    # unexpected walls where we don't want them.
    # On the right, we use the hole() function to fix the problem
    a = pipe_intersection_no_hole() + right(45)(pipe_intersection_hole())

    # Below is an example of how to put objects into holes and have them
    # still appear
    b = up(40)(multipart_hole())
    a += b

    print("%(__file__)s: SCAD file written to: \n%(file_out)s" % vars())
    scad_render_to_file(a, file_out, file_header='$fn = %s;' % SEGMENTS, include_orig_code=True)
