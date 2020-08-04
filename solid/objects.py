"""
Classes for OpenSCAD builtins
"""
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Optional, Sequence, Tuple, Union, List

from .solidpython import OpenSCADObject

PathStr = Union[Path, str]

P2 = Tuple[float, float]
P3 = Tuple[float, float, float]
P4 = Tuple[float, float, float, float]
Vec3 = P3
Vec4 = P4
Vec34 = Union[Vec3, Vec4]
P3s = Sequence[P3]
P23 = Union[P2, P3]
Points = Sequence[P23]
Indexes = Union[Sequence[int], Sequence[Sequence[int]]]
ScadSize = Union[int, Sequence[float]]
OpenSCADObjectPlus = Union[OpenSCADObject, Sequence[OpenSCADObject]]

def _to_point2s(points:Points) -> List[P2]:
    return list([(p[0], p[1]) for p in points])


class polygon(OpenSCADObject):
    """
    Create a polygon with the specified points and paths.

    :param points: the list of points of the polygon
    :type points: sequence of 2 element sequences

    :param paths: Either a single vector, enumerating the point list, ie. the 
    order to traverse the points, or, a vector of vectors, ie a list of point 
    lists for each separate curve of the polygon. The latter is required if the 
    polygon has holes. The parameter is optional and if omitted the points are 
    assumed in order. (The 'pN' components of the *paths* vector are 0-indexed 
    references to the elements of the *points* vector.)

    NOTE: OpenSCAD accepts only 2D points for `polygon()`. Convert any 3D points
    to 2D before compiling
    """

    def __init__(self, points: Points, paths: Indexes = None) -> None:
        if not paths:
            paths = [list(range(len(points)))]
        super().__init__('polygon',
                         {'points': _to_point2s(points), 'paths': paths})


class circle(OpenSCADObject):
    """
    Creates a circle at the origin of the coordinate system. The argument
    name is optional.

    :param r: This is the radius of the circle. Default value is 1.
    :type r: number

    :param d: This is the diameter of the circle. Default value is 1.
    :type d: number

    :param segments: Number of fragments in 360 degrees.
    :type segments: int
    """

    def __init__(self, r: float = None, d: float = None, segments: int = None) -> None:
        super().__init__('circle',
                         {'r': r, 'd': d, 'segments': segments})


class square(OpenSCADObject):
    """
    Creates a square at the origin of the coordinate system. When center is
    True the square will be centered on the origin, otherwise it is created
    in the first quadrant. The argument names are optional if the arguments
    are given in the same order as specified in the parameters

    :param size: If a single number is given, the result will be a square with 
    sides of that length. If a 2 value sequence is given, then the values will 
    correspond to the lengths of the X and Y sides.  Default value is 1.
    :type size: number or 2 value sequence

    :param center: This determines the positioning of the object. If True, 
    object is centered at (0,0). Otherwise, the square is placed in the positive 
    quadrant with one corner at (0,0). Defaults to False.
    :type center: boolean
    """

    def __init__(self, size: ScadSize = None, center: bool = None) -> None:
        super().__init__('square',
                         {'size': size, 'center': center})


class sphere(OpenSCADObject):
    """
    Creates a sphere at the origin of the coordinate system. The argument
    name is optional.

    :param r: Radius of the sphere.
    :type r: number

    :param d: Diameter of the sphere.
    :type d: number

    :param segments: Resolution of the sphere
    :type segments: int
    """

    def __init__(self, r: float = None, d: float = None, segments: int = None) -> None:
        super().__init__('sphere',
                         {'r': r, 'd': d, 'segments': segments})


class cube(OpenSCADObject):
    """
    Creates a cube at the origin of the coordinate system. When center is
    True the cube will be centered on the origin, otherwise it is created in
    the first octant. The argument names are optional if the arguments are
    given in the same order as specified in the parameters

    :param size: If a single number is given, the result will be a cube with 
    sides of that length. If a 3 value sequence is given, then the values will 
    correspond to the lengths of the X, Y, and Z sides. Default value is 1.
    :type size: number or 3 value sequence

    :param center: This determines the positioning of the object. If True, 
    object is centered at (0,0,0). Otherwise, the cube is placed in the positive 
    quadrant with one corner at (0,0,0). Defaults to False
    :type center: boolean
    """

    def __init__(self, size: ScadSize = None, center: bool = None) -> None:
        super().__init__('cube',
                         {'size': size, 'center': center})


class cylinder(OpenSCADObject):
    """
    Creates a cylinder or cone at the origin of the coordinate system. A
    single radius (r) makes a cylinder, two different radii (r1, r2) make a
    cone.

    :param h: This is the height of the cylinder. Default value is 1.
    :type h: number

    :param r: The radius of both top and bottom ends of the cylinder. Use this 
    parameter if you want plain cylinder. Default value is 1.
    :type r: number

    :param r1: This is the radius of the cone on bottom end. Default value is 1.
    :type r1: number

    :param r2: This is the radius of the cone on top end. Default value is 1.
    :type r2: number

    :param d: The diameter of both top and bottom ends of the cylinder.  Use t
    his parameter if you want plain cylinder. Default value is 1.
    :type d: number

    :param d1: This is the diameter of the cone on bottom end. Default value is 1.
    :type d1: number

    :param d2: This is the diameter of the cone on top end. Default value is 1.
    :type d2: number

    :param center: If True will center the height of the cone/cylinder around 
    the origin. Default is False, placing the base of the cylinder or r1 radius 
    of cone at the origin.
    :type center: boolean

    :param segments: Number of fragments in 360 degrees.
    :type segments: int
    """

    def __init__(self, r: float = None, h: float = None, r1: float = None, r2: float = None,
                 d: float = None, d1: float = None, d2: float = None, center: bool = None,
                 segments: int = None) -> None:
        super().__init__('cylinder',
                         {'r': r, 'h': h, 'r1': r1, 'r2': r2, 'd': d,
                          'd1': d1, 'd2': d2, 'center': center,
                          'segments': segments})


class polyhedron(OpenSCADObject):
    """
    Create a polyhedron with a list of points and a list of faces. The point
    list is all the vertices of the shape, the faces list is how the points
    relate to the surfaces of the polyhedron.

    *note: if your version of OpenSCAD is lower than 2014.03 replace "faces"
    with "triangles" in the below examples*

    :param points: sequence of points or vertices (each a 3 number sequence).

    :param triangles: (*deprecated in version 2014.03, use faces*) vector of 
    point triplets (each a 3 number sequence). Each number is the 0-indexed point 
    number from the point vector.

    :param faces: (*introduced in version 2014.03*) vector of point n-tuples 
    with n >= 3. Each number is the 0-indexed point number from the point vector.  
    That is, faces=[[0,1,4]] specifies a triangle made from the first, second, 
    and fifth point listed in points. When referencing more than 3 points in a 
    single tuple, the points must all be on the same plane.

    :param convexity: The convexity parameter specifies the maximum number of 
    front sides (back sides) a ray intersecting the object might penetrate. This 
    parameter is only needed for correctly displaying the object in OpenCSG 
    preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    """

    def __init__(self, points: P3s, faces: Indexes, convexity: int = None, triangles: Indexes = None) -> None:
        super().__init__('polyhedron',
                         {'points': points, 'faces': faces,
                          'convexity': convexity,
                          'triangles': triangles})


class union(OpenSCADObject):
    """
    Creates a union of all its child nodes. This is the **sum** of all
    children.
    """

    def __init__(self) -> None:
        super().__init__('union', {})

    def __add__(self, x: OpenSCADObjectPlus) -> OpenSCADObject:
        new_union = union()
        for child in self.children:
            new_union.add(child)
        new_union.add(x)

        return new_union


class intersection(OpenSCADObject):
    """
    Creates the intersection of all child nodes. This keeps the
    **overlapping** portion
    """

    def __init__(self) -> None:
        super().__init__('intersection', {})

    def __mul__(self, x: OpenSCADObjectPlus) -> OpenSCADObject:
        new_int = intersection()
        for child in self.children:
            new_int.add(child)
        new_int.add(x)

        return new_int


class difference(OpenSCADObject):
    """
    Subtracts the 2nd (and all further) child nodes from the first one.
    """

    def __init__(self) -> None:
        super().__init__('difference', {})

    def __sub__(self, x: OpenSCADObjectPlus) -> OpenSCADObject:
        new_diff = difference()
        for child in self.children:
            new_diff.add(child)
        new_diff.add(x)

        return new_diff


class hole(OpenSCADObject):
    def __init__(self) -> None:
        super().__init__('hole', {})
        self.set_hole(is_hole=True)


class part(OpenSCADObject):
    def __init__(self) -> None:
        super().__init__('part', {})
        self.set_part_root(is_root=True)


class translate(OpenSCADObject):
    """
    Translates (moves) its child elements along the specified vector.

    :param v: X, Y and Z translation
    :type v: 3 value sequence
    """

    def __init__(self, v: P3 = None) -> None:
        super().__init__('translate', {'v': v})


class scale(OpenSCADObject):
    """
    Scales its child elements using the specified vector.

    :param v: X, Y and Z scale factor
    :type v: 3 value sequence
    """

    def __init__(self, v: P3 = None) -> None:
        super().__init__('scale', {'v': v})


class rotate(OpenSCADObject):
    """
    Rotates its child 'a' degrees about the origin of the coordinate system
    or around an arbitrary axis.

    :param a: degrees of rotation, or sequence for degrees of rotation in each of the X, Y and Z axis.
    :type a: number or 3 value sequence

    :param v: sequence specifying 0 or 1 to indicate which axis to rotate by 'a' degrees. Ignored if 'a' is a sequence.
    :type v: 3 value sequence
    """

    def __init__(self, a: Union[float, Vec3] = None, v: Vec3 = None) -> None:
        super().__init__('rotate', {'a': a, 'v': v})


class mirror(OpenSCADObject):
    """
    Mirrors the child element on a plane through the origin.

    :param v: the normal vector of a plane intersecting the origin through which to mirror the object.
    :type v: 3 number sequence

    """

    def __init__(self, v: Vec3) -> None:
        super().__init__('mirror', {'v': v})


class resize(OpenSCADObject):
    """
    Modify the size of the child object to match the given new size.

    :param newsize: X, Y and Z values
    :type newsize: 3 value sequence
    
    :param auto: 3-tuple of booleans to specify which axes should be scaled
    :type auto: 3 boolean sequence
    """

    def __init__(self, newsize: Vec3, auto: Tuple[bool, bool, bool] = None) -> None:
        super().__init__('resize', {'newsize': newsize, 'auto': auto})


class multmatrix(OpenSCADObject):
    """
    Multiplies the geometry of all child elements with the given 4x4
    transformation matrix.

    :param m: transformation matrix
    :type m: sequence of 4 sequences, each containing 4 numbers.
    """

    def __init__(self, m: Tuple[Vec4, Vec4, Vec4, Vec4]) -> None:
        super().__init__('multmatrix', {'m': m})


class color(OpenSCADObject):
    """
    Displays the child elements using the specified RGB color + alpha value.
    This is only used for the F5 preview as CGAL and STL (F6) do not
    currently support color. The alpha value will default to 1.0 (opaque) if
    not specified.

    :param c: RGB color + alpha value.
    :type c: sequence of 3 or 4 numbers between 0 and 1
    """

    def __init__(self, c: Vec34) -> None:
        super().__init__('color', {'c': c})


class minkowski(OpenSCADObject):
    """
    Renders the `minkowski
    sum <http://www.cgal.org/Manual/latest/doc_html/cgal_manual/Minkowski_sum_3/Chapter_main.html>`__
    of child nodes.
    """

    def __init__(self) -> None:
        super().__init__('minkowski', {})


class offset(OpenSCADObject):
    """
    
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

    :param segments: Resolution of any radial curves
    :type segments: int
    """

    def __init__(self, r: float = None, delta: float = None, chamfer: bool = False,
                segments: int=None) -> None:
        if r is not None:
            kwargs = {'r': r}
        elif delta is not None:
            kwargs = {'delta': delta, 'chamfer': chamfer}
        else:
            raise ValueError("offset(): Must supply r or delta")
        if segments:
            kwargs['segments'] = segments
        super().__init__('offset', kwargs)


class hull(OpenSCADObject):
    """
    Renders the `convex
    hull <http://www.cgal.org/Manual/latest/doc_html/cgal_manual/Convex_hull_2/Chapter_main.html>`__
    of child nodes.
    """

    def __init__(self) -> None:
        super().__init__('hull', {})


class render(OpenSCADObject):
    """
    Always calculate the CSG model for this tree (even in OpenCSG preview
    mode).

    :param convexity: The convexity parameter specifies the maximum number of front sides (back sides) a ray intersecting the object might penetrate. This parameter is only needed for correctly displaying the object in OpenCSG preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    """

    def __init__(self, convexity: int = None) -> None:
        super().__init__('render', {'convexity': convexity})


class linear_extrude(OpenSCADObject):
    """
    Linear Extrusion is a modeling operation that takes a 2D polygon as
    input and extends it in the third dimension. This way a 3D shape is
    created.

    :param height: the extrusion height.
    :type height: number

    :param center: determines if the object is centered on the Z-axis after extrusion.
    :type center: boolean

    :param convexity: The convexity parameter specifies the maximum number of 
    front sides (back sides) a ray intersecting the object might penetrate. This 
    parameter is only needed for correctly displaying the object in OpenCSG 
    preview mode and has no effect on the polyhedron rendering.
    :type convexity: int

    :param twist: Twist is the number of degrees of through which the shape is 
    extruded.  Setting to 360 will extrude through one revolution.  The twist 
    direction follows the left hand rule.
    :type twist: number

    :param slices: number of slices to extrude. Can be used to improve the output.
    :type slices: int

    :param scale: relative size of the top of the extrusion compared to the start
    :type scale: number

    """

    def __init__(self, height: float = None, center: bool = None, convexity: int = None,
                 twist: float = None, slices: int = None, scale: float = None) -> None:
        super().__init__('linear_extrude',
                         {'height': height, 'center': center,
                          'convexity': convexity, 'twist': twist,
                          'slices': slices, 'scale': scale})


class rotate_extrude(OpenSCADObject):
    """
    A rotational extrusion is a Linear Extrusion with a twist, literally.
    Unfortunately, it can not be used to produce a helix for screw threads
    as the 2D outline must be normal to the axis of rotation, ie they need
    to be flat in 2D space.

    The 2D shape needs to be either completely on the positive, or negative
    side (not recommended), of the X axis. It can touch the axis, i.e. zero,
    however if the shape crosses the X axis a warning will be shown in the
    console windows and the rotate/_extrude() will be ignored. If the shape
    is in the negative axis the faces will be inside-out, you probably don't
    want to do that; it may be fixed in the future.

    :param angle: Defaults to 360. Specifies the number of degrees to sweep, 
    starting at the positive X axis. The direction of the sweep follows the 
    Right Hand Rule, hence a negative angle will sweep clockwise.
    :type angle: number
    
    :param segments: Number of fragments in 360 degrees.
    :type segments: int

    :param convexity: The convexity parameter specifies the maximum number of 
    front sides (back sides) a ray intersecting the object might penetrate. This 
    parameter is only needed for correctly displaying the object in OpenCSG 
    preview mode and has no effect on the polyhedron rendering.
    :type convexity: int

    """

    def __init__(self, angle: float = 360, convexity: int = None, segments: int = None) -> None:
        super().__init__('rotate_extrude',
                         {'angle': angle, 'segments': segments,
                          'convexity': convexity})


class dxf_linear_extrude(OpenSCADObject):
    def __init__(self, file: PathStr, layer: float = None, height: float = None,
                 center: bool = None, convexity: int = None, twist: float = None,
                 slices: int = None) -> None:
        super().__init__('dxf_linear_extrude',
                         {'file': Path(file).as_posix(), 'layer': layer,
                          'height': height, 'center': center,
                          'convexity': convexity, 'twist': twist,
                          'slices': slices})


class projection(OpenSCADObject):
    """
    Creates 2d shapes from 3d models, and export them to the dxf format.
    It works by projecting a 3D model to the (x,y) plane, with z at 0.

    :param cut: when True only points with z=0 will be considered (effectively 
    cutting the object) When False points above and below the plane will be 
    considered as well (creating a proper projection).
    :type cut: boolean
    """

    def __init__(self, cut: bool = None) -> None:
        super().__init__('projection', {'cut': cut})


class surface(OpenSCADObject):
    """
    Surface reads information from text or image files.

    :param file: The path to the file containing the heightmap data.
    :type file: PathStr

    :param center: This determines the positioning of the generated object. If 
    True, object is centered in X- and Y-axis. Otherwise, the object is placed 
    in the positive quadrant. Defaults to False.
    :type center: boolean

    :param invert: Inverts how the color values of imported images are translated 
    into height values. This has no effect when importing text data files. 
    Defaults to False.
    :type invert: boolean

    :param convexity: The convexity parameter specifies the maximum number of 
    front sides (back sides) a ray intersecting the object might penetrate. 
    This parameter is only needed for correctly displaying the object in OpenCSG 
    preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    """

    def __init__(self, file, center: bool = None, convexity: int = None, invert=None) -> None:
        super().__init__('surface',
                         {'file': file, 'center': center,
                          'convexity': convexity, 'invert': invert})


class text(OpenSCADObject):
    """
    Create text using fonts installed on the local system or provided as separate 
    font file.

    :param text: The text to generate.
    :type text: string

    :param size: The generated text will have approximately an ascent of the given 
    value (height above the baseline). Default is 10.  Note that specific fonts 
    will vary somewhat and may not fill the size specified exactly, usually 
    slightly smaller.
    :type size: number

    :param font: The name of the font that should be used. This is not the name 
    of the font file, but the logical font name (internally handled by the 
    fontconfig library). A list of installed fonts can be obtained using the 
    font list dialog (Help -> Font List).
    :type font: string

    :param halign: The horizontal alignment for the text. Possible values are 
    "left", "center" and "right". Default is "left".
    :type halign: string

    :param valign: The vertical alignment for the text. Possible values are 
    "top", "center", "baseline" and "bottom". Default is "baseline".
    :type valign: string

    :param spacing: Factor to increase/decrease the character spacing.  The 
    default value of 1 will result in the normal spacing for the font, giving 
    a value greater than 1 will cause the letters to be spaced further apart.
    :type spacing: number

    :param direction: Direction of the text flow. Possible values are "ltr" 
    (left-to-right), "rtl" (right-to-left), "ttb" (top-to-bottom) and "btt" 
    (bottom-to-top). Default is "ltr".
    :type direction: string

    :param language: The language of the text. Default is "en".
    :type language: string

    :param script: The script of the text. Default is "latin".
    :type script: string

    :param segments: used for subdividing the curved path segments provided by 
    freetype
    :type segments: int
    """

    def __init__(self, text: str, size: float = None, font: str = None, halign: str = None,
                 valign: str = None, spacing: float = None, direction: str = None,
                 language: str = None, script: str = None, segments: int = None) -> None:
        super().__init__('text',
                         {'text': text, 'size': size, 'font': font,
                          'halign': halign, 'valign': valign,
                          'spacing': spacing, 'direction': direction,
                          'language': language, 'script': script,
                          'segments': segments})


class child(OpenSCADObject):
    def __init__(self, index: int = None, vector: Sequence[int] = None, range=None) -> None:
        super().__init__('child',
                         {'index': index, 'vector': vector,
                          'range': range})


class children(OpenSCADObject):
    """
    The child nodes of the module instantiation can be accessed using the
    children() statement within the module. The number of module children
    can be accessed using the $children variable.

    :param index: select one child, at index value. Index start at 0 and should 
    be less than or equal to $children-1.
    :type index: int

    :param vector: select children with index in vector. Index should be between 
    0 and $children-1.
    :type vector: sequence of int

    :param range: [:] or [::]. select children between to , incremented by (default 1).
    """

    def __init__(self, index: int = None, vector: float = None, range: P23 = None) -> None:
        super().__init__('children',
                         {'index': index, 'vector': vector,
                          'range': range})


class import_stl(OpenSCADObject):
    def __init__(self, file: PathStr, origin: P2 = (0, 0), convexity: int = None, layer: int = None) -> None:
        super().__init__('import',
                         {'file': Path(file).as_posix(), 'origin': origin,
                          'convexity': convexity, 'layer': layer})


class import_dxf(OpenSCADObject):
    def __init__(self, file, origin=(0, 0), convexity: int = None, layer: int = None) -> None:
        super().__init__('import',
                         {'file': file, 'origin': origin,
                          'convexity': convexity, 'layer': layer})


class import_(OpenSCADObject):
    """
    Imports a file for use in the current OpenSCAD model. OpenSCAD currently
    supports import of DXF and STL (both ASCII and Binary) files.

    :param file: path to the STL or DXF file.
    :type file: PathStr

    :param convexity: The convexity parameter specifies the maximum number of 
    front sides (back sides) a ray intersecting the object might penetrate. This 
    parameter is only needed for correctly displaying the object in OpenCSG 
    preview mode and has no effect on the polyhedron rendering.
    :type convexity: int
    """

    def __init__(self, file: PathStr, origin: P2 = (0, 0), convexity: int = None, layer: int = None) -> None:
        super().__init__('import',
                         {'file': Path(file).as_posix(), 'origin': origin,
                          'convexity': convexity, 'layer': layer})


class intersection_for(OpenSCADObject):
    """
    Iterate over the values in a vector or range and take an
    intersection of the contents.
    """

    def __init__(self, n: int) -> None:
        super().__init__('intersection_for', {'n': n})


class assign(OpenSCADObject):
    def __init__(self) -> None:
        super().__init__('assign', {})


# ================================
# = Modifier Convenience Methods =
# ================================
def debug(openscad_obj: OpenSCADObject) -> OpenSCADObject:
    openscad_obj.set_modifier("#")
    return openscad_obj


def background(openscad_obj: OpenSCADObject) -> OpenSCADObject:
    openscad_obj.set_modifier("%")
    return openscad_obj


def root(openscad_obj: OpenSCADObject) -> OpenSCADObject:
    openscad_obj.set_modifier("!")
    return openscad_obj


def disable(openscad_obj: OpenSCADObject) -> OpenSCADObject:
    openscad_obj.set_modifier("*")
    return openscad_obj


# ===========================
# = IMPORTING OPENSCAD CODE =
# ===========================
def import_scad(scad_file_or_dir: PathStr) -> SimpleNamespace:
    '''
    Recursively look in current directory & OpenSCAD library directories for
        OpenSCAD files. Create Python mappings for all OpenSCAD modules & functions
    Return a namespace or raise ValueError if no scad files found
    '''
    scad = Path(scad_file_or_dir)
    candidates: List[Path] = [scad]
    if not scad.is_absolute():
        candidates = [d/scad for d in _openscad_library_paths()]

    for candidate_path in candidates:
        namespace = _import_scad(candidate_path)
        if namespace is not None:
            return namespace
    raise ValueError(f'Could not find .scad files at or under {scad}. \nLocations searched were: {candidates}')

def _import_scad(scad: Path) -> Optional[SimpleNamespace]:
    '''
    cases:
        single scad file:
            return a namespace populated with `use()`
        directory
            recurse into all subdirectories and *.scad files
            return namespace if scad files are underneath, otherwise None
        non-scad file:
            return None            
    '''
    namespace: Optional[SimpleNamespace] = None
    if scad.is_file() and scad.suffix == '.scad':
        namespace = SimpleNamespace()
        use(scad.absolute(), dest_namespace_dict=namespace.__dict__)
    elif scad.is_dir():
        subspaces = [(f, _import_scad(f)) for f in scad.iterdir() if f.is_dir() or f.suffix == '.scad']
        for f, subspace in subspaces:
            if subspace:
                if namespace is None:
                    namespace = SimpleNamespace()
                # Add a subspace to namespace named by the file/dir it represents
                setattr(namespace, f.stem, subspace)

    return namespace
   
def _openscad_library_paths() -> List[Path]:
    """
    Return system-dependent OpenSCAD library paths or paths defined in os.environ['OPENSCADPATH']
    """
    import platform
    import os
    import re

    paths = [Path('.')]

    user_path = os.environ.get('OPENSCADPATH')
    if user_path:
        for s in re.split(r'\s*[;:]\s*', user_path):
            paths.append(Path(s))

    default_paths = {
        'Linux':   Path.home() / '.local/share/OpenSCAD/libraries',
        'Darwin':  Path.home() / 'Documents/OpenSCAD/libraries',
        'Windows': Path('My Documents\OpenSCAD\libraries')
    }

    paths.append(default_paths[platform.system()])
    return paths

def _find_library(library_name: PathStr) -> Path:
    result = Path(library_name)

    if not result.is_absolute():
        paths = _openscad_library_paths()
        for p in paths:
            f = p / result
            # print(f'Checking {f} -> {f.exists()}')
            if f.exists():
                result = f

    return result
 
# use() & include() mimic OpenSCAD's use/include mechanics.
# -- use() makes methods in scad_file_path.scad available to be called.
# --include() makes those methods available AND executes all code in
#   scad_file_path.scad, which may have side effects.
#   Unless you have a specific need, call use().
def use(scad_file_path: PathStr, use_not_include: bool = True, dest_namespace_dict: Dict = None):
    """
    Opens scad_file_path, parses it for all usable calls,
    and adds them to caller's namespace.
    """
    # These functions in solidpython are used here and only here; don't pollute
    # the global namespace with them
    from .solidpython import parse_scad_callables
    from .solidpython import new_openscad_class_str
    from .solidpython import calling_module

    scad_file_path = _find_library(scad_file_path) 

    contents = None
    try:
        contents = scad_file_path.read_text()
    except Exception as e:
        raise Exception(f"Failed to import SCAD module '{scad_file_path}' with error: {e} ")

    # Once we have a list of all callables and arguments, dynamically
    # add OpenSCADObject subclasses for all callables to the calling module's
    # namespace.
    symbols_dicts = parse_scad_callables(contents)

    for sd in symbols_dicts:
        class_str = new_openscad_class_str(sd['name'], sd['args'], sd['kwargs'],
                                           scad_file_path.as_posix(), use_not_include)
        # If this is called from 'include', we have to look deeper in the stack
        # to find the right module to add the new class to.
        if dest_namespace_dict is None:
            stack_depth = 2 if use_not_include else 3
            dest_namespace_dict = calling_module(stack_depth).__dict__
        try:
            exec(class_str, dest_namespace_dict)
        except Exception as e:
            classname = sd['name']
            msg = f"Unable to import SCAD module: `{classname}` from `{scad_file_path.name}`, with error: {e}"
            print(msg)

    return True

def include(scad_file_path: PathStr) -> bool:
    return use(scad_file_path, use_not_include=False)

