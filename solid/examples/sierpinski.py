#! /usr/bin/env python3
import math
import random
import sys
from pathlib import Path

from solid import scad_render_to_file
from solid.objects import cube, polyhedron, translate, union


# =========================================================
# = A basic recursive Sierpinski's gasket implementation,
# outputting a file 'gasket_x.scad' to the argv[1] or $PWD
# =========================================================


class SierpinskiTetrahedron(object):

    def __init__(self, four_points):
        self.points = four_points

    def segments(self):
        indices = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        return [(self.points[a], self.points[b]) for a, b in indices]

    def next_gen(self, midpoint_weight=0.5, jitter_range_vec=None):
        midpoints = [weighted_midpoint(s[0], s[1], weight=midpoint_weight, jitter_range_vec=jitter_range_vec) for s in self.segments()]
        all_points = self.points + midpoints
        new_tet_indices = [(0, 4, 5, 6),
                           (4, 1, 7, 8),
                           (5, 2, 9, 7),
                           (6, 3, 8, 9), ]
        new_tets = []
        for four_ind in new_tet_indices:
            tet_points = [all_points[i] for i in four_ind]
            new_tets.append(SierpinskiTetrahedron(tet_points))

        return new_tets

    def scale(self, factor):

        self.points = [[factor * d for d in p] for p in self.points]

    def scad_code(self):
        faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]]
        return polyhedron(points=self.points, faces=faces, convexity=1)


def distance(a, b):
    return math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]))


def weighted_midpoint(a, b, weight=0.5, jitter_range_vec=None):
    # ignoring jitter_range_vec for now
    x = weight * a[0] + (1 - weight) * b[0]
    y = weight * a[1] + (1 - weight) * b[1]
    z = weight * a[2] + (1 - weight) * b[2]

    dist = distance(a, b)

    if jitter_range_vec:
        x += (random.random() - .5) * dist * jitter_range_vec[0]
        y += (random.random() - .5) * dist * jitter_range_vec[1]
        z += (random.random() - .5) * dist * jitter_range_vec[2]

    return [x, y, z]


def sierpinski_3d(generation, scale=1, midpoint_weight=0.5, jitter_range_vec=None):
    orig_tet = SierpinskiTetrahedron([[1.0, 1.0, 1.0],
                                      [-1.0, -1.0, 1.0],
                                      [-1.0, 1.0, -1.0],
                                      [1.0, -1.0, -1.0]])
    all_tets = [orig_tet]
    for i in range(generation):
        all_tets = [subtet for tet in all_tets for subtet in tet.next_gen(midpoint_weight, jitter_range_vec)]

    if scale != 1:
        for tet in all_tets:
            tet.scale(scale)
    return all_tets


if __name__ == '__main__':
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    generations = 3
    midpoint_weight = 0.5
    # jitter_range_vec adds some randomness to the generated shape,
    # making it more interesting.  Try:
    # jitter_range_vec = [0.5,0, 0]
    jitter_range_vec = None
    all_tets = sierpinski_3d(generations, scale=100, midpoint_weight=midpoint_weight, jitter_range_vec=jitter_range_vec)

    t = union()
    for tet in all_tets:
        # Create the scad code for all tetrahedra
        t.add(tet.scad_code())
        # Draw cubes at all intersections to make the shape manifold.
        for p in tet.points:
            t.add(translate(p).add(cube(5, center=True)))

    file_out = out_dir / f'gasket_{generations}_gen.scad'
    file_out = scad_render_to_file(t, file_out)
    print(f"{__file__}: SCAD file written to: \n{file_out}")
