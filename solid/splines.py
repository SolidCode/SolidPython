#! /usr/bin/env python
from math import copysign, pow, cos, sin, pi, atan2, acos
from itertools import pairwise
from solid import (
    union,
    circle,
    cylinder,
    polygon,
    color,
    OpenSCADObject,
    translate,
    linear_extrude,
    polyhedron,
)
from solid.utils import bounding_box, right, Red, Tuple3, euclidify
from euclid3 import Vector2, Vector3, Point2, Point3, Matrix4

from typing import Sequence, Tuple, Union, List, cast

Point23 = Union[Point2, Point3]
# These *Input types accept either euclid3.Point* objects, or bare n-tuples
Point2Input = Union[Point2, Tuple[float, float]]
Point3Input = Union[Point3, Tuple[float, float, float]]
Point23Input = Union[Point2Input, Point3Input]

PointInputs = Sequence[Point23Input]

FaceTrio = Tuple[int, int, int]
CMPatchPoints = Tuple[Sequence[Point3Input], Sequence[Point3Input]]

Vec23 = Union[Vector2, Vector3]
FourPoints = Tuple[Point23Input, Point23Input, Point23Input, Point23Input]
SEGMENTS = 359
DEBUG = True

DEFAULT_SUBDIVISIONS = 10
DEFAULT_EXTRUDE_HEIGHT = 1


# =======================
# = CATMULL-ROM SPLINES =
# =======================
def catmull_rom_polygon(
    points: Sequence[Point23Input],
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    extrude_height: float = DEFAULT_EXTRUDE_HEIGHT,
    show_controls: bool = False,
    center: bool = True,
) -> OpenSCADObject:
    """
    Return a closed OpenSCAD polygon object through all of `points`,
    extruded to `extrude_height`. If `show_controls` is True, return red
    cylinders at each of the specified control points; this makes it easier to
    move determine which points should move to get a desired shape.

    NOTE: if `extrude_height` is 0, this function returns a 2D `polygon()`
    object, which OpenSCAD can only combine with other 2D objects
    (e.g. `square`, `circle`, but not `cube` or `cylinder`). If `extrude_height`
    is nonzero, the object returned will be 3D and only combine with 3D objects.
    """
    catmull_points = catmull_rom_points(points, subdivisions, close_loop=True)
    shape = polygon(catmull_points)
    if extrude_height > 0:
        shape = linear_extrude(height=extrude_height, center=center)(shape)

    if show_controls:
        shape += control_points(points, extrude_height, center)
    return shape


def catmull_rom_points(
    points: Sequence[Point23Input],
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    close_loop: bool = False,
    start_tangent: Vec23 = None,
    end_tangent: Vec23 = None,
) -> List[Point3]:
    """
    Return a smooth set of points through `points`, with `subdivisions` points
    between each pair of control points.

    If `close_loop` is False, `start_tangent` and `end_tangent` can specify
    tangents at the open ends of the returned curve. If not supplied, tangents
    will be colinear with first and last supplied segments

    Credit due: Largely taken from C# code at:
    https://www.habrador.com/tutorials/interpolation/1-catmull-rom-splines/
    retrieved 20190712
    """
    catmull_points: List[Point3] = []
    cat_points: List[Point3] = []
    # points_list = cast(List[Point23], points)

    points_list = list([euclidify(p, Point3) for p in points])

    if close_loop:
        cat_points = euclidify(
            [points_list[-1]] + points_list + points_list[0:2], Point3
        )
    else:
        # Use supplied tangents or just continue the ends of the supplied points
        start_tangent = start_tangent or (points_list[1] - points_list[0])
        start_tangent = euclidify(start_tangent, Vector3)
        end_tangent = end_tangent or (points_list[-2] - points_list[-1])
        end_tangent = euclidify(end_tangent, Vector3)
        cat_points = (
            [points_list[0] + start_tangent]
            + points_list
            + [points_list[-1] + end_tangent]
        )

    last_point_range = len(cat_points) - 3 if close_loop else len(cat_points) - 3

    for i in range(0, last_point_range):
        include_last = True if i == last_point_range - 1 else False
        controls = cat_points[i : i + 4]
        # If we're closing a loop, controls needs to wrap around the end of the array
        points_needed = 4 - len(controls)
        if points_needed > 0:
            controls += cat_points[0:points_needed]
        controls_tuple = cast(FourPoints, controls)
        catmull_points += _catmull_rom_segment(
            controls_tuple, subdivisions, include_last
        )

    return catmull_points


def _catmull_rom_segment(
    controls: FourPoints, subdivisions: int, include_last=False
) -> List[Point3]:
    """
    Returns `subdivisions` Points between the 2nd & 3rd elements of `controls`,
    on a quadratic curve that passes through all 4 control points.
    If `include_last` is True, return `subdivisions` + 1 points, the last being
    controls[2].

    No reason to call this unless you're trying to do something very specific
    """
    pos: Point23 = None
    positions: List[Point23] = []

    num_points = subdivisions
    if include_last:
        num_points += 1

    p0, p1, p2, p3 = [euclidify(p, Point3) for p in controls]
    a = 2 * p1
    b = p2 - p0
    c = 2 * p0 - 5 * p1 + 4 * p2 - p3
    d = -p0 + 3 * p1 - 3 * p2 + p3

    for i in range(num_points):
        t = i / subdivisions
        pos = 0.5 * (a + (b * t) + (c * t * t) + (d * t * t * t))
        positions.append(Point3(*pos))
    return positions


def catmull_rom_patch_points(
    patch: Tuple[PointInputs, PointInputs],
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    index_start: int = 0,
) -> Tuple[List[Point3], List[FaceTrio]]:
    verts: List[Point3] = []
    faces: List[FaceTrio] = []

    cm_points_a = catmull_rom_points(patch[0], subdivisions=subdivisions)
    cm_points_b = catmull_rom_points(patch[1], subdivisions=subdivisions)

    strip_length = len(cm_points_a)

    for i in range(subdivisions + 1):
        frac = i / subdivisions
        verts += list(
            [affine_combination(a, b, frac) for a, b in zip(cm_points_a, cm_points_b)]
        )
        a_start = i * strip_length + index_start
        b_start = a_start + strip_length
        # This connects the verts we just created to the verts we'll make on the
        # next loop. So don't calculate for the last loop
        if i < subdivisions:
            faces += face_strip_list(a_start, b_start, strip_length)

    return verts, faces


def catmull_rom_patch(
    patch: Tuple[PointInputs, PointInputs], subdivisions: int = DEFAULT_SUBDIVISIONS
) -> OpenSCADObject:

    faces, vertices = catmull_rom_patch_points(patch, subdivisions)
    return polyhedron(faces, vertices)


def catmull_rom_prism(
    control_curves: Sequence[PointInputs],
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    closed_ring: bool = True,
    add_caps: bool = True,
    smooth_edges: bool = False,
) -> polyhedron:
    if smooth_edges:
        return catmull_rom_prism_smooth_edges(
            control_curves, subdivisions, closed_ring, add_caps
        )

    verts: List[Point3] = []
    faces: List[FaceTrio] = []

    curves = list([euclidify(c) for c in control_curves])
    if closed_ring:
        curves.append(curves[0])

    curve_length = (len(curves[0]) - 1) * subdivisions + 1
    for i, (a, b) in enumerate(zip(curves[:-1], curves[1:])):
        index_start = len(verts) - curve_length
        first_new_vert = curve_length
        if i == 0:
            index_start = 0
            first_new_vert = 0

        new_verts, new_faces = catmull_rom_patch_points(
            (a, b), subdivisions=subdivisions, index_start=index_start
        )

        # new_faces describes all the triangles in the patch we just computed,
        # but new_verts shares its first curve_length vertices with the last
        # curve_length vertices; Add on only the new points
        verts += new_verts[first_new_vert:]
        faces += new_faces

    if closed_ring and add_caps:
        bot_indices = range(0, len(verts), curve_length)
        top_indices = range(curve_length - 1, len(verts), curve_length)

        bot_centroid, bot_faces = centroid_endcap(verts, bot_indices)
        verts.append(bot_centroid)
        faces += bot_faces
        # Note that bot_centroid must be added to verts before creating the
        # top endcap; otherwise both endcaps would point to the same centroid point
        top_centroid, top_faces = centroid_endcap(verts, top_indices, invert=True)
        verts.append(top_centroid)
        faces += top_faces

    p = polyhedron(faces=faces, points=verts, convexity=3)
    return p


def catmull_rom_prism_smooth_edges(
    control_curves: Sequence[PointInputs],
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    closed_ring: bool = True,
    add_caps: bool = True,
) -> polyhedron:

    verts: List[Point3] = []
    faces: List[FaceTrio] = []

    # TODO: verify that each control_curve has the same length

    curves = list([euclidify(c) for c in control_curves])

    expanded_curves = [
        catmull_rom_points(c, subdivisions, close_loop=False) for c in curves
    ]
    expanded_length = len(expanded_curves[0])
    for i in range(expanded_length):
        contour_controls = [c[i] for c in expanded_curves]
        contour = catmull_rom_points(
            contour_controls, subdivisions, close_loop=closed_ring
        )
        verts += contour

        contour_length = len(contour)
        # generate the face triangles between the last two rows of vertices
        if i > 0:
            a_start = len(verts) - 2 * contour_length
            b_start = len(verts) - contour_length
            # Note the b_start, a_start order here. This makes sure our faces
            # are pointed outwards for the test cases I ran. I think if control
            # curves were specified clockwise rather than counter-clockwise, all
            # of the faces would be pointed inwards
            new_faces = face_strip_list(
                b_start, a_start, length=contour_length, close_loop=closed_ring
            )
            faces += new_faces

    if closed_ring and add_caps:
        bot_indices = range(0, contour_length)
        top_indices = range(len(verts) - contour_length, len(verts))

        bot_centroid, bot_faces = centroid_endcap(verts, bot_indices)
        verts.append(bot_centroid)
        faces += bot_faces
        # Note that bot_centroid must be added to verts before creating the
        # top endcap; otherwise both endcaps would point to the same centroid point
        top_centroid, top_faces = centroid_endcap(verts, top_indices, invert=True)
        verts.append(top_centroid)
        faces += top_faces

    p = polyhedron(faces=faces, points=verts, convexity=3)
    return p


# ==================
# = BEZIER SPLINES =
# ==================
# Ported from William A. Adams' Bezier OpenSCAD code at:
# https://www.thingiverse.com/thing:8443


def bezier_polygon(
    controls: FourPoints,
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    extrude_height: float = DEFAULT_EXTRUDE_HEIGHT,
    show_controls: bool = False,
    center: bool = True,
) -> OpenSCADObject:
    """
    Return an OpenSCAD object representing a closed quadratic Bezier curve.
    If extrude_height == 0, return a 2D `polygon()` object.
    If extrude_height > 0, return a 3D extrusion of specified height.
    Note that OpenSCAD won't render 2D & 3D objects together correctly, so pick
    one and use that.
    """
    points = bezier_points(controls, subdivisions)
    # OpenSCAD can'ts handle Point3s in creating a polygon. Convert them to Point2s
    # Note that this prevents us from making polygons outside of the XY plane,
    # even though a polygon could reasonably be in some other plane while remaining 2D
    points = list((Point2(p.x, p.y) for p in points))
    shape: OpenSCADObject = polygon(points)
    if extrude_height != 0:
        shape = linear_extrude(extrude_height, center=center)(shape)

    if show_controls:
        control_objs = control_points(
            controls, extrude_height=extrude_height, center=center
        )
        shape += control_objs

    return shape


def bezier_points(
    controls: FourPoints,
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    include_last: bool = True,
) -> List[Point3]:
    """
    Returns a list of `subdivisions` (+ 1, if `include_last` is True) points
    on the cubic bezier curve defined by `controls`. The curve passes through
    controls[0] and controls[3]

    If `include_last` is True, the last point returned will be controls[3]; if
    False, (useful for linking several curves together), controls[3] won't be included

    Ported from William A. Adams' Bezier OpenSCAD code at:
    https://www.thingiverse.com/thing:8443
    """
    # TODO: enable a smooth curve through arbitrarily many points, as described at:
    # https://www.algosome.com/articles/continuous-bezier-curve-line.html

    points: List[Point3] = []
    last_elt = 1 if include_last else 0
    for i in range(subdivisions + last_elt):
        u = i / subdivisions
        points.append(_point_along_bez4(*controls, u))
    return points


def _point_along_bez4(
    p0: Point23Input, p1: Point23Input, p2: Point23Input, p3: Point23Input, u: float
) -> Point3:
    p0 = euclidify(p0)
    p1 = euclidify(p1)
    p2 = euclidify(p2)
    p3 = euclidify(p3)

    x = _bez03(u) * p0.x + _bez13(u) * p1.x + _bez23(u) * p2.x + _bez33(u) * p3.x
    y = _bez03(u) * p0.y + _bez13(u) * p1.y + _bez23(u) * p2.y + _bez33(u) * p3.y
    z = _bez03(u) * p0.z + _bez13(u) * p1.z + _bez23(u) * p2.z + _bez33(u) * p3.z
    return Point3(x, y, z)


def _bez03(u: float) -> float:
    return pow((1 - u), 3)


def _bez13(u: float) -> float:
    return 3 * u * (pow((1 - u), 2))


def _bez23(u: float) -> float:
    return 3 * (pow(u, 2)) * (1 - u)


def _bez33(u: float) -> float:
    return pow(u, 3)


# ================
# = HOBBY CURVES =
# ================
# Based on this post
# https://www.jakelow.com/blog/hobby-curves
# Comments mostly transferred to respective positions
# This code implements Hobby's algorithm for fitting a cubic Bézier curve onto
# a sequence of points in two dimensions.

# Hobby's algorithm was devised by John D. Hobby and Donald Knuth for use in
# the METAFONT program. Their original paper on the algorithm, titled “Smooth,
# Easy to Compute Interpolating Splines”, was published in 'Discrete and
# Computational Geometry' vol. 1 in 1986. A copy can be found at this URL:
# https://link.springer.com/content/pdf/10.1007/BF02187690.pdf


# Based on the paper "Typographers, programmers and mathematicians, or the case
# of an æsthetically pleasing interpolation" by Bogusław Jackowski, published in
# TUGboat, Volume 34 (2013), No. 2, and available at the following URL:
# https://tug.org/TUGboat/tb34-2/tb107jackowski.pdf
def hobby_points(
    points: List[Point3], omega: float = 0, close_loop: bool = False
) -> List[Point3]:
    """Hobby's algorithm: given a set of points, fit a Bézier spline to them.

    The chosen splines tend to have pleasing, rounded shapes.

    Parameters:
    - points: an array of points as [x, y] pairs
    - omega: a number between 0 and 1 (inclusive); controls how much curl
        there will be at the endpoints of the curve

    Returns: an array of points as [x, y] pairs that define a Bézier spline.

    The output array will have 3n - 2 points where n is the number of input points.
    The output will contain every point in the input (these become knots in the
    Bézier spline), interspersed with pairs of new points which define positions
    of handle points on the spline. All points are in the same coordinate space.
    """
    # n is defined such that the points can be numbered P[0] ... P[n].
    # such that there are a total of n-1 points
    # Ensure points are 3d
    if not isinstance(points[0], Point3):
        points = [Point3(*point) for point in points]

    # Track edge control points to smooth things out
    points.append(points[0])
    points.insert(0, points[-2])

    n = len(points) - 1
    if n < 2:
        raise ValueError(
            "Solving for Hobby points only possible for two or more points."
        )
    # chords[i] is the vector from P[i] to P[i+1].
    # d[i] is the length of the ith chord.
    # Chords from first to last point
    chords = [
        Vector3(*(next_point - point).xyz) for point, next_point in pairwise(points)
    ]
    d = [chord.magnitude() for chord in chords]
    if min(d) <= 0:
        # cannot support successive points being the same
        raise ValueError("No chord can be zero-length.")

    # gamma[i] is the signed turning angle at P[i], i.e. the angle between
    # the chords from P[i-1] to P[i] and from P[i] to P[i+1].
    gamma = [chord.angle(next_chord) for chord, next_chord in pairwise(chords)]
    gamma.insert(0, gamma[-1])
    gamma.append(gamma[1])

    normals = [
        vec3_perp_norm(chord, next_chord) for chord, next_chord in pairwise(chords)
    ]
    normals.insert(0, normals[0])
    normals.append(normals[-1])

    # Set up the system of linear equations (Jackowski, formula 38).
    # We're representing this system as a tridiagonal matrix, because
    # we can solve such a system in O(n) time using the Thomas algorithm.
    #
    # Here, A, B, and C are the matrix diagonals and D is the right-hand side.
    # See Wikipedia for a more detailed explanation:
    # https://en.wikipedia.org/wiki/Tridiagonal_matrix_algorithm
    A = [0]
    B = [2.0 + omega]
    C = [2.0 * omega + 1]
    D = [-1.0 * C[0] * gamma[1]]

    for i in range(1, n):
        A.append(1.0 / d[i - 1])
        B.append((2.0 * d[i - 1] + 2 * d[i]) / (d[i - 1] * d[i]))
        C.append(1.0 / d[i])
        D.append(
            (-1.0 * (2 * gamma[i] * d[i] + gamma[i + 1] * d[i - 1])) / (d[i - 1] * d[i])
        )
    A.append(2.0 * omega + 1)
    B.append(2.0 + omega)
    C.append(0)
    D.append(0)

    alpha = thomas(A, B, C, D)

    # Use alpha (the chord angle) and gamma (the turning angle of the chord
    # polyline) to solve for beta at each point (beta is like alpha, but for
    # the chord and handle vector arriving at P[i] rather than leaving from it).
    beta = []
    for i in range(n - 1):
        beta.append(-1 * gamma[i + 1] - alpha[i + 1])
    beta.append(-1 * alpha[n])

    # Now we have the angles between the handle vector and the chord
    # both arrriving at and leaving from each point, we can solve for the
    # positions of the handle (control) points themselves.
    c0 = []
    c1 = []
    for i in range(n):
        # Compute the magnitudes of the handle vectors at this point
        a = (rho(alpha[i], beta[i]) * d[i]) / 3.0
        b = (rho(beta[i], alpha[i]) * d[i]) / 3.0

        # Use the magnitutes, chords, and turning angles to find
        # the positions of the control points in the global coord space.
        c0_vec = chords[i].rotate_around(normals[i], alpha[i])
        c1_vec = chords[i].rotate_around(normals[i + 1], -1 * beta[i])

        c0_new_point = points[i] + c0_vec.normalize() * a
        c1_new_point = points[i + 1] - c1_vec.normalize() * b
        c0.append(c0_new_point)
        c1.append(c1_new_point)

    # Finally gather up and return the spline points (knots & control points)
    # as a List of Point2s
    res_controls = [(points[i], c0[i], c1[i]) for i in range(1, n - 1)]
    if close_loop:
        # Append the curve from the last input point
        # to the first input point,
        res_controls.append(
            (points[n - 1], c0[n - 1], c1[0]),
        )
        res_controls.append((points[1],))
    else:
        # Append the last input point only
        res_controls.append((points[n - 1],))
    return [Point3(*p.xyz) for p in flatten(res_controls)]


# Once the angles alpha and beta have been computed for each knot (which
# determine the direction from the knot to each of its neighboring handles),
# this function is used to compute the lengths of the vectors from the knot to
# those handles. Combining the length and angle together lets us solve for the
# handle positions.
#
# The exact choice of function is somewhat arbitrary. The aim is to return
# handle lengths that produce a Bézier curve which is a good approximation of a
# circular arc for points near the knot.
#
# Hobby and Knuth both proposed multiple candidate functions. This code uses
# the function from Jackowski formula 28, due to its simplicity. For other
# choices see Jackowski, section 5.
def rho(alpha: float, beta: float) -> float:
    """ "Velocity function" to compute the length of handles for a bezier spline."""
    c = 2.0 / 3
    return 2.0 / (1 + c * cos(beta) + (1 - c) * cos(alpha))


def thomas(A: Sequence, B: Sequence, C: Sequence, D: Sequence) -> Sequence:
    """Thomas algorithm: Solve a system of equations encoded in a tridiagonal matrix.

    A, B, and C are diagonals of the matrix. B is the main diagonal.
    D is the vector on the right-hand-side of the equation.

    Both B and D will have n elements. The arrays A and C will have
    length n as well, but each has one fewer element than B (the values
    A[0] and C[n-1] are undefined)."""

    # Note: n is defined here so that B[n] is valid, i.e. we are solving
    # a system of n+1 equations.
    n = len(B) - 1

    # Step 1: forward sweep to eliminate A[I] from each Equation
    # allocate lists for modified C and D coefficients, c_prime, d_prime
    c_prime = [C[0] / B[0]]
    d_prime = [D[0] / B[0]]

    for i in range(1, n + 1):
        denom = B[i] - c_prime[i - 1] * A[i]
        c_prime.append(C[i] / denom)
        d_prime.append((D[i] - d_prime[i - 1] * A[i]) / denom)

    # Step 2: back substitution to solve for x
    X = []
    X.append(d_prime[n])
    # Work back to front, solving for x[i] using x[-1]
    for i in range(n - 1, -1, -1):
        X.append(d_prime[i] - c_prime[i] * X[-1])
    return X[::-1]


# ===========
# = HELPERS =
# ===========
def vec3_perp_norm(v: Vector3, other: Vector3) -> Vector3:
    """Return the normalized cross product of vectors V and OTHER.

    Used to fetch a normalized vector perpendicular to
    both V and OTHER about which to rotate when forming smooth curves.
    """
    return v.cross(other).normalized()


def flatten(matr: Sequence[Sequence], keep_none_values: bool = True) -> List:
    return [item for row in matr for item in row if item or keep_none_values]


def control_points(
    points: Sequence[Point23],
    extrude_height: float = 0,
    center: bool = True,
    points_color: Tuple3 = Red,
) -> OpenSCADObject:
    """
    Return a list of red cylinders/circles (depending on `extrude_height`) at
    a supplied set of 2D points. Useful for visualizing and tweaking a curve's
    control points
    """
    # Figure out how big the circles/cylinders should be based on the spread of points
    min_bb, max_bb = bounding_box(points)
    outline_w = max_bb[0] - min_bb[0]
    outline_h = max_bb[1] - min_bb[1]
    r = min(min(outline_w, outline_h) / 20, 0.25)  #
    if extrude_height == 0:
        c = circle(r=r)
    else:
        h = extrude_height * 1.1
        c = cylinder(r=r, h=h, center=center)
    controls = color(points_color)([translate((p.x, p.y, 0))(c) for p in points])
    return controls


def face_strip_list(
    a_start: int, b_start: int, length: int, close_loop: bool = False
) -> List[FaceTrio]:
    # If a_start is the index of the vertex at one end of a row of points in a surface,
    # and b_start is the index of the vertex at the same end of the next row of points,
    # return a list of lists of indices describing faces for the whole row:
    # face_strip_list(a_start = 0, b_start = 3, length=3) => [[0,4,3], [0,1,4], [1,5,4], [1,2,5]]
    #   3-4-5
    #   |/|/|
    #   0-1-2  =>  [[0,4,3], [0,1,4], [1,5,4], [1,2,5]]
    #
    # If close_loop is true, add one more pair of faces connecting the far
    # edge of the strip to the near edge, in this case [[2,3,5], [2,0,3]]
    faces: List[FaceTrio] = []
    loop = length - 1

    for a, b in zip(range(a_start, a_start + loop), range(b_start, b_start + loop)):
        faces.append((a, b + 1, b))
        faces.append((a, a + 1, b + 1))
    if close_loop:
        faces.append((a + loop, b, b + loop))
        faces.append((a + loop, a, b))
    return faces


def fan_endcap_list(cap_points: int = 3, index_start: int = 0) -> List[FaceTrio]:
    """
    Return a face-triangles list for the endpoint of a tube with cap_points points
    We construct a fan of triangles all starting at point index_start and going
    to each point in turn. 
    
    NOTE that this would not work for non-convex rings. 
    In that case, it would probably be better to create a new centroid point and have
    all triangle reach out from it. That wouldn't handle all polygons, but would
    work with mildly concave ones like a star, for example.

    So fan_endcap_list(cap_points=6, index_start=0), like so:
           0   
         /   \
       5      1
       |      | 
       4      2
         \   /
           3      
    
           returns:  [(0,1,2), (0,2,3), (0,3,4), (0,4,5)]      
    """
    faces: List[FaceTrio] = []
    for i in range(index_start + 1, index_start + cap_points - 1):
        faces.append((index_start, i, i + 1))
    return faces


def centroid_endcap(
    tube_points: Sequence[Point3], indices: Sequence[int], invert: bool = False
) -> Tuple[Point3, List[FaceTrio]]:
    # tube_points: all points in a polyhedron tube
    # indices: the indexes of the points at the desired end of the tube
    # invert: if True, invert the order of the generated faces. One endcap in
    #   each pair should be inverted
    #
    # Return all the triangle information needed to make an endcap polyhedron
    #
    # This is sufficient for some moderately concave polygonal endcaps,
    # (a star shape, say), but wouldn't be enough for more irregularly convex
    # polygons (anyplace where a segment from the centroid to a point on the
    # polygon crosses an edge of the polygon)
    faces: List[FaceTrio] = []
    center = centroid([tube_points[i] for i in indices])
    centroid_index = len(tube_points)

    for a, b in zip(indices[:-1], indices[1:]):
        faces.append((centroid_index, a, b))
    faces.append((centroid_index, indices[-1], indices[0]))

    if invert:
        faces = list((reversed(f) for f in faces))  # type: ignore

    return (center, faces)


def centroid(points: Sequence[Point23]) -> Point23:
    total = Point3(0, 0, 0)
    for p in points:
        total += p
    total /= len(points)
    return total


def affine_combination(a: Point23, b: Point23, fraction: float) -> Point23:
    # Return a Point[23] between a & b, where fraction==0 => a, fraction==1 => b
    return (1 - fraction) * a + fraction * b
