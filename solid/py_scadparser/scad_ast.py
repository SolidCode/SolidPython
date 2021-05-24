from enum import Enum

class ScadTypes(Enum):
    GLOBAL_VAR = 0
    MODULE = 1
    FUNCTION = 2
    USE = 3
    INCLUDE = 4
    PARAMETER = 5

class ScadObject:
    def __init__(self, scadType):
        self.scadType = scadType

    def getType(self):
        return self.scadType

class ScadGlobalVar(ScadObject):
    def __init__(self, name):
        super().__init__(ScadTypes.GLOBAL_VAR)
        self.name = name

class ScadCallable(ScadObject):
    def __init__(self, name, parameters, scadType):
        super().__init__(scadType)
        self.name = name
        self.parameters = parameters

    def __repr__(self):
        return f'{self.name} ({self.parameters})'

class ScadModule(ScadCallable):
    def __init__(self, name, parameters):
        super().__init__(name, parameters, ScadTypes.MODULE)

class ScadFunction(ScadCallable):
    def __init__(self, name, parameters):
        super().__init__(name, parameters, ScadTypes.FUNCTION)

class ScadParameter(ScadObject):
    def __init__(self, name, optional=False):
        super().__init__(ScadTypes.PARAMETER)
        self.name = name
        self.optional = optional

    def __repr__(self):
        return self.name + "=None" if self.optional else  self.name

