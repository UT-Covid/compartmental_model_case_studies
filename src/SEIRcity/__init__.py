#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main file for publish SEIR model
"""

import os
import sys
import numpy as np
import pandas as pd
import pickle
import datetime
import argparse

# SEIRcity modules
from . import cli
from .simulate import simulate_multiple
from .param import aggregate_params_and_data
from .fit_to_data import fitting_workflow

HERE = os.path.dirname(os.path.abspath(__file__))

# -----------------------Configure dependencies-------------------------

np.set_printoptions(linewidth=115)
pd.plotting.register_matplotlib_converters()
pd.set_option('display.width', 115)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.options.display.float_format = '{:,.8f}'.format
# pd.set_option('precision', -1)

# ----------------------------------------------------------------------


def main(config_yaml, out_fp, threads):
    """Entrypoint function for the SEIRcity model app."""
    # ensure YAML file exists
    if not os.path.isfile(config_yaml):
        raise FileNotFoundError("No config YAML file found at {}".format(config_yaml))

    # read and validate YAML file
    params = aggregate_params_and_data(yaml_fp=config_yaml)
    print('t_offset = {}'.format(params['t_offset']))

    # determine if user is_fitting, as opposed to simulating
    # TODO: migrate this check to param module
    is_fitting = params['is_fitting']

    if is_fitting:
        # fit model to existing data, returning a fitted beta0 value
        # and a fitted sd_level value
        fitted_parameters = fitting_workflow(params, out_fp=out_fp)
    else:
        # run model as a as set of simulations across different scenarios
        _ = simulate_multiple(params, out_fp=out_fp, threads=threads)


def get_clargs():
    """Get command line arguments `clargs` via argparse"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-yaml', required=True,
                        help='Config YAML file path')
    parser.add_argument('--out-fp', required=True,
                        help='Path in which to write outputs')
    parser.add_argument('--threads', type=int, required=False,
                        default=48,
                        help='Number of threads to use in simulation')
    clargs = vars(parser.parse_args())
    return clargs
