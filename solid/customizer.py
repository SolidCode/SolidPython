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
        return super(CompoundFloat, cls).__new__(cls, val)

    def __init__(self, val: Real, op: Operator = None, other: Real = None):
        self.val = val
        # TODO: ensure that either op & other are defined, or neither are
        self.op = op
        self.other = other

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

    def __add__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__add__, other)
    def __ceil__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__ceil__, other)
    def __eq__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__eq__, other)
    def __float__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__float__, other)
    def __floor__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__floor__, other)
    def __floordiv__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__floordiv__, other)
    def __le__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__le__, other)
    def __lt__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__lt__, other)
    def __mod__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__mod__, other)
    def __mul__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__mul__, other)
    # def __neg__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__neg__, other)
    # def __pos__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__pos__, other)
    def __pow__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__pow__, other)
    def __radd__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__radd__, other)
    def __rfloordiv__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__rfloordiv__, other)
    def __rmod__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__rmod__, other)
    def __rmul__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__rmul__, other)
    def __round__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__round__, other)
    def __rpow__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__rpow__, other)
    def __rtruediv__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__rtruediv__, other)
    def __truediv__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__truediv__, other)
    def __trunc__(self, other:Real) -> 'CompoundFloat': return CompoundFloat(self, float.__trunc__, other)

class CompundInt(int):
    pass

class CompoundBoolean(int):
    pass

class CompoundString(str):
    pass

class Customizer():
    def scad_declaration(self):
        raise NotImplementedError


class CustomizerSlider(CompoundFloat, Customizer):
    def __new__(cls, name:str, val:float, min_val:float=0, max_val:float = 1, step:float = None):
        return super(CustomizerSlider, cls).__new__(cls, val)
        
    def __init__(self, name:str, val:float, min_val:float=0, max_val:float = 1, step:float = None):
        self.val = val
        self.name = name
        self.min = min_val
        self.max = max_val
        self.step = step

    def scad_declaration(self) -> str:
        # OpenSCAD's customizer makes a guess about step size if not supplied. 
        # Leave it out in that case and let OpenSCAD's logic handle it
        step_str = f': {self.step}' if self.step else ''
        return f'{self.name} = {self.val}; // [{self.min}{step_str}: {self.max}]\n'

    def __str__(self) -> str:
        return self.name

class CustomizerDropdownNumber(CompoundFloat, Customizer):
    pass

class CustomizerDropdownString(CompoundString, Customizer):
    pass

class CustomizerCheckbox(CompoundBoolean, Customizer):
    pass
