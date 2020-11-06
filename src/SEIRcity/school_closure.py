# -*- coding: utf-8 -*-
"""
Decide if school is closing or reopening on a specific day
"""

import numpy as np
import datetime as dt


def school_close(trigger, current_date, current_infected, metro_pop):
    """
    :param trigger: str, format: type_population_number; example: number_all_5 or ratio_school_1 or date__20200315
    :param current_date: datetime object, current date
    :param current_infected: np array of shape (n_age, ), number of infected #TIME LAG DAYS AGO
    :param metro_pop: np array of shape (n_age, riskNum), metro population size
    :return: school_close: tuple, 1 means school is closed
    """

    trigger_type, trigger_pop, trigger_value = trigger.split('_')

    # Not close on a specific date
    if trigger_type[0].lower() != 'd':
        # all population
        if trigger_pop[0].lower() == 'a':
            target_pop_size = np.sum(metro_pop)
            target_infected = np.sum(current_infected)
        # target school-age
        else:
            target_pop_size = np.sum(metro_pop[1])
            target_infected = np.sum(current_infected[1])

        # Close when reach specific number
        if trigger_type[0].lower() == 'n':
            closure_threshold = int(trigger_value)
        # Close when reach proportion / ratio
        else:
            closure_threshold = int(trigger_value) * target_pop_size / 100.0  # need to round? ceil? floor?

        if target_infected >= closure_threshold:
            school_close = True
        else:
            school_close = False

    # Close on a specific date
    else:
        trigger_date = dt.datetime.strptime(np.str(trigger_value), '%Y%m%d')

        if current_date >= trigger_date:
            school_close = True
        else:
            school_close = False

    return school_close


def school_reopen(trigger, closing_infected, current_infected, closing_t, current_t, current_date, interval_per_day):
    """
    :param trigger: str, format: type_population_number, example: monitor_all_75 (75% reduction), no_na_12 (12 weeks)
    :param closing_infected: np.array of shape (n_age, riskNum), number of cases on the day of closure on the day of closure - time lag?
    :param current_infected: np.array of shape (n_age, riskNum), number of infected #TIME LAG DAYS AGO
    :param closing_t: int, time when school closure initiated
    :param current_t: int, current time
    :param current_date: datetime object, current date
    :param interval_per_day: int, number of intervals in a day
    :return: school_reopen: tuple, 1 means school reopen
    """

    trigger_type, trigger_pop, trigger_value = trigger.split('_')

    # Monitor
    if trigger_type[0].lower() == 'm':
        # all population
        if trigger_pop[0].lower() == 'a':
            target_infected = np.sum(current_infected)
            closing_infected = np.sum(closing_infected)
        # target school-age
        else:
            target_infected = np.sum(current_infected[1])
            closing_infected = np.sum(closing_infected[1])

        reopen_threshold = (1 - target_infected / closing_infected) * 100
        if int(trigger_value) <= reopen_threshold:
            school_reopen = True
        else:
            school_reopen = False


    # No monitor
    else:
        if int(trigger_value) < 20200101:  # Not a date
            reopen_threshold = (current_t - closing_t) / interval_per_day / 7.0
            if int(trigger_value) <= reopen_threshold:
                school_reopen = True
            else:
                school_reopen = False

        else:  # date
            trigger_date = dt.datetime.strptime(np.str(trigger_value), '%Y%m%d')
            if trigger_date <= current_date:
                school_reopen = True
            else:
                school_reopen = False

    return school_reopen
