from .. import ptypes
from .varsbuilder import VarsBuilder


class StaticVariables(VarsBuilder):
    # Emulates the VarsBuilder interface but returns a static data
    # structure from to_dict which then goes into the YAML output. Handy for
    # NEVER change on the front end
    TOPIC = None
    ARGDEFS = {}


# These are wrappers so that the variables module has a standalone to_dict and extend_parser method
# that returns all values and args defined in its child classes


def to_dict(parsed_args):
    return {
        'CLOSE_TRIGGER_LIST': ['date__20200319'],
        'REOPEN_TRIGGER_LIST': ['no_na_{{FallStartDate}}'],
        # Gets overridden by extend_dict if START_CONDITION supplied
        'I0': [[0, 0], [0, 0], [1, 0], [0, 0], [0, 0]],
        'age_groups': 5,
        'n_age': 5,
        'age_group_dict': {
            3: ['0-4', '5-17', '18+'],
            5: ['0-4', '5-17', '18-49', '50-64', '65+']
        }
    }


def extend_dict(all_vars):
    # Initial infected are assumed to be in the 18-49 demographic
    if 'START_CONDITION' in all_vars:
        all_vars['I0'] = [[0, 0], [0, 0], [all_vars['START_CONDITION'], 0], [0, 0], [0, 0]]
    return all_vars


def extend_parser(parser):
    return parser


def build_tapis_properties(properties=None):
    return properties


def extend_tapis_shellvars(shellvars=None):
    if shellvars is None:
        shellvars = []
    return shellvars
