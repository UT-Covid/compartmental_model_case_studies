from .. import ptypes
from .varsbuilder import VarsBuilder


class InterventionsVariables(VarsBuilder):
    TOPIC = 'Interventions'

    ARGDEFS = {
        'CONTACT_REDUCTION': {
            'type': ptypes.ListFloats,
            'desc': 'Contact reduction scenarios',
            'longdesc': None,
            'arg': '--contact-reductions',
            'meta': 'f,...',
            'default': '0.5',
            'example': None,
            'required': True
        },
        'sd_date': {
            'type': ptypes.IntDateRange,
            'desc': 'Contact reduction start/end',
            'longdesc': None,
            'arg': '--contact-reduction-dates',
            'meta': 'YYYYMMDD,YYYYMMDD',
            'default': '20200325, 20200818',
            'example': None,
            'required': True
        },
        # 'CLOSE_TRIGGER_LIST': {
        #     'type': ptypes.ListStrings,
        #     'visible': False,
        #     'desc': 'School closure dates',
        #     'longdesc': None,
        #     'arg': '--close-triggers',
        #     'meta': 'date__YYYYMMDD,...',
        #     'default': 'date__20200319',
        #     'example': None,
        #     'required': True
        # },
        # 'REOPEN_TRIGGER_LIST': {
        #     'type': ptypes.ListStrings,
        #     'visible': False,
        #     'desc':
        #     'School reopen dates',
        #     'longdesc': None,
        #     'arg': '--reopen-triggers',
        #     'meta': "no_na_{{FallStartDate}}",
        #     'default': None,
        #     'example': None,
        #     'required': True
        # },
        'trigger_type': {
            'type': ptypes.StringDictEnum,
            'desc': 'Type of school closure trigger considered',
            'visible': False,
            'longdesc': None,
            'arg': '--trigger-type',
            'meta': 'TRIGGER',
            'default': 'cml',
            'example': None,
            'required': True,
            'choices': [{
                'cml': 'CML'
            }]
        }
    }


# These are wrappers so that the variables module has a standalone to_dict and extend_parser method
# that returns all values and args defined in its child classes


def to_dict(parsed_args):
    return InterventionsVariables.to_dict(parsed_args)


def extend_dict(all_vars):
    return  InterventionsVariables.extend_dict(all_vars)

def extend_parser(parser):
    parser = InterventionsVariables.extend_parser(parser)
    return parser


def build_tapis_properties(properties=None):
    properties = InterventionsVariables.build_tapis_properties(properties)
    return properties


def extend_tapis_shellvars(shellvars=None):
    if shellvars is None:
        shellvars = []
    shellvars = InterventionsVariables.extend_tapis_shellvars(shellvars)
    return shellvars
