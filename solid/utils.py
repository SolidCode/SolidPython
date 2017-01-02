#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import sys
import itertools
if sys.version[0]=='2':
    from itertools import izip_longest as zip_longest
else:
    from itertools import zip_longest

from solid import *
from math import *



RIGHT, TOP, LEFT, BOTTOM = range(4)
EPSILON = 0.01
TAU = 2 * pi

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

# ========================
# = Degrees <==> Radians =
# ========================


def degrees(x_radians):
    return 360.0 * x_radians / TAU


def radians(x_degrees):
    return x_degrees / 360.0 * TAU


# ==============
# = Grid Plane =
# ==============
def grid_plane(grid_unit=12, count=10, line_weight=0.1, plane='xz'):

    # Draws a grid of thin lines in the specified plane.  Helpful for
    # reference during debugging.
    l = count * grid_unit
    t = union()
    t.set_modifier('background')
    for i in range(-count / 2, count / 2 + 1):
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


def distribute_in_grid(objects, max_bounding_box, rows_and_cols=None):
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
    elif isinstance(max_bounding_box, (int, long, float, complex)):
        x_trans = y_trans = max_bounding_box
    else:
        pass  # TypeError

    # If we only got passed one object, just return it
    try:
        l = len(objects)
    except:
        return objects

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
                    translate([x * x_trans, y * y_trans])(objects[objs_placed]))
                objs_placed += 1
            else:
                break
    return union()(ret)

# ==============
# = Directions =
# ==============


def up(z):
    return translate([0, 0, z])


def down(z):
    return translate([0, 0, -z])


def right(x):
    return translate([x, 0, 0])


def left(x):
    return translate([-x, 0, 0])


def forward(y):
    return translate([0, y, 0])


def back(y):
    return translate([0, -y, 0])


# ===========================
# = Box-alignment rotations =
# ===========================
def rot_z_to_up(obj):
    # NOTE: Null op
    return rotate(a=0, v=FORWARD_VEC)(obj)


def rot_z_to_down(obj):
    return rotate(a=180, v=FORWARD_VEC)(obj)


def rot_z_to_right(obj):
    return rotate(a=90, v=FORWARD_VEC)(obj)


def rot_z_to_left(obj):
    return rotate(a=-90, v=FORWARD_VEC)(obj)


def rot_z_to_forward(obj):
    return rotate(a=-90, v=RIGHT_VEC)(obj)


def rot_z_to_back(obj):
    return rotate(a=90, v=RIGHT_VEC)(obj)


# ================================
# = Box-aligment and translation =
# ================================
def box_align(obj, direction_func=up, distance=0):
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


def rot_z_to_x(obj):
    return rotate(a=90, v=FORWARD_VEC)(obj)


def rot_z_to_neg_x(obj):
    return rotate(a=-90, v=FORWARD_VEC)(obj)


def rot_z_to_neg_y(obj):
    return rotate(a=90, v=RIGHT_VEC)(obj)


def rot_z_to_y(obj):
    return rotate(a=-90, v=RIGHT_VEC)(obj)


def rot_x_to_y(obj):
    return rotate(a=90, v=UP_VEC)(obj)


def rot_x_to_neg_y(obj):
    return rotate(a=-90, v=UP_VEC)(obj)

# =======
# = Arc =
# =======


def arc(rad, start_degrees, end_degrees, segments=None):
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


def arc_inverted(rad, start_degrees, end_degrees, segments=None):
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

    top_half_square = translate([-(wide - rad), 0])(square([wide, high], center=False))
    bottom_half_square = translate([-(wide - rad), -high])(square([wide, high], center=False))

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
    def __init__(self, size, loc=None):
        loc = loc if loc else [0, 0, 0]
        # self.w, self.h, self.d = size
        # self.x, self.y, self.z = loc
        self.set_size(size)
        self.set_position(loc)

    def size(self):
        return [self.w, self.h, self.d]

    def position(self):
        return [self.x, self.y, self.z]

    def set_position(self, position):
        self.x, self.y, self.z = position

    def set_size(self, size):
        self.w, self.h, self.d = size

    def split_planar(self, cutting_plane_normal=RIGHT_VEC, cut_proportion=0.5, add_wall_thickness=0):
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
        a_sum = 0
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

    def cube(self, larger=False):
        c_size = self.size() if not larger else [s + 2 * EPSILON for s in self.size()]
        c = translate(self.position())(
            cube(c_size, center=True)
        )
        return c

    def min(self, which_dim=None):
        min_pt = [p - s / 2 for p, s in zip(self.position(), self.size())]
        if which_dim:
            return min_pt[which_dim]
        else:
            return min_pt

    def max(self, which_dim=None):
        max_pt = [p + s / 2 for p, s in zip(self.position(), self.size())]
        if which_dim:
            return max_pt[which_dim]
        else:
            return max_pt


# ===================
# = Model Splitting =
# ===================
def split_body_planar(obj, obj_bb, cutting_plane_normal=UP_VEC, cut_proportion=0.5, dowel_holes=False, dowel_rad=4.5, hole_depth=15, add_wall_thickness=0):
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

    slices_and_bbs = [slices[0], part_bbs[0], slices[1], part_bbs[1]]
    return slices_and_bbs


def section_cut_xz(body, y_cut_point=0):
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
g_bom_headers = []

def set_bom_headers(*args):
    global g_bom_headers
    g_bom_headers += args

def bom_part(description='', per_unit_price=None, currency='US$', *args, **kwargs):
    def wrap(f):
        name = description if description else f.__name__

        elements = {}
        elements.update({'Count':0, 'currency':currency, 'Unit Price':per_unit_price})
        # This update also adds empty key value pairs to prevent key exceptions.
        elements.update(dict(zip_longest(g_bom_headers, args, fillvalue='')))
        elements.update(kwargs)

        g_parts_dict[name] = elements

        def wrapped_f(*wargs):
            name = description if description else f.__name__
            g_parts_dict[name]['Count'] += 1
            return f(*wargs)

        return wrapped_f

    return wrap

def bill_of_materials(csv=False):
    field_names = ["Description", "Count", "Unit Price", "Total Price"]
    field_names += g_bom_headers
    
    rows = []
    
    all_costs = {}
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

def _currency_str(value, currency="$"):
    return "{currency:>4} {value:.2f}".format(**vars())
    
def _table_string(field_names, rows, csv=False):
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


def bounding_box(points):
    all_x = []
    all_y = []
    all_z = []
    for p in points:
        all_x.append(p[0])
        all_y.append(p[1])
        if len(p) > 2:
            all_z.append(p[2])
        else:
            all_z.append(0)

    return [[min(all_x), min(all_y), min(all_z)], [max(all_x), max(all_y), max(all_z)]]


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

def screw(screw_type='m3', screw_length=16):
    dims = screw_dimensions[screw_type.lower()]
    shaft_rad = dims['screw_outer_diam'] / 2
    cap_rad = dims['cap_diam'] / 2
    cap_height = dims['cap_height']

    ret = union()(
        cylinder(shaft_rad, screw_length),
        up(screw_length)(
            cylinder(cap_rad, cap_height)
        )
    )
    return ret

def nut(screw_type='m3'):
    dims = screw_dimensions[screw_type.lower()]
    outer_rad = dims['nut_outer_diam']
    inner_rad = dims['screw_outer_diam']

    ret = difference()(
        circle(outer_rad, segments=6),
        circle(inner_rad)
    )
    return ret

def bearing(bearing_type='624'):
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

# ==================
# = PyEuclid Utils =
# = -------------- =
try:
    import euclid3
    from euclid3 import *
    # NOTE: The PyEuclid on PyPi doesn't include several elements added to
    # the module as of 13 Feb 2013.  Add them here until euclid supports them
    # TODO: when euclid updates, remove this cruft. -ETJ 13 Feb 2013
    import solid.patch_euclid
    solid.patch_euclid.run_patch()

    def euclidify(an_obj, intended_class=Vector3):
        # If an_obj is an instance of the appropriate PyEuclid class,
        # return it.  Otherwise, try to turn an_obj into the appropriate
        # class and throw an exception on failure

        # Since we often want to convert an entire array
        # of objects (points, etc.) accept arrays of arrays

        ret = an_obj

        # See if this is an array of arrays.  If so, convert all sublists
        if isinstance(an_obj, (list, tuple)):
            if isinstance(an_obj[0], (list, tuple)):
                ret = [intended_class(*p) for p in an_obj]
            elif isinstance(an_obj[0], intended_class):
                # this array is already euclidified; return it
                ret = an_obj
            else:
                try:
                    ret = intended_class(*an_obj)
                except:
                    raise TypeError("Object: %s ought to be PyEuclid class %s or "
                                    "able to form one, but is not."
                                     % (an_obj, intended_class.__name__))
        elif not isinstance(an_obj, intended_class):
            try:
                ret = intended_class(*an_obj)
            except:
                raise TypeError("Object: %s ought to be PyEuclid class %s or "
                                "able to form one, but is not." 
                                % (an_obj, intended_class.__name__))
        return ret

    def euc_to_arr(euc_obj_or_list):  # Inverse of euclidify()
        # Call as_arr on euc_obj_or_list or on all its members if it's a list
        if hasattr(euc_obj_or_list, "as_arr"):
            return euc_obj_or_list.as_arr()
        elif isinstance(euc_obj_or_list, (list, tuple)) and hasattr(euc_obj_or_list[0], 'as_arr'):
            return [euc_to_arr(p) for p in euc_obj_or_list]
        else:
            # euc_obj_or_list is neither an array-based PyEuclid object,
            # nor a list of them.  Assume it's a list of points or vectors,
            # and return the list unchanged.  We could be wrong about this,
            # though.
            return euc_obj_or_list

    def is_scad(obj):
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
    def transform_to_point(body, dest_point, dest_normal, src_point=Point3(0, 0, 0), src_normal=Vector3(0, 1, 0), src_up=Vector3(0, 0, 1)):
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
    # = -------------- =======================
    def draw_segment(euc_line=None, endless=False, arrow_rad=7, vec_color=None):
        # Draw a tradtional arrow-head vector in 3-space.
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
    # = ------ =
    LEFT, RIGHT = radians(90), radians(-90)

    def offset_points(point_arr, offset, inside=True, closed_poly=True):
        # Given a set of points, return a set of points offset from
        # them.
        # To get reasonable results, the points need to be all in a plane.
        # (Non-planar point_arr will still return results, but what constitutes
        # 'inside' or 'outside' would be different in that situation.)
        #
        # What direction inside and outside lie in is determined by the first
        # three points (first corner).  In a convex closed shape, this corresponds
        # to inside and outside.  If the first three points describe a concave
        # portion of a closed shape, inside and outside will be switched.
        #
        # Basically this means that if you're offsetting a complicated shape,
        # you'll likely have to try both directions (inside=True/False) to
        # figure out which direction you're offsetting to.
        #
        # CAD programs generally require an interactive user choice about which
        # side is outside and which is inside.  Robust behavior with this
        # function will require similar checking.

        # Also note that short segments or narrow areas can cause problems
        # as well.  This method suffices for most planar convex figures where
        # segment length is greater than offset, but changing any of those
        # assumptions will cause unattractive results.  If you want real
        # offsets, use SolidWorks.

        # TODO: check for self-intersections in the line connecting the
        # offset points, and remove them.

        # Using the first three points in point_arr, figure out which direction
        # is inside and what plane to put the points in
        point_arr = euclidify(point_arr[:], Point3)
        in_dir = _inside_direction(*point_arr[0:3])
        normal = _three_point_normal(*point_arr[0:3])
        direction = in_dir if inside else _other_dir(in_dir)

        # Generate offset points for the correct direction
        # for all of point_arr.
        segs = []
        offset_pts = []
        point_arr += point_arr[0:2]  # Add first two points to the end as well
        if closed_poly:
            for i in range(len(point_arr) - 1):
                a, b = point_arr[i:i + 2]
                par_seg = _parallel_seg(a, b, normal=normal, offset=offset, direction=direction)
                segs.append(par_seg)
                if len(segs) > 1:
                    int_pt = segs[-2].intersect(segs[-1])
                    if int_pt:
                        offset_pts.append(int_pt)

            # When calculating based on a closed curve, we can't find the
            # first offset point until all others have been calculated.
            # Now that we've done so, put the last point back to first place
            last = offset_pts[-1]
            offset_pts.insert(0, last)
            del(offset_pts[-1])

        else:
            for i in range(len(point_arr) - 2):
                a, b = point_arr[i:i + 2]
                par_seg = _parallel_seg(a, b, normal=normal, offset=offset, direction=direction)
                segs.append(par_seg)
                # In an open poly, first and last points will be parallel
                # to the first and last segments, not intersecting other segs
                if i == 0:
                    offset_pts.append(par_seg.p1)
                elif i == len(point_arr) - 3:
                    offset_pts.append(segs[-2].p2)
                else:
                    int_pt = segs[-2].intersect(segs[-1])
                    if int_pt:
                        offset_pts.append(int_pt)

        return offset_pts

    # ==================
    # = Offset helpers =
    # ==================
    def _parallel_seg(p, q, offset, normal=Vector3(0, 0, 1), direction=LEFT):
        # returns a PyEuclid Line3 parallel to pq, in the plane determined
        # by p,normal, to the left or right of pq.
        v = q - p
        angle = direction

        rot_v = v.rotate_around(axis=normal, theta=angle)
        rot_v.set_length(offset)
        return Line3(p + rot_v, v)

    def _inside_direction(a, b, c, offset=10):
        # determines which direction (LEFT, RIGHT) is 'inside' the triangle
        # made by a, b, c.  If ab and bc are parallel, return LEFT
        x = _three_point_normal(a, b, c)

        # Make two vectors (left & right) for each segment.
        l_segs = [_parallel_seg(p, q, normal=x, offset=offset, direction=LEFT) for p, q in ((a, b), (b, c))]
        r_segs = [_parallel_seg(p, q, normal=x, offset=offset, direction=RIGHT) for p, q in ((a, b), (b, c))]

        # Find their intersections.
        p1 = l_segs[0].intersect(l_segs[1])
        p2 = r_segs[0].intersect(r_segs[1])

        # The only way I've figured out to determine which direction is
        # 'inside' or 'outside' a joint is to calculate both inner and outer
        # vectors and then to find the intersection point closest to point a.
        # This ought to work but it seems like there ought to be a more direct
        # way to figure this out. -ETJ 21 Dec 2012

        # The point that's closer to point a is the inside point.
        if a.distance(p1) <= a.distance(p2):
            return LEFT
        else:
            return RIGHT

    def _other_dir(left_or_right):
        if left_or_right == LEFT:
            return RIGHT
        else:
            return LEFT

    def _three_point_normal(a, b, c):
        ab = b - a
        bc = c - b

        seg_ab = Line3(a, ab)
        seg_bc = Line3(b, bc)
        x = seg_ab.v.cross(seg_bc.v)
        return x

    # =============
    # = 2D Fillet =
    # =============
    def _widen_angle_for_fillet(start_degrees, end_degrees):
        # Fix start/end degrees as needed; find a way to make an acute angle
        if end_degrees < start_degrees:
            end_degrees += 360

        if end_degrees - start_degrees >= 180:
            start_degrees, end_degrees = end_degrees, start_degrees

        epsilon_degrees = 2
        return start_degrees - epsilon_degrees, end_degrees + epsilon_degrees

    def fillet_2d(three_point_sets, orig_poly, fillet_rad, remove_material=True):
        # NOTE: three_point_sets must be a list of sets of three points
        # (i.e., a list of 3-tuples of points), even if only one fillet is being done:
        # e.g.  [[a, b, c]]
        # a, b, and c are three points that form a corner at b.
        # Return a negative arc (the area NOT covered by a circle) of radius rad
        # in the direction of the more acute angle between

        # Note that if rad is greater than a.distance(b) or c.distance(b), for a
        # 90-degree corner, the returned shape will include a jagged edge.

        # TODO: use fillet_rad = min(fillet_rad, a.distance(b), c.distance(b))

        # If a shape is being filleted in several places, it is FAR faster
        # to add/ remove its set of shapes all at once rather than
        # to cycle through all the points, since each method call requires
        # a relatively complex boolean with the original polygon.
        # So... three_point_sets is either a list of three Euclid points that
        # determine the corner to be filleted, OR, a list of those lists, in
        # which case everything will be removed / added at once.
        # NOTE that if material is being added (fillets) or removed (rounds)
        # each must be called separately.

        if len(three_point_sets) == 3 and isinstance(three_point_sets[0], (Vector2, Vector3)):
            three_point_sets = [three_point_sets]

        arc_objs = []
        for three_points in three_point_sets:

            assert len(three_points) in (2, 3)
            # make two vectors out of the three points passed in
            a, b, c = euclidify(three_points, Point3)

            # Find the center of the arc we'll have to make
            offset = offset_points([a, b, c], offset=fillet_rad, inside=True)
            center_pt = offset[1]

            a2, b2, c2, cp2 = [Point2(p.x, p.y) for p in (a, b, c, center_pt)]

            a2b2 = LineSegment2(a2, b2)
            c2b2 = LineSegment2(c2, b2)

            # Find the point on each segment where the arc starts; Point2.connect()
            # returns a segment with two points; Take the one that's not the
            # center
            afs = cp2.connect(a2b2)
            cfs = cp2.connect(c2b2)

            afp, cfp = [
                seg.p1 if seg.p1 != cp2 else seg.p2 for seg in (afs, cfs)]

            a_degs, c_degs = [
                (degrees(math.atan2(seg.v.y, seg.v.x))) % 360 for seg in (afs, cfs)]

            start_degs = a_degs
            end_degs = c_degs

            # Widen start_degs and end_degs slightly so they overlap the areas
            # they're supposed to join/ remove.
            start_degs, end_degs = _widen_angle_for_fillet(start_degs, end_degs)

            arc_obj = translate(center_pt.as_arr())(
                arc_inverted(
                    rad=fillet_rad, start_degrees=start_degs, end_degrees=end_degs)
            )

            arc_objs.append(arc_obj)

        if remove_material:
            poly = orig_poly - arc_objs
        else:
            poly = orig_poly + arc_objs

        return poly

    # ==========================
    # = Extrusion along a path =
    # = ---------------------- =
    # Possible: twist
    def extrude_along_path(shape_pts, path_pts, scale_factors=None):
        # Extrude the convex curve defined by shape_pts along path_pts.
        # -- For predictable results, shape_pts must be planar, convex, and lie
        # in the XY plane centered around the origin.
        #
        # -- len(scale_factors) should equal len(path_pts).  If not present, scale
        #       will be assumed to be 1.0 for each point in path_pts
        # -- Future additions might include corner styles (sharp, flattened, round)
        #       or a twist factor
        polyhedron_pts = []
        facet_indices = []

        if not scale_factors:
            scale_factors = [1.0] * len(path_pts)

        # Make sure we've got Euclid Point3's for all elements
        shape_pts = euclidify(shape_pts, Point3)
        path_pts = euclidify(path_pts, Point3)

        src_up = Vector3(*UP_VEC)

        for which_loop in range(len(path_pts)):
            path_pt = path_pts[which_loop]
            scale = scale_factors[which_loop]

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
            if scale != 1.0:
                this_loop = [(scale * sh) for sh in shape_pts]
                # Convert this_loop back to points; scaling changes them to
                # Vectors
                this_loop = [Point3(v.x, v.y, v.z) for v in this_loop]
            else:
                this_loop = shape_pts[:]

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
                    facet_indices.append([i, i + shape_pt_count, i + 1])
                    facet_indices.append([i + 1, i + shape_pt_count, i + shape_pt_count + 1])
                facet_indices.append([segment_start, segment_end, segment_end + shape_pt_count])
                facet_indices.append([segment_start, segment_end + shape_pt_count, segment_start + shape_pt_count])

        # Cap the start of the polyhedron
        for i in range(1, shape_pt_count - 1):
            facet_indices.append([0, i, i + 1])

        # And the end (could be rolled into the earlier loop)
        # FIXME: concave cross-sections will cause this end-capping algorithm
        # to fail
        end_cap_base = len(polyhedron_pts) - shape_pt_count
        for i in range(end_cap_base + 1, len(polyhedron_pts) - 1):
            facet_indices.append([end_cap_base, i + 1, i])

        return polyhedron(points=euc_to_arr(polyhedron_pts), faces=facet_indices)


except Exception as e:
    # euclid isn't available; these methods won't be either
    print("\n\nUnable to load euclid library. Skipping euclid-based tests "
            "with exception: \n%s\n" % e)

# {{{ http://code.activestate.com/recipes/577068/ (r1)


def frange(*args):
    """frange([start, ] end [, step [, mode]]) -> generator

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

# end of http://code.activestate.com/recipes/577068/ }}}

# =====================
# = D e b u g g i n g =
# =====================


def obj_tree_str(sp_obj, vars_to_print=None):
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
        s += indent(obj_tree_str(c, vars_to_print))

    return s
