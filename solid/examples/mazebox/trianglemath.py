from math import acos, atan2, pi, sqrt


def Tripple2Vec3D(t):
    return Vec3D(t[0], t[1], t[2])


class Vec3D:

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def angle2D(self):
        a = atan2(self.x, self.y)
        if a < 0:
            a += 2 * pi
        return a

    def set(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def times(self, t):
        return Vec3D(self.x * t, self.y * t, self.z * t)

    # changes the object itself
    def add(self, v):
        self.x += v.x
        self.y += v.y
        self.z += v.z

    def plus(self, v):
        return Vec3D(self.x + v.x, self.y + v.y, self.z + v.z)

    def minus(self, v):
        return Vec3D(self.x - v.x, self.y - v.y, self.z - v.z)

    def len(self):
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    # changes the object itself
    def normalize(self):
        l = self.len()
        self.x /= l
        self.y /= l
        self.z /= l

    def asTripple(self):
        return [self.x, self.y, self.z]

    def scalarProduct(self, v):
        return self.x * v.x + self.y * v.y + self.z * v.z

    def crossProduct(self, v):
        return Vec3D(self.y * v.z - self.z * v.y,
                     self.z * v.x - self.x * v.z,
                     self.x * v.y - self.y * v.x)


def planeNormal(p):
    t1 = Tripple2Vec3D(p[0])
    t2 = Tripple2Vec3D(p[1])
    t3 = Tripple2Vec3D(p[2])
    t1.add(t3.times(-1))
    t2.add(t3.times(-1))
    return t1.crossProduct(t2)


# plane defined by a list of three len 3 lists of points in R3
def angleBetweenPlanes(p1, p2):
    n1 = planeNormal(p1)
    n2 = planeNormal(p2)
    n1.normalize()
    n2.normalize()

    s = n1.scalarProduct(n2)
    if s > 1:
        s = 1
    if s < -1:
        s = -1
    return acos(s)
