#! /usr/bin/env python

#    Simple Python OpenSCAD Code Generator
#    Copyright (C) 2009    Philipp Tiefenbacher <wizards23@gmail.com>
#    Amendments & additions, (C) 2011-2019 Evan Jones <evan_t_jones@mac.com>
#
#   License: LGPL 2.1 or later
#

from __future__ import annotations

import datetime
import inspect
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import keyword

from typing import Set, Sequence, List, Callable, Optional, Union, Iterable

from types import ModuleType
from typing import Callable, Iterable, List, Optional, Sequence, Set, Union

import pkg_resources
import regex as re

PathStr = Union[Path, str]
AnimFunc = Callable[[Optional[float]], 'OpenSCADObject']
# These are features added to SolidPython but NOT in OpenSCAD.
# Mark them for special treatment
non_rendered_classes = ['hole', 'part']

# Words reserved in Python but not OpenSCAD
# Re: https://github.com/SolidCode/SolidPython/issues/99

PYTHON_ONLY_RESERVED_WORDS = keyword.kwlist


# =========================
# = Internal Utilities    =
# =========================
class OpenSCADObject:

    def __init__(self, name: str, params: dict):
        self.name = name
        self.params = params
        self.children: List["OpenSCADObject"] = []
        self.modifier = ""
        self.parent: Optional["OpenSCADObject"] = None
        self.is_hole = False
        self.has_hole_children = False
        self.is_part_root = False

    def set_hole(self, is_hole: bool = True) -> "OpenSCADObject":
        self.is_hole = is_hole
        return self

    def set_part_root(self, is_root: bool = True) -> "OpenSCADObject":
        self.is_part_root = is_root
        return self

    def find_hole_children(self, path: List["OpenSCADObject"] = None) -> List["OpenSCADObject"]:
        """
        Because we don't force a copy every time we re-use a node
        (e.g a = cylinder(2, 6);  b = right(10) (a)
         the identical 'a' object appears in the tree twice),
        we can't count on an object's 'parent' field to trace its
        path to the root.  Instead, keep track explicitly
        """
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

    def set_modifier(self, m: str) -> "OpenSCADObject":
        """
        Used to add one of the 4 single-character modifiers:
        #(debug) !(root) %(background) or *(disable)
        """
        string_vals = {'disable': '*',
                       'debug': '#',
                       'background': '%',
                       'root': '!',
                       '*': '*',
                       '#': '#',
                       '%': '%',
                       '!': '!'}

        self.modifier = string_vals.get(m.lower(), '')
        return self

    def _render(self, render_holes: bool = False) -> str:
        """
        NOTE: In general, you won't want to call this method. For most purposes,
        you really want scad_render(), 
        Calling obj._render won't include necessary 'use' or 'include' statements
        """
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

    def _render_str_no_children(self) -> str:
        callable_name = _unsubbed_keyword(self.name)
        s = "\n" + self.modifier + callable_name + "("
        first = True

        # Re: https://github.com/SolidCode/SolidPython/issues/99
        # OpenSCAD will accept Python reserved words as callables or argument names,
        # but they won't compile in Python. Those have already been substituted
        # out (e.g 'or' => 'or_'). Sub them back here.
        self.params = {_unsubbed_keyword(k): v for k, v in self.params.items()}

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
            if v is None:
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

    def _render_hole_children(self) -> str:
        # Run down the tree, rendering only those nodes
        # that are holes or have holes beneath them
        if not self.has_hole_children:
            return ""
        s = ""
        for child in self.children:
            if child.is_hole:
                s += child._render(render_holes=True)
            elif child.has_hole_children:
                s += child._render_hole_children()
        if self.name in non_rendered_classes:
            pass
        else:
            s = self._render_str_no_children() + "{" + indent(s) + "\n}"

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

        return s

    def add(self, child: Union["OpenSCADObject", Sequence["OpenSCADObject"]]) -> "OpenSCADObject":
        """
        if child is a single object, assume it's an OpenSCADObjects and 
        add it to self.children

        if child is a list, assume its members are all OpenSCADObjects and
        add them all to self.children
        """
        if isinstance(child, (list, tuple)):
            # __call__ passes us a list inside a tuple, but we only care
            # about the list, so skip single-member tuples containing lists
            if len(child) == 1 and isinstance(child[0], (list, tuple)):
                child = child[0]
            [self.add(c) for c in child]
        elif isinstance(child, int):
            # Allowing for creating object by adding to 0 (as in sum())
            if child != 0:
                raise ValueError
        else:
            self.children.append(child)  # type: ignore
            child.set_parent(self)  # type: ignore
        return self

    def set_parent(self, parent: "OpenSCADObject"):
        self.parent = parent

    def add_param(self, k: str, v: float) -> "OpenSCADObject":
        if k == '$fn':
            k = 'segments'
        self.params[k] = v
        return self

    def copy(self) -> "OpenSCADObject":
        """
        Provides a copy of this object and all children,
        but doesn't copy self.parent, meaning the new object belongs
        to a different tree
        Initialize an instance of this class with the same params
        that created self, the object being copied.
        """

        # Python can't handle an '$fn' argument, while openSCAD only wants
        # '$fn'.  Swap back and forth as needed; the final renderer will
        # sort this out.
        if '$fn' in self.params:
            self.params['segments'] = self.params.pop('$fn')

        other = type(self)(**self.params)
        other.set_modifier(self.modifier)
        other.set_hole(self.is_hole)
        other.set_part_root(self.is_part_root)
        other.has_hole_children = self.has_hole_children
        for c in self.children:
            other.add(c.copy())
        return other

    def __call__(self, *args: "OpenSCADObject") -> "OpenSCADObject":
        """
        Adds all objects in args to self.  This enables OpenSCAD-like syntax,
        e.g.:
        union()(
            cube(),
            sphere()
        )
        """
        return self.add(args)

    def __add__(self, x: "OpenSCADObject") -> "OpenSCADObject":
        """
        This makes u = a+b identical to:
        u = union()(a, b )
        """
        return objects.union()(self, x)

    def __radd__(self, x: "OpenSCADObject") -> "OpenSCADObject":
        """
        This makes u = a+b identical to:
        u = union()(a, b )
        """
        return objects.union()(self, x)

    def __sub__(self, x: "OpenSCADObject") -> "OpenSCADObject":
        """
        This makes u = a - b identical to:
        u = difference()(a, b )
        """
        return objects.difference()(self, x)

    def __mul__(self, x: "OpenSCADObject") -> "OpenSCADObject":
        """
        This makes u = a * b identical to:
        u = intersection()(a, b )
        """
        return objects.intersection()(self, x)

    def _repr_png_(self) -> Optional[bytes]:
        """
        Allow rich clients such as the IPython Notebook, to display the current
        OpenSCAD rendering of this object.
        """
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


class IncludedOpenSCADObject(OpenSCADObject):
    """
    Identical to OpenSCADObject, but each subclass of IncludedOpenSCADObject
    represents imported scad code, so each instance needs to store the path
    to the scad file it's included from.
    """

    def __init__(self, name, params, include_file_path, use_not_include=False, **kwargs):
        self.include_file_path = self._get_include_path(include_file_path)

        use_str = 'use' if use_not_include else 'include'
        self.include_string = f'{use_str} <{self.include_file_path}>\n'

        # Just pass any extra arguments straight on to OpenSCAD; it'll accept
        # them
        if kwargs:
            params.update(kwargs)

        OpenSCADObject.__init__(self, name, params)

    def _get_include_path(self, include_file_path):
        # Look through sys.path for anyplace we can find a valid file ending
        # in include_file_path.  Return that absolute path
        if os.path.isabs(include_file_path) and os.path.isfile(include_file_path):
            return include_file_path
        else:
            for p in sys.path:
                whole_path = os.path.join(p, include_file_path)
                if os.path.isfile(whole_path):
                    return os.path.abspath(whole_path)

        # No loadable SCAD file was found in sys.path.  Raise an error
        raise ValueError(f"Unable to find included SCAD file: {include_file_path} in sys.path")


# =========================================
# = Rendering Python code to OpenSCAD code=
# =========================================
def _find_include_strings(obj: Union[IncludedOpenSCADObject, OpenSCADObject]) -> Set[str]:
    include_strings = set()
    if isinstance(obj, IncludedOpenSCADObject):
        include_strings.add(obj.include_string)
    for child in obj.children:
        include_strings.update(_find_include_strings(child))
    return include_strings


def scad_render(scad_object: OpenSCADObject, file_header: str = '') -> str:
    # Make this object the root of the tree
    root = scad_object

    # Scan the tree for all instances of
    # IncludedOpenSCADObject, storing their strings
    include_strings = _find_include_strings(root)

    # and render the string
    includes = ''.join(include_strings) + "\n"
    scad_body = root._render()

    if file_header and not file_header.endswith('\n'): 
        file_header += '\n'

    return file_header + includes + scad_body


def scad_render_animated(func_to_animate: AnimFunc, 
                         steps: int =20, 
                         back_and_forth: bool=True, 
                         file_header: str='') -> str:
    # func_to_animate takes a single float argument, _time in [0, 1), and
    # returns an OpenSCADObject instance.
    #
    # Outputs an OpenSCAD file with func_to_animate() evaluated at "steps"
    # points between 0 & 1, with time never evaluated at exactly 1

    # If back_and_forth is True, smoothly animate the full extent of the motion
    # and then reverse it to the beginning; this avoids skipping between beginning
    # and end of the animated motion

    # NOTE: This is a hacky way to solve a simple problem.  To use OpenSCAD's
    # animation feature, our code needs to respond to changes in the value
    # of the OpenSCAD variable $t, but I can't think of a way to get a
    # float variable from our code and put it into the actual SCAD code.
    # Instead, we just evaluate our code at each desired step, and write it
    # all out in the SCAD code for each case, with an if/else tree.  Depending
    # on the number of steps, this could create hundreds of times more SCAD
    # code than is needed.  But... it does work, with minimal Python code, so
    # here it is. Better solutions welcome. -ETJ 28 Mar 2013

    # NOTE: information on the OpenSCAD manual wiki as of November 2012 implies
    # that the OpenSCAD app does its animation irregularly; sometimes it animates
    # one loop in steps iterations, and sometimes in (steps + 1).  Do it here
    # in steps iterations, meaning that we won't officially reach $t =1.

    # Note also that we check for ranges of time rather than equality; this
    # should avoid any rounding error problems, and doesn't require the file
    # to be animated with an identical number of steps to the way it was
    # created. -ETJ 28 Mar 2013
    scad_obj = func_to_animate(_time=0)  # type: ignore
    include_strings = _find_include_strings(scad_obj)
    # and render the string
    includes = ''.join(include_strings) + "\n"

    rendered_string = file_header + includes

    if back_and_forth:
        steps *= 2

    for i in range(steps):
        time = i * 1.0 / steps
        end_time = (i + 1) * 1.0 / steps
        eval_time = time
        # Looping back and forth means there's no jump between the start and
        # end position
        if back_and_forth:
            if time < 0.5:
                eval_time = time * 2
            else:
                eval_time = 2 - 2 * time
        scad_obj = func_to_animate(_time=eval_time)  # type: ignore

        scad_str = indent(scad_obj._render())
        rendered_string += f"if ($t >= {time} && $t < {end_time}){{" \
                           f"   {scad_str}\n" \
                           f"}}\n"
    return rendered_string


def scad_render_animated_file(func_to_animate:AnimFunc, 
                              steps: int=20, 
                              back_and_forth: bool=True, 
                              filepath: Optional[str]=None, 
                              out_dir: PathStr=None, 
                              file_header: str='', 
                              include_orig_code: bool=True) -> str:
    rendered_string = scad_render_animated(func_to_animate, steps, 
                                            back_and_forth, file_header)
    return _write_code_to_file(rendered_string, filepath, out_dir=out_dir, 
                include_orig_code=include_orig_code)

def scad_render_to_file(scad_object: OpenSCADObject,
                        filepath: PathStr=None, 
                        out_dir: PathStr=None,
                        file_header: str='', 
                        include_orig_code: bool=True) -> str:
    header = file_header
    if include_orig_code:
        version = _get_version()
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"// Generated by SolidPython {version} on {date}\n" + file_header

    rendered_string = scad_render(scad_object, header)
    return _write_code_to_file(rendered_string, filepath, out_dir, include_orig_code)

def _write_code_to_file(rendered_string: str, 
                        filepath: PathStr=None, 
                        out_dir: PathStr=None, 
                        include_orig_code: bool=True) -> str:
    try:
        calling_file = Path(calling_module(stack_depth=3).__file__).absolute()
        # Output path is determined four ways:
        # -- If filepath is supplied, use filepath
        # -- If no filepath is supplied but an out_dir is supplied, 
        #       give the calling file a .scad suffix and put it in out_dir
        # -- If neither filepath nor out_dir are supplied, give the new
        #       file a .scad suffix and put it next to the calling file
        # -- If no path info is supplied and we can't find a calling file 
        #       (i.e, this is being called from an interactive terminal), 
        #       write a file to Path.cwd() / 'solid.scad'
        out_path = Path()
        if filepath:
            out_path = Path(filepath)
        elif out_dir:
            odp = Path(out_dir)
            if not odp.exists():
                odp.mkdir()
            out_path = odp / calling_file.with_suffix('.scad').name
        else:
            out_path = calling_file.with_suffix('.scad')
        
        if include_orig_code:
            rendered_string += sp_code_in_scad_comment(calling_file)
    except AttributeError as e:
        # If no calling_file was found, this is being called from the terminal.
        # We can't read original code from a file, so don't try,
        # and can't read filename from the calling file either, so just save to
        # solid.scad.

        if filepath:
            out_path = Path(filepath)
        else:
            odp = Path(out_dir) if out_dir else Path.cwd()
            if not odp.exists():
                odp.mkdir()
            out_path = odp / 'solid.scad'

    out_path.write_text(rendered_string)
    return out_path.absolute().as_posix()


def _get_version() -> str:
    """
    Returns SolidPython version
    Returns '<Unknown>' if no version can be found
    """
    version = '<Unknown>'
    try:
        # if SolidPython is installed use `pkg_resources`
        version = pkg_resources.get_distribution('solidpython').version

    except pkg_resources.DistributionNotFound:
        # if the running SolidPython is not the one installed via pip,
        # try to read it from the project setup file
        version_pattern = re.compile(r"version = ['\"]([^'\"]*)['\"]")
        version_file_path = Path(__file__).parent.parent / 'pyproject.toml'
        if version_file_path.exists():
            version_match = version_pattern.search(version_file_path.read_text())
            if version_match:
                version = version_match.group(1)
    return version

def sp_code_in_scad_comment(calling_file: PathStr) -> str:
    """
    Once a SCAD file has been created, it's difficult to reconstruct
    how it got there, since it has no variables, modules, etc.  So, include
    the Python code that generated the scad code as comments at the end of
    the SCAD code
    """
    pyopenscad_str = Path(calling_file).read_text()

    # TODO: optimally, this would also include a version number and
    # git hash (& date & github URL?) for the version of solidpython used
    # to create a given file; That would future-proof any given SP-created
    # code because it would point to the relevant dependencies as well as
    # the actual code
    pyopenscad_str = (f"\n"
                      f"/***********************************************\n"
                      f"*********      SolidPython code:      **********\n"
                      f"************************************************\n"
                      f" \n"
                      f"{pyopenscad_str} \n"
                      f" \n"
                      f"************************************************/\n")
    return pyopenscad_str


# ===========
# = Parsing =
# ===========
def extract_callable_signatures(scad_file_path: PathStr) -> List[dict]:
    scad_code_str = Path(scad_file_path).read_text()
    return parse_scad_callables(scad_code_str)


def parse_scad_callables(scad_code_str: str) -> List[dict]:
    callables = []

    # Note that this isn't comprehensive; tuples or nested data structures in
    # a module definition will defeat it.

    # Current implementation would throw an error if you tried to call a(x, y)
    # since Python would expect a(x);  OpenSCAD itself ignores extra arguments,
    # but that's not really preferable behavior

    # TODO:  write a pyparsing grammar for OpenSCAD, or, even better, use the yacc parse grammar
    # used by the language itself.  -ETJ 06 Feb 2011

    # FIXME: OpenSCAD use/import includes top level variables. We should parse 
    # those out (e.g. x = someValue;) as well -ETJ 21 May 2019
    no_comments_re = r'(?mxs)(//.*?\n|/\*.*?\*/)'

    # Also note: this accepts: 'module x(arg) =' and 'function y(arg) {', both
    # of which are incorrect syntax
    mod_re = r'(?mxs)^\s*(?:module|function)\s+(?P<callable_name>\w+)\s*\((?P<all_args>.*?)\)\s*(?:{|=)'

    # See https://github.com/SolidCode/SolidPython/issues/95; Thanks to https://github.com/Torlos
    args_re = r'(?mxs)(?P<arg_name>\w+)(?:\s*=\s*(?P<default_val>([\w.\"\s\?:\-+\\\/*]+|\((?>[^()]|(?2))*\)|\[(?>[^\[\]]|(?2))*\])+))?(?:,|$)'

    # remove all comments from SCAD code
    scad_code_str = re.sub(no_comments_re, '', scad_code_str)
    # get all SCAD callables
    mod_matches = re.finditer(mod_re, scad_code_str)

    for m in mod_matches:
        callable_name = m.group('callable_name')
        args = []
        kwargs = []
        all_args = m.group('all_args')
        if all_args:
            arg_matches = re.finditer(args_re, all_args)
            for am in arg_matches:
                arg_name = am.group('arg_name')
                if am.group('default_val'):
                    kwargs.append(arg_name)
                else:
                    args.append(arg_name)

        callables.append({'name': callable_name, 'args': args, 'kwargs': kwargs})

    return callables


def calling_module(stack_depth: int = 2) -> ModuleType:
    """
    Returns the module *2* back in the frame stack.  That means:
    code in module A calls code in module B, which asks calling_module()
    for module A.

    This means that we have to know exactly how far back in the stack
    our desired module is; if code in module B calls another function in 
    module B, we have to increase the stack_depth argument to account for
    this.

    Got that?
    """
    frm = inspect.stack()[stack_depth]
    calling_mod = inspect.getmodule(frm[0])
    # If calling_mod is None, this is being called from an interactive session.
    # Return that module.  (Note that __main__ doesn't have a __file__ attr,
    # but that's caught elsewhere.)
    if not calling_mod:
        import __main__ as calling_mod  # type: ignore
    return calling_mod


def new_openscad_class_str(class_name: str,
                           args: Sequence[str] = None,
                           kwargs: Sequence[str] = None,
                           include_file_path: Optional[str] = None,
                           use_not_include: bool = True) -> str:
    args_str = ''
    args_pairs = ''

    args = args or []
    kwargs = kwargs or []

    # Re: https://github.com/SolidCode/SolidPython/issues/99
    # Don't allow any reserved words as argument names or module names
    # (They might be valid OpenSCAD argument names, but not in Python)
    class_name = _subbed_keyword(class_name)

    args = map(_subbed_keyword, args)  # type: ignore
    for arg in args:
        args_str += ', ' + arg
        args_pairs += f"'{arg}':{arg}, "

    # kwargs have a default value defined in their SCAD versions.  We don't
    # care what that default value will be (SCAD will take care of that), just
    # that one is defined.
    kwargs = map(_subbed_keyword, kwargs)  # type: ignore
    for kwarg in kwargs:
        args_str += f', {kwarg}=None'
        args_pairs += f"'{kwarg}':{kwarg}, "

    if include_file_path:
        # include_file_path may include backslashes on Windows; escape them
        # again here so any backslashes don't get used as escape characters
        # themselves
        include_file_str = Path(include_file_path).as_posix()

        # NOTE the explicit import of 'solid' below. This is a fix for:
        # https://github.com/SolidCode/SolidPython/issues/20 -ETJ 16 Jan 2014
        result = (f"import solid\n"
                  f"class {class_name}(solid.IncludedOpenSCADObject):\n"
                  f"   def __init__(self{args_str}, **kwargs):\n"
                  f"       solid.IncludedOpenSCADObject.__init__(self, '{class_name}', {{{args_pairs} }}, include_file_path='{include_file_str}', use_not_include={use_not_include}, **kwargs )\n"
                  f"   \n"
                  f"\n")
    else:
        result = (f"class {class_name}(OpenSCADObject):\n"
                  f"   def __init__(self{args_str}):\n"
                  f"       OpenSCADObject.__init__(self, '{class_name}', {{{args_pairs }}})\n"
                  f"   \n"
                  f"\n")

    return result


def _subbed_keyword(keyword: str) -> str:
    """
    Append an underscore to any python reserved word.
    No-op for all other strings, e.g. 'or' => 'or_', 'other' => 'other'
    """
    new_key = keyword + '_' if keyword in PYTHON_ONLY_RESERVED_WORDS else keyword
    if new_key != keyword:
        print(f"\nFound OpenSCAD code that's not compatible with Python. \n"
              f"Imported OpenSCAD code using `{keyword}` \n"
              f"can be accessed with `{new_key}` in SolidPython\n")
    return new_key


def _unsubbed_keyword(subbed_keyword: str) -> str:
    """
    Remove trailing underscore for already-subbed python reserved words.
    No-op for all other strings: e.g. 'or_' => 'or', 'other_' => 'other_'
    """
    shortened = subbed_keyword[:-1]
    return shortened if shortened in PYTHON_ONLY_RESERVED_WORDS else subbed_keyword


# now that we have the base class defined, we can do a circular import
from . import objects


def py2openscad(o: Union[bool, float, str, Iterable]) -> str:
    if type(o) == bool:
        return str(o).lower()
    if type(o) == float:
        return f"{o:.10f}"  # type: ignore
    if type(o) == str:
        return f'\"{o}\"'  # type: ignore
    if type(o).__name__ == "ndarray":
        import numpy  # type: ignore
        return numpy.array2string(o, separator=",", threshold=1000000000)
    if hasattr(o, "__iter__"):
        s = "["
        first = True
        for i in o:  # type: ignore
            if not first:
                s += ", "
            first = False
            s += py2openscad(i)
        s += "]"
        return s
    return str(o)


def indent(s: str) -> str:
    return s.replace("\n", "\n\t")
