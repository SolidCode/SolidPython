#! /usr/bin/env python3
import sys

from solid import scad_render_to_file
from solid.objects import cylinder
from solid.utils import up

SEGMENTS = 48


def show_appended_python_code():
    a = cylinder(r=10, h=10, center=True) + up(5)(cylinder(r1=10, r2=0, h=10))

    return a


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    a = show_appended_python_code()

    # ================================================================
    # = include_orig_code appends all python code as comments to the
    # = bottom of the generated OpenSCAD code, so the final document
    # = contains the easy-to-read python code as well as the SCAD.
    # = ------------------------------------------------------------ =
    file_out = scad_render_to_file(a, out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{file_out}")
