import tempfile
import os
import subprocess

from . import py2openscad, indent

# These are features added to SolidPython but NOT in OpenSCAD.
# Mark them for special treatment
# TODO: move this elsewhere
non_rendered_classes = ['hole', 'part']

class OpenSCADObject(object):
    """ Base class for all scad objects """
    def __init__(self, name, params):
        self.name = name
        self.params = params
        self.children = []
        self.modifier = ""
        self.parent = None
        self.is_hole = False
        self.has_hole_children = False
        self.is_part_root = False

    def set_hole(self, is_hole=True):
        self.is_hole = is_hole
        return self

    def set_part_root(self, is_root=True):
        self.is_part_root = is_root
        return self

    def find_hole_children(self, path=None):
        # Because we don't force a copy every time we re-use a node
        # (e.g a = cylinder(2, 6);  b = right(10) (a)
        #  the identical 'a' object appears in the tree twice),
        # we can't count on an object's 'parent' field to trace its
        # path to the root.  Instead, keep track explicitly
        path = path if path else [self]
        hole_kids = []

        for child in self.children:
            path.append(child)
            if child.is_hole:
                hole_kids.append(child)
                # Mark all parents as having a hole child
                for p in path:
                    p.has_hole_children = True
            # Don't append holes from separate parts below us
            elif child.is_part_root:
                continue
            # Otherwise, look below us for children
            else:
                hole_kids += child.find_hole_children(path)
            path.pop()

        return hole_kids

    def set_modifier(self, m):
        # Used to add one of the 4 single-character modifiers: 
        # #(debug) !(root) %(background) or *(disable)
        string_vals = {'disable':      '*',
                       'debug':        '#',
                       'background':   '%',
                       'root':         '!',
                       '*': '*',
                       '#': '#',
                       '%': '%',
                       '!': '!'}

        self.modifier = string_vals.get(m.lower(), '')
        return self

    def _render(self, render_holes=False):
        '''
        NOTE: In general, you won't want to call this method. For most purposes,
        you really want scad_render(), 
        Calling obj._render won't include necessary 'use' or 'include' statements
        '''
        # First, render all children
        s = ""
        for child in self.children:
            # Don't immediately render hole children.
            # Add them to the parent's hole list,
            # And render after everything else
            if not render_holes and child.is_hole:
                continue
            s += child._render(render_holes)

        # Then render self and prepend/wrap it around the children
        # I've added designated parts and explicit holes to SolidPython.
        # OpenSCAD has neither, so don't render anything from these objects
        if self.name in non_rendered_classes:
            pass
        elif not self.children:
            s = self._render_str_no_children() + ";"
        else:
            s = self._render_str_no_children() + " {" + indent(s) + "\n}"

        # If this is the root object or the top of a separate part,
        # find all holes and subtract them after all positive geometry
        # is rendered
        if (not self.parent) or self.is_part_root:
            hole_children = self.find_hole_children()

            if len(hole_children) > 0:
                s += "\n/* Holes Below*/"
                s += self._render_hole_children()

                # wrap everything in the difference
                s = "\ndifference(){" + indent(s) + " /* End Holes */ \n}"
        return s

    def _render_str_no_children(self):
        s = "\n" + self.modifier + self.name + "("
        first = True

        # OpenSCAD doesn't have a 'segments' argument, but it does
        # have '$fn'.  Swap one for the other
        if 'segments' in self.params:
            self.params['$fn'] = self.params.pop('segments')

        valid_keys = self.params.keys()

        # intkeys are the positional parameters
        intkeys = list(filter(lambda x: type(x) == int, valid_keys))
        intkeys.sort()

        # named parameters
        nonintkeys = list(filter(lambda x: not type(x) == int, valid_keys))
        all_params_sorted = intkeys + nonintkeys
        if all_params_sorted:
            all_params_sorted = sorted(all_params_sorted)

        for k in all_params_sorted:
            v = self.params[k]
            if v == None:
                continue

            if not first:
                s += ", "
            first = False

            if type(k) == int:
                s += py2openscad(v)
            else:
                s += k + " = " + py2openscad(v)

        s += ")"
        return s

    def _render_hole_children(self):
        # Run down the tree, rendering only those nodes
        # that are holes or have holes beneath them
        if not self.has_hole_children:
            return ""
        s = ""
        for child in self.children:
            if child.is_hole:
                s += child._render(render_holes=True)
            elif child.has_hole_children:
                # Holes exist in the compiled tree in two pieces:
                # The shapes of the holes themselves, (an object for which
                # obj.is_hole is True, and all its children) and the
                # transforms necessary to put that hole in place, which
                # are inherited from non-hole geometry.

                # Non-hole Intersections & differences can change (shrink)
                # the size of holes, and that shouldn't happen: an
                # intersection/difference with an empty space should be the
                # entirety of the empty space.
                #  In fact, the intersection of two empty spaces should be
                # everything contained in both of them:  their union.
                # So... replace all super-hole intersection/diff transforms
                # with union in the hole segment of the compiled tree.
                # And if you figure out a better way to explain this,
                # please, please do... because I think this works, but I
                # also think my rationale is shaky and imprecise. 
                # -ETJ 19 Feb 2013
                s = s.replace("intersection", "union")
                s = s.replace("difference", "union")
                s += child._render_hole_children()
        if self.name in non_rendered_classes:
            pass
        else:
            s = self._render_str_no_children() + "{" + indent(s) + "\n}"
        return s

    def add(self, child):
        '''
        if child is a single object, assume it's an OpenSCADObject and 
        add it to self.children

        if child is a list, assume its members are all OpenSCADObjects and
        add them all to self.children
        '''
        if isinstance(child, (list, tuple)):
            # __call__ passes us a list inside a tuple, but we only care
            # about the list, so skip single-member tuples containing lists
            if len(child) == 1 and isinstance(child[0], (list, tuple)):
                child = child[0]
            [self.add(c) for c in child]
        else:
            self.children.append(child)
            child.set_parent(self)
        return self

    def set_parent(self, parent):
        self.parent = parent

    def add_param(self, k, v):
        if k == '$fn':
            k = 'segments'
        self.params[k] = v
        return self

    def copy(self):
        # Provides a copy of this object and all children,
        # but doesn't copy self.parent, meaning the new object belongs
        # to a different tree
        # If we're copying a scad object, we know it is an instance of
        # a dynamically created class called self.name.
        # Initialize an instance of that class with the same params
        # that created self, the object being copied.

        # Python can't handle an '$fn' argument, while openSCAD only wants
        # '$fn'.  Swap back and forth as needed; the final renderer will
        # sort this out.
        if '$fn' in self.params:
            self.params['segments'] = self.params.pop('$fn')

        other = globals()[self.name](**self.params)
        other.set_modifier(self.modifier)
        other.set_hole(self.is_hole)
        other.set_part_root(self.is_part_root)
        other.has_hole_children = self.has_hole_children
        for c in self.children:
            other.add(c.copy())
        return other

    def __call__(self, *args):
        '''
        Adds all objects in args to self.  This enables OpenSCAD-like syntax,
        e.g.:
        union()(
            cube(),
            sphere()
        )
        '''
        return self.add(args)

    def __add__(self, x):
        '''
        This makes u = a+b identical to:
        u = union()(a, b )
        '''
        from ._builtins import union
        return union()(self, x)

    def __sub__(self, x):
        '''
        This makes u = a - b identical to:
        u = difference()(a, b )
        '''
        from ._builtins import difference
        return difference()(self, x)

    def __mul__(self, x):
        '''
        This makes u = a * b identical to:
        u = intersection()(a, b )
        '''
        from ._builtins import intersection
        return intersection()(self, x)

    def _repr_png_(self):
        '''
        Allow rich clients such as the IPython Notebook, to display the current
        OpenSCAD rendering of this object.
        '''
        from ._render import scad_render
        png_data = None
        tmp = tempfile.NamedTemporaryFile(suffix=".scad", delete=False)
        tmp_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        try:
            scad_text = scad_render(self).encode("utf-8")
            tmp.write(scad_text)
            tmp.close()
            tmp_png.close()
            subprocess.Popen([
                "openscad",
                "--preview",
                "-o", tmp_png.name,
                tmp.name
            ]).communicate()

            with open(tmp_png.name, "rb") as png:
                png_data = png.read()
        finally:
            os.unlink(tmp.name)
            os.unlink(tmp_png.name)

        return png_data
