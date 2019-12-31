import euclid3
from euclid3 import Vector3, Vector2, Line3

# NOTE: The PyEuclid on PyPi doesn't include several elements added to
# the module as of 13 Feb 2013.  Add them here until euclid supports them

def as_arr_local2(self):
    return [self.x, self.y]

def as_arr_local3(self):
    return [self.x, self.y, self.z]

def set_length_local2(self, length):
    d = self.magnitude()
    if d:
        factor = length / d
        self.x *= factor
        self.y *= factor

    return self

def set_length_local3(self, length):
    d = self.magnitude()
    if d:
        factor = length / d
        self.x *= factor
        self.y *= factor
        self.z *= factor

    return self

def _intersect_line3_line3(A, B):
    # Connect A & B
    # If the length of the connecting segment  is 0, they intersect
    # at the endpoint(s) of the connecting segment
    sol = euclid3._connect_line3_line3(A, B)
    # TODO: Ray3 and LineSegment3 would like to be able to know
    # if their intersection points fall within the segment.
    if sol.magnitude_squared() < 0.001:
        return sol.p
    else:
        return None

def run_euclid_patch():
    if 'as_arr' not in dir(Vector3):
        Vector3.as_arr = as_arr_local3
    if 'as_arr' not in dir(Vector2):
        Vector2.as_arr = as_arr_local2

    if 'set_length' not in dir(Vector3):
        Vector3.set_length = set_length_local3
    if 'set_length' not in dir(Vector2):
        Vector2.set_length = set_length_local2
        
    if '_intersect_line3' not in dir(Line3):
        Line3._intersect_line3 = _intersect_line3_line3
