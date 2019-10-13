#! /usr/bin/env python3
from solid import scad_render_to_file
from solid.objects import union

SEGMENTS = 48


def assembly():
    # Your code here!
    a = union()

    return a


if __name__ == '__main__':
    a = assembly()
    scad_render_to_file(a, file_header=f'$fn = {SEGMENTS};', include_orig_code=True)
