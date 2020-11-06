from .. import ptypes
from ..ptypes.builder import TapisProperties
from .varsbuilder import VarsBuilder


class DemoVariables(VarsBuilder):
    TOPIC = 'Demonstration'

    ARGDEFS = {
        'float': {
            'type': ptypes.Float,
            'desc': 'Float Type',
            'longdesc': None,
            'arg': '--float',
            'meta': None,
            'default': 2.71828,
            'example': None,
            'required': True
        },
        'integer': {
            'type': ptypes.Integer,
            'desc': 'Integer Type',
            'longdesc': None,
            'arg': '--integer',
            'meta': None,
            'default': 42,
            'example': None,
            'required': True
        },
        'string': {
            'type': ptypes.String,
            'desc': 'String Type',
            'longdesc': None,
            'arg': '--string',
            'meta': None,
            'default': 'Example String',
            'example': None,
            'required': True
        },
        'int_date': {
            'type': ptypes.MatlabIntDate,
            'desc': 'Integer Date Type',
            'longdesc': 'YYYYMMDD',
            'arg': '--integer-date',
            'meta': 'YYYYMMDD',
            'default': 20200301,
            'example': 20200301,
            'required': True
        },
        'positive_float': {
            'type': ptypes.PositiveFloat,
            'desc': 'Positive Float Type',
            'longdesc': None,
            'arg': '--positive-float',
            'meta': None,
            'default': 3.141529,
            'example': None,
            'required': True
        },
        'positive_int': {
            'type': ptypes.PositiveInt,
            'desc': 'Positive Integer Type',
            'longdesc': None,
            'arg': '--positive-int',
            'meta': None,
            'default': 300,
            'example': None,
            'required': True
        },
        'positive_random_int': {
            'type': ptypes.PositiveOrRandomInt,
            'desc': 'Positive|Random Integer Type',
            'longdesc': None,
            'arg': '--positive-rand-int',
            'meta': None,
            'default': -1,
            'example': None,
            'required': True
        },
        'list_floats': {
            'type': ptypes.ListFloats,
            'desc': 'List of Floats',
            'longdesc': None,
            'arg': '--list-floats',
            'meta': 'f,f,f...',
            'default': '0.1, 0.3, 0.05, 1.5',
            'example': None,
            'required': True
        },
        'list_3_floats': {
            'type': ptypes.ListThreeFloats,
            'desc': 'List of 3 Floats',
            'longdesc': None,
            'arg': '--list-3-floats',
            'meta': 'f,f,f...',
            'default': '0.1, 0.3, 0.05',
            'example': None,
            'required': True
        },
        'key_float': {
            'type': ptypes.KeyFloatDict,
            'desc': 'Key:Float',
            'longdesc': None,
            'arg': '--key-float',
            'meta': 'k:f',
            'default': 'a:0.1',
            'example': None,
            'required': True
        },
        'list_key_float': {
            'type': ptypes.ListKeyFloats,
            'desc': 'List of Key:Floats',
            'longdesc': None,
            'arg': '--list-key-float',
            'meta': 'k:f, k:f, k:f...',
            'default': 'a:0.25, b:0.75, c:0.50',
            'example': None,
            'required': True
        }
    }


# These are wrappers so that the variables module has a standalone to_dict and extend_parser method
# that returns all values and args defined in its child classes


def to_dict(parsed_args):
    return DemoVariables.to_dict(parsed_args)

def extend_dict(all_vars):
    return DemoVariables.extend_dict(all_vars)

def extend_parser(parser):
    parser = DemoVariables.extend_parser(parser)
    return parser


def build_tapis_properties(properties=None):
    properties = TapisProperties.tapis_properties(properties)
    properties = DemoVariables.build_tapis_properties(properties)
    return properties


def extend_tapis_shellvars(shellvars=None):
    if shellvars is None:
        shellvars = []
    shellvars = DemoVariables.extend_tapis_shellvars(shellvars)
    return shellvars
