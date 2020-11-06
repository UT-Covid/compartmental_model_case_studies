import numpy as np
import pickle
import os
from datetime import datetime, timedelta
import pandas as pd
# todo: this fxn is duplicated in io_support -- reorganize so it gets a single def that is easily imported where needed

class InitialModelState:

    def __init__(self, total_time, interval_per_day, n_age, n_risk, initial_i, metro_pop):

        self.total_time = total_time
        self.interval_per_day = interval_per_day
        self.n_age = n_age
        self.n_risk = n_risk
        self.initial_i = initial_i
        self.metro_pop = metro_pop
        self.start_day = None
        self.offset = None

    def initialize(self):

        if isinstance(self.initial_i, str):
            if os.path.exists(self.initial_i):
                return self.initialize_from_deterministic()
            else:
                raise ValueError('Initial state is provided as a string that does not map to a valid file path.')

        elif isinstance(self.initial_i, np.ndarray):
            return self.initialize_from_start()

        elif isinstance(self.initial_i, list):
            return self.initialize_from_start()

        else:
            print(type(self.initial_i))
            raise ValueError('Initial conditions provided are not supported.')

    def instantaneous_state(self, min_hosp=10):

        # todo: implement checks to make sure the deterministic solution read in is actually the one you want
        # todo: for example, is it the right city? the right params?
        # todo: this might require packaging the config with the outputs so a few things can be checked easily after loading this file
        with open(self.initial_i, 'rb') as xp:
            data = pickle.load(xp)

        if len(data.c_reduction.values) > 1:
            raise ValueError('Instantaneous states are currently only supported for deterministic runs with fixed contact reduction levels.')

        dataset = data.to_dataset('compartment')

        # todo: this syntax can replace compartment_stack() where resolution == 'point'
        hosp_slice = dataset['Iy'].sel({
            'beta0': dataset['beta0'].values.item(),
            'c_reduction': dataset['c_reduction'].values.item(),
            'g_rate': 'high',
            'reopen_trigger': dataset['reopen_trigger'].values.item(),
            'close_trigger': dataset['close_trigger'].values.item()
        }).sum(dim=['age_group', 'risk_group']).to_dataframe().reset_index()

        # assume the first date's HH:MM:SS is always 00:00:00
        hosp_slice_daily = hosp_slice.iloc[::self.interval_per_day, :]

        # assumption: single peak in hospitalizations; deterministic sim starts at 1 infected person so the
        #    beginning of the time series will always be below the threshold
        threshold_slice = hosp_slice_daily[hosp_slice_daily['Iy'] >= min_hosp]
        start_slice = threshold_slice['time'].min()
        self.offset = timedelta(hours       = start_slice.hour,
                                minutes     = start_slice.minute,
                                seconds     = start_slice.second,
                                microseconds= start_slice.microsecond)

        # we don't want to start mid-day because that would require a refactor how how the SEIR model handles dates
        # instead, drop day fraction to begin at zero hours of day 
        self.start_day = datetime(start_slice.year, start_slice.month, start_slice.day)

        compartment_slices = {i: dataset[i].sel({
            'beta0': dataset['beta0'].values.item(),
            'c_reduction': dataset['c_reduction'].values.item(),
            'g_rate': 'high',
            'reopen_trigger': dataset['reopen_trigger'].values.item(),
            'close_trigger': dataset['close_trigger'].values.item(),
            'time': start_slice,
            'replicate': 0  # possibly irrelevant for deterministic runs
        }).values for i in data.compartment.values}

        return compartment_slices

    def initialize_empty(self):
        """ Make an empty numpy array for each compartment, and return as a dictionary. """

        compt_s = np.zeros(shape=(self.total_time * self.interval_per_day, self.n_age, self.n_risk))  # (t,a,r)
        compt_e, compt_ia, compt_iy, compt_e2compt_i = compt_s.copy(), compt_s.copy(), compt_s.copy(), compt_s.copy()
        compt_ih, compt_r, compt_e2compt_iy, compt_d = compt_s.copy(), compt_s.copy(), compt_s.copy(), compt_s.copy()
        compt_iy2compt_ih, compt_h2compt_d = compt_s.copy(), compt_s.copy()

        return {'S': compt_s, 'E': compt_e, 'Ia': compt_ia, 'Iy': compt_iy, 'E2I': compt_e2compt_i, 'Ih': compt_ih,
                'R': compt_r, 'E2Iy': compt_e2compt_iy, 'D': compt_d, 'Iy2Ih': compt_iy2compt_ih, 'H2D': compt_h2compt_d}

    # todo: make a static method
    def update_initial_cond(self, array, t0_value):
        """ Update the initial condition of a compartment. """

        array[0] = t0_value

        return array

    def initialize_infected_only(self, empty):
        """ Add infected compartment totals from the config and adjust metro pop accordingly. """

        empty['S'] = self.update_initial_cond(empty['S'], self.metro_pop - self.initial_i)
        empty['Iy'] = self.update_initial_cond(empty['Iy'], self.initial_i)

        return empty

    def initialize_from_start(self):
        """ Return a dictionary of compartments, where only infected susceptible compartment contains non-zero entries """

        # get empty arrays
        initial_comp_dict = self.initialize_empty()

        return self.initialize_infected_only(initial_comp_dict)

    def initialize_from_deterministic(self):
        """ Return a dictionary of compartments, each with initial conditions from a deterministic sim at time zero """

        # get empty arrays
        initial_comp_dict = self.initialize_empty()

        # get start conditions from deterministic model
        deterministic_comp_dict = self.instantaneous_state()

        # add deterministic start conditions to the empty arrays
        for key, value in initial_comp_dict.items():
            if key not in deterministic_comp_dict.keys():
                # todo: move this error checking to param parser
                raise ValueError('Initial condition for compartment {} missing from input'.format(key))
            initial_cond = deterministic_comp_dict[key]
            initial_comp_dict[key] = self.update_initial_cond(initial_comp_dict[key], initial_cond)

        return initial_comp_dict