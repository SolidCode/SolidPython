#! /usr/bin/env python3
import sys

from solid import scad_render_to_file
from solid import screw_thread
from solid.objects import cylinder

SEGMENTS = 48

inner_rad = 40
screw_height = 80


def assembly():
    section = screw_thread.default_thread_section(tooth_height=10, tooth_depth=5)
    s = screw_thread.thread(outline_pts=section,
                            inner_rad=inner_rad,
                            pitch=screw_height,
                            length=screw_height,
                            segments_per_rot=SEGMENTS,
                            neck_in_degrees=90,
                            neck_out_degrees=90)

    c = cylinder(r=inner_rad, h=screw_height)
    return s + c


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    a = assembly()
    file_out = scad_render_to_file(a, out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{file_out}")
