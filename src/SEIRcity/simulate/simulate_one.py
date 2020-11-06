#!/usr/bin/env python
import numpy as np
from SEIRcity import model
from SEIRcity.utils import R0_arr_to_float, assert_has_keys
from SEIRcity.get_phi import get_phi
from SEIRcity.scenario import BaseScenario
from SEIRcity.param import SEIR_get_param

# DEV
from SEIRcity.dev_utils import base_decorator


def simulate_one(scenario):
    """Given an instance of BaseScenario `scenario`, run a simulation
    using the SEIR model. Returns a stacked numpy array.
    """
    assert isinstance(scenario, BaseScenario), "arg `scenario` is type " + \
        "{}, must be an instance of scenario.BaseScenario".format(type(scenario))

    # seed numpy.random
    # TODO: use a numpy.random.Generator to generate stochastic dists
    seed = scenario.get("seed", None)
    # print("seed is: {}".format(seed))
    np.random.seed(seed)

    # get epi parameters
    scenario.update(SEIR_get_param(scenario['config']))

    # ------------------------------------------------------------------

    # argument names for model function
    model_arg_names = (
        'metro_pop', 'school_calendar',
        'beta0',
        'c_reduction', 'c_reduction_date',
        'phi',
        'sigma', 'gamma', 'eta', 'mu', 'omega', 'tau', 'nu', 'pi',
        'n_age', 'n_risk', 'total_time', 'interval_per_day', 'shift_week',
        'time_begin',
        'time_begin_sim', 'initial_state', 'trigger_type',
        'close_trigger', 'reopen_trigger',
        'monitor_lag', 'report_rate',
        'deterministic', 't_offset'
    )
    # attrs needed for preprocessing below
    require_from_args = ['beta0', 'n_age', 'phi',
                         'c_reduction', 'interval_per_day',
                         'close_trigger']
    # make sure passed scenario object has all the necessary attrs
    # for preprocessing before calling model function
    _ = assert_has_keys(d=scenario, required_keys=require_from_args)
    model_kwargs = scenario.copy()

    # ------------------------------------------------------------------

    # get epidemiological parameters
    # Get epidemiological parameters
    # This needs to be run for each scenario to honor stochasticity


    # manually change beta0 to correct type
    model_kwargs['beta0'] = scenario['beta0'] * np.ones(scenario['n_age'])
    # manually set c_reduction to sd_level
    # they are the same in v1.1
    # model_kwargs['sd_level'] = scenario['c_reduction']
    # model_kwargs['sd_date'] = scenario['c_reduction_date']

    # validate that model_kwargs has all the necessary keys
    _ = assert_has_keys(d=model_kwargs, required_keys=model_arg_names)

    # assert all([k in model_kwargs.keys() for k in model_arg_names])
    # filter to the necessary keys
    model_kwargs_filtered = {
        k: model_kwargs[k] for k in model_kwargs.keys()
        if k in model_arg_names
    }

    # run model
    S, E, Ia, Iy, Ih, R, D, E2Iy, E2I, Iy2Ih, H2D, SchoolCloseTime, \
        SchoolReopenTime = model.SEIR_model_publish_w_risk(**model_kwargs_filtered)

    compute_R0 = bool(scenario['c_reduction'] == 0 and
                          scenario['close_trigger'].split('_')[-1] == '20220101')
    if compute_R0:
        R0_float = model.compute_R0(E2I, scenario['interval_per_day'],
                                    scenario['Para'], scenario['g_rate'])
        R0 = R0_float * np.ones_like(E2Iy)
    else:
        R0 = np.nan * np.ones_like(E2Iy)

    return np.stack([
            S,
            E2Iy,
            E2I,
            Iy2Ih,
            H2D,
            Ia,
            Iy,
            Ih,
            R,
            E,
            D,
            SchoolCloseTime,
            SchoolReopenTime,
            R0
        ], axis=0)

    # else:
    #     compute_R0 = bool(scenario['c_reduction'] == 0 and
    #                       scenario['close_trigger'].split('_')[-1] == '20220101')
    #     if compute_R0:
    #         R0_float = model.compute_R0(E2I, scenario['interval_per_day'],
    #                                     scenario['Para'], scenario['g_rate'])
    #         R0 = R0_float * np.ones_like(E2Iy)
    #     else:
    #         R0 = np.nan * np.ones_like(E2Iy)
    #
    #     return np.stack([
    #         S,
    #         E2Iy,
    #         E2I,
    #         Iy2Ih,
    #         H2D,
    #         Ia,
    #         Iy,
    #         Ih,
    #         R,
    #         E,
    #         D,
    #         SchoolCloseTime,
    #         SchoolReopenTime,
    #         R0
    #     ], axis=0)
