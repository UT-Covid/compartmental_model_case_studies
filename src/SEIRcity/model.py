# -*- coding: utf-8 -*-
"""
Main file for SEIR model
"""
from . import school_closure

# DEBUG - dev_utils decorator
from . import dev_utils
dev_utils.decorate_all_in_module(school_closure, dev_utils.base_decorator)

import numpy as np
import pandas as pd
import datetime as dt
from scipy import stats

np.set_printoptions(linewidth=115)
pd.set_option('display.width', 115)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.options.display.float_format = '{:,.8f}'.format
# pd.set_option('precision', -1)

def SEIR_model_publish_w_risk(metro_pop, school_calendar, beta0,
                              phi, sigma, gamma, eta, mu,
                              omega, tau, nu, pi,
                              n_age, n_risk, total_time, interval_per_day,
                              shift_week, time_begin, time_begin_sim,
                              initial_state, c_reduction_date, c_reduction, trigger_type, close_trigger,
                              reopen_trigger, monitor_lag, report_rate, t_offset,
                              deterministic=True, print_vals=False):
    """
    :param metro_pop: np.array of shape (n_age, n_risk)
    :param school_calendar: np.array of shape(), school calendar from data
    :param beta0: np.array of shape (n_age, ), baseline beta
    :param phi: dict of 4 np.array of shape (n_age, n_age), \
    contact matrix of all, school, work, home
    :param sigma: np.array of shape (n_age, ), rate of E to I
    :param gamma: np.array of shape (3, n_age), rate of I to R
    :param eta: old: np.array of shape (n_age, ), rate from I^y to I^H
    :param mu: np.array of shape (n_age, ), rate from I^H to D
    :param omega: np.array of shape (4, n_age), relative infectiousness of I / E
    :param tau: np.array of shape (n_age, ), symptomatic rate of I
    :param nu: np.array of shape (n_risk, n_age), case fatality rate in I^H
    :param pi: np.array of shape (n_risk, n_age), Pr[I^Y to I^H]
    :param n_age: int, number of age groups
    :param n_risk: int, number of risk groups
    :param total_time: int, total length of simulation in (Days)
    :param interval_per_day: int, number of intervals within a day
    :param shift_week: int, shift week !!
    :param time_begin: datetime, time begin (school calendar start date)
    :param time_begin_sim: int, time to begin simulation
    :param initial_state: np.array of shape(n_age, n_risk), initial_i
    :param c_reduction_date: list of 2 int, time to start and end social distancing
    :param c_reduction: float, % reduction in non-household contacts
    :param trigger_type: str, {'cml', 'current', 'new'}
    :param close_trigger: str, format: type_population_number; example: number_all_5 or ratio_school_1 or date__20200315
    :param reopen_trigger: str, format: type_population_number, example: monitor_all_75 (75% reduction), no_na_12 (12 weeks)
    :param monitor_lag: int, time lag between surveillance and real time in (Days)
    :param report_rate: float, proportion Y can seen
    :param deterministic: boolean, whether to remove poisson stochasticity
    :return: compt_s, compt_e, compt_ia, compt_ih, compt_ih, compt_r, compt_d, compt_e2compt_iy
    """

    compt_s = initial_state['S']
    compt_e = initial_state['E']
    compt_ia = initial_state['Ia']
    compt_iy = initial_state['Iy']
    compt_e2compt_i = initial_state['E2I']
    compt_ih = initial_state['Ih']
    compt_r = initial_state['R']
    compt_e2compt_iy = initial_state['E2Iy']
    compt_d = initial_state['D']
    compt_iy2compt_ih = initial_state['Iy2Ih']
    compt_h2compt_d = initial_state['H2D']

    initial_i = initial_state['Iy'][0]

    # these are returned by init_state.initialize() but they're empty anyway...
    school_close_arr = np.zeros_like(compt_s, dtype=float)
    school_reopen_arr = np.zeros_like(compt_s, dtype=float)

    ## -- set up timings

    date_begin = dt.datetime.strptime(np.str(time_begin_sim), '%Y%m%d') + dt.timedelta(weeks=shift_week)

    sd_begin_date = dt.datetime.strptime(np.str(c_reduction_date[0]), '%Y%m%d')
    sd_end_date = dt.datetime.strptime(np.str(c_reduction_date[1]), '%Y%m%d')

    # find the index in the school calendar where the simulations will start
    sim_begin_idx = (date_begin - time_begin).days
    school_calendar = school_calendar[sim_begin_idx:]

    ## -- get contact matrices

    # Contact matrix for 5 age groups, adjusted to time-step
    phi_all = phi['phi_all'] / interval_per_day
    phi_school = phi['phi_school'] / interval_per_day
    phi_work = phi['phi_work'] / interval_per_day
    phi_home = phi['phi_home'] / interval_per_day
    phi_other = phi_all - phi_school - phi_work - phi_home
    if print_vals:
        print('Contact matrices\n\
        All: {}\nSchool: {}\nWork: {}\nHome: {}\nOther places: {}'.format(phi_all * interval_per_day,
                                                                          phi_school * interval_per_day,
                                                                          phi_work * interval_per_day,
                                                                          phi_home * interval_per_day,
                                                                          phi_other * interval_per_day))

    ## -- define rates based on model timings

    # Rate from symptom onset to hospitalized
    eta = eta / interval_per_day
    if print_vals:
        print('eta', eta)
        print('Duration from symptom onset to hospitalized', 1 / eta / interval_per_day)

    # Symptomatic rate
    if print_vals:
        print('Asymptomatic rate', 1 - tau)

    # Rate from hospitalized to death
    mu = mu / interval_per_day
    if print_vals:
        print('mu', mu)
        print('Duration from hospitalized to death', 1 / mu / interval_per_day)

    # Relative Infectiousness for Ia, Iy, It compartment
    omega_a, omega_y, omega_h, omega_e = omega
    if print_vals:
        print('Relative infectiousness for Ia, Iy, Ih, E is {0} {1} {2} {3}'.format(*omega))

    # Incubation period
    sigma = sigma / interval_per_day
    if print_vals:
        print('sigma', sigma)
        print('Incubation period is {}'.format(1 / sigma / interval_per_day))

    # Recovery rate
    gamma_a, gamma_y, gamma_h = gamma / interval_per_day
    if print_vals:
        print('gamma', gamma_a, gamma_y, gamma_h)
        print('Infectious period for Ia, Iy, Ih is {0} {1} {2}'.format(1 / gamma_a.mean() / interval_per_day,
                                                                       1 / gamma_y.mean() / interval_per_day,
                                                                       1 / gamma_h.mean() / interval_per_day))

    # Case Fatality Rate
    nu_l, nu_h = nu
    if print_vals:
        print('Hospitalized fatality rate for low risk group is {0}, for high risk group is {1}'.format(*nu))

    # Probability symptomatic go to hospital
    pi_l, pi_h = pi
    if print_vals:
        print('Probability of symptomatic individuals go to hospital', pi)

    # Placeholders for
    school_closed = False
    school_reopened = False
    school_close_date = 'NA'
    school_reopen_date = 'NA'

    ## -- Start simulation

    # Iterate over intervals
    for t in range(1, total_time * interval_per_day):
        days_from_t0 = np.floor((t + 0.1) / interval_per_day)
        if t_offset:
            t_date = date_begin + t_offset + dt.timedelta(days=days_from_t0)
        else:
            t_date = date_begin + dt.timedelta(days=days_from_t0)
        # print(t_date)

        # Use appropriate contact matrix
        # Use different phi values on different days of the week
        if sd_begin_date <= t_date < sd_end_date:
            kappa = 1.0 - c_reduction

        else:
            kappa = 1.0

        """
        phi_weekday - ((1 - contact_reduction) * phi_school)
        (phi_weekday - phi_school) * (1-contact_reduction) 
        """

        phi_weekday = phi_all
        phi_weekend = (phi_all - phi_school - phi_work)
        phi_weekday_holiday = phi_weekend
        phi_weekday_long_break = phi_weekday - phi_school
        phi_open = [phi_weekday, phi_weekend, phi_weekday_holiday, phi_weekday_long_break]
        phi_close = [phi_weekday - phi_school, phi_weekend, phi_weekday_holiday, phi_weekday_long_break]

        calendar_code = int(school_calendar[int(days_from_t0)])  # 1-weekday, 2-weekend, 3-weekday holiday, 4-weekday long break
        if school_closed == school_reopened:
            phi = phi_open[calendar_code - 1]
        else:
            phi = phi_close[calendar_code - 1]

        temp_s = np.zeros(shape=(n_age, n_risk))
        temp_e2iy = np.zeros(shape=(n_age, n_risk))
        temp_e2i = np.zeros(shape=(n_age, n_risk))
        temp_e = np.zeros(shape=(n_age, n_risk))
        temp_ia = np.zeros(shape=(n_age, n_risk))
        temp_iy = np.zeros(shape=(n_age, n_risk))
        temp_ih = np.zeros(shape=(n_age, n_risk))
        temp_r = np.zeros(shape=(n_age, n_risk))
        temp_d = np.zeros(shape=(n_age, n_risk))
        temp_iy2ih = np.zeros(shape=(n_age, n_risk))
        temp_h2d = np.zeros(shape=(n_age, n_risk))

        ## within nodes
        # for each age group
        for a in range(n_age):
            # for each risk group
            for r in range(n_risk):
                rate_s2e = 0.

                # TODO: assumptions are hard-coded
                # TODO: pass a single nu arg
                if r == 0:  # p0 is low-risk group, 1 is high risk group
                    temp_nu = nu_l
                    temp_pi = pi_l
                else:
                    temp_nu = nu_h
                    temp_pi = pi_h

                # Calculate infection force (F)
                # As far as I can tell, the ONLY instance in these
                # age-risk iterators where there is interaction between
                # age-risk categories
                for a2 in range(n_age):
                    for r2 in range(n_risk):
                        # Rate of change from S -> E compartment
                        rate_s2e += beta0[a2] * kappa * phi[a, a2] * omega_a[a2] * compt_s[t - 1, a, r] * compt_ia[
                            t - 1, a2, r2] / np.sum(metro_pop[a2]) + \
                                    beta0[a2] * kappa * phi[a, a2] * omega_y[a2] * compt_s[t - 1, a, r] * compt_iy[
                                        t - 1, a2, r2] / np.sum(metro_pop[a2]) + \
                                    beta0[a2] * kappa * phi[a, a2] * omega_y[a2] * compt_s[t - 1, a, r] * compt_e[
                                        t - 1, a2, r2] * omega_e[a2] / np.sum(metro_pop[a2])
                if np.isnan(rate_s2e):
                    rate_s2e = 0

                # Rate change of each compartment
                # (besides S -> E calculated above)
                rate_e2i = sigma[a] * compt_e[t - 1, a, r]
                rate_ia2r = gamma_a[a] * compt_ia[t - 1, a, r]
                rate_iy2r = (1 - temp_pi[a]) * gamma_y[a] * compt_iy[t - 1, a, r]
                rate_ih2r = (1 - temp_nu[a]) * gamma_h[a] * compt_ih[t - 1, a, r]
                rate_iy2ih = temp_pi[a] * eta[a] * compt_iy[t - 1, a, r]
                rate_ih2d = temp_nu[a] * mu[a] * compt_ih[t - 1, a, r]

                if not deterministic:
                    rate_s2e = np.random.poisson(rate_s2e)
                if np.isinf(rate_s2e):
                    rate_s2e = 0

                if not deterministic:
                    rate_e2i = np.random.poisson(rate_e2i)
                if np.isinf(rate_e2i):
                    rate_e2i = 0

                if not deterministic:
                    rate_ia2r = np.random.poisson(rate_ia2r)
                if np.isinf(rate_ia2r):
                    rate_ia2r = 0

                if not deterministic:
                    rate_iy2r = np.random.poisson(rate_iy2r)
                if np.isinf(rate_iy2r):
                    rate_iy2r = 0

                if not deterministic:
                    rate_ih2r = np.random.poisson(rate_ih2r)
                if np.isinf(rate_ih2r):
                    rate_ih2r = 0

                if not deterministic:
                    rate_iy2ih = np.random.poisson(rate_iy2ih)
                if np.isinf(rate_iy2ih):
                    rate_iy2ih = 0

                if not (deterministic):
                    rate_ih2d = np.random.poisson(rate_ih2d)
                if np.isinf(rate_ih2d):
                    rate_ih2d = 0


                # In the below block, calculate values and deltas of each category
                # in SEIR, for each age-risk category, at this timepoint

                d_s = -rate_s2e
                temp_s[a, r] = compt_s[t - 1, a, r] + d_s
                if temp_s[a, r] < 0:
                    rate_s2e = compt_s[t - 1, a, r]
                    temp_s[a, r] = 0

                d_e = rate_s2e - rate_e2i
                temp_e[a, r] = compt_e[t - 1, a, r] + d_e
                if temp_e[a, r] < 0:
                    rate_e2i = compt_e[t - 1, a, r] + rate_s2e
                    temp_e[a, r] = 0

                temp_e2i[a, r] = rate_e2i
                temp_e2iy[a, r] = tau[a] * rate_e2i
                if temp_e2iy[a, r] < 0:
                    rate_e2i = 0
                    temp_e2i[a, r] = 0
                    temp_e2iy[a, r] = 0

                d_ia = (1 - tau[a]) * rate_e2i - rate_ia2r
                temp_ia[a, r] = compt_ia[t - 1, a, r] + d_ia
                if temp_ia[a, r] < 0:
                    rate_ia2r = compt_ia[t - 1, a, r] + (1 - tau[a]) * rate_e2i
                    temp_ia[a, r] = 0

                d_iy = tau[a] * rate_e2i - rate_iy2r - rate_iy2ih
                temp_iy[a, r] = compt_iy[t - 1, a, r] + d_iy
                if temp_iy[a, r] < 0:
                    rate_iy2r = (compt_iy[t - 1, a, r] + tau[a] * rate_e2i) * rate_iy2r / (rate_iy2r + rate_iy2ih)
                    rate_iy2ih = compt_iy[t - 1, a, r] + tau[a] * rate_e2i - rate_iy2r
                    temp_iy[a, r] = 0

                temp_iy2ih[a, r] = rate_iy2ih
                if temp_iy2ih[a, r] < 0:
                    temp_iy2ih[a, r] = 0

                d_ih = rate_iy2ih - rate_ih2r - rate_ih2d
                temp_ih[a, r] = compt_ih[t - 1, a, r] + d_ih
                if temp_ih[a, r] < 0:
                    rate_ih2r = (compt_ih[t - 1, a, r] + rate_iy2ih) * rate_ih2r / (rate_ih2r + rate_ih2d)
                    rate_ih2d = compt_ih[t - 1, a, r] + rate_iy2ih - rate_ih2r
                    temp_ih[a, r] = 0

                d_r = rate_ia2r + rate_iy2r + rate_ih2r
                temp_r[a, r] = compt_r[t - 1, a, r] + d_r

                d_d = rate_ih2d
                temp_h2d[a, r] = rate_ih2d
                temp_d[a, r] = compt_d[t - 1, a, r] + d_d

        # We are now done calculating compartment values for each
        # age-risk category
        # Copy this vector array as a slice on time axis
        compt_s[t] = temp_s
        compt_e[t] = temp_e
        compt_ia[t] = temp_ia
        compt_iy[t] = temp_iy
        compt_ih[t] = temp_ih
        compt_r[t] = temp_r
        compt_d[t] = temp_d
        compt_e2compt_iy[t] = temp_e2iy
        compt_e2compt_i[t] = temp_e2i
        compt_iy2compt_ih[t] = temp_iy2ih
        compt_h2compt_d[t] = temp_h2d

        # Check if school closure is triggered
        # TODO: could probably be a separate, downstream function
        t_surveillance = np.maximum(t - monitor_lag * interval_per_day, 0)
        current_iy = compt_iy[t_surveillance]  # Current number of infected
        new_iy = compt_e2compt_iy[t_surveillance]  # New number of infected of current time-step
        cml_iy = np.sum(compt_e2compt_iy[:(t_surveillance + 1)], axis=0) + initial_i  # Cumulative number of infected
        trigger_type_dict = {'cml': cml_iy, 'current': current_iy, 'new': new_iy}
        trigger_iy = trigger_type_dict[trigger_type.lower()]

        if not school_closed:
            school_closed = school_closure.school_close(
                close_trigger, t_date, trigger_iy, metro_pop)
            if school_closed:
                school_close_arr[t, :, :] = 1
                school_close_time = t
                school_close_date = t_date
                school_close_iy = trigger_iy
        else:
            if not school_reopened:
                school_reopened = school_closure.school_reopen(
                    reopen_trigger, school_close_iy, trigger_iy,
                    school_close_time, t, t_date, interval_per_day)
                if school_reopened:
                    school_reopen_arr[t, :, :] = 1.
                    school_reopen_date = t_date

    # print('School closed: {0}, school reopened: {1}'.format(school_closed, school_reopened))

    # if t > 14 * interval_per_day and np.sum(compt_e2compt_iy[np.maximum(t - 10 * interval_per_day, 1):]) < np.sum(initial_i):
    #     print('No new infection for 10 days')
    #     break

    # In SEIR_main_publish, maps to
    # compt_s=S, compt_e=E, compt_ia=Ia, compt_iy=Iy, compt_ih=Ih, compt_r=R,
    # compt_d=D, compt_e2compt_iy=E2Iy, compt_e2compt_i=E2I,
    # compt_iy2compt_ih=Iy2Ih, compt_h2compt_d=H2D, \
    # SchoolCloseTime, SchoolReopenTime
    return (compt_s, compt_e, compt_ia, compt_iy, compt_ih, compt_r, compt_d,
            compt_e2compt_iy, compt_e2compt_i, compt_iy2compt_ih,
            compt_h2compt_d, school_close_arr, school_reopen_arr)


def compute_R0(compt_e2compt_i, interval_per_day, para, growth_rate):
    """
    :param: np.array containing new symptomatic cases in each time step
    :param: interval_per_day: int, number of time steps per day
    :param: para: dict, parameter dictionary
    :return: a single number as estimate of R0
    """
    # Get total cases (summed over risk and age groups)
    cases_ts = compt_e2compt_i.sum(axis=2).sum(axis=1)

    # Get generation time implied by doubling time and growth rate
    R0_obj = para['r0']  # target R0
    double_time = para['double_time'][growth_rate]
    gen_time = double_time * (R0_obj - 1) / (np.log(2))

    # Find peak of new cases
    max_idx = np.where(cases_ts == cases_ts.max())[0][0]

    # Remove last full day of data (plus part of day if any)
    cutoff = max_idx - np.mod(max_idx, interval_per_day) - interval_per_day
    growing_cases = cases_ts[:cutoff]

    # Get number of days in time series, aggregate per day
    nb_days = np.int(cutoff / interval_per_day)
    cases_daily = growing_cases.reshape(nb_days, interval_per_day).sum(axis=1)

    # Compute growth rate (Get rid of starting zeros for log)
    #    min_pos_day = np.where(cases_daily>0)[0][0]
    nb_zeros = len(np.where(cases_daily == 0)[0])
    if nb_zeros > 0:
        min_pos_day = np.where(cases_daily == 0)[0][-1] + 1
    else:
        min_pos_day = 0

    if min_pos_day < len(cases_daily):
        time = list(range(min_pos_day, nb_days))
        log_cases = np.log(cases_daily[min_pos_day:])
        # NOTE: growth_rate here is not the same as arg
        # it is a new var probably type == float
        growth_rate, y0, r_val, p_val, std_err = stats.linregress(time, log_cases)

        # Get estimate R0
        R0 = gen_time * growth_rate + 1
    else:
        R0 = 0

    return R0

# Using parameter document (not scaled for 10 daily time steps)
# rate_y2r = (1 - pi['low']) * gamma_y_c
# rate_y2h = pi['low'] * eta_c
# 100*rate_y2h/(rate_y2h+rate_y2r) # must be CDC's pi_0 by construction
#
## Using model values (above), so after scaled for 10 daily time steps
# rate_iy2r_model = (1 - pi) * gamma_y
# rate_iy2ih_model = pi * eta
# 100*rate_iy2ih_model/(rate_iy2r_model+rate_iy2ih_model) # must be CDC's pi_0 as well
#
# rate_ih2r_model = (1 - temp_nu) * gamma_h
# rate_ih2d_model = temp_nu * mu
# 100*rate_ih2d_model/(rate_ih2r_model+rate_ih2d_model) # must be CDC's nu_0 as well
