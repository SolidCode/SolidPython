SolidPython
-----------

.. image:: https://circleci.com/gh/SolidCode/SolidPython.svg?style=shield
    :target: https://circleci.com/gh/SolidCode/SolidPython
.. image:: https://readthedocs.org/projects/solidpython/badge/?version=latest
    :target: http://solidpython.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

-  `SolidPython: OpenSCAD for
   Python <#solidpython--openscad-for-python>`__
-  `Advantages <#advantages>`__
-  `Installing SolidPython <#installing-solidpython>`__
-  `Using SolidPython <#using-solidpython>`__
-  `Importing OpenSCAD Code <#importing-openscad-code>`__
-  `Example Code <#example-code>`__
-  `Extra syntactic sugar <#extra-syntactic-sugar>`__

   -  `Basic operators <#basic-operators>`__
   -  `First-class Negative Space
      (Holes) <#first-class-negative-space-holes>`__
   -  `Animation <#animation>`__

-  `solid.utils <#solidutils>`__

   -  `Directions: (up, down, left, right, forward, back) for arranging
      things: <#directions-up-down-left-right-forward-back-for-arranging-things>`__
   -  `Arcs <#arcs>`__
   -  `Extrude Along Path <#extrude_along_path>`__
   -  `Bill Of Materials <#bill-of-materials>`__

-  `solid.screw\_thread <#solidscrew_thread>`__
-  `solid.splines <#solidsplines>`__
-  `Jupyter Renderer <#jupyter-renderer>`__
-  `Contact <#contact>`__
-  `License <#license>`__

SolidPython: OpenSCAD for Python
================================

SolidPython is a generalization of Phillip Tiefenbacher's openscad
module, found on
`Thingiverse <http://www.thingiverse.com/thing:1481>`__. It generates
valid OpenSCAD code from Python code with minimal overhead. Here's a
simple example:

This Python code:

.. code:: python

    from solid import *
    d = difference()(
        cube(10),
        sphere(15)
    )
    print(scad_render(d))

Generates this OpenSCAD code:

.. code:: python

    difference(){
        cube(10);
        sphere(15);
    }

That doesn't seem like such a savings, but the following SolidPython
code is a lot shorter (and I think clearer) than the SCAD code it compiles to:

.. code:: python

    from solid import *
    from solid.utils import *
    d = cube(5) + right(5)(sphere(5)) - cylinder(r=2, h=6)

Generates this OpenSCAD code:

.. code::

    difference(){
        union(){
            cube(5);
            translate( [5, 0,0]){
                sphere(5);
            }
        }
        cylinder(r=2, h=6);
    }

Advantages
==========

Because you're using Python, a lot of things are easy that would be hard
or impossible in pure OpenSCAD. Among these are:

-  built-in dictionary types
-  mutable, slice-able list and string types
-  recursion
-  external libraries (images! 3D geometry! web-scraping! ...)

Installing SolidPython
======================

-  Install latest release via
   `PyPI <https://pypi.python.org/pypi/solidpython>`__:

   .. code:: bash

       pip install solidpython

   (You may need to use ``sudo pip install solidpython``, depending on
   your environment. This is commonly discouraged though. You'll be happiest 
   working in a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`__ 
   where you can easily control dependencies for a given project)

- Install current master straight from Github:

  .. code:: bash

      pip install git+https://github.com/SolidCode/SolidPython.git

Using SolidPython
=================

-  Include SolidPython at the top of your Python file:

   .. code:: python

       from solid import *
       from solid.utils import *  # Not required, but the utils module is useful

   (See `this issue <https://github.com/SolidCode/SolidPython/issues/114>`__ for 
   a discussion of other import styles)

-  OpenSCAD uses curly-brace blocks ({}) to create its tree. SolidPython
   uses parentheses with comma-delimited lists. 
   
   **OpenSCAD:**

   .. code::

       difference(){
           cube(10);
           sphere(15);
       }

   **SolidPython:**

   .. code::

       d = difference()(
           cube(10),  # Note the comma between each element!
           sphere(15)
       )

-  Call ``scad_render(py_scad_obj)`` to generate SCAD code. This returns
   a string of valid OpenSCAD code.
-  *or*: call ``scad_render_to_file(py_scad_obj, filepath.scad)`` to store
   that code in a file.
-  If ``filepath.scad`` is open in the OpenSCAD IDE and Design => 'Automatic
   Reload and Compile' is checked in the OpenSCAD IDE, running
   ``scad_render_to_file()`` from Python will load the object in the
   IDE.
-  Alternately, you could call OpenSCAD's command line and render
   straight to STL.

Importing OpenSCAD code
=======================

- Use ``solid.import_scad(path)`` to import OpenSCAD code. Relative paths will 
check the current location designated in `OpenSCAD library directories <https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Libraries>`__.

**Ex:** 

``scadfile.scad``

.. code::

    module box(w,h,d){
        cube([w,h,d]);
    }

``your_file.py``

.. code:: python

    from solid import *

    scadfile = import_scad('/path/to/scadfile.scad') 
    b = scadfile.box(2,4,6)
    scad_render_to_file(b, 'out_file.scad')

- Recursively import OpenSCAD code by calling ``import_scad()`` with a directory argument.

.. code:: python

    from solid import *

    # MCAD is OpenSCAD's most common utility library: https://github.com/openscad/MCAD
    # If it's installed for OpenSCAD (on MacOS, at: ``$HOME/Documents/OpenSCAD/libraries``)
    mcad = import_scad('MCAD')

    # MCAD contains about 15 separate packages, each included as its own namespace
    print(dir(mcad)) # => ['bearing', 'bitmap', 'boxes', etc...]
    mount = mcad.motors.stepper_motor_mount(nema_standard=17)
    scad_render_to_file(mount, 'motor_mount_file.scad')

- OpenSCAD has the ``use()`` and ``include()`` statements for importing SCAD code, and SolidPython has them, too. They pollute the global namespace, though, and you may have better luck with ``import_scad()``,

**Ex:**

``scadfile.scad``

.. code::

    module box(w,h,d){
        cube([w,h,d]);
    }

``your_file.py``

.. code:: python

    from solid import *

    # use() puts the module `box()` into the global namespace
    use('/path/to/scadfile.scad') 
    b = box(2,4,6)
    scad_render_to_file(b, 'out_file.scad')


Example Code
============

The best way to learn how SolidPython works is to look at the included
example code. If you've installed SolidPython, the following line of
Python will print(the location of ) the examples directory:

.. code:: python

    import os, solid; print(os.path.dirname(solid.__file__) + '/examples')
        

Or browse the example code on Github
`here <https://github.com/SolidCode/SolidPython/tree/master/solid/examples>`__

Adding your own code to the example file
`solid/examples/solidpython_template.py <https://github.com/SolidCode/SolidPython/blob/master/solid/examples/solidpython_template.py>`__
will make some of the setup easier.

Extra syntactic sugar
=====================

Basic operators
---------------

Following Elmo Mäntynen's suggestion, SCAD objects override the basic
operators + (union), - (difference), and \* (intersection). So

.. code:: python

    c = cylinder(r=10, h=5) + cylinder(r=2, h=30)

is the same as:

.. code:: python

    c = union()(
        cylinder(r=10, h=5),
        cylinder(r=2, h=30)
    )

Likewise:

.. code:: python

    c = cylinder(r=10, h=5)
    c -= cylinder(r=2, h=30)

is the same as:

.. code:: python

    c = difference()(
        cylinder(r=10, h=5),
        cylinder(r=2, h=30)
    )

First-class Negative Space (Holes)
----------------------------------

OpenSCAD requires you to be very careful with the order in which you add
or subtract objects. SolidPython's ``hole()`` function makes this
process easier.

Consider making a joint where two pipes come together. In OpenSCAD you
need to make two cylinders, union them, then make two smaller cylinders,
union them, then subtract the smaller from the larger.

Using hole(), you can make a pipe, specify that its center should remain
open, and then add two pipes together knowing that the central void area
will stay empty no matter what other objects are added to that
structure.

Example:

.. code:: python

    outer = cylinder(r=pipe_od, h=seg_length)
    inner = cylinder(r=pipe_id, h=seg_length)
    pipe_a = outer - hole()(inner)

Once you've made something a hole, eventually you'll want to put
something, like a bolt, into it. To do this, we need to specify that
there's a given 'part' with a hole and that other parts may occupy the
space in that hole. This is done with the ``part()`` function.

See
`solid/examples/hole_example.py <https://github.com/SolidCode/SolidPython/blob/master/solid/examples/hole_example.py>`__
for the complete picture.

Animation
---------

OpenSCAD has a special variable, ``$t``, that can be used to animate
motion. SolidPython can do this, too, using the special function
``scad_render_animated_file()``.

See
`solid/examples/animation_example.py <https://github.com/SolidCode/SolidPython/blob/master/solid/examples/animation_example.py>`__
for more details.

solid.utils
===========

SolidPython includes a number of useful functions in
`solid/utils.py <https://github.com/SolidCode/SolidPython/blob/master/solid/utils.py>`__.
Currently these include:

Directions: (up, down, left, right, forward, back) for arranging things:
------------------------------------------------------------------------

.. code:: python

    up(10)(
        cylinder()
    )

seems a lot clearer to me than:

.. code:: python

    translate( [0,0,10])(
        cylinder()
    )

| I took this from someone's SCAD work and have lost track of the
  original author.
| My apologies.

Arcs
----

I've found this useful for fillets and rounds.

.. code:: python

    arc(rad=10, start_degrees=90, end_degrees=210)

draws an arc of radius 10 counterclockwise from 90 to 210 degrees.

.. code:: python

    arc_inverted(rad=10, start_degrees=0, end_degrees=90) 

draws the portion of a 10x10 square NOT in a 90 degree circle of radius
10. This is the shape you need to add to make fillets or remove to make
rounds.

Extrude Along Path
------------------

``solid.utils.extrude_along_path()`` is quite powerful. It can do everything that
OpenSCAD's ``linear_extrude() `` and ``rotate_extrude()`` can do, and lots, lots more. 
Scale to custom values throughout the extrusion. Rotate smoothly through the entire 
extrusion or specify particular rotations for each step. Apply arbitrary transform
functions to every point in the extrusion. 

See
`solid/examples/path_extrude_example.py <https://github.com/SolidCode/SolidPython/blob/master/solid/examples/path_extrude_example.py>`__
for use.

Bill Of Materials
-----------------

Put ``@bom_part()`` before any method that defines a part, then call
``bill_of_materials()`` after the program is run, and all parts will be
counted, priced and reported.

The example file
`solid/examples/bom_scad.py <https://github.com/SolidCode/SolidPython/blob/master/solid/examples/bom_scad.py>`__
illustrates this. Check it out.

solid.screw\_thread
-------------------

solid.screw\_thread includes a method, thread() that makes internal and
external screw threads.

See
`solid/examples/screw_thread_example.py <https://github.com/SolidCode/SolidPython/blob/master/solid/examples/screw_thread_example.py>`__
for more details.

solid.splines
-------------

`solid.splines` contains functions to generate smooth Catmull-Rom curves through
control points. 

::

    from solid import translate
    from solid.splines import catmull_rom_polygon, bezier_polygon
    from euclid3 import Point2

    points = [ Point2(0,0), Point2(1,1), Point2(2,1), Point2(2,-1) ]  
    shape = catmull_rom_polygon(points, show_controls=True)

    bezier_shape = translate([3,0,0])(bezier_polygon(points, subdivisions=20))
    
See 
`solid/examples/splines_example.py <https://github.com/SolidCode/SolidPython/blob/master/solid/examples/splines_example.py>`__ 
for more details and options.

Jupyter Renderer
----------------

Render SolidPython or OpenSCAD code in Jupyter notebooks using `ViewSCAD <https://github.com/nickc92/ViewSCAD>`__, or install directly via:

.. code:: bash

    pip install viewscad

(Take a look at the `repo page <https://github.com/nickc92/ViewSCAD>`__, though, since there's a tiny bit more installation required)

Contact
=======

Enjoy, and please send any questions or bug reports to me at
``evan_t_jones@mac.com``.

Cheers!

Evan

License
=======

This library is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.

This library is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
General Public License for more details.

`Full text of the
license <http://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt>`__.

Some class docstrings are derived from the `OpenSCAD User Manual
<https://en.wikibooks.org/wiki/OpenSCAD_User_Manual>`__, so 
are available under the `Creative Commons Attribution-ShareAlike License
<https://creativecommons.org/licenses/by-sa/3.0/>`__. 
