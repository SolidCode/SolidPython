#! /usr/bin/env python3

from numbers import Real

from typing import Callable, Union, Dict, List, Sequence, Any
from typing import Generator, TypeVar

Operator = Any

class CompoundFloat(float):
    def __new__(cls, val: Real, op: Operator = None, other: Real = None):
        val = val
        if op and other:
            val = op(val, other) 
        self =  super(CompoundFloat, cls).__new__(cls, val)
        # TODO: ensure that either op & other are defined, or neither are
        self.op = op
        self.other = other
        return self

    def op_string(self) -> str:
        # FIXME: add support for unary operators and non-infix ops like __ceil__()
        symbols = {
            '__add__': '+',
            # '__ceil__': '',
            '__eq__': '==',
            # '__float__': '',
            # '__floor__': '',
            '__floordiv__': '//',
            '__le__': '<=',
            '__lt__': '<',
            '__mod__': '%',
            '__mul__': '*',
            '__neg__': '-',
            '__pos__': '+',
            '__pow__': '**',
            '__radd__': '+',
            '__rfloordiv__': '//',
            '__rmod__': '%',
            '__rmul__': '*',
            # '__round__': '',
            '__rpow__': '**',
            '__rtruediv__': '/',
            '__truediv__': '/',
            # '__trunc__': '',

        }
        if self.op:
            result = symbols.get(self.op.__name__, '')
        else: 
            result = ''
        return result

    def __str__(self) -> str:
        val_str = f'{self.val}'
        op_str = f' {self.op_string()}' if self.op else ''
        other_str = f' {self.other}' if self.other else ''
        return f'({val_str}{op_str}{other_str})'

    def __add__(self, other:Real) ->        'CompoundFloat': return CompoundFloat(self, float.__add__, other)
    def __ceil__(self, other:Real) ->       'CompoundFloat': return CompoundFloat(self, float.__ceil__, other)
    def __eq__(self, other:Real) ->         'CompoundFloat': return CompoundFloat(self, float.__eq__, other)
    def __float__(self, other:Real) ->      'CompoundFloat': return CompoundFloat(self, float.__float__, other)
    def __floor__(self, other:Real) ->      'CompoundFloat': return CompoundFloat(self, float.__floor__, other)
    def __floordiv__(self, other:Real) ->   'CompoundFloat': return CompoundFloat(self, float.__floordiv__, other)
    def __le__(self, other:Real) ->         'CompoundFloat': return CompoundFloat(self, float.__le__, other)
    def __lt__(self, other:Real) ->         'CompoundFloat': return CompoundFloat(self, float.__lt__, other)
    def __mod__(self, other:Real) ->        'CompoundFloat': return CompoundFloat(self, float.__mod__, other)
    def __mul__(self, other:Real) ->        'CompoundFloat': return CompoundFloat(self, float.__mul__, other)
    # FIXME: CompoundFloat breaks on unary operators +/-/!  ?
    # def __neg__(self, other:Real) ->      'CompoundFloat': return CompoundFloat(self, float.__neg__, other)
    # def __pos__(self, other:Real) ->      'CompoundFloat': return CompoundFloat(self, float.__pos__, other)
    def __pow__(self, other:Real) ->        'CompoundFloat': return CompoundFloat(self, float.__pow__, other)
    def __radd__(self, other:Real) ->       'CompoundFloat': return CompoundFloat(self, float.__radd__, other)
    def __rfloordiv__(self, other:Real) ->  'CompoundFloat': return CompoundFloat(self, float.__rfloordiv__, other)
    def __rmod__(self, other:Real) ->       'CompoundFloat': return CompoundFloat(self, float.__rmod__, other)
    def __rmul__(self, other:Real) ->       'CompoundFloat': return CompoundFloat(self, float.__rmul__, other)
    def __round__(self, other:Real) ->      'CompoundFloat': return CompoundFloat(self, float.__round__, other)
    def __rpow__(self, other:Real) ->       'CompoundFloat': return CompoundFloat(self, float.__rpow__, other)
    def __rtruediv__(self, other:Real) ->   'CompoundFloat': return CompoundFloat(self, float.__rtruediv__, other)
    def __truediv__(self, other:Real) ->    'CompoundFloat': return CompoundFloat(self, float.__truediv__, other)
    def __trunc__(self, other:Real) ->      'CompoundFloat': return CompoundFloat(self, float.__trunc__, other)

class CompundInt(int):
    pass

class CompoundBoolean(int):
    pass

class CompoundString(str):
    pass

class Customizer():
    def scad_declaration(self):
        raise NotImplementedError

    def __str__(self):
        return self.name


class CustomizerSlider(CompoundFloat, Customizer):
    def __new__(cls, name:str, val:float, min_val:float=0, max_val:float = 1, step:float = None):
        inst =  super(CustomizerSlider, cls).__new__(cls, val)
        inst.val = val
        inst.name = name
        inst.min = min_val
        inst.max = max_val
        inst.step = step
        return inst

    def scad_declaration(self) -> str:
        # OpenSCAD's customizer makes a guess about step size if not supplied. 
        # Leave it out in that case and let OpenSCAD's logic handle it
        step_str = f': {self.step}' if self.step else ''
        return f'{self.name} = {self.val}; // [{self.min}{step_str}: {self.max}]\n'

    def __str__(self) -> str:
        return self.name

class CustomizerDropdownNumber(CompoundFloat, Customizer):
    def __new__(cls, name:str, val:float, options:Union[List[float],  Dict[float,str]]):
        self = super(CustomizerDropdownNumber, cls).__new__(cls, val)
        self.name = name
        self.val = val
        # TODO: validate that all entries in options are floats, or 
        # that self.options is a Dict[float, str]
        self.options = options
        return self
    
    def scad_declaration(self):
        options_str = f'{self.options}'
        if isinstance(self.options, dict):
            dict_pairs = [f'{k}:{v}' for k,v in self.options.items()]
            options_str = '[' + ', '.join(dict_pairs) + ']'
        return f'{self.name} = {self.val}; // {options_str}\n'

    def __str__(self):
        return self.name

class CustomizerDropdownString(CompoundString, Customizer):
    def __new__(cls, name:str, val:str, options:Union[List[str],  Dict[str,str]]):
        self =  super(CustomizerDropdownString, cls).__new__(cls, val)
        self.name = name
        self.val = val
        # TODO: validate that all entries in options are floats, or 
        # that self.options is a Dict[str, float]
        self.options = options
        return self

    def scad_declaration(self):
        if isinstance(self.options, dict):
            opts = [f'{k}:{v}' for k,v in self.options.items()]
        else:
            opts = self.options
        options_str = '[' + ', '.join(opts) + ']'
        return f'{self.name} = "{self.val}"; // {options_str}\n'

    def __str__(self):
        return self.name


class CustomizerCheckbox(CompoundBoolean, Customizer):
    def __new__(cls, name:str, val:bool):
        self = super(CustomizerCheckbox, cls).__new__(cls, val)
        self.name = name
        self.val = val
        return self

    def scad_declaration(self):
        # No special comment syntax required for checkboxes
        val_str = f'{self.val}'.lower()
        return f'{self.name} = {val_str};\n'

    def __str__(self):
        return self.name

class CustomizerSpinbox(CompoundFloat, Customizer):
    # NOTE: if val is an integer (1, or 1.0), each spin step will be 1
    # If val is a decimal, spin step will be one decimal unit, 
    # i.e. 5.5 -> 0.1 step,  5.002 => 0.001 step
    def __new__(cls, name:str, val:float):
        self = super(CustomizerSpinbox, cls).__new__(cls, val)
        self.name = name
        self.val = val
        return self

    def scad_declaration(self):
        # No special comment syntax required for spinboxes
        return f'{self.name} = {self.val};\n'

    def __str__(self):
        return self.name

class CustomizerTextbox(CompoundString, Customizer):
    def __new__(cls, name:str, val:str):
        self = super(CustomizerTextbox, cls).__new__(cls, val)
        self.name = name
        self.val = val
        return self

    def scad_declaration(self):
        # No special comment syntax required for textboxes
        return f'{self.name} = "{self.val}";\n'

    def __str__(self):
        return self.name

# TODO: Support OpenSCAD Parameter tabs, with the syntax:
#  '/* [$TAB_NAME] */'
# Note that this would require either asking Python `CustomizerTab`
# objects to explicitly add Customizer elements or some 
# other mechanism for ordering parameters, since all OpenSCAD
# customizer params are at the top module level and hierarchy
# is described by order of elements


# TODO: write CustomizerVector, which is a list of number
# spinboxes (with optional ranges) for 0-4 numbers, or a 
# text field for 5+ numbers
class CustomizerVector(Customizer):
    def __str__(self):
        return self.name
