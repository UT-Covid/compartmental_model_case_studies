#!/usr/bin/env python
import os
import sys
import numpy as np
import pickle
import datetime as dt

from SEIRcity.scenario import BaseScenario as Scenario
from SEIRcity.get_scenarios import get_scenarios
from .simulate_one import simulate_one
from SEIRcity import param_parser
from SEIRcity import param as param_module
from SEIRcity import model, utils
from . import multiple_serial, multiple_pool

# DEV
from SEIRcity import dev_utils


def simulate_multiple(config, out_fp=None, threads=48, verbosity=0):
    """"""
    # pull parameters from config YAML file `yaml_fp`
    #config = param_module.aggregate_params_and_data(yaml_fp=yaml_fp)

    # run Scenarios in parallel, returning an instance of OutcomeHandler
    oh = multiple_pool(config=config, threads=threads)

    # write outcomes to pickled xarray.DataArray
    if out_fp is None:
        raise ValueError('Output file path not provided.')
        # basename for output filepath
        #basename = os.path.splitext(os.path.basename(yaml_fp))[0]
        #out_fp = os.path.join("outputs",  basename + ".pckl")
    #else:
    #    basename = os.path.splitext(os.path.basename(out_fp))[0]
    oh.to_pickle(out_fp=out_fp)

    # write to CSV as well, in the same directory
    # csv_fp = os.path.join(os.path.dirname(out_fp), basename + '.csv')
    # oh.to_dataframe(out_fp=csv_fp)

    return oh.outcomes
