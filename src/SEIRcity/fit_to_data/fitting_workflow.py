# -*- coding: utf-8 -*-
"""
Functions necessary for fitting SEIR to data
"""

import datetime as dt
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy import stats
import os
import datetime
from datetime import timedelta
import multiprocessing as mp
import pickle
import json
from collections import defaultdict

from SEIRcity.model import SEIR_model_publish_w_risk
from SEIRcity import param as param_module
from SEIRcity import get_scenarios, utils
from .defaults import DEFAULT_FIT_VAR_NAMES, DEFAULT_FIT_GUESS, DEFAULT_FIT_BOUNDS
from ..simulate import simulate_one

def fitting_workflow(config, out_fp=None):
    """Recapitulation of fit_to_data.fitting_workflow from branch
    parameter_fitting. Main handler for fitting.
    """
    # get YAML params
    #config = param_module.aggregate_params_and_data(yaml_fp=yaml_fp)

    # get list of params to float, as well as guesses and bounds,
    # from the config YAML
    fit_var_names = config.get("fit_var_names", DEFAULT_FIT_VAR_NAMES)
    fit_guess = config.get("fit_guess", DEFAULT_FIT_GUESS)
    fit_bounds = config.get("fit_bounds", DEFAULT_FIT_BOUNDS)

    # TODO: validation on fit_var_* data formats

    # get hosp data as pandas df
    case_data = pd.read_csv(config['hosp_data_fp'])

    # get a list of Scenario instances. similar to gather_params
    scenarios_tup = get_scenarios.get_scenarios(config=config)
    # assert that there is only one Scenario in the list
    if len(scenarios_tup) > 1:
        # print(scenarios_tup)
        raise ValueError('{} parameter '.format(len(scenarios_tup)) +
                         'sets generated for fitting, but only one is ' +
                         'allowed. Please check the config file.')
    else:
        scenario = scenarios_tup[0]
        scenario.inject()
        scenario['config'] = config

    # Kelly's addition to workflow
    data_start_date = dt.datetime.strptime(np.str(case_data['date'][0]), '%Y-%m-%d')
    data_pts = case_data['hospitalized'].values
    date_begin = dt.datetime.strptime(np.str(scenario['time_begin_sim']), '%Y%m%d') + \
        dt.timedelta(weeks=scenario['shift_week'])

    if date_begin > data_start_date:
        sim_begin_idx = (date_begin - data_start_date).days
        case_data_values = data_pts[sim_begin_idx:]
        comparison_offset = 0
    else:
        comparison_offset = (data_start_date - date_begin).days
        case_data_values = data_pts

    # run the solver, returning dictionary containing error
    # and fitted values
    solution = fit_to_data(
        fit_var_names=fit_var_names,
        fit_guess=fit_guess,
        fit_bounds=fit_bounds,
        sim_func=simulate_one, #SEIR_model_publish_w_risk,
        scenario=scenario,
        data=case_data_values,
        offset=comparison_offset)

    # pretty logging
    for var_name in solution.keys():
        print("{}: {}".format(var_name, solution[var_name]))

    # write solution to a tiny CSV
    if out_fp is not None:
        print("Writing fitted values to: {}".format(out_fp))
        as_df = pd.DataFrame([solution])
        as_df.to_csv(out_fp, index=False)
    return solution


def fit_to_data(fit_var_names, fit_guess, fit_bounds,
                sim_func, scenario, data, offset):
    """Wrapper around scipy.optimize.least_squares"""

    # Ensure that there are guess and bounds values
    # for each floating parameter
    utils.assert_has_keys(fit_guess, fit_var_names)
    utils.assert_has_keys(fit_bounds, fit_var_names)
    utils.assert_has_keys(scenario, fit_var_names)

    # Flatten guess and bounds arrays into x0 and bounds
    # args, respectively
    x0 = list()
    bounds_lst = list()
    for var_name in fit_var_names:
        x0.append(fit_guess[var_name])
        bounds_lst.append(fit_bounds[var_name])

    # least_squares needs bounds in the format
    # [[lower1, lower2], [upper1, upper2]], not
    # [[lower1, upper1], [lower2, upper2]]
    bounds = np.stack(bounds_lst, axis=1)

    # define x_scale: same as multipying beta0 by 100
    x_scale = np.ones_like(x0)
    if 'beta0' in fit_var_names:
        beta_idx = fit_var_names.index('beta0')
        x_scale[beta_idx] = 0.01

    # call scipy.optimize.least_squares
    soln_full = least_squares(
        fun=calc_residual,
        x0=x0,
        #x_scale=x_scale,
        #xtol=1e-8,  # default
        bounds=bounds,
        args=(fit_var_names, sim_func, scenario, data, offset))

    # convert fitted values to dictionary
    soln_lst = list(soln_full['x'])
    soln_dict = dict({
        name: val for name, val in zip(fit_var_names, soln_lst)
    })

    # get the final error
    soln_dict['final_error'] = soln_full['fun']

    # Calculate final rmsd and nrmsd
    soln_dict['final_rmsd'] = rmsd_t(soln_dict['final_error'])
    soln_dict['final_nrmsd_t'] = nrmsd_t(soln_dict['final_rmsd'], data)

    return soln_dict


def calc_residual(fit_var, fit_var_names, sim_func, scenario, data, comp_offset):
    """Callback function for fit_to_data"""

    assert len(fit_var) == len(fit_var_names), \
        "length of fit_var: {}, but expected {}".format(len(fit_var), len(fit_var_names))
    assert hasattr(scenario, 'n_age'), "Scenario instance has no attribute 'n_age'"

    # Make sure beta0 is array, not float, before running model function
    scenario['beta0'] = scenario['beta0'] * np.ones(scenario['n_age'])

    # For each variable parameter in fit_var, update the corresponding key in the scenario
    for var_idx in range(len(fit_var_names)):
        var_name = fit_var_names[var_idx]
        scenario[var_name] = fit_var[var_idx]

        # Special treatment for beta0
        if var_name == 'beta0':
            scenario[var_name] = fit_var[var_idx] * np.ones(scenario['n_age'])

    for var in fit_var_names:
        print('Variable {} = {}'.format(var, scenario[var]))

    # filter to only the params needed for model function
    #scenario_final = filter_params(scenario)
    sim_args = {'scenario': scenario}

    # run the model function
    #S, E, Ia, Iy, Ih, R, D, E2Iy, E2I, Iy2Ih, H2D, SchoolCloseTime, \
    #    SchoolReopenTime = \
    comp_stack = sim_func(**sim_args)
    Ih = comp_stack[7]
    fit_compt = Ih.sum(axis=1).sum(axis=1)[
        range(0, scenario['total_time'] * scenario['interval_per_day'],
              scenario['interval_per_day'])]

    # TODO: explore ways to make the fitting flexible to extend to other compartments
    #fit_compt = hosp_error(Ih, data, scenario=scenario)
    return fit_compt[comp_offset: comp_offset + len(data)] - data


def hosp_error(hosp_model, hosp_observed, scenario):

    fit_compt = hosp_model.sum(axis=1).sum(axis=1)[
        range(0, scenario['total_time'] * scenario['interval_per_day'],
              scenario['interval_per_day'])]

    return fit_compt[:len(hosp_observed)] - hosp_observed


def rmsd_t(error):
    """Root mean squared deviation for time series"""

    return sum([i**2 for i in error])/len(error)


def nrmsd_t(rmsd, data):
    """Normalised root mean squared deviation"""

    return rmsd/(max(data) - min(data))


def filter_params(param_dict):

    assert isinstance(param_dict['beta0'], np.ndarray), \
        "beta0 is not a numpy ndarray: beta0 == {}".format(param_dict['beta0'])
    core_param_keys = {
        'metro_pop', 'school_calendar', 'c_reduction_date', 'c_reduction', 'beta0',
        'phi', 'sigma',
        'gamma', 'eta', 'mu', 'omega', 'tau', 'nu', 'pi', 'n_age',
        'n_risk', 'total_time', 'interval_per_day', 'shift_week',
        'time_begin', 'time_begin_sim', 'initial_state', 'trigger_type',
        'close_trigger', 'reopen_trigger', 'monitor_lag', 'report_rate',
        'deterministic', 'config', 't_offset'}
    # grab only the pars needed for the SEIR model
    utils.assert_has_keys(param_dict, core_param_keys)
    drop_keys = set(param_dict.keys()).difference(core_param_keys)
    for key in drop_keys:
        param_dict.pop(key)

    return param_dict
