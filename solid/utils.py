#! /usr/bin/env python
from itertools import zip_longest
from math import pi, ceil, floor, sqrt, atan2, degrees, radians

from solid import union, cube, translate, rotate, square, circle, polyhedron, polygon
from solid import difference, intersection, multmatrix, cylinder, color
from solid import text, linear_extrude, resize
from solid import run_euclid_patch

from solid import OpenSCADObject, P2, P3, P4, Vec3 , Vec4, Vec34, P3s, P23
from solid import Points, Indexes, ScadSize

from euclid3 import Point2, Point3, Vector2, Vector3, Line2, Line3
from euclid3 import LineSegment2, LineSegment3, Matrix4
run_euclid_patch()

# ==========
# = TYPING =
# ==========
from typing import Any, Union, Tuple, Sequence, List, Optional, Callable, Dict, cast
Point23 = Union[Point2, Point3]
Vector23 = Union[Vector2, Vector3]
Line23 = Union[Line2, Line3]
LineSegment23 = Union[LineSegment2, LineSegment3]

Tuple2 = Tuple[float, float]
Tuple3 = Tuple[float, float, float]
EucOrTuple = Union[Point3, 
                Vector3, 
                Tuple2, 
                Tuple3
            ]
DirectionLR = float # LEFT or RIGHT in 2D

# =============
# = CONSTANTS =
# =============

EPSILON = 0.01
RIGHT, TOP, LEFT, BOTTOM = range(4)

X, Y, Z = (0, 1, 2)

ORIGIN      = ( 0, 0, 0)
UP_VEC      = ( 0, 0, 1)
RIGHT_VEC   = ( 1, 0, 0)
FORWARD_VEC = ( 0, 1, 0)
DOWN_VEC    = ( 0, 0,-1)
LEFT_VEC    = (-1, 0, 0)
BACK_VEC    = ( 0,-1, 0)

# ==========
# = Colors =
# ========== 
# From Hans Häggström's materials.scad in MCAD: https://github.com/openscad/MCAD
Red         = (1, 0, 0)
Green       = (0, 1, 0)
Blue        = (0, 0, 1)
Cyan        = (0, 1, 1)
Magenta     = (1, 0, 1)
Yellow      = (1, 1, 0)
Black       = (0, 0, 0)
White       = (1, 1, 1)
Oak         = (0.65, 0.50, 0.40)
Pine        = (0.85, 0.70, 0.45)
Birch       = (0.90, 0.80, 0.60)
FiberBoard  = (0.70, 0.67, 0.60)
BlackPaint  = (0.20, 0.20, 0.20)
Iron        = (0.36, 0.33, 0.33)
Steel       = (0.65, 0.67, 0.72)
Stainless   = (0.45, 0.43, 0.50)
Aluminum    = (0.77, 0.77, 0.80)
Brass       = (0.88, 0.78, 0.50)
Transparent = (1,    1,    1,   0.2)

# ==============
# = Grid Plane =
# ==============
def grid_plane(grid_unit:int=12, count:int=10, line_weight:float=0.1, plane:str='xz') -> OpenSCADObject:

    # Draws a grid of thin lines in the specified plane.  Helpful for
    # reference during debugging.
    l = count * grid_unit
    t = union()
    t.set_modifier('background')
    for i in range(int(-count / 2), int(count / 2 + 1)):
        if 'xz' in plane:
            # xz-plane
            h = up(i * grid_unit)(cube([l, line_weight, line_weight], center=True))
            v = right(i * grid_unit)(cube([line_weight, line_weight, l], center=True))
            t.add([h, v])

        # xy plane
        if 'xy' in plane:
            h = forward(i * grid_unit)(cube([l, line_weight, line_weight], center=True))
            v = right(i * grid_unit)(cube([line_weight, l, line_weight], center=True))
            t.add([h, v])

        # yz plane
        if 'yz' in plane:
            h = up(i * grid_unit)(cube([line_weight, l, line_weight], center=True))
            v = forward(i * grid_unit)(cube([line_weight, line_weight, l], center=True))

            t.add([h, v])

    return t


def distribute_in_grid(objects:Sequence[OpenSCADObject], 
                       max_bounding_box:Tuple[float,float], 
                       rows_and_cols: Tuple[int,int]=None) -> OpenSCADObject:
    # Translate each object in objects in a grid with each cell of size
    # max_bounding_box.
    #
    # objects:  array of SCAD objects
    # max_bounding_box: 2-tuple with x & y dimensions of grid cells.
    #   if a single number is passed, x  & y will both use it
    # rows_and_cols: 2-tuple of how many rows and columns to use. If
    #       not supplied, rows_and_cols will be the smallest square that
    #       can contain all members of objects (e.g, if len(objects) == 80,
    #       rows_and_cols will default to (9,9))

    # Distributes object in a grid in the xy plane
    # with objects spaced max_bounding_box apart
    if isinstance(max_bounding_box, (list, tuple)):
        x_trans, y_trans = max_bounding_box[0:2]
    elif isinstance(max_bounding_box, (int, float, complex)):
        x_trans = y_trans = max_bounding_box
    else:
        pass  # TypeError

    ret = []
    if rows_and_cols:
        grid_w, grid_h = rows_and_cols
    else:
        grid_w = grid_h = int(ceil(sqrt(len(objects))))

    objs_placed = 0
    for y in range(grid_h):
        for x in range(grid_w):
            if objs_placed < len(objects):
                ret.append(
                    translate((x * x_trans, y * y_trans, 0))(objects[objs_placed]))
                objs_placed += 1
            else:
                break
    return union()(*ret)

# ==============
# = Directions =
# ==============
def up(z:float) -> OpenSCADObject:
    return translate((0, 0, z))

def down(z: float) -> OpenSCADObject:
    return translate((0, 0, -z))

def right(x: float) -> OpenSCADObject:
    return translate((x, 0, 0))

def left(x: float) -> OpenSCADObject:
    return translate((-x, 0, 0))

def forward(y: float) -> OpenSCADObject:
    return translate((0, y, 0))

def back(y: float) -> OpenSCADObject:
    return translate((0, -y, 0))

# ===========================
# = Box-alignment rotations =
# ===========================
def rot_z_to_up(obj:OpenSCADObject) -> OpenSCADObject:
    # NOTE: Null op
    return rotate(a=0, v=FORWARD_VEC)(obj)

def rot_z_to_down(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=180, v=FORWARD_VEC)(obj)

def rot_z_to_right(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=90, v=FORWARD_VEC)(obj)

def rot_z_to_left(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=-90, v=FORWARD_VEC)(obj)

def rot_z_to_forward(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=-90, v=RIGHT_VEC)(obj)

def rot_z_to_back(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=90, v=RIGHT_VEC)(obj)

# ================================
# = Box-aligment and translation =
# ================================
def box_align(obj:OpenSCADObject, 
              direction_func:Callable[[float], OpenSCADObject]=up, 
              distance:float=0) -> OpenSCADObject:
    # Given a box side (up, left, etc) and a distance,
    # rotate obj (assumed to be facing up) in the
    # correct direction and move it distance in that
    # direction
    trans_and_rot = {
        up:         rot_z_to_up,  # Null
        down:       rot_z_to_down,
        right:      rot_z_to_right,
        left:       rot_z_to_left,
        forward:    rot_z_to_forward,
        back:       rot_z_to_back,
    }

    assert(direction_func in trans_and_rot)
    rot = trans_and_rot[direction_func]
    return direction_func(distance)(rot(obj))

# =======================
# = 90-degree Rotations =
# =======================

def rot_z_to_x(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=90, v=FORWARD_VEC)(obj)

def rot_z_to_neg_x(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=-90, v=FORWARD_VEC)(obj)

def rot_z_to_neg_y(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=90, v=RIGHT_VEC)(obj)

def rot_z_to_y(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=-90, v=RIGHT_VEC)(obj)

def rot_x_to_y(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=90, v=UP_VEC)(obj)

def rot_x_to_neg_y(obj:OpenSCADObject) -> OpenSCADObject:
    return rotate(a=-90, v=UP_VEC)(obj)

# =======
# = Arc =
# =======
def arc(rad:float, start_degrees:float, end_degrees:float, segments:int=None) -> OpenSCADObject:
    # Note: the circle that this arc is drawn from gets segments,
    # not the arc itself.  That means a quarter-circle arc will
    # have segments/4 segments.

    bottom_half_square = back(rad)(square([3 * rad, 2 * rad], center=True))
    top_half_square = forward(rad)(square([3 * rad, 2 * rad], center=True))

    start_shape = circle(rad, segments=segments)

    if abs((end_degrees - start_degrees) % 360) <= 180:
        end_angle = end_degrees - 180
        ret = difference()(
            start_shape,
            rotate(a=start_degrees)(bottom_half_square.copy()),
            rotate(a=end_angle)(bottom_half_square.copy())
        )
    else:
        ret = intersection()(
            start_shape,
            union()(
                rotate(a=start_degrees)(top_half_square.copy()),
                rotate(a=end_degrees)(bottom_half_square.copy())
            )
        )

    return ret

def arc_inverted(rad:float, start_degrees:float, end_degrees:float, segments:int=None) -> OpenSCADObject:
    # Return the segment of an arc *outside* the circle of radius rad,
    # bounded by two tangents to the circle.  This is the shape
    # needed for fillets.

    # Note: the circle that this arc is drawn from gets segments,
    # not the arc itself.  That means a quarter-circle arc will
    # have segments/4 segments.

    # Leave the portion of a circumscribed square of sides
    # 2*rad that is NOT in the arc behind.  This is most useful for 90-degree
    # segments, since it's what you'll add to create fillets and take away
    # to create rounds.

    # NOTE: an inverted arc is only valid for end_degrees-start_degrees <= 180.
    # If this isn't true, end_degrees and start_degrees will be swapped so
    # that an acute angle can be found.  end_degrees-start_degrees == 180
    # will yield a long rectangle of width 2*radius, since the tangent lines
    # will be parallel and never meet.

    # Fix start/end degrees as needed; find a way to make an acute angle
    if end_degrees < start_degrees:
        end_degrees += 360

    if end_degrees - start_degrees >= 180:
        start_degrees, end_degrees = end_degrees, start_degrees

    # We want the area bounded by:
    # -- the circle from start_degrees to end_degrees
    # -- line tangent to the circle at start_degrees
    # -- line tangent to the circle at end_degrees
    # Note that this shape is only valid if end_degrees - start_degrees < 180,
    # since if the two angles differ by more than 180 degrees,
    # the tangent lines don't converge
    if end_degrees - start_degrees == 180:
        raise ValueError("Unable to draw inverted arc over 180 or more "
                         "degrees. start_degrees: %s end_degrees: %s"
                         % (start_degrees, end_degrees))

    wide = 1000
    high = 1000

    top_half_square = translate((-(wide - rad), 0, 0))(square([wide, high], center=False))
    bottom_half_square = translate((-(wide - rad), -high, 0))(square([wide, high], center=False))

    a = rotate(start_degrees)(top_half_square)
    b = rotate(end_degrees)(bottom_half_square)

    ret = (a * b) - circle(rad, segments=segments)

    return ret

# TODO: arc_to that creates an arc from point to another point.
# This is useful for making paths.  See the SVG path command:
# See: http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes

# ======================
# = Bounding Box Class =
# ======================
class BoundingBox(object):
    # A basic Bounding Box representation to enable some more introspection about
    # objects.  For instance, a BB will let us say "put this new object on top of
    # that old one".  Bounding Boxes *can't* be relied on for boolean operations
    # without compiling in OpenSCAD, so they're limited, but good for some purposes.
    # Be careful to understand what things this BB implementation can and
    # can't do -ETJ 15 Oct 2013

    # Basically you can use a BoundingBox to describe the extents of an object
    # the moment it's created, but once you perform any CSG operation on it, it's
    # more or less useless.
    def __init__(self, size:List[float], loc: List[float]=None):
        loc = loc if loc else [0, 0, 0]
        # self.w, self.h, self.d = size
        # self.x, self.y, self.z = loc
        self.set_size(size)
        self.set_position(loc)

    def size(self) -> List[float]:
        return [self.w, self.h, self.d]

    def position(self) -> List[float]:
        return [self.x, self.y, self.z]

    def set_position(self, position: Sequence[float]):
        self.x, self.y, self.z = position

    def set_size(self, size:Sequence[float]):
        self.w, self.h, self.d = size

    def split_planar(self, 
                     cutting_plane_normal: Vec3=RIGHT_VEC, 
                     cut_proportion: float=0.5, 
                     add_wall_thickness:float=0) -> List['BoundingBox']:
        cpd = {RIGHT_VEC: 0, LEFT_VEC: 0, FORWARD_VEC: 1,
               BACK_VEC: 1, UP_VEC: 2, DOWN_VEC: 2}
        cutting_plane = cpd.get(cutting_plane_normal, 2)

        # Figure what  the cutting plane offset should be
        dim_center = self.position()[cutting_plane]
        dim = self.size()[cutting_plane]
        dim_min = dim_center - dim / 2
        dim_max = dim_center + dim / 2
        cut_point = (cut_proportion) * dim_min + (1 - cut_proportion) * dim_max

        # Now create bounding boxes with the appropriate sizes
        part_bbs = []
        a_sum = 0.0
        for i, part in enumerate([cut_proportion, (1 - cut_proportion)]):
            part_size = self.size()
            part_size[cutting_plane] = part_size[cutting_plane] * part

            part_loc = self.position()
            part_loc[cutting_plane] = dim_min + a_sum + dim * (part / 2)

            # If extra walls are requested around the slices, add them here
            if add_wall_thickness != 0:
                # Expand the walls as requested
                for j in [X, Y, Z]:
                    part_size[j] += 2 * add_wall_thickness
                # Don't expand in the direction of the cutting_plane, only away
                # from it
                part_size[cutting_plane] -= add_wall_thickness

                # add +/- add_wall_thickness/2 to the location in the
                # slicing dimension so we stay at the center of the piece
                loc_offset = -add_wall_thickness / 2 + i * add_wall_thickness
                part_loc[cutting_plane] += loc_offset

            part_bbs.append(BoundingBox(part_size, part_loc))

            a_sum += part * dim

        return part_bbs

    def cube(self, larger: bool=False) -> OpenSCADObject:
        c_size = self.size() if not larger else [s + 2 * EPSILON for s in self.size()]
        c = translate(self.position())(
            cube(c_size, center=True)
        )
        return c

# ===================
# = Model Splitting =
# ===================
def split_body_planar(obj: OpenSCADObject, 
                      obj_bb: BoundingBox, 
                      cutting_plane_normal: Vec3=UP_VEC, 
                      cut_proportion: float=0.5, 
                      dowel_holes: bool=False, 
                      dowel_rad: float=4.5, 
                      hole_depth: float=15, 
                      add_wall_thickness=0) -> Tuple[OpenSCADObject, BoundingBox, OpenSCADObject, BoundingBox]:
    # Split obj along the specified plane, returning two pieces and
    # general bounding boxes for each.
    # Note that the bounding boxes are NOT accurate to the sections,
    # they just indicate which portion of the original BB is in each
    # section.  Given the limits of OpenSCAD, this is the best we can do 
    # -ETJ 17 Oct 2013

    # Optionally, leave holes in both bodies to allow the pieces to be put
    # back together with short dowels.

    # Find the splitting bounding boxes
    part_bbs = obj_bb.split_planar(
        cutting_plane_normal, cut_proportion, add_wall_thickness=add_wall_thickness)

    # And intersect the bounding boxes with the object itself
    slices = [obj * part_bb.cube() for part_bb in part_bbs]

    # Make holes for dowels if requested.
    # In case the bodies need to be aligned properly, make two holes,
    # separated by one dowel-width
    if dowel_holes:
        cpd = {RIGHT_VEC: 0, LEFT_VEC: 0, FORWARD_VEC: 1,
               BACK_VEC: 1, UP_VEC: 2, DOWN_VEC: 2}
        cutting_plane = cpd.get(cutting_plane_normal, 2)

        dowel = cylinder(r=dowel_rad, h=hole_depth * 2, center=True)
        # rotate dowels to correct axis
        if cutting_plane != 2:
            rot_vec = RIGHT_VEC if cutting_plane == 1 else FORWARD_VEC
            dowel = rotate(a=90, v=rot_vec)(dowel)

        cut_point = part_bbs[
            0].position()[cutting_plane] + part_bbs[0].size()[cutting_plane] / 2

        # Move dowels away from center of face by 2*dowel_rad in each
        # appropriate direction
        dowel_trans_a = part_bbs[0].position()
        dowel_trans_a[cutting_plane] = cut_point
        separation_index = {0: 1, 1: 2, 2: 0}[cutting_plane]
        dowel_trans_a[separation_index] -= 2 * dowel_rad
        dowel_trans_b = dowel_trans_a[:]
        dowel_trans_b[separation_index] += 4 * dowel_rad

        dowel_a = translate(dowel_trans_a)(dowel)
        dowel_b = translate(dowel_trans_b)(dowel)

        dowels = dowel_a + dowel_b
        # subtract dowels from each slice
        slices = [s - dowels for s in slices]

    slices_and_bbs = (slices[0], part_bbs[0], slices[1], part_bbs[1])
    return slices_and_bbs

def section_cut_xz(body: OpenSCADObject, y_cut_point:float=0) -> OpenSCADObject:
    big_w = 10000
    d = 2
    c = forward(d / 2 + y_cut_point)(cube([big_w, d, big_w], center=True))
    return c * body

# =====================
# = Bill of Materials =
# =====================
# Any part defined in a method can be automatically counted using the
# `@bom_part()` decorator. After all parts have been created, call
# `bill_of_materials()`
# to generate a report.  See `examples/bom_scad.py` for usage
#
# Additional columns can be added (such as leftover material or URL to part)
# by calling `set_bom_headers()` with a series of string arguments. 
#
# Calling `bom_part()` with additional, non-keyworded arguments will 
# populate the new columns in order of their addition via bom_headers, or 
# keyworded arguments can be used in any order.

g_parts_dict = {}
g_bom_headers: List[str] = []

def set_bom_headers(*args):
    global g_bom_headers
    g_bom_headers += args

def bom_part(description: str='', per_unit_price:float=None, currency: str='US$', *args, **kwargs) -> Callable:
    def wrap(f):
        name = description if description else f.__name__

        elements = {}
        elements.update({'Count':0, 'currency':currency, 'Unit Price':per_unit_price})
        # This update also adds empty key value pairs to prevent key exceptions.
        elements.update(dict(zip_longest(g_bom_headers, args, fillvalue='')))
        elements.update(kwargs)

        g_parts_dict[name] = elements

        def wrapped_f(*wargs, **wkwargs):
            name = description if description else f.__name__
            g_parts_dict[name]['Count'] += 1
            return f(*wargs, **wkwargs)

        return wrapped_f

    return wrap

def bill_of_materials(csv:bool=False) -> str:
    field_names = ["Description", "Count", "Unit Price", "Total Price"]
    field_names += g_bom_headers
    
    rows = []
    
    all_costs: Dict[str, float] = {}
    for desc, elements in g_parts_dict.items():
        count = elements['Count']
        currency = elements['currency']
        price = elements['Unit Price']

        if count > 0:
            if price:
                total = price * count
                if currency not in all_costs:
                    all_costs[currency] = 0 
                
                all_costs[currency] += total
                unit_price = _currency_str(price, currency)
                total_price = _currency_str(total, currency)
            else:
                unit_price = total_price = ""
            row = [desc, count, unit_price, total_price]

        for key in g_bom_headers:
            value = elements[key]
            row.append(value)
        rows.append(row)

    # Add total costs if we have values to add
    if len(all_costs) > 0:
        empty_row = [""] * len(field_names)
        rows.append(empty_row)
        for currency, cost in all_costs.items():
            row = empty_row[:]
            row[0] = "Total Cost, {currency:>4}".format(**vars())
            row[3] = "{currency:>4} {cost:.2f}".format(**vars())
            
            rows.append(row)

    res = _table_string(field_names, rows, csv)

    return res

def _currency_str(value:float, currency: str="$") -> str:
    return "{currency:>4} {value:.2f}".format(**vars())
    
def _table_string(field_names: Sequence[str], rows:Sequence[Sequence[float]], csv:bool=False) -> str:
    # Output a justified table string using the prettytable module.
    # Fall back to Excel-ready tab-separated values if prettytable's not found 
    # or CSV is requested
    if not csv:
        try:
            import prettytable
            table = prettytable.PrettyTable(field_names=field_names)
            for row in rows:
                table.add_row(row)
            res = table.get_string()
        except ImportError as e:
            print("Unable to import prettytable module.  Outputting in TSV format")
            csv = True
    if csv:
        lines = ["\t".join(field_names)]
        for row in rows:
            line = "\t".join([str(f) for f in row])
            lines.append(line)

        res = "\n".join(lines) 
        
    return res  + "\n"            

# ================
# = Bounding Box =
# ================
def bounding_box(points: Sequence[EucOrTuple]) -> Tuple[Tuple3, Tuple3]:
    all_x = []
    all_y = []
    all_z = []
    for p in points:
        all_x.append(p[0])
        all_y.append(p[1])
        if len(p) > 2:
            all_z.append(p[2]) # type:ignore 
        else:
            all_z.append(0)

    return ((min(all_x), min(all_y), min(all_z)), (max(all_x), max(all_y), max(all_z)))

# =======================
# = Hardware dimensions =
# =======================
screw_dimensions = {
    'm3': {'nut_thickness': 2.4, 'nut_inner_diam': 5.4, 'nut_outer_diam': 6.1, 'screw_outer_diam': 3.0, 'cap_diam': 5.5, 'cap_height': 3.0},
    'm4': {'nut_thickness': 3.1, 'nut_inner_diam': 7.0, 'nut_outer_diam': 7.9, 'screw_outer_diam': 4.0, 'cap_diam': 6.9, 'cap_height': 3.9},
    'm5': {'nut_thickness': 4.7, 'nut_inner_diam': 7.9, 'nut_outer_diam': 8.8, 'screw_outer_diam': 5.0, 'cap_diam': 8.7, 'cap_height': 5},
}
bearing_dimensions = {
    '608': {'inner_d':8, 'outer_d':22, 'thickness':7},
    '688': {'inner_d':8, 'outer_d':16, 'thickness':5},
    '686': {'inner_d':6, 'outer_d':13, 'thickness':5},
    '626': {'inner_d':6, 'outer_d':19, 'thickness':6},
    '625': {'inner_d':5, 'outer_d':16, 'thickness':5},
    '624': {'inner_d':4, 'outer_d':13, 'thickness':5},
    '623': {'inner_d':3, 'outer_d':10, 'thickness':4},
    '603': {'inner_d':3, 'outer_d':9,  'thickness':5},
    '633': {'inner_d':3, 'outer_d':13, 'thickness':5},
}

def screw(screw_type:str='m3', screw_length:float=16) -> OpenSCADObject:
    dims = screw_dimensions[screw_type.lower()]
    shaft_rad = dims['screw_outer_diam'] / 2
    cap_rad = dims['cap_diam'] / 2
    cap_height = dims['cap_height']

    ret = union()(
        cylinder(shaft_rad, screw_length + EPSILON),
        up(screw_length)(
            cylinder(cap_rad, cap_height)
        )
    )
    return ret

def nut(screw_type:str='m3') -> OpenSCADObject:
    dims = screw_dimensions[screw_type.lower()]
    outer_rad = dims['nut_outer_diam']
    inner_rad = dims['screw_outer_diam']

    ret = difference()(
        circle(outer_rad, segments=6),
        circle(inner_rad)
    )
    return ret

def bearing(bearing_type: str='624') -> OpenSCADObject:
    dims = bearing_dimensions[bearing_type.lower()]
    outerR = dims['outer_d']/2
    innerR = dims['inner_d']/2
    thickness = dims['thickness']
    bearing = cylinder(outerR,thickness)
    bearing.add_param('$fs', 1)
    hole = cylinder(innerR,thickness+2)
    hole.add_param('$fs', 1)
    bearing = difference()(
        bearing,
        translate([0,0,-1])(hole)
    )
    return bearing

# =========
# = LABEL =
# =========
def label(a_str:str, width:float=15, halign:str="left", valign:str="baseline", 
          size:int=10, depth:float=0.5, lineSpacing:float=1.15, 
          font:str="MgOpen Modata:style=Bold", segments:int=40, spacing:int=1) -> OpenSCADObject:
    """Renders a multi-line string into a single 3D object.
    
    __author__    = 'NerdFever.com'
    __copyright__ = 'Copyright 2018-2019 NerdFever.com'
    __version__   = ''
    __email__     = 'dave@nerdfever.com'
    __status__    = 'Development'
    __license__   = Copyright 2018-2019 NerdFever.com
    """

    lines = a_str.splitlines()

    texts = []

    for idx, l in enumerate(lines):
        t = text(text=l, halign=halign, valign=valign, font=font, spacing=spacing).add_param('$fn', segments)
        t = linear_extrude(height=1)(t)
        t = translate([0, -size * idx * lineSpacing, 0])(t)

        texts.append(t)

    result = union()(texts)
    result = resize([width, 0, depth])(result)
    result = translate([0, (len(lines)-1)*size / 2, 0])(result)

    return result

# ==================
# = PyEuclid Utils =
# ==================
def euclidify(an_obj:EucOrTuple, intended_class:type=Vector3) -> Union[Point23, Vector23, List[Union[Point23, Vector23]]]:
    '''
    Accept an object or list of objects of any relevant type (2-tuples, 3-tuples, Vector2/3, Point2/3)
    and return one or more euclid3 objects of intended_class. 

    # -- 3D input has its z-values dropped when intended_class is 2D
    # -- 2D input has its z-values set to 0 when intended_class is 3D

    The general idea is to take in data in whatever form is handy to users
    and return euclid3 types with vector math capabilities
    '''
    sequence = (list, tuple)
    euclidable = (list, tuple, Vector2, Vector3, Point2, Point3)
    numeric = (int, float)
    # If this is a list of lists, return a list of euclid objects
    if isinstance(an_obj, sequence) and isinstance(an_obj[0], euclidable):
        return list((_euc_obj(ao, intended_class) for ao in an_obj))
    elif isinstance(an_obj, euclidable):
        return _euc_obj(an_obj, intended_class)
    else:
        raise TypeError(f'''Object: {an_obj} ought to be PyEuclid class 
                        {intended_class.__name__} or able to form one, but is not.''')
    
def _euc_obj(an_obj: Any, intended_class:type=Vector3) -> Union[Point23, Vector23]:
    ''' Take a single object (not a list of them!) and return a euclid type
        # If given a euclid obj, return the desired type, 
        # -- 3d types are projected to z=0 when intended_class is 2D
        # -- 2D types are projected to z=0 when intended class is 3D
        _euc_obj( Vector3(0,1,2), Vector3) -> Vector3(0,1,2)
        _euc_obj( Vector3(0,1,2), Point3) -> Point3(0,1,2)
        _euc_obj( Vector2(0,1), Vector3) -> Vector3(0,1,0)
        _euc_obj( Vector2(0,1), Point3) -> Point3(0,1,0)
        _euc_obj( (0,1), Vector3) -> Vector3(0,1,0)
        _euc_obj( (0,1), Point3) -> Point3(0,1,0)
        _euc_obj( (0,1), Point2) -> Point2(0,1,0)
        _euc_obj( (0,1,2), Point2) -> Point2(0,1)
        _euc_obj( (0,1,2), Point3) -> Point3(0,1,2)
    '''
    elts_in_constructor = 3
    if intended_class in (Point2, Vector2):
        elts_in_constructor = 2
    result = intended_class(*an_obj[:elts_in_constructor])
    return result

def euc_to_arr(euc_obj_or_list: EucOrTuple) -> List[float]:  # Inverse of euclidify()
    # Call as_arr on euc_obj_or_list or on all its members if it's a list
    result: List[float] = []

    if hasattr(euc_obj_or_list, "as_arr"):
        result = euc_obj_or_list.as_arr()   # type: ignore
    elif isinstance(euc_obj_or_list, (list, tuple)) and hasattr(euc_obj_or_list[0], 'as_arr'):
        result = [euc_to_arr(p) for p in euc_obj_or_list] # type: ignore
    else:
        # euc_obj_or_list is neither an array-based PyEuclid object,
        # nor a list of them.  Assume it's a list of points or vectors,
        # and return the list unchanged.  We could be wrong about this,
        # though.
        result = euc_obj_or_list # type: ignore
    return result

def project_to_2D(euc_obj:Union[Point23, Vector23]) -> Union[Vector2, Point2]:
    """
    Given a Point3/Vector3, return a Point2/Vector2 ignoring the original Z coordinate
    """
    result:Union[Vector2, Point2] = None
    if isinstance(euc_obj, (Point2, Vector2)):
        result = euc_obj
    elif isinstance(euc_obj, Point3):
        result = Point2(euc_obj.x, euc_obj.y)
    elif isinstance(euc_obj, Vector3):
        result = Vector2(euc_obj.x, euc_obj.y)
    else:
        raise ValueError(f"Can't transform object {euc_obj} to a Point2 or Vector2")

    return result

def is_scad(obj:OpenSCADObject) -> bool:
    return isinstance(obj, OpenSCADObject)

def scad_matrix(euclid_matrix4):
    a = euclid_matrix4
    return [[a.a, a.b, a.c, a.d],
            [a.e, a.f, a.g, a.h],
            [a.i, a.j, a.k, a.l],
            [a.m, a.n, a.o, a.p]
            ]

# ==============
# = Transforms =
# ==============
def transform_to_point( body: OpenSCADObject, 
                        dest_point: Point3, 
                        dest_normal: Vector3, 
                        src_point: Point3=Point3(0, 0, 0), 
                        src_normal: Vector3=Vector3(0, 1, 0), 
                        src_up: Vector3=Vector3(0, 0, 1)) -> OpenSCADObject:
    # Transform body to dest_point, looking at dest_normal.
    # Orientation & offset can be changed by supplying the src arguments

    # Body may be:
    #   -- an openSCAD object
    #   -- a list of 3-tuples  or PyEuclid Point3s
    #   -- a single 3-tuple or Point3
    dest_point = euclidify(dest_point, Point3)
    dest_normal = euclidify(dest_normal, Vector3)
    at = dest_point + dest_normal

    EUC_UP = euclidify(UP_VEC)
    EUC_FORWARD = euclidify(FORWARD_VEC)
    EUC_ORIGIN = euclidify(ORIGIN, Vector3)
    # if dest_normal and src_up are parallel, the transform collapses
    # all points to dest_point.  Instead, use EUC_FORWARD if needed
    if dest_normal.cross(src_up) == EUC_ORIGIN:
        if src_up.cross(EUC_UP) == EUC_ORIGIN:
            src_up = EUC_FORWARD
        else:
            src_up = EUC_UP
            
    def _orig_euclid_look_at(eye, at, up):
        '''
        Taken from the original source of PyEuclid's Matrix4.new_look_at() 
        prior to 1184a07d119a62fc40b2c6becdbeaf053a699047 (11 Jan 2015), 
        as discussed here:
        https://github.com/ezag/pyeuclid/commit/1184a07d119a62fc40b2c6becdbeaf053a699047
    
        We were dependent on the old behavior, which is duplicated here:
        '''
        z = (eye - at).normalized()
        x = up.cross(z).normalized()
        y = z.cross(x)

        m = Matrix4.new_rotate_triple_axis(x, y, z)
        m.d, m.h, m.l = eye.x, eye.y, eye.z
        return m
            
    look_at_matrix = _orig_euclid_look_at(eye=dest_point, at=at, up=src_up)
    
    if is_scad(body):
        # If the body being altered is a SCAD object, do the matrix mult
        # in OpenSCAD
        sc_matrix = scad_matrix(look_at_matrix)
        res = multmatrix(m=sc_matrix)(body)
    else:
        body = euclidify(body, Point3)
        if isinstance(body, (list, tuple)):
            res = [look_at_matrix * p for p in body]
        else:
            res = look_at_matrix * body
    return res
    
# ========================================
# = Vector drawing: 3D arrow from a line =
# ========================================
def draw_segment(euc_line: Union[Vector3, Line3]=None, 
                 endless:bool=False, 
                 arrow_rad:float=7, 
                 vec_color: Union[str, Tuple3]=None) -> OpenSCADObject:
    # Draw a traditional arrow-head vector in 3-space.
    vec_arrow_rad = arrow_rad
    vec_arrow_head_rad = vec_arrow_rad * 1.5
    vec_arrow_head_length = vec_arrow_rad * 3

    if isinstance(euc_line, Vector3):
        p = Point3(*ORIGIN)
        v = euc_line
    elif isinstance(euc_line, Line3):
        p = euc_line.p
        v = -euc_line.v
    elif isinstance(euc_line, list) or isinstance(euc_line, tuple):
        # TODO: This assumes p & v are PyEuclid classes.
        # Really, they could as easily be two 3-tuples. Should
        # check for this.
        p, v = euc_line[0], euc_line[1]

    shaft_length = v.magnitude() - vec_arrow_head_length
    arrow = cylinder(r=vec_arrow_rad, h=shaft_length)
    arrow += up(shaft_length)(
        cylinder(r1=vec_arrow_head_rad, r2=0, h=vec_arrow_head_length)
    )
    if endless:
        endless_length = max(v.magnitude() * 10, 200)
        arrow += cylinder(r=vec_arrow_rad / 3,
                            h=endless_length, center=True)

    arrow = transform_to_point(body=arrow, dest_point=p, dest_normal=v)

    if vec_color:
        arrow = color(vec_color)(arrow)

    return arrow

# ==========
# = Offset =
# ==========
# TODO: Make a NamedTuple for LEFT_DIR and RIGHT_DIR
LEFT_DIR, RIGHT_DIR =  1,2

def offset_point(a:Point2, b:Point2, c:Point2, offset:float, direction:DirectionLR=LEFT_DIR) -> Point2:
    ab_perp = perpendicular_vector(b-a, direction, length=offset)
    bc_perp = perpendicular_vector(c-b, direction, length=offset)

    ab_par = Line2(a + ab_perp, b + ab_perp)
    bc_par = Line2(b + bc_perp, c + bc_perp)
    result = ab_par.intersect(bc_par)
    return result

def offset_points(points:Sequence[Point23], 
                  offset:float, 
                  internal:bool=True,
                  closed=True) -> List[Point2]:
    """
    Given a set of points, return a set of points offset by `offset`, in the
    direction specified by `internal`. 

    NOTE: OpenSCAD has the native `offset()` function that generates offset 
    polygons nicely as well as doing fillets & rounds. If you just need a shape,
    prefer using the native `offset()`.  If you need the actual points for some
    purpose, use this function.
    See: https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Transformations#offset

    # NOTE: We accept Point2s or Point3s, but ignore all Z values and return Point2s

    What is internal or external is defined by by the direction of curvature
    between the first and second points; for non-convex shapes, we will return
    an incorrect (internal points are all external, or vice versa) if the first
    segment pair is concave. This could be mitigated with a point_is_in_polygon()
    function, but I haven't written that yet.
    """
    # Note that we could just call offset_point() repeatedly, but we'd do 
    # a lot of repeated calculations that way
    src_points = euclidify(points, Point2)
    if closed:
        src_points.append(src_points[0])

    vecs = vectors_between_points(src_points)
    direction = direction_of_bend(*src_points[:3])
    if not internal:
        direction = opposite_direction(direction)

    perp_vecs = list((perpendicular_vector(v, direction=direction, length=offset) for v in vecs))

    lines: List[Line2] = []
    for perp, a, b in zip(perp_vecs, src_points[:-1], src_points[1:]):
        lines.append(Line2(a+perp, b+perp))
    
    intersections = list((a.intersect(b) for a,b in zip(lines[:-1], lines[1:])))
    if closed:
        # First point is determined by intersection of first and last lines
        intersections.insert(0, lines[0].intersect(lines[-1]))
    else:
        # otherwise use first and last points in lines
        intersections.insert(0, lines[0].p)
        intersections.append(lines[-1].p + lines[-1].v)
    return intersections

# ==================
# = Offset helpers =
# ==================

def pairwise_zip(l:Sequence) -> zip: # type:ignore
    return zip(l[:-1], l[1:])

def cross_2d(a:Vector2, b:Vector2) -> float:
    """
    scalar value; tells direction of rotation from a to b; 
    see direction_of_bend()
    # See http://www.allenchou.net/2013/07/cross-product-of-2d-vectors/
    """
    return a.x * b.y - a.y * b.x

def direction_of_bend(a:Point2, b:Point2, c:Point2) -> DirectionLR:
    """ 
    Return LEFT_DIR if angle abc is a turn to the left, otherwise RIGHT_DIR
    Returns RIGHT_DIR if ab and bc are colinear
    """
    direction = LEFT_DIR if cross_2d(b-a, c-b) > 0 else RIGHT_DIR
    return direction

def opposite_direction(direction:DirectionLR) -> DirectionLR:
    return LEFT_DIR if direction == RIGHT_DIR else RIGHT_DIR

def perpendicular_vector(v:Vector2, direction:DirectionLR=RIGHT_DIR, length:float=None) -> Vector2:
    perp_vec = Vector2(v.y, -v.x)
    result = perp_vec if direction == RIGHT_DIR else -perp_vec
    if length is not None:
        result.set_length(length)
    return result

def vectors_between_points(points: Sequence[Point23]) -> List[Vector23]:
    """
    Return a list of the vectors from each point in points to the point that follows
    """
    vecs = list((b-a for a,b in pairwise_zip(points))) # type:ignore
    return vecs

# =============
# = 2D Fillet =
# =============

def fillet_2d(three_point_sets: Sequence[Tuple[Point23, Point23, Point23]], 
              orig_poly: OpenSCADObject, 
              fillet_rad: float, 
              remove_material: bool=True) -> OpenSCADObject:
    """
    Return a polygon with arcs of radius `fillet_rad` added/removed (according to
    `remove_material`) to corners specified in `three_point_sets`. 

    e.g. Turn a sharp external corner to a rounded one, or add material
    to a sharp interior corner to smooth it out.
    """
    arc_objs: List[OpenSCADObject] = []
    # TODO: accept Point3s, and project them all to z==0
    for three_points in three_point_sets:
        a, b, c = (project_to_2D(p) for p in three_points)
        ab = a - b
        bc = b - c

        direction = direction_of_bend(a, b, c)

        # center lies at the intersection of two lines parallel to
        # ab and bc, respectively, each offset from their respective 
        # line by fillet_rad
        ab_perp = perpendicular_vector(ab, direction, length=fillet_rad)
        bc_perp = perpendicular_vector(bc, direction, length=fillet_rad)
        center = offset_point(a,b,c, offset=fillet_rad, direction=direction)
        # start_pt = center + ab_perp
        # end_pt = center + bc_perp

        start_degrees = degrees(atan2(ab_perp.y, ab_perp.x))
        end_degrees   = degrees(atan2(bc_perp.y, bc_perp.x))

        # Widen start_degrees and end_degrees slightly so they overlap the areas
        # they're supposed to join/ remove.
        start_degrees, end_degrees = _widen_angle_for_fillet(start_degrees, end_degrees)

        arc_obj = translate(center.as_arr())(
            arc_inverted(rad=fillet_rad, start_degrees=start_degrees, end_degrees=end_degrees)
        )
        arc_objs.append(arc_obj)

    if remove_material:
        poly = orig_poly - arc_objs 
    else:
        poly = orig_poly + arc_objs 

    return poly 

def _widen_angle_for_fillet(start_degrees:float, end_degrees:float) -> Tuple[float, float]:
    # Fix start/end degrees as needed; find a way to make an acute angle
    if end_degrees < start_degrees:
        end_degrees += 360

    if end_degrees - start_degrees >= 180:
        start_degrees, end_degrees = end_degrees, start_degrees

    epsilon_degrees = 0.1
    return start_degrees - epsilon_degrees, end_degrees + epsilon_degrees

# ==============
# = 2D DRAWING =
# ==============
def path_2d(points:Sequence[Point23], width:float=1, closed:bool=False) -> List[Point2]:
    '''
    Return a set of points describing a path of width `width` around `points`,
    suitable for use as a polygon().  

    Note that if `closed` is True, the polygon will have a hole in it, meaning
    that `polygon()` would need to specify its `paths` argument. Assuming 3 elements
    in the original `points` list, we'd have to call:
    path_points = path_2d(points, closed=True)
    poly = polygon(path_points, paths=[[0,1,2],[3,4,5]])

    Or, you know, just call `path_2d_polygon()` and let it do that for you
    '''
    p_a = offset_points(points, offset=width/2, internal=True, closed=closed)
    p_b = list(reversed(offset_points(points, offset=width/2, internal=False, closed=closed)))
    return p_a + p_b

def path_2d_polygon(points:Sequence[Point23], width:float=1, closed:bool=False) -> polygon:
    '''
    Return an OpenSCAD `polygon()` in an area `width` units wide around `points`
    '''
    path_points = path_2d(points, width, closed)
    paths = [list(range(len(path_points)))]
    if closed:
        paths = [list(range(len(points))), list(range(len(points), len(path_points)))]
    return polygon(path_points, paths=paths)

# ==========================
# = Extrusion along a path =
# ==========================
def extrude_along_path( shape_pts:Points, 
                        path_pts:Points, 
                        scale_factors:Sequence[float]=None) -> OpenSCADObject:
    # Extrude the convex curve defined by shape_pts along path_pts.
    # -- For predictable results, shape_pts must be planar, convex, and lie
    # in the XY plane centered around the origin.
    #
    # -- len(scale_factors) should equal len(path_pts).  If not present, scale
    #       will be assumed to be 1.0 for each point in path_pts
    # -- Future additions might include corner styles (sharp, flattened, round)
    #       or a twist factor
    polyhedron_pts:Points= []
    facet_indices:List[Tuple[int, int, int]] = []

    if not scale_factors:
        scale_factors = [1.0] * len(path_pts)

    # Make sure we've got Euclid Point3's for all elements
    shape_pts = euclidify(shape_pts, Point3)
    path_pts = euclidify(path_pts, Point3)

    src_up = Vector3(*UP_VEC)

    for which_loop in range(len(path_pts)):
        path_pt = path_pts[which_loop]
        scale = float(scale_factors[which_loop])

        # calculate the tangent to the curve at this point
        if which_loop > 0 and which_loop < len(path_pts) - 1:
            prev_pt = path_pts[which_loop - 1]
            next_pt = path_pts[which_loop + 1]

            v_prev = path_pt - prev_pt
            v_next = next_pt - path_pt
            tangent = v_prev + v_next
        elif which_loop == 0:
            tangent = path_pts[which_loop + 1] - path_pt
        elif which_loop == len(path_pts) - 1:
            tangent = path_pt - path_pts[which_loop - 1]

        # Scale points
        this_loop:Point3 = []
        if scale != 1.0:
            this_loop = [(scale * sh) for sh in shape_pts]
            # Convert this_loop back to points; scaling changes them to Vectors
            this_loop = [Point3(v.x, v.y, v.z) for v in this_loop]
        else:
            this_loop = shape_pts[:] # type: ignore

        # Rotate & translate
        this_loop = transform_to_point(this_loop, dest_point=path_pt, 
                                        dest_normal=tangent, src_up=src_up)

        # Add the transformed points to our final list
        polyhedron_pts += this_loop
        # And calculate the facet indices
        shape_pt_count = len(shape_pts)
        segment_start = which_loop * shape_pt_count
        segment_end = segment_start + shape_pt_count - 1
        if which_loop < len(path_pts) - 1:
            for i in range(segment_start, segment_end):
                facet_indices.append( (i, i + shape_pt_count, i + 1) )
                facet_indices.append( (i + 1, i + shape_pt_count, i + shape_pt_count + 1) )
            facet_indices.append( (segment_start, segment_end, segment_end + shape_pt_count) )
            facet_indices.append( (segment_start, segment_end + shape_pt_count, segment_start + shape_pt_count) )

    # Cap the start of the polyhedron
    for i in range(1, shape_pt_count - 1):
        facet_indices.append((0, i, i + 1))

    # And the end (could be rolled into the earlier loop)
    # FIXME: concave cross-sections will cause this end-capping algorithm
    # to fail
    end_cap_base = len(polyhedron_pts) - shape_pt_count
    for i in range(end_cap_base + 1, len(polyhedron_pts) - 1):
        facet_indices.append( (end_cap_base, i + 1, i) )

    return polyhedron(points=euc_to_arr(polyhedron_pts), faces=facet_indices) # type: ignore

def frange(*args):
    """
    # {{{ http://code.activestate.com/recipes/577068/ (r1)
    frange([start, ] end [, step [, mode]]) -> generator

    A float range generator. If not specified, the default start is 0.0
    and the default step is 1.0.

    Optional argument mode sets whether frange outputs an open or closed
    interval. mode must be an int. Bit zero of mode controls whether start is
    included (on) or excluded (off); bit one does the same for end. Hence:

        0 -> open interval (start and end both excluded)
        1 -> half-open (start included, end excluded)
        2 -> half open (start excluded, end included)
        3 -> closed (start and end both included)

    By default, mode=1 and only start is included in the output.
    """
    mode = 1  # Default mode is half-open.
    n = len(args)
    if n == 1:
        args = (0.0, args[0], 1.0)
    elif n == 2:
        args = args + (1.0,)
    elif n == 4:
        mode = args[3]
        args = args[0:3]
    elif n != 3:
        raise TypeError('frange expects 1-4 arguments, got %d' % n)
    assert len(args) == 3
    try:
        start, end, step = [a + 0.0 for a in args]
    except TypeError:
        raise TypeError('arguments must be numbers')
    if step == 0.0:
        raise ValueError('step must not be zero')
    if not isinstance(mode, int):
        raise TypeError('mode must be an int')
    if mode & 1:
        i, x = 0, start
    else:
        i, x = 1, start + step
    if step > 0:
        if mode & 2:
            from operator import le as comp
        else:
            from operator import lt as comp
    else:
        if mode & 2:
            from operator import ge as comp
        else:
            from operator import gt as comp
    while comp(x, end):
        yield x
        i += 1
        x = start + i * step

# =====================
# = D e b u g g i n g =
# =====================
def obj_tree_str(sp_obj:OpenSCADObject, vars_to_print:Sequence[str]=None) -> str:
    # For debugging.  This prints a string of all of an object's
    # children, with whatever attributes are specified in vars_to_print

    # Takes an optional list (vars_to_print) of variable names to include in each
    # element (e.g. ['is_part_root', 'is_hole', 'name'])
    if not vars_to_print:
        vars_to_print = []

    # Signify if object has parent or not
    parent_sign = "\nL " if sp_obj.parent else "\n* "

    # Print object
    s = parent_sign + str(sp_obj) + "\t"

    # Extra desired fields
    for v in vars_to_print:
        if hasattr(sp_obj, v):
            s += "%s: %s\t" % (v, getattr(sp_obj, v))

    # Add all children
    for c in sp_obj.children:
        s += indent(obj_tree_str(c, vars_to_print)) # type: ignore

    return s
