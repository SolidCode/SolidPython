#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

from solid import *

# Import OpenSCAD code and call it from Python code.
# The path given to use() (or include()) must be absolute or findable in
# sys.path


def demo_scad_include():
    # scad_to_include.scad includes a module called steps()
    scad_path = os.path.join(os.path.dirname(__file__), "scad_to_include.scad")
    use(scad_path)  # could also use 'include', but that has side-effects;
    # 'use' just imports without executing any of the imported code
    return steps(5)


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir
    file_out = os.path.join(out_dir, 'scad_include_example.scad')

    a = demo_scad_include()

    print("%(__file__)s: SCAD file written to: \n%(file_out)s" % vars())

    scad_render_to_file(a, file_out)
