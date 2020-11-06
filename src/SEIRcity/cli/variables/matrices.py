from .. import ptypes
from .varsbuilder import VarsBuilder


class DemoMatricesVariables(VarsBuilder):
    TOPIC = 'Demographic Matrices'

    ARGDEFS = {
        'HIGH_RISK_RATIO': {
            'type': ptypes.DictKeyFloats,
            'desc': 'High Risk Ratio',
            'visible': False,
            'longdesc': None,
            'arg': '--high-risk-ratio',
            'meta': 'a1:f, a2:f,...a5:f',
            'example': None,
            'default':
            '0-4: 8.2825, 5-17: 14.1121, 18-49: 16.5298, 50-64: 32.9912, 65+: 47.0568',
            'required': True
        },
        'H_FATALITY_RATIO': {
            'type': ptypes.DictKeyFloats,
            'desc': 'Hospitalization Fatality Ratio',
            'visible': False,
            'longdesc': None,
            'arg': '--hospitalize-fatality-ratio',
            'meta': 'a1:f, a2:f,...a9:f',
            'example': None,
            'default':
            '0-9: 0.0, 10-19: 0.2, 20-29: 0.2, 30-39: 0.2, 40-49: 0.4, 50-59: 1.3, 60-69: 3.6, 70-79: 8.0, 80+: 14.8',
            'required': True
        },
        'INFECTION_FATALITY_RATIO': {
            'type': ptypes.DictKeyFloats,
            'desc': 'Infection Fatality Ratio',
            'visible': False,
            'longdesc': None,
            'arg': '--infection-fatality-ratio',
            'meta': 'a1:f, a2:f,...a9:f',
            'example': None,
            'default':
            '0-9: 0.0016, 10-19: 0.007, 20-29: 0.031, 30-39: 0.084, 40-49: 0.16, 50-59: 0.6, 60-69: 1.9, 70-79: 4.3, 80+: 7.8',
            'required': True
        },
        'OVERALL_H_RATIO': {
            'type': ptypes.DictKeyFloats,
            'desc': 'Overall Hospitalization Ratio',
            'visible': False,
            'longdesc': None,
            'arg': '--overall-hospitalize-ratio',
            'meta': 'a1:f, a2:f,...a9:f',
            'example': None,
            'default':
            '0-9: 0.04, 10-19: 0.04, 20-29: 1.1, 30-39: 3.4, 40-49: 4.3, 50-59: 8.2, 60-69: 11.8, 70-79: 16.6, 80+: 18.4',
            'required': True
        }
    }


# These are wrappers so that the variables module has a standalone to_dict and extend_parser method
# that returns all values and args defined in its child classes


def to_dict(parsed_args):
    return DemoMatricesVariables.to_dict(parsed_args)

def extend_dict(all_vars):
    return DemoMatricesVariables.extend_dict(all_vars)

def extend_parser(parser):
    parser = DemoMatricesVariables.extend_parser(parser)
    return parser


def build_tapis_properties(properties=None):
    properties = DemoMatricesVariables.build_tapis_properties(properties)
    return properties


def extend_tapis_shellvars(shellvars=None):
    if shellvars is None:
        shellvars = []
    shellvars = DemoMatricesVariables.extend_tapis_shellvars(shellvars)
    return shellvars
