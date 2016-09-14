"""
Code to extract the names of modules and functions from existing scad files
"""
import re

def extract_callable_signatures(scad_file_path):
    with open(scad_file_path) as f:
        scad_code_str = f.read()
    return parse_scad_callables(scad_code_str)


def parse_scad_callables(scad_code_str):
    callables = []

    # Note that this isn't comprehensive; tuples or nested data structures in
    # a module definition will defeat it.

    # Current implementation would throw an error if you tried to call a(x, y)
    # since Python would expect a(x);  OpenSCAD itself ignores extra arguments,
    # but that's not really preferable behavior

    # TODO:  write a pyparsing grammar for OpenSCAD, or, even better, use the yacc parse grammar
    # used by the language itself.  -ETJ 06 Feb 2011

    no_comments_re = r'(?mxs)(//.*?\n|/\*.*?\*/)'

    # Also note: this accepts: 'module x(arg) =' and 'function y(arg) {', both
    # of which are incorrect syntax
    mod_re = r'(?mxs)^\s*(?:module|function)\s+(?P<callable_name>\w+)\s*\((?P<all_args>.*?)\)\s*(?:{|=)'

    # This is brittle.  To get a generally applicable expression for all arguments,
    # we'd need a real parser to handle nested-list default args or parenthesized statements.
    # For the moment, assume a maximum of one square-bracket-delimited list
    args_re = r'(?mxs)(?P<arg_name>\w+)(?:\s*=\s*(?P<default_val>[\w.-]+|\[.*\]))?(?:,|$)'

    # remove all comments from SCAD code
    scad_code_str = re.sub(no_comments_re, '', scad_code_str)
    # get all SCAD callables
    mod_matches = re.finditer(mod_re, scad_code_str)

    for m in mod_matches:
        callable_name = m.group('callable_name')
        args = []
        kwargs = []
        all_args = m.group('all_args')
        if all_args:
            arg_matches = re.finditer(args_re, all_args)
            for am in arg_matches:
                arg_name = am.group('arg_name')
                if am.group('default_val'):
                    kwargs.append(arg_name)
                else:
                    args.append(arg_name)

        callables.append({'name': callable_name, 'args': args, 'kwargs': kwargs})

    return callables



