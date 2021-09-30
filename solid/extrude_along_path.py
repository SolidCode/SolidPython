#! /usr/bin/env python
from math import radians
from solid import OpenSCADObject, Points, Indexes, ScadSize, polyhedron
from solid.utils import euclidify, euc_to_arr, transform_to_point, centroid
from euclid3 import Point2, Point3, Vector2, Vector3

from typing import Dict, Optional, Sequence, Tuple, Union, List, Callable

Tuple2 = Tuple[float, float]
FacetIndices = Tuple[int, int, int]
Point3Transform = Callable[[Point3, Optional[float], Optional[float]], Point3]

# ==========================
# = Extrusion along a path =
# ==========================
def extrude_along_path( shape_pts:Points, 
                        path_pts:Points, 
                        scales:Sequence[Union[Vector2, float, Tuple2]] = None,
                        rotations: Sequence[float] = None,
                        transforms: Sequence[Point3Transform] = None,
                        connect_ends = False,
                        cap_ends = True) -> OpenSCADObject:
    '''
    Extrude the curve defined by shape_pts along path_pts.
    -- For predictable results, shape_pts must be planar, convex, and lie
    in the XY plane centered around the origin. *Some* nonconvexity (e.g, star shapes)
    and nonplanarity will generally work fine
    
    -- len(scales) should equal len(path_pts).  No-op if not supplied
          Each entry may be a single number for uniform scaling, or a pair of 
          numbers (or Point2) for differential X/Y scaling
          If not supplied, no scaling will occur.
          
    -- len(rotations) should equal 1 or len(path_pts). No-op if not supplied.
          Each point in shape_pts will be rotated by rotations[i] degrees at
          each point in path_pts. Or, if only one rotation is supplied, the shape
          will be rotated smoothly over rotations[0] degrees in the course of the extrusion
    
    -- len(transforms) should be 1 or be equal to len(path_pts).  No-op if not supplied.
          Each entry should be have the signature: 
             def transform_func(p:Point3, path_norm:float, loop_norm:float): Point3
          where path_norm is in [0,1] and expresses progress through the extrusion
          and loop_norm is in [0,1] and express progress through a single loop of the extrusion
    
    -- if connect_ends is True, the first and last loops of the extrusion will
          be joined, which is useful for toroidal geometries. Overrides cap_ends

    -- if cap_ends is True, each point in the first and last loops of the extrusion
        will be connected to the centroid of that loop. For planar, convex shapes, this
        works nicely. If shape is less planar or convex, some self-intersection may happen.
        Not applied if connect_ends is True
    '''


    polyhedron_pts:Points= []
    facet_indices:List[Tuple[int, int, int]] = []

    # Make sure we've got Euclid Point3's for all elements
    shape_pts = euclidify(shape_pts, Point3)
    path_pts = euclidify(path_pts, Point3)

    src_up = Vector3(0, 0, 1)

    shape_pt_count = len(shape_pts)

    tangent_path_points: List[Point3] = []
    if connect_ends:
        tangent_path_points = [path_pts[-1]] + path_pts + [path_pts[0]]
    else:
        first = Point3(*(path_pts[0] - (path_pts[1] - path_pts[0])))
        last = Point3(*(path_pts[-1] - (path_pts[-2] - path_pts[-1])))
        tangent_path_points = [first] + path_pts + [last]
    tangents = [tangent_path_points[i+2] - tangent_path_points[i] for i in range(len(path_pts))]

    for which_loop in range(len(path_pts)):
        # path_normal is 0 at the first path_pts and 1 at the last
        path_normal = which_loop/ (len(path_pts) - 1)

        path_pt = path_pts[which_loop]
        tangent = tangents[which_loop]
        scale = scales[which_loop] if scales else 1

        rotate_degrees = None
        if rotations:
            rotate_degrees = rotations[which_loop] if len(rotations) > 1 else rotations[0] * path_normal

        transform_func = None
        if transforms:
            transform_func = transforms[which_loop] if len(transforms) > 1 else transforms[0]

        this_loop = shape_pts[:]
        this_loop = _scale_loop(this_loop, scale)
        this_loop = _rotate_loop(this_loop, rotate_degrees)
        this_loop = _transform_loop(this_loop, transform_func, path_normal)

        this_loop = transform_to_point(this_loop, dest_point=path_pt, dest_normal=tangent, src_up=src_up)
        loop_start_index = which_loop * shape_pt_count

        if (which_loop < len(path_pts) - 1):
            loop_facets = _loop_facet_indices(loop_start_index, shape_pt_count)
            facet_indices += loop_facets

        # Add the transformed points & facets to our final list
        polyhedron_pts += this_loop

    if connect_ends:
        connect_loop_start_index = len(polyhedron_pts) - shape_pt_count
        loop_facets = _loop_facet_indices(connect_loop_start_index, shape_pt_count, 0)
        facet_indices += loop_facets

    elif cap_ends:
        # OpenSCAD's polyhedron will automatically triangulate faces as needed.
        # So just include all points at each end of the tube 
        last_loop_start_index = len(polyhedron_pts) - shape_pt_count 
        start_loop_indices = list(reversed(range(shape_pt_count)))
        end_loop_indices = list(range(last_loop_start_index, last_loop_start_index + shape_pt_count))   
        facet_indices.append(start_loop_indices)
        facet_indices.append(end_loop_indices)

    return polyhedron(points=euc_to_arr(polyhedron_pts), faces=facet_indices) # type: ignore

def _loop_facet_indices(loop_start_index:int, loop_pt_count:int, next_loop_start_index=None) -> List[FacetIndices]:
    facet_indices: List[FacetIndices] = []
    # nlsi == next_loop_start_index
    if next_loop_start_index == None:
        next_loop_start_index = loop_start_index + loop_pt_count
    loop_indices      = list(range(loop_start_index,      loop_pt_count + loop_start_index)) + [loop_start_index]
    next_loop_indices = list(range(next_loop_start_index, loop_pt_count + next_loop_start_index )) + [next_loop_start_index]

    for i, (a, b) in enumerate(zip(loop_indices[:-1], loop_indices[1:])):
        c, d = next_loop_indices[i: i+2]
        # OpenSCAD's polyhedron will accept quads and do its own triangulation with them,
        # so we could just append (a,b,d,c). 
        # However, this lets OpenSCAD (Or CGAL?) do its own triangulation, leading
        # to some strange outcomes. Prefer to do our own triangulation.
        #   c--d
        #   |\ |
        #   | \|
        #   a--b               
        # facet_indices.append((a,b,d,c))
        facet_indices.append((a,b,c))
        facet_indices.append((b,d,c))
    return facet_indices

def _rotate_loop(points:Sequence[Point3], rotation_degrees:float=None) -> List[Point3]:
    if rotation_degrees is None:
        return points
    up = Vector3(0,0,1)
    rads = radians(rotation_degrees)
    return [p.rotate_around(up, rads) for p in points]

def _scale_loop(points:Sequence[Point3], scale:Union[float, Point2, Tuple2]=None) -> List[Point3]:
    if scale is None:
        return points

    if isinstance(scale, (float, int)):
        scale = [scale] * 2
    return [Point3(point.x * scale[0], point.y * scale[1], point.z) for point in points]

def _transform_loop(points:Sequence[Point3], transform_func:Point3Transform = None, path_normal:float = None) -> List[Point3]:
    # transform_func is a function that takes a point and optionally two floats,
    # a `path_normal`, in [0,1] that indicates where this loop is in a path extrusion,
    # and `loop_normal` in [0,1] that indicates where this point is in a list of points
    if transform_func is None:
        return points

    result = []
    for i, p in enumerate(points):
        # i goes from 0 to 1 across points
        loop_normal = i/(len(points) -1)
        new_p = transform_func(p, path_normal, loop_normal)
        result.append(new_p)
    return result

