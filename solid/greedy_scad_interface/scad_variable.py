import math

sin = lambda x: ScadValue(f'sin({x})') if isinstance(x, ScadValue) else math.sin(x)
cos = lambda x: ScadValue(f'cos({x})') if isinstance(x, ScadValue) else math.cos(x)
tan = lambda x: ScadValue(f'tan({x})') if isinstance(x, ScadValue) else math.tan(x)
asin = lambda x: ScadValue(f'asin({x})') if isinstance(x, ScadValue) else math.asin(x)
acos = lambda x: ScadValue(f'acos({x})') if isinstance(x, ScadValue) else math.acos(x)
atan = lambda x: ScadValue(f'atan({x})') if isinstance(x, ScadValue) else math.atan(x)
sqrt = lambda x: ScadValue(f'sqrt({x})') if isinstance(x, ScadValue) else math.sqrt(x)
not_ = lambda x: ScadValue(f'!{x}')

class ScadValue:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'{self.value}'

    def __operator_base__(self, op, other):
        return ScadValue(f'({self} {op} {other})')

    def __unary_operator_base__(self, op):
        return ScadValue(f'({op}{self})')

    #basic operators +, -, *, /, %, **
    def __add__(self, other): return self.__operator_base__("+", other)
    def __sub__(self, other): return self.__operator_base__("-", other)
    def __mul__(self, other): return self.__operator_base__("*", other)
    def __mod__(self, other): return self.__operator_base__("%", other)
    def __pow__(self, other): return self.__operator_base__("^", other)
    def __truediv__(self, other): return self.__operator_base__("/", other)

    def __radd__(self, other): return self.__operator_base__("+", other)
    def __rsub__(self, other): return self.__operator_base__("-", other)
    def __rmul__(self, other): return self.__operator_base__("*", other)
    def __rmod__(self, other): return self.__operator_base__("%", other)
    def __rpow__(self, other): return self.__operator_base__("^", other)
    def __rtruediv__(self, other): return self.__operator_base__("/", other)

    #unary operators
    def __neg__(self): return self.__unary_operator_base__("-")

    #other operators
    def __abs__(self): return ScadValue(f'abs({self})')

    def __bool__(self):
        raise Exception("You can't use scad variables as truth statement because " +\
                        "we don't know the value of a customized variable at SolidPython " +\
                        "runtime.")

    def __illegal_operator__(self):
       raise Exception("You can't compare a ScadValue with something else, " +\
                       "because we don't know the customized value at SolidPythons runtime " +\
                       "because it might get customized at OpenSCAD runtime.")

    def __eq__(self, other): return self.__illegal_operator__()
    def __ne__(self, other): return self.__illegal_operator__()
    def __le__(self, other): return self.__illegal_operator__()
    def __ge__(self, other): return self.__illegal_operator__()
    def __lt__(self, other): return self.__illegal_operator__()
    def __gt__(self, other): return self.__illegal_operator__()

class ScadVariable(ScadValue):
    registered_variables = {}

    def __init__(self, name, default_value, options_str='', label='', tab=''):
        super().__init__(name)

        if name in self.registered_variables.keys():
            raise ValueError("Multiple instances of ScadVariable with the same name.")

        def_str = self.get_definition(name, default_value, options_str, label, tab)
        self.registered_variables.update({name : def_str})

    def get_definition(self, name, default_value, options_str, label, tab):
        tab = tab and f'/* [{tab}] */\n'
        label = label and f'//{label}\n'
        options_str = options_str and f' //{options_str}'

        if isinstance(default_value, str):
            default_value = f'"{default_value}"'

        return f'{tab}{label}{name} = {default_value};{options_str}'

