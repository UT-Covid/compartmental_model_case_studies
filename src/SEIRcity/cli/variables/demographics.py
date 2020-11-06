from .. import ptypes
from .varsbuilder import VarsBuilder


class DemographicsVariables(VarsBuilder):
    TOPIC = 'Demographics'

    ARGDEFS = {
        'n_risk': {
            'type': ptypes.PositiveInt,
            'desc': 'Number of risk groups',
            'visible': False,
            'longdesc': None,
            'arg': '--risk-groups',
            'meta': 'INT',
            'default': 2,
            'example': None,
            'required': True
        },
        'CITY': {
            'type':
            ptypes.StringDictEnum,
            'desc':
            'Name of city/metro area involved',
            'longdesc':
            None,
            'arg':
            '--city',
            'default':
            'Austin-Round_Rock',
            'meta':
            'CITY',
            'example':
            None,
            'required':
            True,
            'choices': [{
                'Abilene': 'Abilene'
            }, {
                'Amarillo': 'Amarillo'
            }, {
                'Austin-Round_Rock': 'Austin-Round Rock'
            }, {
                'Beaumont-Port_Arthur': 'Beaumont-Port Arthur'
            }, {
                'Brownsville-Harlingen': 'Brownsville-Harlingen'
            }, {
                'College_Station-Bryan': 'College Station-Bryan'
            }, {
                'Corpus_Christi': 'Corpus Christi'
            }, {
                'Dallas-Fort_Worth-Arlington':
                'Dallas-Fort Worth-Arlington'
            }, {
                'El_Paso': 'El Paso'
            }, {
                'Houston-The_Woodlands-Sugar_Land':
                'Houston-The Woodlands-Sugar Land'
            }, {
                'Killeen-Temple': 'Killeen-Temple'
            }, {
                'Laredo': 'Laredo'
            }, {
                'Longview': 'Longview'
            }, {
                'Lubbock': 'Lubbock'
            }, {
                'McAllen-Edinburg-Mission': 'McAllen-Edinburg-Mission'
            }, {
                'Midland': 'Midland'
            }, {
                'Odessa': 'Odessa'
            }, {
                'San_Angelo': 'San Angelo'
            }, {
                'San_Antonio-New_Braunfels':
                'San Antonio-New Braunfels'
            }, {
                'Tyler': 'Tyler'
            }, {
                'Waco': 'Waco'
            }, {
                'Wichita_Falls': 'Wichita Falls'
            }]
        }
    }


# These are wrappers so that the variables module has a standalone to_dict and extend_parser method
# that returns all values and args defined in its child classes


def to_dict(parsed_args):
    return DemographicsVariables.to_dict(parsed_args)

def extend_dict(all_vars):
    return DemographicsVariables.extend_dict(all_vars)

def extend_parser(parser):
    parser = DemographicsVariables.extend_parser(parser)
    return parser


def build_tapis_properties(properties=None):
    properties = DemographicsVariables.build_tapis_properties(properties)
    return properties


def extend_tapis_shellvars(shellvars=None):
    if shellvars is None:
        shellvars = []
    shellvars = DemographicsVariables.extend_tapis_shellvars(shellvars)
    return shellvars
