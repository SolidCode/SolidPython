#! /usr/bin/python
# -*- coding: UTF-8 -*-
import os, sys, re



from pyopenscad import *
# use( '../Libs.scad')
use('/Users/jonese/Downloads/3D/SCAD/Libs.scad')
h = hex( width=10, height=10, flats= True, center=False)
g = roundRect()
t = union()
t.add(h)
t.add(g)
# print h.render()
print scad_render( h)