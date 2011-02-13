from pyopenscad import *
use( '/Users/jonese/Desktop/3D/SCAD/rambo-MCAD-ec568b4/boxes.scad')

d = difference()
d.add( roundedBox( size=[15, 20, 10], radius=2.5, sidesonly=False))
d.add( cube(8))

# render_to_file( d, '/path/my_notched_box.scad')
print scad_render( d)