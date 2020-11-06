from .. import ptypes
from .varsbuilder import VarsBuilder


class ControlVariables(VarsBuilder):
    TOPIC = 'Control'

    ARGDEFS = {
        'RESULTS_DIR': {
            'type': ptypes.String,
            'desc': 'Results directory',
            'visible': False,
            'longdesc': None,
            'arg': '--results-dir',
            'default': './outputs',
            'example': None,
            'required': True
        },
        'DATA_FOLDER': {
            'type': ptypes.String,
            'desc': 'Local data directory',
            'visible': False,
            'longdesc': None,
            'arg': '--data-dir',
            'default': './data/Cities_Data/',
            'example': None,
            'required': True
        },
        'deterministic': {
            'type': ptypes.Boolean,
            'desc': 'Run the model deterministically',
            'longdesc': None,
            'arg': '--deterministic',
            'default': False,
            'example': None,
            'required': True
        },
        'NUM_SIM': {
            'type': ptypes.PositiveInt,
            'desc': 'Number of runs per scenario',
            'longdesc': None,
            'arg': '--num-sim',
            'meta': 'INT',
            'default': 100,
            'example': None,
            'required': True
        },
        'NUM_SIM_FIT': {
            'type': ptypes.PositiveInt,
            'desc': 'Number of runs for fitting',
            'longdesc': None,
            'arg': '--num-sim-fit',
            'meta': 'INT',
            'default': 1,
            'example': None,
            'required': True
        },
        'is_fitting': {
            'type': ptypes.Boolean,
            'desc': 'Fit to data rather than run a simulation',
            'longdesc': None,
            'arg': '--fit-data',
            'default': False,
            'example': None,
            'required': True
        },
        'verbose': {
            'type': ptypes.Boolean,
            'desc': 'Generate verbose output',
            'longdesc': None,
            'arg': '--verbose',
            'default': False,
            'example': None,
            'required': True
        }
    }


# These are wrappers so that the variables module has a standalone to_dict and extend_parser method
# that returns all values and args defined in its child classes


def to_dict(parsed_args):
    return ControlVariables.to_dict(parsed_args)

def extend_dict(all_vars):
    return ControlVariables.extend_dict(all_vars)

def extend_parser(parser):
    parser = ControlVariables.extend_parser(parser)
    return parser


def build_tapis_properties(properties=None):
    properties = ControlVariables.build_tapis_properties(properties)
    return properties


def extend_tapis_shellvars(shellvars=None):
    if shellvars is None:
        shellvars = []
    shellvars = ControlVariables.extend_tapis_shellvars(shellvars)
    return shellvars
