from math import *
from pyopenscad import *
from testpng import *
from inset import *
from trianglemath import *

rn = 3*64
#r = 10
innerR=25
gap = 0.5
wall = 1.50
baseH=2
gripH=9
hn=90
s = 0.775




h = hn*s
hone = h/hn

toph = (h-gripH)+3



depth=[]

def flip(img):
  #for l in img:
  #  l.reverse()
  img.reverse()
  return img


for i in range(0, hn):
  depth.append([])
  for j in range(0, rn):
    depth[i].append(0.0)

depth = getPNG('playground/maze7.png')
depth = flip(depth)

def getPx(x, y, default):
  x = int(x)
  y = int(y)
  x = x % len(depth[0])
  if (y >= len(depth)):
    y = len(depth) - 1
  if (x >= 0 and x < len(depth[0]) and y >= 0 and y < len(depth)):
    return depth[y][x]
  return default

def myComp(x, y):
  d = Tripple2Vec3D(y).angle2D() - Tripple2Vec3D(x).angle2D()
  if (d  < 0):
    return -1
  elif (d == 0):
    return 0
  else:
    return 1

def bumpMapCylinder(theR, hn, inset, default):
  pts = []
  trls = []
  for i in xrange(0, hn):
    circ = []
    for j in xrange(0, rn):
        a = j*2*pi/rn
        r = theR - ((255-getPx(j, i, default))/150.0)
        p = [r*cos(a), r*sin(a), i*hone]
        circ.append(p)
    circ = insetPoly(circ, inset)
    #circ.sort(lambda x, y: -1 if (Tripple2Vec3D(y).angle2D() - Tripple2Vec3D(x).angle2D() < 0) else 1)
    aold = Tripple2Vec3D(circ[0]).angle2D()
    for c in circ:
      a = Tripple2Vec3D(c).angle2D()
      #print a
      if (a > aold and (abs(a-aold) < 1*pi)):
        #print a, aold
        #exit()
        pass
      aold = a
      pts.append(c)

  pts.append([0, 0, 0])
  pts.append([0, 0, i*hone])

  for j in range(0, rn):
    t = [j, (j+1)%rn, rn*hn]
    trls.append(t)
    t = [(rn*hn-1)-j, (rn*hn-1)-((j+1)%rn), rn*hn+1]
    trls.append(t)
    for i in range(0, hn-1):
      p1 = i*rn+((j+1)%rn)
      p2 = i*rn+j
      p3 = (i+1)*rn+j
      p4 = (i+1)*rn+((j+1)%rn)
      a1 = angleBetweenPlanes([pts[p1], pts[p2], pts[p3]], [pts[p4], pts[p1], pts[p3]])
      a1 = min(a1, pi-a1)
      a2 = angleBetweenPlanes([pts[p2], pts[p1], pts[p4]], [pts[p2], pts[p3], pts[p4]])
      a2 = min(a2, pi-a2)
      #print a1, a2
      if (a1 < a2):
        t = [p1, p2, p3]
        trls.append(t)
        t = [p4, p1, p3]
        trls.append(t)
      else:
        t = [p2, p4, p1]
        trls.append(t)
        t = [p2, p3, p4]
        trls.append(t)

  return polyhedron(pts, trls, 6)

# to generate the top part
part = 1

# to generate the bottom part
# part = 2

if part==1:
  d = difference()
  u = union()
  u.add(bumpMapCylinder(innerR, hn, 0, 255))
  u.add(cylinder(r=innerR+wall+gap, h=gripH))
  d.add(u)
  #u.add(translate([80,0,0]).add(bumpMapCylinder(innerR, wall)))
  d.add(intersection().add(bumpMapCylinder(innerR, hn+2, wall, 0).set_modifier("")).add(translate([0,0,baseH]).add(cylinder(r=innerR+2*wall,h=h*1.1).set_modifier(""))))
  #u.add()
  print "$fa=2; $fs=0.5;\n"
  print d.render()
elif part==2:
  top = difference()
  u = union()
  u2 = union()
  top.add(u)
  d = difference()
  d.add(cylinder(r = innerR+wall+gap, h=toph))
  d.add(translate([0,0,baseH]).add(cylinder(r = innerR+gap, h=toph)))
  u.add(d)
  top.add(u2)
  for i in range(0,3):
    a = i * 2*pi/3.0
    r = innerR+gap+wall/2
    u.add(translate([(r-0.3)*cos(a),(r-0.3)*sin(a), toph-6]).add(sphere(r=2.4)))
    u2.add(translate([(r+wall-0.3)*cos(a),(r+wall-0.3)*sin(a), toph-6]).add(sphere(r=2.4)))
  #top.add(cylinder(r = innerR+wall+gap, h=h))
  print "$fa=2; $fs=0.5;\n"
  print top.render()
else:
  top = difference()
  u = union()
  u2 = union()
  top.add(u)
  d = difference()
  d.add(cylinder(r = innerR+wall+gap, h=6))
  d.add(translate([0,0,-baseH]).add(cylinder(r = innerR+gap, h=h)))
  u.add(d)
  top.add(u2)
  for i in range(0,3):
    a = i * 2*pi/3.0
    r = innerR+gap+wall/2
    u.add(translate([r*cos(a),r*sin(a), 4]).add(sphere(r=2.3)))
    u2.add(translate([(r+wall)*cos(a),(r+wall)*sin(a), 4]).add(sphere(r=2.3)))
  #top.add(cylinder(r = innerR+wall+gap, h=h))
  print "//$fn=20;\n"
  print top.render()






