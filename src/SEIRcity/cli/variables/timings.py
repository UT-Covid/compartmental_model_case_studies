from .. import ptypes
from .varsbuilder import VarsBuilder


class TimingVariables(VarsBuilder):
    TOPIC = 'Timing'

    ARGDEFS = {
        'shift_week': {
            'type': ptypes.PositiveInt,
            'visible': False,
            'desc':
            'Number of weeks to shift calendar when aligning year-to-year',
            'longdesc': None,
            'arg': '--shift-week',
            'meta': 'INT',
            'default': 0,
            'example': None,
            'required': True
        },
        'time_begin_sim': {
            'type': ptypes.MatlabIntDate,
            'desc': 'Date on which the simulation starts',
            'longdesc': None,
            'arg': '--begin-sim-date',
            'default': 20200215,
            'meta': 'YYYMMDD',
            'example': None,
            'required': True
        },
        'interval_per_day': {
            'type': ptypes.PositiveInt,
            'desc': 'Number of discrete time steps to evaluate per day',
            'longdesc': None,
            'visble': False,
            'arg': '--interval-per-day',
            'default': 10,
            'meta': 'INT',
            'example': None,
            'required': True
        },
        'total_time': {
            'type': ptypes.PositiveInt,
            'desc': 'Number of days to simulate',
            'longdesc': None,
            'arg': '--simulation-days',
            'default': 175,
            'meta': 'INT',
            'example': None,
            'required': True
        },
        'monitor_lag': {
            'type': ptypes.PositiveInt,
            'visible': False,
            'desc': 'MONITOR_LAG',
            'longdesc': None,
            'arg': '--monitor-lag',
            'default': 0,
            'meta': 'INT',
            'example': None,
            'required': True
        },
        'report_rate': {
            'type': ptypes.PositiveFloat,
            'visible': False,
            'desc': 'REPORT_RATE',
            'longdesc': None,
            'arg': '--report-rate',
            'default': 1.0,
            'meta': 'FLOAT',
            'example': None,
            'required': True
        }
    }


# These are wrappers so that the variables module has a standalone to_dict and extend_parser method
# that returns all values and args defined in its child classes


def to_dict(parsed_args):
    return TimingVariables.to_dict(parsed_args)

def extend_dict(all_vars):
    return TimingVariables.extend_dict(all_vars)


def extend_parser(parser):
    parser = TimingVariables.extend_parser(parser)
    return parser


def build_tapis_properties(properties=None):
    properties = TimingVariables.build_tapis_properties(properties)
    return properties


def extend_tapis_shellvars(shellvars=None):
    if shellvars is None:
        shellvars = []
    shellvars = TimingVariables.extend_tapis_shellvars(shellvars)
    return shellvars
