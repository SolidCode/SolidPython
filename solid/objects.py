"""
Classes for OpenSCAD builtins
"""
from .solidpython import OpenSCADObject
from .solidpython import IncludedOpenSCADObject

class polygon(OpenSCADObject):
    '''
    Create a polygon with the specified points and paths.

    :param points: the list of points of the polygon
    :type points: sequence of 2 element sequences

    :param paths: Either a single vector, enumerating the point list, ie. the order to traverse the points, or, a vector of vectors, ie a list of point lists for each separate curve of the polygon. The latter is required if the polygon has holes. The parameter is optional and if omitted the points are assumed in order. (The 'pN' components of the *paths* vector are 0-indexed references to the elements of the *points* vector.)
    '''
    def __init__(self, points, paths=None):
        if not paths:
            paths = [list(range(len(points)))]
        OpenSCADObject.__init__(self, 'polygon',
                                {'points': points, 'paths': paths})


class circle(OpenSCADObject):
    '''
    Creates a circle at the origin of the coordinate system. The argument
    name is optional.

    :param r: This is the radius of the circle. Default value is 1.
    :type r: number

    :param d: This is the diameter of the circle. Default value is 1.
    :type d: number

    :param segments: Number of fragments in 360 degrees.
    :type segments: int
    '''
    def __init__(self, r=None, d=None, segments=None):
        OpenSCADObject.__init__(self, 'circle',
                                {'r': r, 'd': d, 'segments': segments})


class square(OpenSCADObject):
    '''
    Creates a square at the origin of the coordinate system. When center is
    True the square will be centered on the origin, otherwise it is created
    in the first quadrant. The argument names are optional if the arguments
    are given in the same order as specified in the parameters

    :param size: If a single number is given, the result will be a square with sides of that length. If a 2 value sequence is given, then the values will correspond to the lengths of the X and Y sides.  Default value is 1.
    :type size: number or 2 value sequence

    :param center: This determines the positioning of the object. If True, object is centered at (0,0). Otherwise, the square is placed in the positive quadrant with one corner at (0,0). Defaults to False.
    :type center: boolean
    '''
    def __init__(self, size=None, center=None):
        OpenSCADObject.__init__(self, 'square',
                                {'size': size, 'center': center})


class sphere(OpenSCADObject):
    '''
    Creates a sphere at the origin of the coordinate system. The argument
    name is optional.

    :param r: Radius of the sphere.
    :type r: number

    :param d: Diameter of the sphere.
    :type d: number

    :param segments: Resolution of the sphere
    :type segments: int
    '''
    def __init__(self, r=None, d=None, segments=None):
        OpenSCADObject.__init__(self, 'sphere',
                                {'r': r, 'd': d, 'segments': segments})


class cube(OpenSCADObject):
    '''
    Creates a cube at the origin of the coordinate system. When center is
    True the cube will be centered on the origin, otherwise it is created in
    the first octant. The argument names are optional if the arguments are
    given in the same order as specified in the parameters

    :param size: If a single number is given, the result will be a cube with sides of that length. If a 3 value sequence is given, then the values will correspond to the lengths of the X, Y, and Z sides. Default value is 1.
    :type size: number or 3 value sequence

    :param center: This determines the positioning of the object. If True, object is centered at (0,0,0). Otherwise, the cube is placed in the positive quadrant with one corner at (0,0,0). Defaults to False
    :type center: boolean
    '''
    def __init__(self, size=None, center=None):
        OpenSCADObject.__init__(self, 'cube',
                                {'size': size, 'center': center})


class cylinder(OpenSCADObject):
    '''
    Creates a cylinder or cone at the origin of the coordinate system. A
    single radius (r) makes a cylinder, two different radi (r1, r2) make a
    cone.

    :param h: This is the height of the cylinder. Default value is 1.
    :type h: number

    :param r: The radius of both top and bottom ends of the cylinder. Use this parameter if you want plain cylinder. Default value is 1.
    :type r: number

    :param r1: This is the radius of the cone on bottom end. Default value is 1.
    :type r1: number

    :param r2: This is the radius of the cone on top end. Default value is 1.
    :type r2: number

    :param d: The diameter of both top and bottom ends of the cylinder.  Use this parameter if you want plain cylinder. Default value is 1.
    :type d: number

    :param d1: This is the diameter of the cone on bottom end. Default value is 1.
    :type d1: number

    :param d2: This is the diameter of the cone on top end. Default value is 1.
    :type d2: number

    :param center: If True will center the height of the cone/cylinder around the origin. Default is False, placing the base of the cylinder or r1 radius of cone at the origin.
    :type center: boolean

    :param segments: The fixed number of fragments to use.
    :type segments: int
    '''
    def __init__(self, r=None, h=None, r1=None, r2=None, d=None, d1=None,
                 d2=None, center=None, segments=None):
        OpenSCADObject.__init__(self, 'cylinder',
                                {'r': r, 'h': h, 'r1': r1, 'r2': r2, 'd': d,
                                 'd1': d1, 'd2': d2, 'center': center,
                                 'segments': segments})


class polyhedron(OpenSCADObject):
    '''
    Create a polyhedron with a list of points and a list of faces. The point
    list is all the vertices of the shape, the faces list is how the points
    relate to the surfaces of the polyhedron.

    *note: if your version of OpenSCAD is lower than 2014.03 replace "faces"
    with "triangles" in the below examples*

    :param points: sequence of points or vertices (each a 3 number sequence).

    :param triangles: (*deprecated in version 2014.03, use faces*) vector of point triplets (each a 3 number sequence). Each number is the 0-indexed point number from the point vector.

    :param faces: (*introduced in version 2014.03*) vector of point n-tuples with n >= 3. Each number is the 0-indexed point number from the point vector.  That is, faces=[[0,1,4]] specifies a triangle made from the first, second, and fifth point listed in points. When referencing more than 3 points in a single tuple, the points must all be on the same plane.

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    '''
    def __init__(self, points, faces, convexity=None, triangles=None):
        OpenSCADObject.__init__(self, 'polyhedron',
                                {'points': points, 'faces': faces,
                                 'convexity': convexity,
                                 'triangles': triangles})


class union(OpenSCADObject):
    '''
    Creates a union of all its child nodes. This is the **sum** of all
    children.
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'union', {})


class intersection(OpenSCADObject):
    '''
    Creates the intersection of all child nodes. This keeps the
    **overlapping** portion
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'intersection', {})


class difference(OpenSCADObject):
    '''
    Subtracts the 2nd (and all further) child nodes from the first one.
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'difference', {})


class hole(OpenSCADObject):
    def __init__(self):
        OpenSCADObject.__init__(self, 'hole', {})
        self.set_hole(True)


class part(OpenSCADObject):
    def __init__(self):
        OpenSCADObject.__init__(self, 'part', {})
        self.set_part_root(True)


class translate(OpenSCADObject):
    '''
    Translates (moves) its child elements along the specified vector.

    :param v: X, Y and Z translation
    :type v: 3 value sequence
    '''
    def __init__(self, v=None):
        OpenSCADObject.__init__(self, 'translate', {'v': v})


class scale(OpenSCADObject):
    '''
    Scales its child elements using the specified vector.

    :param v: X, Y and Z scale factor
    :type v: 3 value sequence
    '''
    def __init__(self, v=None):
        OpenSCADObject.__init__(self, 'scale', {'v': v})


class rotate(OpenSCADObject):
    '''
    Rotates its child 'a' degrees about the origin of the coordinate system
    or around an arbitrary axis.

    :param a: degrees of rotation, or sequence for degrees of rotation in each of the X, Y and Z axis.
    :type a: number or 3 value sequence

    :param v: sequence specifying 0 or 1 to indicate which axis to rotate by 'a' degrees. Ignored if 'a' is a sequence.
    :type v: 3 value sequence
    '''
    def __init__(self, a=None, v=None):
        OpenSCADObject.__init__(self, 'rotate', {'a': a, 'v': v})


class mirror(OpenSCADObject):
    '''
    Mirrors the child element on a plane through the origin.

    :param v: the normal vector of a plane intersecting the origin through which to mirror the object.
    :type v: 3 number sequence

    '''
    def __init__(self, v):
        OpenSCADObject.__init__(self, 'mirror', {'v': v})


class resize(OpenSCADObject):
    '''
    Modify the size of the child object to match the given new size.

    :param newsize: X, Y and Z values
    :type newsize: 3 value sequence
    '''
    def __init__(self, newsize):
        OpenSCADObject.__init__(self, 'resize', {'newsize': newsize})


class multmatrix(OpenSCADObject):
    '''
    Multiplies the geometry of all child elements with the given 4x4
    transformation matrix.

    :param m: transformation matrix
    :type m: sequence of 4 sequences, each containing 4 numbers.
    '''
    def __init__(self, m):
        OpenSCADObject.__init__(self, 'multmatrix', {'m': m})


class color(OpenSCADObject):
    '''
    Displays the child elements using the specified RGB color + alpha value.
    This is only used for the F5 preview as CGAL and STL (F6) do not
    currently support color. The alpha value will default to 1.0 (opaque) if
    not specified.

    :param c: RGB color + alpha value.
    :type c: sequence of 3 or 4 numbers between 0 and 1
    '''
    def __init__(self, c):
        OpenSCADObject.__init__(self, 'color', {'c': c})


class minkowski(OpenSCADObject):
    '''
    Renders the `minkowski
    sum <http://www.cgal.org/Manual/latest/doc_html/cgal_manual/Minkowski_sum_3/Chapter_main.html>`__
    of child nodes.
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'minkowski', {})

class offset(OpenSCADObject):
    '''
    
    :param r: Amount to offset the polygon (rounded corners). When negative, 
        the polygon is offset inwards. The parameter r specifies the radius 
        that is used to generate rounded corners, using delta gives straight edges.
    :type r: number
    
    :param delta: Amount to offset the polygon (sharp corners). When negative, 
        the polygon is offset inwards. The parameter r specifies the radius 
        that is used to generate rounded corners, using delta gives straight edges.
    :type delta: number
    
    :param chamfer: When using the delta parameter, this flag defines if edges 
        should be chamfered (cut off with a straight line) or not (extended to 
        their intersection).
    :type chamfer: bool
    '''
    def __init__(self, r=None, delta=None, chamfer=False):
        if r:
            kwargs = {'r':r}
        elif delta:
            kwargs = {'delta':delta, 'chamfer':chamfer}
        else:
            raise ValueError("offset(): Must supply r or delta")
        OpenSCADObject.__init__(self, 'offset', kwargs)

class hull(OpenSCADObject):
    '''
    Renders the `convex
    hull <http://www.cgal.org/Manual/latest/doc_html/cgal_manual/Convex_hull_2/Chapter_main.html>`__
    of child nodes.
    '''
    def __init__(self):
        OpenSCADObject.__init__(self, 'hull', {})


class render(OpenSCADObject):
    '''
    Always calculate the CSG model for this tree (even in OpenCSG preview
    mode).

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    '''
    def __init__(self, convexity=None):
        OpenSCADObject.__init__(self, 'render', {'convexity': convexity})


class linear_extrude(OpenSCADObject):
    '''
    Linear Extrusion is a modeling operation that takes a 2D polygon as
    input and extends it in the third dimension. This way a 3D shape is
    created.

    :param height: the extrusion height.
    :type height: number

    :param center: determines if the object is centered on the Z-axis after extrusion.
    :type center: boolean

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int

    :param twist: Twist is the number of degrees of through which the shape is extruded.  Setting to 360 will extrude through one revolution.  The twist direction follows the left hand rule.
    :type twist: number

    :param slices: number of slices to extrude. Can be used to improve the output.
    :type slices: int

    :param scale: relative size of the top of the extrusion compared to the start
    :type scale: number

    '''
    def __init__(self, height=None, center=None, convexity=None, twist=None,
                 slices=None, scale=None):
        OpenSCADObject.__init__(self, 'linear_extrude',
                                {'height': height, 'center': center,
                                 'convexity': convexity, 'twist': twist,
                                 'slices': slices, 'scale':scale})


class rotate_extrude(OpenSCADObject):
    '''
    A rotational extrusion is a Linear Extrusion with a twist, literally.
    Unfortunately, it can not be used to produce a helix for screw threads
    as the 2D outline must be normal to the axis of rotation, ie they need
    to be flat in 2D space.

    The 2D shape needs to be either completely on the positive, or negative
    side (not recommended), of the X axis. It can touch the axis, i.e. zero,
    however if the shape crosses the X axis a warning will be shown in the
    console windows and the rotate\_extrude() will be ignored. If the shape
    is in the negative axis the faces will be inside-out, you probably don't
    want to do that; it may be fixed in the future.

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int

    :param segments: The fixed number of fragments to use.
    :type segments: int

    '''
    def __init__(self, convexity=None, segments=None):
        OpenSCADObject.__init__(self, 'rotate_extrude',
                                {'convexity': convexity, 'segments': segments})


class dxf_linear_extrude(OpenSCADObject):
    def __init__(self, file, layer=None, height=None, center=None,
                 convexity=None, twist=None, slices=None):
        OpenSCADObject.__init__(self, 'dxf_linear_extrude',
                                {'file': file, 'layer': layer,
                                 'height': height, 'center': center,
                                 'convexity': convexity, 'twist': twist,
                                 'slices': slices})


class projection(OpenSCADObject):
    '''
    Creates 2d shapes from 3d models, and export them to the dxf format.
    It works by projecting a 3D model to the (x,y) plane, with z at 0.

    :param cut: when True only points with z=0 will be considered (effectively cutting the object) When False points above and below the plane will be considered as well (creating a proper projection).
    :type cut: boolean
    '''
    def __init__(self, cut=None):
        OpenSCADObject.__init__(self, 'projection', {'cut': cut})


class surface(OpenSCADObject):
    '''
    Surface reads information from text or image files.

    :param file: The path to the file containing the heightmap data.
    :type file: string

    :param center: This determines the positioning of the generated object. If True, object is centered in X- and Y-axis. Otherwise, the object is placed in the positive quadrant. Defaults to False.
    :type center: boolean

    :param invert: Inverts how the color values of imported images are translated into height values. This has no effect when importing text data files. Defaults to False.
    :type invert: boolean

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    '''
    def __init__(self, file, center=None, convexity=None, invert=None):
        OpenSCADObject.__init__(self, 'surface',
                                {'file': file, 'center': center,
                                 'convexity': convexity, 'invert': invert})


class text(OpenSCADObject):
    '''
    Create text using fonts installed on the local system or provided as separate font file.

    :param text: The text to generate.
    :type text: string

    :param size: The generated text will have approximately an ascent of the given value (height above the baseline). Default is 10.  Note that specific fonts will vary somewhat and may not fill the size specified exactly, usually slightly smaller.
    :type size: number

    :param font: The name of the font that should be used. This is not the name of the font file, but the logical font name (internally handled by the fontconfig library). A list of installed fonts can be obtained using the font list dialog (Help -> Font List).
    :type font: string

    :param halign: The horizontal alignment for the text. Possible values are "left", "center" and "right". Default is "left".
    :type halign: string

    :param valign: The vertical alignment for the text. Possible values are "top", "center", "baseline" and "bottom". Default is "baseline".
    :type valign: string

    :param spacing: Factor to increase/decrease the character spacing.  The default value of 1 will result in the normal spacing for the font, giving a value greater than 1 will cause the letters to be spaced further apart.
    :type spacing: number

    :param direction: Direction of the text flow. Possible values are "ltr" (left-to-right), "rtl" (right-to-left), "ttb" (top-to-bottom) and "btt" (bottom-to-top). Default is "ltr".
    :type direction: string

    :param language: The language of the text. Default is "en".
    :type language: string

    :param script: The script of the text. Default is "latin".
    :type script: string

    :param segments: used for subdividing the curved path segments provided by freetype
    :type segments: int
    '''
    def __init__(self, text, size=None, font=None, halign=None, valign=None,
                 spacing=None, direction=None, language=None, script=None,
                 segments=None):
        OpenSCADObject.__init__(self, 'text',
                                {'text': text, 'size': size, 'font': font,
                                 'halign': halign, 'valign': valign,
                                 'spacing': spacing, 'direction': direction,
                                 'language': language, 'script': script,
                                 'segments': segments})


class child(OpenSCADObject):
    def __init__(self, index=None, vector=None, range=None):
        OpenSCADObject.__init__(self, 'child',
                                {'index': index, 'vector': vector,
                                 'range': range})


class children(OpenSCADObject):
    '''
    The child nodes of the module instantiation can be accessed using the
    children() statement within the module. The number of module children
    can be accessed using the $children variable.

    :param index: select one child, at index value. Index start at 0 and should be less than or equal to $children-1.
    :type index: int

    :param vector: select children with index in vector. Index should be between 0 and $children-1.
    :type vector: sequence of int

    :param range: [:] or [::]. select children between to , incremented by (default 1).
    '''
    def __init__(self, index=None, vector=None, range=None):
        OpenSCADObject.__init__(self, 'children',
                                {'index': index, 'vector': vector,
                                 'range': range})


class import_stl(OpenSCADObject):
    def __init__(self, file, origin=(0, 0), layer=None):
        OpenSCADObject.__init__(self, 'import',
                                {'file': file, 'origin': origin,
                                 'layer': layer})


class import_dxf(OpenSCADObject):
    def __init__(self, file, origin=(0, 0), layer=None):
        OpenSCADObject.__init__(self, 'import',
                                {'file': file, 'origin': origin,
                                 'layer': layer})


class import_(OpenSCADObject):
    '''
    Imports a file for use in the current OpenSCAD model. OpenSCAD currently
    supports import of DXF and STL (both ASCII and Binary) files.

    :param file: path to the STL or DXF file.
    :type file: string

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    '''
    def __init__(self, file, origin=(0, 0), layer=None):
        OpenSCADObject.__init__(self, 'import',
                                {'file': file, 'origin': origin,
                                 'layer': layer})


class intersection_for(OpenSCADObject):
    '''
    Iterate over the values in a vector or range and take an
    intersection of the contents.
    '''
    def __init__(self, n):
        OpenSCADObject.__init__(self, 'intersection_for', {'n': n})


class assign(OpenSCADObject):
    def __init__(self):
        OpenSCADObject.__init__(self, 'assign', {})

# ================================
# = Modifier Convenience Methods =
# ================================
def debug(openscad_obj):
    openscad_obj.set_modifier("#")
    return openscad_obj


def background(openscad_obj):
    openscad_obj.set_modifier("%")
    return openscad_obj


def root(openscad_obj):
    openscad_obj.set_modifier("!")
    return openscad_obj


def disable(openscad_obj):
    openscad_obj.set_modifier("*")
    return openscad_obj


# ===============
# = Including OpenSCAD code =
# ===============

# use() & include() mimic OpenSCAD's use/include mechanics.
# -- use() makes methods in scad_file_path.scad available to
#   be called.
# --include() makes those methods available AND executes all code in
#   scad_file_path.scad, which may have side effects.
#   Unless you have a specific need, call use().
def use(scad_file_path, use_not_include=True):
    '''
    Opens scad_file_path, parses it for all usable calls,
    and adds them to caller's namespace.
    '''
    # These functions in solidpython are used here and only here; don't pollute
    # the global namespace with them
    from .solidpython import extract_callable_signatures
    from .solidpython import new_openscad_class_str 
    from .solidpython import calling_module    
    
    try:
        with open(scad_file_path) as module:
            contents = module.read()
    except Exception as e:
        raise Exception("Failed to import SCAD module '%(scad_file_path)s' "
                        "with error: %(e)s " % vars())

    # Once we have a list of all callables and arguments, dynamically
    # add OpenSCADObject subclasses for all callables to the calling module's
    # namespace.
    symbols_dicts = extract_callable_signatures(scad_file_path)

    for sd in symbols_dicts:
        class_str = new_openscad_class_str(sd['name'], sd['args'], sd['kwargs'], 
                                            scad_file_path, use_not_include)
        # If this is called from 'include', we have to look deeper in the stack
        # to find the right module to add the new class to.
        stack_depth = 2 if use_not_include else 3
        exec(class_str, calling_module(stack_depth).__dict__)

    return True


def include(scad_file_path):
    return use(scad_file_path, use_not_include=False)
