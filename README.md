PyOpenSCAD/ SolidPython
-----------------------

PyOpenSCAD is a generalization of Phillip Tiefenbacher's openscad module, 
found at http://www.thingiverse.com/thing:1481.  It generates valid OpenSCAD 
code from Python code with minimal overhead.  Here's a simple example:
    
This Python code: 

    from pyopenscad import *
    d = difference()(
        cube(10),
        sphere(15)
    )
    print scad_render( d)
 

Generates this OpenSCAD code:

    difference(){
        cube(10);
        sphere(15);
    }

Steps to using PyOpenSCAD
-------------------------
*   ```from pyopenscad import *```
*   call ```use( "/path/to/scadfile.scad")``` or ```include("/path/to/scadfile.scad")```
    for any included SCAD code
*   OpenSCAD uses curly-brace blocks ({}) to create its tree.  PyOpenSCAD uses
    parentheses with comma-delimited lists.
    *   OpenSCAD:
    
    difference(){
        cube(10);
        sphere(15);
    }

    *   PyOpenSCAD:
    
    d = difference()(
        cube(10),  # Note the comma between each element!
        sphere(15)
    )
           
*   Call ```scad_render( py_scad_obj)``` to generate SCAD code. This returns a string 
    of valid OpenSCAD code.
*   *or*: call ```scad_render_to_file( py_scad_obj, filepath)``` to
    store that code in a file. 
*   If 'filepath' is open in the OpenSCAD IDE and Design =>
    'Automatic Reload and Compile' is checked, calling
    scad_render_to_file() from Python will load the object in
    the IDE.
*   Alternately, you could call OpenSCAD's command line and render straight 
    to STL.   

Extra syntactic sugar
---------------------
### Basic operators
Following Elmo Mäntynen's suggestion, SCAD objects override 
the basic operators + (union), - (difference), and * (intersection).
So

    c = cylinder( r=10, h=5) + cylinder( r=2, h=30)
is the same as:

    c = union()(
        cylinder( r=10, h=5),
        cylinder( r=2, h=30)
    )

Likewise:

    c = cylinder( r=10, h=5)
    c -= cylinder( r=2, h=30)

is the same as:

    c = difference()(
        cylinder( r=10, h=5),
        cylinder( r=2, h=30)
    )

SP_utils
--------
I've been adding utilities to sp_utils.py.  Currently these include:
### Basic color library
I took this from someone on Thingiverse and I'm 
ashamed that I can't find the original source.  I owe someone some 
attribution.
    
### Directions: (up, down, left, right, forward, back) for arranging things:
    
    up(10)(
        cylinder()
    )

seems a lot clearer to me than:

    transform( [0,0,10])(
        cylinder()
    )
    
Again, I took this from someone's SCAD work and have lost track of the 
original author.  My apologies.
    
### Arcs
I've found this useful for fillets and rounds.
```arc( rad=10, 90, 210)``` draws an arc of radius 10 counterclockwise from 90 to 210 degrees. 
```arc( rad=10, 0, 90, invert=True )``` draws the portion of a 10x10 square NOT in a 90 degree circle of radius 10.
This is the shape you need to add to make fillets or remove to make rounds.
    
    
### Bill Of Materials
Put ```@part()``` before any method that defines a part, then 
call ```bill_of_materials()``` after the program is run, and all parts will be 
counted, priced and reported. Check it out.
    
Advantages
----------
Because you're using Python, a lot of things are easy that would be hard or 
impossible in pure OpenSCAD.  Among these are:
* recursion
* built-in dictionary types
* mutable, slice-able list and string types
* external libraries (images! 3D geometry!  web-scraping! ...)

Enjoy, and please send any questions or bug reports to me at evan_t_jones@mac.com. Cheers!
Evan
