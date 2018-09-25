#! /usr/bin/env python
# -*- coding: utf-8 -*-

#   A-Mazing Box, http://www.thingiverse.com/thing:1481
#   Copyright (C) 2009    Philipp Tiefenbacher <wizards23@gmail.com>
#   With very minor changes for SolidPython compatibility, 8 March 2011
#   With further changes for clarity, 25 September 2018
#

import sys
import os

from math import *
from solid import *

import png
from inset import *
from trianglemath import *

SEGMENTS = 48

rn = 3 * 64
#r = 10
innerR = 25
gap = 0.5
wall = 1.50
baseH = 2
gripH = 9
hn = 90
s = 0.775

h = hn * s
hone = h / hn

toph = (h - gripH) + 3

def getPNG(fn):
    with open(fn, 'rb') as f:
        r = png.Reader(file=f)
        data = r.read()
        pixel = data[2]
        raw = []
        # print(data)
        for row in pixel:
            # print(row)
            # exit()
            r = []
            raw.append(r)
            for px in row:
                r.append(px)
        return raw

def build_depth_map(img_path):
    depth = []
    for i in range(0, hn):
        depth.append([0.0] * rn)

    depth = getPNG(img_path)
    depth.reverse()
    return depth

def getPx(depth_map, x, y, default):
    x = int(x)
    y = int(y)
    x = x % len(depth_map[0])
    if (y >= len(depth_map)):
        y = len(depth_map) - 1
    if (x >= 0 and x < len(depth_map[0]) and y >= 0 and y < len(depth_map)):
        return depth_map[y][x]
    return default

def myComp(x, y):
    d = Tripple2Vec3D(y).angle2D() - Tripple2Vec3D(x).angle2D()
    if (d < 0):
        return -1
    elif (d == 0):
        return 0
    else:
        return 1

def bumpMapCylinder(depth_map, theR, hn, inset, default):

    pts = []
    trls = []
    for i in range(0, hn):
        circ = []
        for j in range(0, rn):
            a = j * 2 * pi / rn
            r = theR - ((255 - getPx(depth_map, j, i, default)) / 150.0)
            p = [r * cos(a), r * sin(a), i * hone]
            circ.append(p)
        circ = insetPoly(circ, inset)
        #circ.sort(lambda x, y: -1 if (Tripple2Vec3D(y).angle2D() - Tripple2Vec3D(x).angle2D() < 0) else 1)
        aold = Tripple2Vec3D(circ[0]).angle2D()
        for c in circ:
            a = Tripple2Vec3D(c).angle2D()
            # print(a)
            if (a > aold and (abs(a - aold) < 1 * pi)):
                #print(a, aold)
                # exit()
                pass
            aold = a
            pts.append(c)

    pts.append([0, 0, 0])
    pts.append([0, 0, i * hone])

    for j in range(0, rn):
        t = [j, (j + 1) % rn, rn * hn]
        trls.append(t)
        t = [(rn * hn - 1) - j, (rn * hn - 1) - ((j + 1) % rn), rn * hn + 1]
        trls.append(t)
        for i in range(0, hn - 1):
            p1 = i * rn + ((j + 1) % rn)
            p2 = i * rn + j
            p3 = (i + 1) * rn + j
            p4 = (i + 1) * rn + ((j + 1) % rn)
            a1 = angleBetweenPlanes([pts[p1], pts[p2], pts[p3]], [pts[p4], pts[p1], pts[p3]])
            a1 = min(a1, pi - a1)
            a2 = angleBetweenPlanes([pts[p2], pts[p1], pts[p4]], [pts[p2], pts[p3], pts[p4]])
            a2 = min(a2, pi - a2)
            #print(a1, a2)
            if (a1 < a2):
                t = [p1, p2, p3]
                trls.append(t)
                t = [p4, p1, p3]
                trls.append(t)
            else:
                t = [p2, p4, p1]
                trls.append(t)
                t = [p2, p3, p4]
                trls.append(t)

    return polyhedron(pts, trls, 6)

def top_part():
    maze_path = os.path.join(os.path.dirname(__file__), 'maze7.png')

    depth_map = build_depth_map(maze_path)

    d = difference()
    u = union()
    u.add(bumpMapCylinder(depth_map, innerR, hn, 0, 255))
    u.add(cylinder(r=innerR + wall + gap, h=gripH))
    d.add(u)
    #u.add(translate([80,0,0]).add(bumpMapCylinder(depth_map, innerR, wall)))
    d.add(intersection()
    .add(bumpMapCylinder(depth_map, innerR, hn + 2, wall, 0).set_modifier("") )
    .add(translate([0, 0, baseH])
    .add(cylinder(r=innerR + 2 * wall, h=h * 1.1).set_modifier(""))))

    # u.add()
    # print("$fa=2; $fs=0.5;\n")
    # print(d._render())
    return d

def bottom_part():
    top = difference()
    u = union()
    u2 = union()
    top.add(u)
    d = difference()
    d.add(cylinder(r=innerR + wall + gap, h=toph))
    d.add(translate([0, 0, baseH]).add(cylinder(r=innerR + gap, h=toph)))
    u.add(d)
    top.add(u2)
    for i in range(0, 3):
        a = i * 2 * pi / 3.0
        r = innerR + gap + wall / 2
        u.add(translate([(r - 0.3) * cos(a), (r - 0.3) * sin(a), toph - 6]).add(sphere(r=2.4)))
        u2.add(translate([(r + wall - 0.3) * cos(a), (r + wall - 0.3) * sin(a), toph - 6]).add(sphere(r=2.4)))

    return top

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir
    file_out = os.path.join(out_dir, 'mazebox.scad')

    assm = union()(
        top_part(),
        translate([3*innerR, 0,0])(
            bottom_part()
        )
    )

    print("%(__file__)s: SCAD file written to: \n%(file_out)s" % vars())
    scad_render_to_file(assm, file_out, file_header='$fn = %s;' % SEGMENTS, include_orig_code=True)
