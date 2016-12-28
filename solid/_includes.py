"""
Including existing scad files in a SolidPython file
"""
import os
import sys

from . import calling_module
from ._object import OpenSCADObject
from ._parse import extract_callable_signatures


class IncludedOpenSCADObject(OpenSCADObject):
    # Identical to OpenSCADObject, but each subclass of IncludedOpenSCADObject
    # represents imported scad code, so each instance needs to store the path
    # to the scad file it's included from.

    def __init__(self, name, params, include_file_path, use_not_include=False, **kwargs):
        self.include_file_path = self._get_include_path(include_file_path)

        if use_not_include:
            self.include_string = 'use <%s>\n' % self.include_file_path
        else:
            self.include_string = 'include <%s>\n' % self.include_file_path

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
        # Just pass any extra arguments straight on to OpenSCAD; it'll accept
        # them
                whole_path = os.path.join(p, include_file_path)
                if os.path.isfile(whole_path):
                    return os.path.abspath(whole_path)

        # No loadable SCAD file was found in sys.path.  Raise an error
        raise ValueError("Unable to find included SCAD file: "
                         "%(include_file_path)s in sys.path" % vars())


def new_openscad_class_str(class_name, args=[], kwargs=[], include_file_path=None, use_not_include=True):
    args_str = ''
    args_pairs = ''

    for arg in args:
        args_str += ', ' + arg
        args_pairs += "'%(arg)s':%(arg)s, " % vars()

    # kwargs have a default value defined in their SCAD versions.  We don't
    # care what that default value will be (SCAD will take care of that), just
    # that one is defined.
    for kwarg in kwargs:
        args_str += ', %(kwarg)s=None' % vars()
        args_pairs += "'%(kwarg)s':%(kwarg)s, " % vars()

    if include_file_path:
        # include_file_path may include backslashes on Windows; escape them
        # again here so any backslashes don't get used as escape characters
        # themselves
        include_file_path = include_file_path.replace('\\', '\\\\')

        # NOTE the explicit import of 'solid' below. This is a fix for:
        # https://github.com/SolidCode/SolidPython/issues/20 -ETJ 16 Jan 2014
        result = ("import solid\n"
                  "class %(class_name)s(solid.IncludedOpenSCADObject):\n"
                  "   def __init__(self%(args_str)s, **kwargs):\n"
                  "       solid.IncludedOpenSCADObject.__init__(self, '%(class_name)s', {%(args_pairs)s }, include_file_path='%(include_file_path)s', use_not_include=%(use_not_include)s, **kwargs )\n"
                  "   \n"
                  "\n" % vars())
    else:
        result = ("class %(class_name)s(OpenSCADObject):\n"
                  "   def __init__(self%(args_str)s):\n"
                  "       OpenSCADObject.__init__(self, '%(class_name)s', {%(args_pairs)s })\n"
                  "   \n"
                  "\n" % vars())

    return result

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
    # TODO:  doctest needed
    try:
        module = open(scad_file_path)
        contents = module.read()
        module.close()
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
