from .. import ptypes
from .varsbuilder import VarsBuilder


class EpiVariables(VarsBuilder):
    TOPIC = 'Epidemiological'

    ARGDEFS = {
        'GROWTH_RATE_LIST': {
            'type': ptypes.ListStrings,
            'desc': 'GROWTH_RATE_LIST',
            'longdesc': None,
            'arg': '--growth-rates',
            'meta': 'str, str...',
            'default': 'high',
            'example': None,
            'required': True
        },
        'R0': {
            'type': ptypes.PositiveFloat,
            'desc': 'R0 - basic reproductive number',
            'longdesc': None,
            'arg': '--r0',
            'meta': 'FLOAT',
            'default': 2.2,
            'example': None,
            'required': True
        },
        'DOUBLE_TIME': {
            'type': ptypes.DictKeyFloats,
            'desc': 'Doubling time (Low/High)',
            'longdesc': None,
            'arg': '--double-time',
            'meta': 'low:f, high:f',
            'default': 'low:7.2, high:4.0',
            'example': None,
            'required': True
        },
        'beta0_dict': {
            'type': ptypes.DictKeyFloats,
            'desc': 'Beta-0 (Low/High)',
            'longdesc': None,
            'arg': '--beta0',
            'meta': 'low:f, high:f',
            'default': 'low:0.01622242, high:0.02599555',
            'example': None,
            'required': True
        },
        'ASYMP_RATE': {
            'type': ptypes.Rate,
            'desc': 'Rate of asymptomatic infected persons',
            'longdesc': None,
            'arg': '--asymp-rate',
            'meta': 'RATE',
            'default': 0.179,
            'example': None,
            'required': True
        },
        'PROP_TRANS_IN_E': {
            'type': ptypes.Proportion,
            'desc':
            'Proportion of total infections that occur when patients are in the incubation period',
            'longdesc': None,
            'arg': '--prop-trans-e',
            'meta': 'PROPORTION',
            'default': 0.126,
            'example': None,
            'required': True
        },
        'T_ONSET_TO_H': {
            'type': ptypes.PositiveFloat,
            'desc': 'Time from onset to hospitalization (days)',
            'longdesc': None,
            'arg': '--t-onset-to-h',
            'meta': 'FLOAT',
            'default': 5.9,
            'example': None,
            'required': True
        },
        'T_H_TO_D': {
            'type': ptypes.PositiveFloat,
            'desc': 'Time from hospitalization to death (days)',
            'longdesc': None,
            'arg': '--t-h-to-d',
            'meta': 'FLOAT',
            'default': 14.0,
            'example': None,
            'required': True
        },
        'T_H_TO_R': {
            'type': ptypes.PositiveFloat,
            'desc': 'Time from hospitalization to recovery (days)',
            'longdesc': None,
            'arg': '--t-h-to-r',
            'meta': 'FLOAT',
            'default': 11.5,
            'example': None,
            'required': True
        },
        'T_EXPOSED_DIST': {
            'type': ptypes.StringDictEnum,
            'desc': 'T_EXPOSED_DIST',
            'visible': False,
            'longdesc': None,
            'arg': '--t-exposed-dist',
            'meta': 'DIST',
            'default': 'triangular',
            'example': None,
            'required': True,
            'choices': [{
                'triangular': 'Triangular'
            }]
        },
        'T_Y_TO_R_DIST': {
            'type': ptypes.StringDictEnum,
            'desc': 'Triangular: Parameters for infectious/recovery period',
            'visible': False,
            'longdesc': None,
            'arg': '--t-ytor-dist',
            'meta': 'DIST',
            'default': 'triangular',
            'example': None,
            'required': True,
            'choices': [{
                'triangular': 'Triangular'
            }]
        },
        'T_EXPOSED_PARA': {
            'type': ptypes.Triangular,
            'desc': 'Triangular: Parameters for incubation period',
            'longdesc': None,
            'arg': '--t-exposed-para',
            'meta': 'f,f,f',
            'default': '5.6, 7, 8.2',
            'example': None,
            'required': True
        },
        'T_Y_TO_R_PARA': {
            'type': ptypes.Triangular,
            'desc': 'T_Y_TO_R_PARA',
            'longdesc': None,
            'arg': '--t-ytor-para',
            'meta': ' f,f,f',
            'default': '21.1, 22.6, 24.4',
            'example': None,
            'required': True
        },
        'H_RELATIVE_RISK_IN_HIGH': {
            'type': ptypes.PositiveInt,
            'desc': 'Hospitalization Relative Risk',
            'longdesc': None,
            'arg': '--h-rel-risk-hi',
            'meta': 'INT',
            'default': 10,
            'example': None,
            'required': True
        },
        'D_RELATIVE_RISK_IN_HIGH': {
            'type': ptypes.PositiveInt,
            'desc': 'Death Relative Risk',
            'longdesc': None,
            'arg': '--d-rel-risk-hi',
            'meta': 'INT',
            'default': 10,
            'example': None,
            'required': True
        },
        'START_CONDITION': {
            'type': ptypes.PositiveInt,
            'desc': 'Initial number of infected',
            'longdesc': None,
            'arg': '--start-condition',
            'meta': 'INT',
            'default': 1,
            'example': None,
            'required': True
        },
        'hosp_data_fp': {
            'type': ptypes.CSVFile,
            'desc': 'Current hospitalization data',
            'longdesc': 'CSV file. See default example for structure',
            'arg': '--hospitalization-data',
            'meta': 'FILENAME',
            'default': 'inputs/Austin-Round_Rock_TX_hospitalized_20200402_through_20200408.csv',
            'example':
            'agave://covid19.community.storage/inputs/hospitalization/latest/Austin-Round_Rock_TX_hospitalized_20200402_through_20200408.csv',
            'required': True
        }
    }


# These are wrappers so that the variables module has a standalone to_dict and extend_parser method
# that returns all values and args defined in its child classes


def to_dict(parsed_args):
    return EpiVariables.to_dict(parsed_args)


def extend_dict(all_vars):
    return EpiVariables.extend_dict(all_vars)

def extend_parser(parser):
    parser = EpiVariables.extend_parser(parser)
    return parser


def build_tapis_properties(properties=None):
    properties = EpiVariables.build_tapis_properties(properties)
    return properties


def extend_tapis_shellvars(shellvars=None):
    if shellvars is None:
        shellvars = []
    shellvars = EpiVariables.extend_tapis_shellvars(shellvars)
    return shellvars
