#! /usr/bin/env python3
from solid import scad_render_animated, scad_render_to_file, cube
from typing import List

def main():
    a = cube()
    scad_render_to_file(a)

if __name__ == '__main__':
    main()
