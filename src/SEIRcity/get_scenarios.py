#!/usr/bin/env python
import os
import sys
import numpy as np
import pickle
import datetime as dt

from .scenario import BaseScenario as Scenario
from .simulate import simulate_one
from . import param_parser, utils
from . import param as param_module

# DEV
from . import dev_utils


def get_scenarios(config, verbosity=0):
    # list of Scenario instances
    # converted to tuple when returned
    scenarios = list()

    # params that are same for all Scenarios
    # only here because the model function needs them
    consistent_params_keys = (
        'city',
        'NUM_SIM',
        'n_age',
        'n_risk',
        'total_time',
        'interval_per_day',
        'shift_week',
        'time_begin',
        'time_begin_sim',
        'initial_state',
        'trigger_type',
        'monitor_lag',
        'report_rate',
        'phi',
        'metro_pop',
        'FallStartDate',
        'school_calendar',
        'deterministic',
        # added in 1.1, `sd_date` is still supported
        'c_reduction_date',
        't_offset'
    )

    # filtered using only the above keys
    utils.assert_has_keys(config, consistent_params_keys)
    consistent_params = {
        k: config[k] for k in config.keys()
        if k in consistent_params_keys
    }

    # TODO: for passing pytests
    consistent_params['verbosity'] = 0

    # ensure that params dict has keys necessary to run
    # SEIR_get_param for every scenario
    get_param_arg_names = tuple([
        'symp_h_ratio_overall',
        'symp_h_ratio', 'hosp_f_ratio',
        'n_age', 'n_risk', 'deterministic',
    ])
    utils.assert_has_keys(config, get_param_arg_names)
    get_param_kwargs = {
        k: config[k] for k in config.keys()
        if k in get_param_arg_names
    }

    # ------------------------------------------------------------------

    # generate one Scenario for each unique combination of
    # growth rate, contact reduction, close trigger, and reopen trigger
    for g_rate in config['GROWTH_RATE_LIST']:
        beta0 = config['beta0_dict'][g_rate]
        for c_reduction in config['CONTACT_REDUCTION']:
            for close_trigger in config['CLOSE_TRIGGER_LIST']:
                for reopen_trigger in config['REOPEN_TRIGGER_LIST']:
                    unique_params = {
                        'close_trigger': close_trigger,
                        'reopen_trigger': reopen_trigger,
                        'g_rate': g_rate,
                        'c_reduction': c_reduction,
                        'beta0': beta0,
                    }
                    # add all the params that are consistent between
                    # Scenarios, but need to be passed as args to the
                    # model function
                    unique_params.update(consistent_params)
                    # add this unique Scenario to the list
                    scenarios.append(Scenario(unique_params))
    return tuple(scenarios)
