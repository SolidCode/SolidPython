#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys

from solid import *
from solid.utils import *

SEGMENTS = 48


def show_appended_python_code():
    a = cylinder(r=10, h=10, center=True) + up(5)(cylinder(r1=10, r2=0, h=10))

    return a

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir
    file_out = os.path.join(out_dir, 'append_solidpython_code.scad')

    a = show_appended_python_code()

    print("%(__file__)s: SCAD file written to: \n%(file_out)s" % vars())
    # ================================================================
    # = include_orig_code appends all python code as comments to the
    # = bottom of the generated OpenSCAD code, so the final document
    # = contains the easy-to-read python code as well as the SCAD.
    # = ------------------------------------------------------------ =
    scad_render_to_file(a, file_out,  include_orig_code=True)
