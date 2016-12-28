import os

from . import calling_module, indent
from ._includes import IncludedOpenSCADObject

def _find_include_strings(obj):
    include_strings = set()
    if isinstance(obj, IncludedOpenSCADObject):
        include_strings.add(obj.include_string)
    for child in obj.children:
        include_strings.update(_find_include_strings(child))
    return include_strings


def scad_render(scad_object, file_header=''):
    # Make this object the root of the tree
    root = scad_object

    # Scan the tree for all instances of
    # IncludedOpenSCADObject, storing their strings
    include_strings = _find_include_strings(root)

    # and render the string
    includes = ''.join(include_strings) + "\n"
    scad_body = root._render()
    return file_header + includes + scad_body


def scad_render_animated(func_to_animate, steps=20, back_and_forth=True, filepath=None, file_header=''):
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
    scad_obj = func_to_animate()
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
        scad_obj = func_to_animate(_time=eval_time)

        scad_str = indent(scad_obj._render())
        rendered_string += ("if ($t >= %(time)s && $t < %(end_time)s){"
                            "   %(scad_str)s\n"
                            "}\n" % vars())
    return rendered_string


def scad_render_animated_file(func_to_animate, steps=20, back_and_forth=True, 
                              filepath=None, file_header='', include_orig_code=True):
    rendered_string = scad_render_animated(func_to_animate, steps, 
                                            back_and_forth, file_header)
    return _write_code_to_file(rendered_string, filepath, include_orig_code)


def scad_render_to_file(scad_object, filepath=None, file_header='', include_orig_code=True):
    rendered_string = scad_render(scad_object, file_header)
    return _write_code_to_file(rendered_string, filepath, include_orig_code)


def _write_code_to_file(rendered_string, filepath=None, include_orig_code=True):
    try:
        calling_file = os.path.abspath(calling_module(stack_depth=3).__file__)

        if include_orig_code:
            rendered_string += sp_code_in_scad_comment(calling_file)

        # This write is destructive, and ought to do some checks that the write
        # was successful.
        # If filepath isn't supplied, place a .scad file with the same name
        # as the calling module next to it
        if not filepath:
            filepath = os.path.splitext(calling_file)[0] + '.scad'
    except AttributeError as e:
        # If no calling_file was found, this is being called from the terminal.
        # We can't read original code from a file, so don't try,
        # and can't read filename from the calling file either, so just save to
        # solid.scad.
        if not filepath:
            filepath = os.path.abspath('.') + "/solid.scad"

    f = open(filepath, "w")
    f.write(rendered_string)
    f.close()
    return True


def sp_code_in_scad_comment(calling_file):
    # Once a SCAD file has been created, it's difficult to reconstruct
    # how it got there, since it has no variables, modules, etc.  So, include
    # the Python code that generated the scad code as comments at the end of
    # the SCAD code
    pyopenscad_str = open(calling_file, 'r').read()

    # TODO: optimally, this would also include a version number and
    # git hash (& date & github URL?) for the version of solidpython used
    # to create a given file; That would future-proof any given SP-created
    # code because it would point to the relevant dependencies as well as
    # the actual code
    pyopenscad_str = ("\n"
                      "/***********************************************\n"
                      "*********      SolidPython code:      **********\n"
                      "************************************************\n"
                      " \n"
                      "%(pyopenscad_str)s \n"
                      " \n"
                      "************************************************/\n") % vars()
    return pyopenscad_str
