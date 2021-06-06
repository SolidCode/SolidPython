from .scad_variable import ScadVariable

class CustomizerDropdownVariable(ScadVariable):
    def __init__(self, name, default_value, options='', label='', tab=''):
        if isinstance(options, list):
            options_str = '[' + ", ".join(map(str, options)) + ']'

        if isinstance(options, dict):
            reverse_options = [ f"{options[k]} : {k}" for k in options.keys()]
            options_str = f'[{", ".join(reverse_options)}]'

        super().__init__(name, default_value, options_str, label=label, tab=tab)

class CustomizerSliderVariable(ScadVariable):
    def __init__(self, name, default_value, min_, max_, step='', label='', tab=''):
        options_str = '['
        options_str += min_ and str(min_) + ':'
        options_str += step and str(step) + ':'
        options_str += str(max_) + ']'

        super().__init__(name, default_value, options_str, label=label, tab=tab)

class CustomizerCheckboxVariable(ScadVariable):
    def __init__(self, name, default_value, label='', tab=''):
        super().__init__(name, default_value, label=label, tab=tab)

class CustomizerTextboxVariable(ScadVariable):
    def __init__(self, name, default_value, max_length='', label='', tab=''):
        options_str = max_length and str(max_length)
        super().__init__(name, f'"{default_value}"', options_str, label=label, tab=tab)

