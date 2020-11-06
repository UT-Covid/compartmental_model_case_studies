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

# DEV
from SEIRcity import dev_utils


def school_date_from_arr(arr, interval_per_day, time_begin_sim, shift_week):
    """Converts school event dates from boolean arrays to time index
    at which the event occurred. Used only for pytests.
    """
    # for 2D currently
    t_slice = arr[:, 0]
    assert len(t_slice.shape) == 1, t_slice.shape
    try:
        time_idx = np.where(t_slice == 1.)[0][0]
        time_idx = float(time_idx)
        assert isinstance(time_idx, float), time_idx
    except KeyError:
        # legacy result
        return "NA"
    print("time_idx: ", time_idx)

    # convert to datetime
    date_begin = dt.datetime.strptime(np.str(time_begin_sim), '%Y%m%d') + \
        dt.timedelta(weeks=shift_week)
    days_from_t0 = np.floor((time_idx + 0.1) / interval_per_day)
    t_date = date_begin + dt.timedelta(days=days_from_t0)
    return t_date


def _legacy_simulate_multiple(yaml_fp, out_fp=None, verbosity=0):

    # ------------------Get params from paramparser---------------------

    params = param_module.aggregate_params_and_data(yaml_fp=yaml_fp)

    DATA_FOLDER = params['DATA_FOLDER']
    RESULTS_DIR = params['RESULTS_DIR']
    GROWTH_RATE_LIST = params['GROWTH_RATE_LIST']
    CONTACT_REDUCTION = params['CONTACT_REDUCTION']
    CLOSE_TRIGGER_LIST = params['CLOSE_TRIGGER_LIST']
    REOPEN_TRIGGER_LIST = params['REOPEN_TRIGGER_LIST']
    NUM_SIM = params['NUM_SIM']
    beta0_dict = params['beta0_dict']
    n_age = params['n_age']
    n_risk = params['n_risk']
    CITY = params['CITY']
    shift_week = params['shift_week']
    time_begin_sim = params['time_begin_sim']
    interval_per_day = params['interval_per_day']
    total_time = params['total_time']
    monitor_lag = params['monitor_lag']
    report_rate = params['report_rate']
    # START_CONDITION = 5
    I0 = params['I0']
    trigger_type = params['trigger_type']
    deterministic = params['deterministic']

    # from SEIR_get_data
    metro_pop = params['metro_pop']
    school_calendar = params['school_calendar']
    time_begin = params['time_begin']
    FallStartDate = params['FallStartDate']

    # from SEIR_get_param
    Phi = params['phi']

    # ------------------------------------------------------------------

    all_growth_rates = dict()
    for g_rate in GROWTH_RATE_LIST:
        beta0 = beta0_dict[g_rate] # * np.ones(n_age)
        E2Iy_dict = {}
        E2I_dict = {}
        Iy2Ih_dict = {}
        Ih2D_dict = {}
        Ia_dict = {}
        Iy_dict = {}
        Ih_dict = {}
        R_dict = {}
        CloseDate_dict = {}
        ReopenDate_dict = {}
        R0_baseline = []
        for c_reduction in CONTACT_REDUCTION:
            E2Iy_dict_temp = {}
            E2I_dict_temp = {}
            Iy2Ih_dict_temp = {}
            Ih2D_dict_temp = {}
            Ia_dict_temp = {}
            Iy_dict_temp = {}
            Ih_dict_temp = {}
            R_dict_temp = {}
            CloseDate_dict_temp = {}
            ReopenDate_dict_temp = {}
            # parse to list of datetime points
            DateVar = []
            for t in range(0, total_time):
                DateVar.append(dt.datetime.strptime(np.str(time_begin_sim), '%Y%m%d') + dt.timedelta(days=t))
            # print(DateVar)
            for c_trigger in CLOSE_TRIGGER_LIST:
                close_trigger = c_trigger
                for r_trigger in REOPEN_TRIGGER_LIST:
                    reopen_trigger = r_trigger
                    print(reopen_trigger)
                    # DEBUG: disable color cycling
                    # LineColor = COLOR_PALETTE[CLOSE_TRIGGER_LIST.index(close_trigger)][REOPEN_TRIGGER_LIST.index(reopen_trigger)]
                    LineColor = 'black'
                    E2Iy_list = []
                    E2I_list = []
                    Iy2Ih_list = []
                    Ih2D_list = []
                    Ia_list = []
                    Iy_list = []
                    Ih_list = []
                    R_list = []
                    CloseDate_list = []
                    ReopenDate_list = []
                    for sim in range(NUM_SIM):
                        assert all([k in Phi.keys() for k in
                                    ('phi_all', 'phi_school', 'phi_work', 'phi_home')])
                        # get epi params
                        assert 'initial_state' in params
                        Para = param_module.SEIR_get_param(config=params)
                        scenario = Scenario({
                            'n_age': n_age,
                            'n_risk': n_risk,
                            'total_time': total_time,
                            'interval_per_day': interval_per_day,
                            'c_reduction_date': params['sd_date'],
                            'shift_week': shift_week,
                            'time_begin': time_begin,
                            'time_begin_sim': time_begin_sim,
                            'initial_i': I0,
                            'trigger_type': trigger_type,
                            'close_trigger': close_trigger,
                            'reopen_trigger': reopen_trigger,
                            'monitor_lag': monitor_lag,
                            'report_rate': report_rate,
                            'g_rate': g_rate,
                            'c_reduction': c_reduction,
                            'beta0': beta0,
                            'phi': Phi,
                            'metro_pop': metro_pop,
                            'FallStartDate': FallStartDate,
                            'school_calendar': school_calendar,
                            'deterministic': deterministic,
                            'verbosity': verbosity,
                            'initial_state': params['initial_state'],
                            't_offset': params['t_offset'],
                            'config': params
                        })
                        scenario.update(Para)
                        # from pprint import pprint
                        # pprint(scenario)
                        # assert 0 == scenario
                        result = simulate_one(scenario)

                        # ----------------------------------------------

                        # convert school event times to legacy
                        # datetime.datetime
                        bool_to_dt_kwargs = {
                            'interval_per_day': interval_per_day,
                            'time_begin_sim': time_begin_sim,
                            'shift_week': shift_week}
                        SchoolCloseTime = utils.bool_arr_to_dt(
                            result[11], **bool_to_dt_kwargs)
                        SchoolReopenTime = utils.bool_arr_to_dt(
                            result[12], **bool_to_dt_kwargs)

                        # convert to legacy R0
                        R0 = utils.R0_arr_to_float(result[13])
                        if R0 is not None:
                            R0_baseline.append(R0)

                        # ----------------------------------------------
                        # DEBUG: we remove the first element (S compartment)
                        # because legacy code did not report it

                        E2Iy_list.append(result[1])
                        E2I_list.append(result[2])
                        Iy2Ih_list.append(result[3])
                        Ih2D_list.append(result[4])
                        Ia_list.append(result[5])
                        Iy_list.append(result[6])
                        Ih_list.append(result[7])
                        R_list.append(result[8])
                        CloseDate_list.append(SchoolCloseTime)
                        ReopenDate_list.append(SchoolReopenTime)

                        # ----------------------------------------------


                    # Aggregate sums from each replicate
                    E2Iy_dict_temp[close_trigger + '/' + reopen_trigger] = np.array(E2Iy_list)
                    E2I_dict_temp[close_trigger + '/' + reopen_trigger] = np.array(E2I_list)
                    Iy2Ih_dict_temp[close_trigger + '/' + reopen_trigger] = np.array(Iy2Ih_list)
                    Ih2D_dict_temp[close_trigger + '/' + reopen_trigger] = np.array(Ih2D_list)
                    Ia_dict_temp[close_trigger + '/' + reopen_trigger] = np.array(Ia_list)
                    Iy_dict_temp[close_trigger + '/' + reopen_trigger] = np.array(Iy_list)
                    Ih_dict_temp[close_trigger + '/' + reopen_trigger] = np.array(Ih_list)
                    R_dict_temp[close_trigger + '/' + reopen_trigger] = np.array(R_list)
                    CloseDate_dict_temp[close_trigger + '/' + reopen_trigger] = CloseDate_list
                    ReopenDate_dict_temp[close_trigger + '/' + reopen_trigger] = ReopenDate_list

                    if close_trigger.split('_')[-1] == '20220101':
                        break

            # Aggregate compartment data into dict keyed by
            # CONTACT_REDUCTION scenario
            E2Iy_dict[c_reduction] = E2Iy_dict_temp
            E2I_dict[c_reduction] = E2I_dict_temp
            Iy2Ih_dict[c_reduction] = Iy2Ih_dict_temp
            Ih2D_dict[c_reduction] = Ih2D_dict_temp
            Ia_dict[c_reduction] = Ia_dict_temp
            Iy_dict[c_reduction] = Iy_dict_temp
            Ih_dict[c_reduction] = Ih_dict_temp
            R_dict[c_reduction] = R_dict_temp
            CloseDate_dict[c_reduction] = CloseDate_dict_temp
            ReopenDate_dict[c_reduction] = ReopenDate_dict_temp

        # Assemble dictionary for *.pckl file
        data_for_pckl = {
            'CITY': CITY,
            'GROWTH_RATE': g_rate,
            'CONTACT_REDUCTION': CONTACT_REDUCTION,
            'time_begin_sim': time_begin_sim,
            'beta0': beta0 * np.ones(n_age),
            'Para': Para,
            'metro_pop': metro_pop,
            'CLOSE_TRIGGER_LIST': CLOSE_TRIGGER_LIST,
            'REOPEN_TRIGGER_LIST': REOPEN_TRIGGER_LIST,
            'E2Iy_dict': E2Iy_dict,
            'E2I_dict': E2I_dict,
            'Ia_dict': Ia_dict,
            'Iy_dict': Iy_dict,
            'Ih_dict': Ih_dict,
            'R_dict': R_dict,
            'Iy2Ih_dict': Iy2Ih_dict,
            'Ih2D_dict': Ih2D_dict,
            'CloseDate_dict': CloseDate_dict,
            'ReopenDate_dict': ReopenDate_dict,
            'R0_baseline': R0_baseline}

        # Write results to *.pckl file in RESULTS_DIR
        # pckl_fname = str(CITY + '-' + g_rate + str(time_begin_sim) + '_' + str(NUM_SIM) + '.pckl')
        # if out_fp is None:
        #     pckl_fp = os.path.join(RESULTS_DIR, pckl_fname)
        # else:
        #     pckl_fp = out_fp
        # with open(pckl_fp, 'wb') as pckl_file:
        #     pickle.dump(data_for_pckl, pckl_file)

        all_growth_rates[g_rate] = data_for_pckl
    return all_growth_rates
