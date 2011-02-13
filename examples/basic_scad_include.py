#! /usr/bin/python
# -*- coding: UTF-8 -*-
import sys, os

# Make sure we have access to pyopenscad
superdir = os.path.dirname( os.path.dirname(__file__))
sys.path.append( superdir)

from pyopenscad import *
use( "../../stepper.scad") #  could also use 'include', but that has side-effects

print scad_render( motor())