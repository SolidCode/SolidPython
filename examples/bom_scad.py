#! /usr/bin/python
# -*- coding: UTF-8 -*-

# Basic shape with several repeated parts, demonstrating the use of 
# sp_utils.bill_of_materials() 
# Writes a scad file to '$HOME/Desktop/BOM_example.scad'
#
# Basically:  
#   -- Define every part you want in the Bill of Materials in a function
#   -- Use the 'part' decorator ahead of the definition of each part's function
#           e.g.:  
                # @part()
                # def my_part():
                #     pass
#   -- Optionally, you can add a description and a per-unit cost to the 
#       decorator invocations.  If cost is supplied, 
#   -- To generate the bill of materials, call bill_of_materials()
#
#       -ETJ 08 Mar 2011

import os, sys

# Make sure we have access to pyopenscad
superdir = os.path.dirname( os.path.dirname(__file__))
sys.path.append( superdir)

from pyopenscad import *
from sp_utils import *

head_rad = 2.65
head_height = 2.8

nut_height = 2.3
nut_rad = 3

m3_rad = 1.4

doohickey_h = 5

def head():
    return cylinder( h=head_height, r =head_rad)


@part("M3x16 Bolt", 0.12)
def m3_16( a=3):
    bolt_height = 16
    m = union()(
            head(),
            translate( [0,0, -bolt_height])(
                cylinder( r=m3_rad, h=bolt_height)
            )
        )
    return m


@part("M3x12 Bolt", 0.09)
def m3_12():
    bolt_height = 12
    m = union()(
            head(),
            translate( [ 0, 0, -bolt_height])(
                cylinder( r=m3_rad, h=bolt_height)
            )
        )
    return m


@part()
def m3_nut():
    hx = cylinder( r=nut_rad, h=nut_height)
    hx.add_param('$fn', 6) # make the nut hexagonal
    n = difference()(
            hx,
            translate([0,0,-EPSILON])(
                cylinder( r=m3_rad, h=nut_height+2*EPSILON )
            )
        )
    return n


@part()
def doohickey():
    d = cube([30, 10, doohickey_h], center=True)
    hole_cyl = translate([0,0,-EPSILON])(
                    cylinder(r=m3_rad, h=doohickey_h+2*EPSILON )
                )
    d = difference()(
            cube([30, 10, doohickey_h], center=True),
            translate([-10, 0,0])( hole_cyl),
            hole_cyl,
            translate([10,0,0])( hole_cyl)
        )
    return d


def assemble():
    return union()(
                doohickey(),
                translate( [-10, 0, doohickey_h/2])(  m3_12()),
                translate( [ 0, 0, doohickey_h/2])(   m3_16()),
                translate( [10, 0, doohickey_h/2])(   m3_12()),
                # Nuts
                translate( [-10, 0, -nut_height-doohickey_h/2])(  m3_nut()),
                translate( [ 0, 0, -nut_height-doohickey_h/2])(   m3_nut()),
                translate( [10, 0, -nut_height-doohickey_h/2])(   m3_nut()),                
            )

if __name__ == '__main__':
    a = assemble()
    
    bom = bill_of_materials()
    print bom
    
    file_out = os.path.join( os.getenv('HOME'), 'Desktop', 'BOM_example.scad')
    scad_render_to_file( a, file_out)
