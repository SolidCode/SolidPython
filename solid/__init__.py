# Some __init__ magic so we can include all solidpython code with:
#   from solid import *
#   from solid.utils import *
try:
    from solidpython import *
except ImportError:
    from solid.solidpython import *
