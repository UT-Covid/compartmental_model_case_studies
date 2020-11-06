import argparse
import json
import logging
import os
import sys
import yaml

from . import app as appmodule
from . import command
from .utils import dynamic_import

DEFAULT_OUTFILE = 'config.yml'

# Modules implementing the Variables interface
# VARIABLES_MODULES = [
#     'src.SEIRcity.cli.variables.demo'
# ]

VARIABLES_MODULES = [
    # 'src.SEIRcity.cli.variables.demo',
    'src.SEIRcity.cli.variables.control',
    'src.SEIRcity.cli.variables.demographics',
    'src.SEIRcity.cli.variables.epi',
    'src.SEIRcity.cli.variables.interventions',
    'src.SEIRcity.cli.variables.timings',
    'src.SEIRcity.cli.variables.matrices',
    'src.SEIRcity.cli.variables.static'
]

# Private - holds dynamically loaded variables mods
_MODULES = []


def _shellvars(parsed_args):
    shellvars = []
    for mod in _MODULES:
        shellvars = mod.extend_tapis_shellvars(shellvars)
    shellvars = sorted(shellvars)
    escaped_shellvars = ['${' + sv + '}' for sv in shellvars]
    return ' '.join(escaped_shellvars)


def _properties(parsed_args):
    properties = {}
    for mod in _MODULES:
        properties = mod.build_tapis_properties(properties)
    return properties


def app(parsed_args):
    """Prints the app.json to screen
    """
    props = _properties(parsed_args)
    appj = appmodule.build_app_def(props)
    print(json.dumps(appj, indent=4, sort_keys=False))


def shell(parsed_args):
    """Prints the complete command for runner.sh
    """
    print('\n{0} {1}\n'.format(command.CONFIG_CMD, _shellvars(parsed_args)))
    print('{0}\n'.format(command.RUN_CMD))


def run(parsed_args):
    logging.basicConfig(level=parsed_args.logging)

    all_vars = {}
    for mod in _MODULES:
        variables = mod.to_dict(parsed_args)
        all_vars = {**all_vars, **variables}

    # Compute dynamic variables
    # A notable example is I0 which contains STARTING_CONDITION. Another might be 
    # the name of the hospitalization file 
    for mod in _MODULES:
        all_vars = mod.extend_dict(all_vars)

    yaml.dump(all_vars, stream=open(parsed_args.output, 'w'))


def debug(parsed_args):
    logging.basicConfig(level='DEBUG')
    all_vars = {}

    for mod in _MODULES:
        variables = mod.to_dict(parsed_args)
        all_vars = {**all_vars, **variables}

    logging.debug(_shellvars(parsed_args))
    logging.debug(_properties(parsed_args)['parameters'])
    logging.debug(all_vars)
    logging.debug(yaml.dump(all_vars))


def main(parsed_args):
    fn = globals().get(parsed_args.command)
    fn(parsed_args)
    sys.exit(0)


def get_clargs():
    """Get command line arguments `clargs` via argparse"""
    parser = argparse.ArgumentParser(prog='{0}'.format(command.CONFIG),
                                     description='{0}: {1}'.format(
                                         appmodule.LABEL,
                                         appmodule.DESCRIPTION))

    parser.add_argument('command',
                        type=str,
                        default='run',
                        nargs='?',
                        choices=['run', 'debug', 'shell', 'app'])
    parser.add_argument(
        '-O',
        dest='output',
        type=str,
        default=DEFAULT_OUTFILE,
        help='Output YML file name (default: {0})'.format(DEFAULT_OUTFILE))
    parser.add_argument(
        '--logging',
        dest='logging',
        default=None,
        help='Logging level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    # Load modules implementing the Variables interface
    for varmod in VARIABLES_MODULES:
        m = dynamic_import(varmod)
        _MODULES.append(m)

    # Extend parser with Variables modules
    for mod in _MODULES:
        parser = mod.extend_parser(parser)

    parsed_args = parser.parse_args()
    return parsed_args
