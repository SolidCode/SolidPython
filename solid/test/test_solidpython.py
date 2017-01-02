#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import re

import unittest
import tempfile
from solid.test.ExpandedTestCase import DiffOutput
from solid import *

scad_test_case_templates = [
{'name': 'polygon',     'kwargs': {'paths': [[0, 1, 2]]}, 'expected': '\n\npolygon(paths = [[0, 1, 2]], points = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]);', 'args': {'points': [[0, 0, 0], [1, 0, 0], [0, 1, 0]]}, },
{'name': 'circle',      'kwargs': {'segments': 12, 'r': 1}, 'expected': '\n\ncircle($fn = 12, r = 1);', 'args': {}, },
{'name': 'circle',      'kwargs': {'segments': 12, 'd': 1}, 'expected': '\n\ncircle($fn = 12, d = 1);', 'args': {}, },
{'name': 'square',      'kwargs': {'center': False, 'size': 1}, 'expected': '\n\nsquare(center = false, size = 1);', 'args': {}, },
{'name': 'sphere',      'kwargs': {'segments': 12, 'r': 1}, 'expected': '\n\nsphere($fn = 12, r = 1);', 'args': {}, },
{'name': 'sphere',      'kwargs': {'segments': 12, 'd': 1}, 'expected': '\n\nsphere($fn = 12, d = 1);', 'args': {}, },
{'name': 'cube',        'kwargs': {'center': False, 'size': 1}, 'expected': '\n\ncube(center = false, size = 1);', 'args': {}, },
{'name': 'cylinder',    'kwargs': {'r1': None, 'r2': None, 'h': 1, 'segments': 12, 'r': 1, 'center': False}, 'expected': '\n\ncylinder($fn = 12, center = false, h = 1, r = 1);', 'args': {}, },
{'name': 'cylinder',    'kwargs': {'d1': 4, 'd2': 2, 'h': 1, 'segments': 12, 'center': False}, 'expected': '\n\ncylinder($fn = 12, center = false, d1 = 4, d2 = 2, h = 1);', 'args': {}, },
{'name': 'polyhedron',  'kwargs': {'convexity': None}, 'expected': '\n\npolyhedron(faces = [[0, 1, 2]], points = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]);', 'args': {'points': [[0, 0, 0], [1, 0, 0], [0, 1, 0]], 'faces': [[0, 1, 2]]}, },
{'name': 'union',       'kwargs': {}, 'expected': '\n\nunion();', 'args': {}, },
{'name': 'intersection','kwargs': {}, 'expected': '\n\nintersection();', 'args': {}, },
{'name': 'difference',  'kwargs': {}, 'expected': '\n\ndifference();', 'args': {}, },
{'name': 'translate',   'kwargs': {'v': [1, 0, 0]}, 'expected': '\n\ntranslate(v = [1, 0, 0]);', 'args': {}, },
{'name': 'scale',       'kwargs': {'v': 0.5}, 'expected': '\n\nscale(v = 0.5000000000);', 'args': {}, },
{'name': 'rotate',      'kwargs': {'a': 45, 'v': [0, 0, 1]}, 'expected': '\n\nrotate(a = 45, v = [0, 0, 1]);', 'args': {}, },
{'name': 'mirror',      'kwargs': {}, 'expected': '\n\nmirror(v = [0, 0, 1]);', 'args': {'v': [0, 0, 1]}, },
{'name': 'multmatrix',  'kwargs': {}, 'expected': '\n\nmultmatrix(m = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]);', 'args': {'m': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]}, },
{'name': 'color',       'kwargs': {}, 'expected': '\n\ncolor(c = [1, 0, 0]);', 'args': {'c': [1, 0, 0]}, },
{'name': 'minkowski',   'kwargs': {}, 'expected': '\n\nminkowski();', 'args': {}, },
{'name': 'offset',      'kwargs': {'r': 1}, 'expected': '\n\noffset(r = 1);', 'args': {}, },
{'name': 'offset',      'kwargs': {'delta': 1}, 'expected': '\n\noffset(chamfer = false, delta = 1);', 'args': {}, },
{'name': 'hull',        'kwargs': {}, 'expected': '\n\nhull();', 'args': {}, },
{'name': 'render',      'kwargs': {'convexity': None}, 'expected': '\n\nrender();', 'args': {}, },
{'name': 'projection',  'kwargs': {'cut': None}, 'expected': '\n\nprojection();', 'args': {}, },
{'name': 'surface',     'kwargs': {'center': False, 'convexity': None}, 'expected': '\n\nsurface(center = false, file = "/Path/to/dummy.dxf");', 'args': {'file': "'/Path/to/dummy.dxf'"}, },
{'name': 'import_stl',  'kwargs': {'layer': None, 'origin': (0,0)}, 'expected': '\n\nimport(file = "/Path/to/dummy.stl", origin = [0, 0]);', 'args': {'file': "'/Path/to/dummy.stl'"}, },
{'name': 'import_dxf',  'kwargs': {'layer': None, 'origin': (0,0)}, 'expected': '\n\nimport(file = "/Path/to/dummy.dxf", origin = [0, 0]);', 'args': {'file': "'/Path/to/dummy.dxf'"}, },
{'name': 'import_',     'kwargs': {'layer': None, 'origin': (0,0)}, 'expected': '\n\nimport(file = "/Path/to/dummy.dxf", origin = [0, 0]);', 'args': {'file': "'/Path/to/dummy.dxf'"}, },
{'name': 'linear_extrude',      'kwargs': {'twist': None, 'slices': None, 'center': False, 'convexity': None, 'height': 1, 'scale': 0.9}, 'expected': '\n\nlinear_extrude(center = false, height = 1, scale = 0.9000000000);', 'args': {}, },
{'name': 'rotate_extrude',      'kwargs': {'convexity': None}, 'expected': '\n\nrotate_extrude();', 'args': {}, },
{'name': 'intersection_for',    'kwargs': {}, 'expected': '\n\nintersection_for(n = [0, 1, 2]);', 'args': {'n': [0, 1, 2]}, },
]

class TemporaryFileBuffer(object):
    name = None
    contents = None
    def __enter__(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        self.name = f.name
        try:
            f.close()
        except:
            self._cleanup()
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            with open(self.name, 'r') as f:
                self.contents = f.read()
        finally:
            self._cleanup()

    def _cleanup(self):
        try:
            os.unlink(self.name)
        except:
            pass


class TestSolidPython(DiffOutput):
    # test cases will be dynamically added to this instance

    def expand_scad_path(self, filename):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
        return os.path.join(path, filename)

    def test_infix_union(self):
        a = cube(2)
        b = sphere(2)
        expected = '\n\nunion() {\n\tcube(size = 2);\n\tsphere(r = 2);\n}'
        actual = scad_render(a + b)
        self.assertEqual(expected, actual)

    def test_infix_difference(self):
        a = cube(2)
        b = sphere(2)
        expected = '\n\ndifference() {\n\tcube(size = 2);\n\tsphere(r = 2);\n}'
        actual = scad_render(a - b)
        self.assertEqual(expected, actual)

    def test_infix_intersection(self):
        a = cube(2)
        b = sphere(2)
        expected = '\n\nintersection() {\n\tcube(size = 2);\n\tsphere(r = 2);\n}'
        actual = scad_render(a * b)
        self.assertEqual(expected, actual)

    def test_parse_scad_callables(self):
        test_str = (""
                    "module hex (width=10, height=10,    \n"
                    "            flats= true, center=false){}\n"
                    "function righty (angle=90) = 1;\n"
                    "function lefty(avar) = 2;\n"
                    "module more(a=[something, other]) {}\n"
                    "module pyramid(side=10, height=-1, square=false, centerHorizontal=true, centerVertical=false){}\n"
                    "module no_comments(arg=10,   //test comment\n"
                    "other_arg=2, /* some extra comments\n"
                    "on empty lines */\n"
                    "last_arg=4){}\n"
                    "module float_arg(arg=1.0){}\n")
        expected = [{'args': [], 'name': 'hex', 'kwargs': ['width', 'height', 'flats', 'center']}, {'args': [], 'name': 'righty', 'kwargs': ['angle']}, {'args': ['avar'], 'name': 'lefty', 'kwargs': []}, {'args': [], 'name': 'more', 'kwargs': ['a']}, {
            'args': [], 'name': 'pyramid', 'kwargs': ['side', 'height', 'square', 'centerHorizontal', 'centerVertical']}, {'args': [], 'name': 'no_comments', 'kwargs': ['arg', 'other_arg', 'last_arg']}, {'args': [], 'name': 'float_arg', 'kwargs': ['arg']}]
        from solid.solidpython import parse_scad_callables
        actual = parse_scad_callables(test_str)
        self.assertEqual(expected, actual)

    def test_use(self):
        include_file = self.expand_scad_path("examples/scad_to_include.scad")
        use(include_file)
        a = steps(3)
        actual = scad_render(a)

        abs_path = a._get_include_path(include_file)
        expected = "use <%s>\n\n\nsteps(howmany = 3);" % abs_path
        self.assertEqual(expected, actual)

    def test_include(self):
        include_file = self.expand_scad_path("examples/scad_to_include.scad")
        self.assertIsNotNone(include_file, 'examples/scad_to_include.scad not found')
        include(include_file)
        a = steps(3)

        actual = scad_render(a)
        abs_path = a._get_include_path(include_file)
        expected = "include <%s>\n\n\nsteps(howmany = 3);" % abs_path
        self.assertEqual(expected, actual)

    def test_extra_args_to_included_scad(self):
        include_file = self.expand_scad_path("examples/scad_to_include.scad")
        use(include_file)
        a = steps(3, external_var=True)
        actual = scad_render(a)

        abs_path = a._get_include_path(include_file)
        expected = "use <%s>\n\n\nsteps(external_var = true, howmany = 3);" % abs_path
        self.assertEqual(expected, actual)

    def test_background(self):
        a = cube(10)
        expected = '\n\n%cube(size = 10);'
        actual = scad_render(background(a))
        self.assertEqual(expected, actual)

    def test_debug(self):
        a = cube(10)
        expected = '\n\n#cube(size = 10);'
        actual = scad_render(debug(a))
        self.assertEqual(expected, actual)

    def test_disable(self):
        a = cube(10)
        expected = '\n\n*cube(size = 10);'
        actual = scad_render(disable(a))
        self.assertEqual(expected, actual)

    def test_root(self):
        a = cube(10)
        expected = '\n\n!cube(size = 10);'
        actual = scad_render(root(a))
        self.assertEqual(expected, actual)

    def test_explicit_hole(self):
        a = cube(10, center=True) + hole()(cylinder(2, 20, center=True))
        expected = '\n\ndifference(){\n\tunion() {\n\t\tcube(center = true, size = 10);\n\t}\n\t/* Holes Below*/\n\tunion(){\n\t\tcylinder(center = true, h = 20, r = 2);\n\t} /* End Holes */ \n}'
        actual = scad_render(a)
        self.assertEqual(expected, actual)

    def test_hole_transform_propagation(self):
        # earlier versions of holes had problems where a hole
        # that was used a couple places wouldn't propagate correctly.
        # Confirm that's still happening as it's supposed to
        h = hole()(
                rotate(a=90, v=[0, 1, 0])(
                    cylinder(2, 20, center=True)
                )
            )

        h_vert = rotate(a=-90, v=[0, 1, 0])(
            h
        )

        a = cube(10, center=True) + h + h_vert
        expected = '\n\ndifference(){\n\tunion() {\n\t\tunion() {\n\t\t\tcube(center = true, size = 10);\n\t\t}\n\t\trotate(a = -90, v = [0, 1, 0]) {\n\t\t}\n\t}\n\t/* Holes Below*/\n\tunion(){\n\t\tunion(){\n\t\t\trotate(a = 90, v = [0, 1, 0]) {\n\t\t\t\tcylinder(center = true, h = 20, r = 2);\n\t\t\t}\n\t\t}\n\t\trotate(a = -90, v = [0, 1, 0]){\n\t\t\trotate(a = 90, v = [0, 1, 0]) {\n\t\t\t\tcylinder(center = true, h = 20, r = 2);\n\t\t\t}\n\t\t}\n\t} /* End Holes */ \n}'
        actual = scad_render(a)
        self.assertEqual(expected, actual)

    def test_separate_part_hole(self):
        # Make two parts, a block with hole, and a cylinder that
        # fits inside it.  Make them separate parts, meaning
        # holes will be defined at the level of the part_root node,
        # not the overall node.  This allows us to preserve holes as
        # first class space, but then to actually fill them in with
        # the parts intended to fit in them.
        b = cube(10, center=True)
        c = cylinder(r=2, h=12, center=True)
        p1 = b - hole()(c)

        # Mark this cube-with-hole as a separate part from the cylinder
        p1 = part()(p1)

        # This fits in the hole.  If p1 is set as a part_root, it will all appear.
        # If not, the portion of the cylinder inside the cube will not appear,
        # since it would have been removed by the hole in p1
        p2 = cylinder(r=1.5, h=14, center=True)

        a = p1 + p2

        expected = '\n\nunion() {\n\tdifference(){\n\t\tdifference() {\n\t\t\tcube(center = true, size = 10);\n\t\t}\n\t\t/* Holes Below*/\n\t\tdifference(){\n\t\t\tcylinder(center = true, h = 12, r = 2);\n\t\t} /* End Holes */ \n\t}\n\tcylinder(center = true, h = 14, r = 1.5000000000);\n}'
        actual = scad_render(a)
        self.assertEqual(expected, actual)

    def test_scad_render_animated_file(self):
        def my_animate(_time=0):
            import math
            # _time will range from 0 to 1, not including 1
            rads = _time * 2 * math.pi
            rad = 15
            c = translate([rad * math.cos(rads), rad * math.sin(rads)])(square(10))
            return c
        with TemporaryFileBuffer() as tmp:
            scad_render_animated_file(my_animate, steps=2, back_and_forth=False,
                                      filepath=tmp.name, include_orig_code=False)

        actual = tmp.contents
        expected = '\nif ($t >= 0.0 && $t < 0.5){   \n\ttranslate(v = [15.0000000000, 0.0000000000]) {\n\t\tsquare(size = 10);\n\t}\n}\nif ($t >= 0.5 && $t < 1.0){   \n\ttranslate(v = [-15.0000000000, 0.0000000000]) {\n\t\tsquare(size = 10);\n\t}\n}\n'

        self.assertEqual(expected, actual)

    def test_scad_render_to_file(self):
        a = circle(10)

        # No header, no included original code
        with TemporaryFileBuffer() as tmp:
            scad_render_to_file(a, filepath=tmp.name, include_orig_code=False)

        actual = tmp.contents
        expected = '\n\ncircle(r = 10);'

        self.assertEqual(expected, actual)

        # Header
        with TemporaryFileBuffer() as tmp:
            scad_render_to_file(a, filepath=tmp.name, include_orig_code=False,
                                file_header='$fn = 24;')

        actual = tmp.contents
        expected = '$fn = 24;\n\ncircle(r = 10);'

        self.assertEqual(expected, actual)

        # TODO: test include_orig_code=True, but that would have to
        # be done from a separate file, or include everything in this one


def single_test(test_dict):
    name, args, kwargs, expected = test_dict['name'], test_dict['args'], test_dict['kwargs'], test_dict['expected']

    def test(self):
        call_str = name + "("
        for k, v in args.items():
            call_str += "%s=%s, " % (k, v)
        for k, v in kwargs.items():
            call_str += "%s=%s, " % (k, v)
        call_str += ')'

        scad_obj = eval(call_str)
        actual = scad_render(scad_obj)

        self.assertEqual(expected, actual)

    return test


def generate_cases_from_templates():
    for test_dict in scad_test_case_templates:
        test = single_test(test_dict)
        test_name = "test_%(name)s" % test_dict
        setattr(TestSolidPython, test_name, test)


if __name__ == '__main__':
    generate_cases_from_templates()
    unittest.main()
