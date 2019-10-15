#! /usr/bin/env python3
from solid import cube, scad_render_to_file


def main():
    a = cube()
    scad_render_to_file(a)


if __name__ == '__main__':
    main()
