import sys
import os
from solid import polygon, scad_render_to_file
from solid.splines import SEGMENTS, bezier_points, control_points
from solid.examples.path_extrude_example import circle_points
from euclid3 import Vector3, Point3

from solid import splines
from solid.utils import right, extrude_along_path

SCALE = 30
OMEGA = 1.0
SUBDIVISIONS = 12
SEGMENTS = 12


def assembly():
    knot_points = [
        Point3(0, 0, -1),
        Point3(1, -2, -2),
        Point3(2, 0, 1),
        Point3(3, -1, 2),
        Point3(3, 1, -2),
    ]
    knot_points = [kp * SCALE for kp in knot_points]
    path = splines.hobby_points(knot_points, OMEGA, close_loop=True)
    path_open = splines.hobby_points(knot_points, OMEGA, close_loop=False)
    bzp = []  # Closed Hobby spline control points used to make beziers
    bzp_open = []  # Open Hobby spline control for same thing
    for i in range(0, len(path) - 3, 3):
        # Controls take the form of: Knot, control vec, control vec, knot
        controls = path[i : i + 4]
        controls_open = path_open[i : i + 4]
        bzp += bezier_points(controls, subdivisions=SUBDIVISIONS)
        if len(controls_open) == 4:
            # PATH_OPEN may have fewer segments than PATH so assume last valid
            # group of 4 points is the final segment of the open curve
            bzp_open += bezier_points(controls_open, subdivisions=SUBDIVISIONS)

    assembly = polygon(bzp) + right(5 * SCALE)(
        extrude_along_path(circle_points(0.3 * SCALE, SEGMENTS), bzp)
        + right(5 * SCALE)(
            extrude_along_path(circle_points(0.3 * SCALE, SEGMENTS), bzp_open)
            + right(5 * SCALE)(polygon(bzp_open))
        )
    )
    return assembly


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.curdir

    a = assembly()

    out_path = scad_render_to_file(a, out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{out_path}")
