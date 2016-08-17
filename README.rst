pysolid
=======

-  `pysolid: OpenSCAD for Python <#solidpython--openscad-for-python>`__
-  `Advantages <#advantages>`__
-  `Installing pysolid <#installing-solidpython>`__
-  `Using pysolid <#using-solidpython>`__
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
   -  `Offsets <#offsets>`__
   -  `Extrude Along Path <#extrude_along_path>`__
   -  `Basic color library <#basic-color-library>`__
   -  `Bill Of Materials <#bill-of-materials>`__

-  `solid.screw\_thread <#solidscrew_thread>`__
-  `Contact <#contact>`__
-  `License <#license>`__

pysolid: OpenSCAD for Python
----------------------------

pysolid is a fork of [SolidPython]
(http://github.com/SolidCode/SolidPython.git), which is a generalization
of Phillip Tiefenbacher's openscad module, found on
`Thingiverse <http://www.thingiverse.com/thing:1481>`__. It generates
valid OpenSCAD code from Python code with minimal overhead. Here's a
simple example:

This Python code:

::

    from solid import *
    d = difference()(
        cube(10),
        sphere(15)
    )
    print(scad_render(d))

Generates this OpenSCAD code:

::

    difference(){
        cube(10);
        sphere(15);
    }

That doesn't seem like such a savings, but the following pysolid code is
a lot shorter (and I think a lot clearer) than the SCAD code it compiles
to:

::

    d = cube(5) + right(5)(sphere(5)) - cylinder(r=2, h=6)

Generates this OpenSCAD code:

::

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
----------

Because you're using Python, a lot of things are easy that would be hard
or impossible in pure OpenSCAD. Among these are:

-  built-in dictionary types
-  mutable, slice-able list and string types
-  recursion
-  external libraries (images! 3D geometry! web-scraping! ...)

Installing pysolid
------------------

-  Install via
   `PyPI <python%20setup.py%20sdist%20bdist_wininst%20upload>`__:

   ::

       pip install pysolid

   (You may need to use ``sudo pip install solidpython``, depending on
   your environment.)

-  **OR:** Download pysolid (Click
   `here <https://github.com/plumps/pysolid/archive/master.zip>`__ to
   download directly, or use git to pull it all down)

   (Note that pysolid also depends on the
   `PyEuclid <http://pypi.python.org/pypi/euclid>`__ Vector math
   library, installable via ``sudo pip install euclid``)

   -  Unzip the file, probably in ~/Downloads/pysolid-master
   -  In a terminal, cd to location of file:

      ::

          cd ~/Downloads/pysolid-master

   -  Run the install script:

      ::

          sudo python setup.py --install

Using pysolid
-------------

-  Include pysolid at the top of your Python file:

   ::

       from solid import *
       from solid.utils import *  # Not required, but the utils module is useful

-  To include other scad code, call ``use("/path/to/scadfile.scad")`` or
   ``include("/path/to/scadfile.scad")``. This is identical to what you
   would do in OpenSCAD.
-  OpenSCAD uses curly-brace blocks ({}) to create its tree. pysolid
   uses parentheses with comma-delimited lists. **OpenSCAD:**

   ::

       difference(){
           cube(10);
           sphere(15);
       }

   **pysolid:**

   ::

       d = difference()(
           cube(10),  # Note the comma between each element!
           sphere(15)
       )

-  Call ``scad_render(py_scad_obj)`` to generate SCAD code. This returns
   a string of valid OpenSCAD code.
-  *or*: call ``scad_render_to_file(py_scad_obj, filepath)`` to store
   that code in a file.
-  If 'filepath' is open in the OpenSCAD IDE and Design => 'Automatic
   Reload and Compile' is checked (in the OpenSCAD IDE), calling
   ``scad_render_to_file()`` from Python will load the object in the
   IDE.
-  Alternately, you could call OpenSCAD's command line and render
   straight to STL.

Example Code
------------

The best way to learn how pysolid works is to look at the included
example code. If you've installed pysolid, the following line of Python
will print(the location of ) the examples directory:

::

    import os, solid; print(os.path.dirname(solid.__file__) + '/examples')

Or browse the example code on Github
`here <https://github.com/plumps/pysolid/tree/master/solid/examples>`__

Adding your own code to the example file
`solid/examples/solidpython\_template.py <https://github.com/plumps/pysolid/blob/master/solid/examples/solidpython_template.py>`__
will make some of the setup easier.

Extra syntactic sugar
---------------------

Basic operators
~~~~~~~~~~~~~~~

Following Elmo Mäntynen's suggestion, SCAD objects override the basic
operators + (union), - (difference), and \* (intersection). So

::

    c = cylinder(r=10, h=5) + cylinder(r=2, h=30)

is the same as:

::

    c = union()(
        cylinder(r=10, h=5),
        cylinder(r=2, h=30)
    )

Likewise:

::

    c = cylinder(r=10, h=5)
    c -= cylinder(r=2, h=30)

is the same as:

::

    c = difference()(
        cylinder(r=10, h=5),
        cylinder(r=2, h=30)
    )

First-class Negative Space (Holes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OpenSCAD requires you to be very careful with the order in which you add
or subtract objects. pysolid's ``hole()`` function makes this process
easier.

Consider making a joint where two pipes come together. In OpenSCAD you
need to make two cylinders, union them, then make two smaller cylinders,
union them, then subtract the smaller from the larger.

Using hole(), you can make a pipe, specify that its center should remain
open, and then add two pipes together knowing that the central void area
will stay empty no matter what other objects are added to that
structure.

Example:

::

    outer = cylinder(r=pipe_od, h=seg_length)
    inner = cylinder(r=pipe_id, h=seg_length)
    pipe_a = outer - hole()(inner)

Once you've made something a hole, eventually you'll want to put
something, like a bolt, into it. To do this, we need to specify that
there's a given 'part' with a hole and that other parts may occupy the
space in that hole. This is done with the ``part()`` function.

See
`solid/examples/hole\_example.py <https://github.com/plumps/pysolid/blob/master/solid/examples/hole_example.py>`__
for the complete picture.

Animation
~~~~~~~~~

OpenSCAD has a special variable, ``$t``, that can be used to animate
motion. pysolid can do this, too, using the special function
``scad_render_animated_file()``.

See
`solid/examples/animation\_example.py <https://github.com/plumps/pysolid/blob/master/solid/examples/animation_example.py>`__
for more details.

solid.utils
-----------

pysolid includes a number of useful functions in
`solid/utils.py <https://github.com/plumps/pysolid/blob/master/solid/utils.py>`__.
Currently these include:

Directions: (up, down, left, right, forward, back) for arranging things:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    up(10)(
        cylinder()
    )

seems a lot clearer to me than:

::

    translate( [0,0,10])(
        cylinder()
    )

| I took this from someone's SCAD work and have lost track of the
  original author.
| My apologies.

Arcs
~~~~

I've found this useful for fillets and rounds.

::

    arc(rad=10, start_degrees=90, end_degrees=210)

draws an arc of radius 10 counterclockwise from 90 to 210 degrees.

::

    arc_inverted(rad=10, start_degrees=0, end_degrees=90) 

draws the portion of a 10x10 square NOT in a 90 degree circle of radius
10. This is the shape you need to add to make fillets or remove to make
rounds.

Offsets
~~~~~~~

To offset a set of points in one direction or another (inside or outside
a closed figure, for example) use
``solid.utils.offset_points(point_arr, offset, inside=True)``

Note that, for a non-convex figure, inside and outside may be
non-intuitive. The simple solution is to manually check that your offset
is going in the direction you intend, and change the boolean value of
``inside`` if you're not happy.

See the code for futher explanation. Improvements on the inside/outside
algorithm would be welcome.

Extrude Along Path
~~~~~~~~~~~~~~~~~~

``solid.utils.extrude_along_path(shape_pts, path_pts, scale_factors=None)``

See
`solid/examples/path\_extrude\_example.py <https://github.com/plumps/pysolid/blob/master/solid/examples/path_extrude_example.py>`__
for use.

Basic color library
~~~~~~~~~~~~~~~~~~~

You can change an object's color by using the OpenSCAD
``color([rgba_array])`` function:

::

    transparent_blue = color([0,0,1, 0.5])(cube(10))  # Specify with RGB[A]
    red_obj = color(Red)(cube(10))                    # Or use predefined colors

These colors are pre-defined in solid.utils:

+------------------+---------------+--------------------+
| Red              | Green         |     Blue           |
+------------------+---------------+--------------------+
| Cyan             | Magenta       |     Yellow         |
+------------------+---------------+--------------------+
| Black            | White         |     Transparent    |
+------------------+---------------+--------------------+
| Oak              | Pine          |     Birch          |
+------------------+---------------+--------------------+
| Iron             | Steel         |     Stainless      |
+------------------+---------------+--------------------+
| Aluminum         | Brass         |     BlackPaint     |
+------------------+---------------+--------------------+
| FiberBoard       |               |                    |
+------------------+---------------+--------------------+

They're a conversion of the materials in the `MCAD OpenSCAD
library <https://github.com/openscad/MCAD>`__, as seen [here]
(https://github.com/openscad/MCAD/blob/master/materials.scad).

Bill Of Materials
~~~~~~~~~~~~~~~~~

Put ``@bom_part()`` before any method that defines a part, then call
``bill_of_materials()`` after the program is run, and all parts will be
counted, priced and reported.

The example file
`solid/examples/bom\_scad.py <https://github.com/plumps/pysolid/blob/master/solid/examples/bom_scad.py>`__
illustrates this. Check it out.

solid.screw\_thread
===================

solid.screw\_thread includes a method, thread() that makes internal and
external screw threads.

See
`solid/examples/screw\_thread\_example.py <https://github.com/plumps/pysolid/blob/master/solid/examples/screw_thread_example.py>`__
for more details.
