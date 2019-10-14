from math import sqrt


class Vec2D:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def set(self, x, y):
        self.x = x
        self.y = y

    def times(self, t):
        return Vec2D(self.x * t, self.y * t)

    def add(self, v):
        self.x += v.x
        self.y += v.y

    def plus(self, v):
        return Vec2D(self.x + v.x, self.y + v.y)

    def minus(self, v):
        return Vec2D(self.x - v.x, self.y - v.y)

    def len(self):
        return sqrt(self.x * self.x + self.y * self.y)

    def normalize(self):
        l = self.len()
        self.x /= l
        self.y /= l

    def asTripple(self, z):
        return [self.x, self.y, z]

    def scalarProduct(self, v):
        return self.x * v.x + self.y * v.y

    def interpolate(self, v, t):
        return Vec2D(self.x * t + v.x * (1.0 - t), self.y * t + v.y * (1.0 - t))


class MetaCADLine:

    def __init__(self, s, e):
        self.start = Vec2D(s.x, s.y)
        self.end = Vec2D(e.x, e.y)
        self.dir = self.end.minus(self.start)
        self.normal = Vec2D(self.dir.x, self.dir.y)
        self.normal.normalize()
        self.normal.set(-self.normal.y, self.normal.x)

    def parallelMove(self, d):
        move = self.normal.times(d)
        self.start.add(move)
        self.end.add(move)

    def intersect(self, l):
        solve = LinearSolve2(l.dir.x, -self.dir.x, l.dir.y, -self.dir.y,
                             self.start.x - l.start.x, self.start.y - l.start.y)
        if solve.error:
            return None
        else:
            point = self.start.plus(self.dir.times(solve.x2))
            return Vec2D(point.x, point.y)


# matrix looks like this
# a b
# c d
def det(a, b, c, d):
    return a * d - b * c


# solves system of 2 linear equations in 2 unknown


class LinearSolve2:
    # the equations look like this looks like this
    # x1*a + x2*b = r1
    # x1*c + x2*d = r2

    def __init__(self, a, b, c, d, r1, r2):
        q = det(a, b, c, d)
        if abs(q) < 0.000000001:
            self.error = True
        else:
            self.error = False
            self.x1 = det(r1, b, r2, d) / q
            self.x2 = det(a, r1, c, r2) / q


def asVec2D(l):
    return Vec2D(l[0], l[1])


def insetPoly(poly, inset):
    points = []
    for i in range(len(poly)):
        iprev = (i + len(poly) - 1) % len(poly)
        inext = (i + 1) % len(poly)

        prev = MetaCADLine(asVec2D(poly[iprev]), asVec2D(poly[i]))
        next = MetaCADLine(asVec2D(poly[i]), asVec2D(poly[inext]))

        prev.parallelMove(inset)
        next.parallelMove(inset)

        intersect = prev.intersect(next)
        if intersect is None:
            # take parallel moved poly[i]
            # from the line thats longer (in case we    have a degenerate line
            # in there)
            if prev.dir.len() < next.dir.len():
                intersect = Vec2D(next.start.x, next.start.y)
            else:
                intersect = Vec2D(prev.end.x, prev.end.y)
        points.append(intersect.asTripple(poly[i][2]))

    istart = -1
    ilen = 0
    for i in range(len(poly)):
        iprev = (i + len(poly) - 1) % len(poly)
        prev = MetaCADLine(asVec2D(poly[iprev]), asVec2D(poly[i]))
        oldnorm = Vec2D(prev.normal.x, prev.normal.y)
        newLine = MetaCADLine(asVec2D(points[iprev]), asVec2D(points[i]))
        diff = newLine.normal.minus(oldnorm).len()
        if diff > 0.1:
            if istart == -1:
                istart = i
                ilen = 1
            else:
                ilen += 1
        else:
            if ilen > 0:
                if istart != 0:
                    idxs = (len(poly) + istart - 1) % len(poly)
                    idxe = i % len(poly)
                    p1 = points[idxs]
                    p2 = points[idxe]
                    for j in range(istart, i):
                        t = float(1 + j - istart) / (1 + i - istart)
                        points[j] = [
                            p2[0] * t + p1[0] * (1 - t),
                            p2[1] * t + p1[1] * (1 - t),
                            p2[2] * t + p1[2] * (1 - t)
                        ]
                    istart = -1
                    ilen = 0
    return points
