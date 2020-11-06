import yaml
import pickle
from datetime import datetime, timedelta
import xarray
import pandas as pd
import numpy as np
from collections import defaultdict
import math
import logging
import sys
from SEIRcity.param_parser import convert_legacy_param_names

""" Tools for handling single city SEIR model outputs """

## needed since np.datetime64.astype(datetime) borks on datetime64 with second fractions
def datetime64_to_datetime(dt64):
    str_fmt_dt = str(dt64).split('.')[0]
    return datetime.strptime(str_fmt_dt, '%Y-%m-%dT%H:%M:%S')

def summary_stats(wide_array):

    median = np.median(wide_array, axis=0)
    range_2pt5_97pt5 = np.percentile(wide_array, [2.5, 97.5], axis=0)
    range_5_95 = np.percentile(wide_array, [5, 95], axis=0)
    range_25_75 = np.percentile(wide_array, [25, 75], axis=0)
    max_val = np.amax(wide_array, axis=0)
    min_val = np.amin(wide_array, axis=0)

    return median, range_2pt5_97pt5, range_5_95, range_25_75, max_val, min_val

class OutputViewer:

    def __init__(self, config_path, xarray_path, threshold=datetime(2020, 3, 24)):

        # --- get config, parse city element, and convert legacy names
        with open(config_path, 'r') as cp:
            config = yaml.safe_load(cp)
        self.config = convert_legacy_param_names(config)
        self.city = self.config['city']

        # --- get xarray
        with open(xarray_path, 'rb') as xp:
            self.data = pickle.load(xp)

        # --- check xarray contents
        self.required_coords = {
            'age_group',
            'time',
            'compartment',
            'risk_group',
            'replicate',
            'beta0',
            'contact_reduction',
            'g_rate',
            'reopen_trigger',
            'close_trigger'
        }
        self.optional_coords = {'contact_reduction2'}
        self.data_coords = {i for i in self.data.coords}
        self.check_coordinates()
        self.check_scenarios()

        # --- find start date from data (mid-epidemic starts will override the config setting, so data is the most reliable source
        self.start_date = datetime64_to_datetime(min(self.data.time.values))

        # --- assume that two levels of contact reduction are possible
        self.cr1 = self.data.contact_reduction.values
        if len(self.optional_coords.difference(self.data_coords)) == 0:
            self.cr2 = self.data.contact_reduction2.values
            self.cr_scenarios = [(i, j) for i in self.cr1 for j in self.cr2]
        else:
            self.cr_scenarios = [(i) for i in self.cr1]

        # --- set other instance variables
        self.dataset = self.data.to_dataset('compartment')
        self.threshold = threshold
        self.zero_epidemics = None
        self.find_zeros()

        # currently fixed data not in config, but possibly may be updated in future
        # tuples are for human convenience, element 0 in each is not used by algorithm
        self.icu_prop_hosp = [
            ('0-4', 0.15),
            ('5-17', 0.2),
            ('18-49', 0.15),
            ('50-64', 0.2),
            ('65+', 0.15)
        ]
        self.vent_prop_icu = [
            ('0-4', 2 / 3),
            ('5-17', 2 / 3),
            ('18-49', 2 / 3),
            ('50-64', 2 / 3),
            ('65+', 2 / 3)
        ]
        self.icu_length = 10.0
        self.vent_length = 10.0
        self.hosp_length = 14.0

    ## -- QA METHODS -- ##

    def check_coordinates(self):
        """ Check that all required coordinates are present """

        overlap = self.data_coords.intersection(self.required_coords)
        assert len(overlap) == len(self.required_coords)

    def check_scenarios(self):
        """ Check that the number of scenarios present are supported """

        ERROR = 0

        if len(self.data['reopen_trigger'].values) != 1:
            logging.error('{} repoen trigger values found; OutputViewer currently only supports a single reopen trigger value.'.format(len(self.dataset['reopen_trigger'])))
            ERROR += 1
        if len(self.data['close_trigger'].values) != 1:
            logging.error('{} close_trigger values found; OutputViewer currently only supports a single reopen trigger value.'.format(len(self.dataset['close_trigger'])))
            ERROR += 1
        if len(self.data['beta0'].values) != 1:
            logging.error('{} beta0 values found; OutputViewer currently only supports a single reopen trigger value.'.format(len(self.dataset['beta0'])))
            ERROR += 1
        if len(self.data['g_rate'].values) != 1:
            logging.error('{} g_rate values found; OutputViewer currently only supports a single reopen trigger value.'.format(len(self.dataset['g_rate'])))
            ERROR += 1

        assert ERROR == 0

    def find_zeros(self):
        """ identify simulations that yielded stalled epidemics """

        zero_scenarios = {}

        for cr in self.cr_scenarios:

            # get symptomatic incidence compartment, aggregate by day
            time_by_replicate = self.compartment_stack('E2Iy', cr_scenario=cr, resolution='daily_sum')

            wide = time_by_replicate.transpose()
            zero_idx = []
            rm_count = 0

            # assuming all time_by_replicate arrays have days (and not fractions of days) as one axis
            threshold_index = (self.threshold - self.start_date).days

            for i, row in enumerate(wide):
                if row[threshold_index] < 1:
                    zero_idx.append(i)
                    rm_count += 1
            zero_scenarios[cr] = zero_idx

            print('Removed {} simulations with no cases on {}.'.format(rm_count, self.threshold))

        self.zero_epidemics = zero_scenarios

    ## -- XARRAY METHODS -- ##

    def stack_slice_two_beta(self, compartment, cr):
        """ Slice array with only one contact reduction coordinate (two beta values in model) """

        stack_slice = np.stack([self.dataset[compartment].sel({
            'beta0': self.dataset['beta0'].values.item(),
            'contact_reduction': cr,
            'g_rate': self.dataset['g_rate'].values.item(),
            'reopen_trigger': self.dataset['reopen_trigger'].values.item(),
            'close_trigger': self.dataset['close_trigger'].values.item(),
            'time': t}).values for t in self.dataset[compartment].time.values])

        return stack_slice

    def stack_slice_three_beta(self, compartment, cr):
        """ Slice array with two contact reduction coordinates (three beta values in model) """

        stack_slice = np.stack([self.dataset[compartment].sel({
            'beta0': self.dataset['beta0'].values.item(),
            'contact_reduction': cr[0],
            'contact_reduction2': cr[1],
            'g_rate': 'high',
            'reopen_trigger': self.dataset['reopen_trigger'].values.item(),
            'close_trigger': self.dataset['close_trigger'].values.item(),
            'time': t}).values for t in self.dataset[compartment].time.values])

        return stack_slice

    def stack_slice_xarray(self, compartment, cr_scenario):
        """ Generic(ish) method for selecting appropriate method for array slicing by contact reduction"""

        if isinstance(cr_scenario, np.float):
            return self.stack_slice_two_beta(compartment, cr_scenario)

        elif len(cr_scenario) == 2:
            return self.stack_slice_three_beta(compartment, cr_scenario)

        elif len(cr_scenario) == 1:
            return self.stack_slice_two_beta(compartment, cr_scenario)

        else:
            raise ValueError('Contact reduction scenario {} has length {}, which is not supported.'.format(str(cr_scenario), str(len(cr_scenario))))

    def add_scenario_indicator_column(self, summary, cr):

        if 'contact_reduction2' in self.data_coords:
            summary['contact_reduction'] = cr[0]
            summary['contact_reduction2'] = cr[1]
        else:
            summary['contact_reduction'] = cr

        return summary

    def compartment_stack(self, compartment, cr_scenario, resolution):

        if resolution not in ['daily_sum', 'weekly_sum', 'daily_point', 'point']:

            raise ValueError('Resolution {} is not currently supported. Valid inputs are "daily_sum", "weekly_sum", "daily_point" or "point".'.format(resolution))

        stack_slice = self.stack_slice_xarray(compartment, cr_scenario)

        # sum all the age categories
        stack_slice_across_age = stack_slice.sum(axis=2)

        # sum all the risk groups
        stack_slice_across_risk_age = stack_slice_across_age.sum(axis=2)

        # if we need to sum by day
        if resolution == 'daily_sum':

            stack_slice_scaled = stack_slice_across_risk_age.reshape(
                self.config['total_time'],
                self.config['interval_per_day'],
                self.config['num_sim']
            ).sum(axis=1)

            return stack_slice_scaled  #(time, n_sim)

        elif resolution == 'weekly_sum':

            # total time is measured in days, div by 7 to get 7-day chunks and take the floor to truncate incomplete final 7-day chunk
            n_weeks = math.floor(self.config['total_time'] / 7)
            clean_time_slice = n_weeks * 7 * self.config['interval_per_day']

            # first axis is time; truncate along that axis if necessary
            stack_slice_truncated = stack_slice_across_risk_age[0:min(clean_time_slice+1, stack_slice_across_risk_age.shape[0]), 0:]

            stack_slice_scaled = stack_slice_truncated.reshape(
                n_weeks,
                self.config['interval_per_day'] * 7,  # for now we won't try to start weeks on a Sun or Mon
                self.config['num_sim']
            ).sum(axis=1)

            return stack_slice_scaled  #(time, n_sim)

        # if instead we just want one observation per day (a sample of every day, rather than a sum of every day)
        elif resolution == 'daily_point':

            stack_slice_scaled = stack_slice_across_risk_age[
                range(0, self.config['total_time'] * self.config['interval_per_day'], self.config['interval_per_day'])]

            return stack_slice_scaled

        elif resolution == 'point':

            return stack_slice_across_risk_age  #(time, n_sim)


    def icu_vent_incidence(self):

        icu_needs_list = []
        vent_needs_list = []

        for cr in self.cr_scenarios:
            # incident hospitalizations
            incidence = self.stack_slice_xarray('Iy2Ih', cr)

            incidence_dates = [self.start_date + timedelta(days=t / self.config['interval_per_day']) for t in
                               range(0, self.config['total_time'] * self.config['interval_per_day'])]

            incidence_across_risk = incidence.sum(axis=3)  # (time, n_sim, age, risk)

            icu_props = np.array([i[1] for i in self.icu_prop_hosp])
            icu_by_age = incidence_across_risk * icu_props * self.icu_length / self.hosp_length
            icu_summed = icu_by_age.sum(axis=2)  # sum across ages
            icu_total = np.delete(icu_summed, self.zero_epidemics[cr], axis=1).transpose()
            icu_cumulative = np.cumsum(icu_total, axis=1)
            icu_cumulative_median, icu_cumulative_range95, icu_cumulative_range90, icu_cumulative_range75, icu_cumulative_max, icu_cumulative_min = summary_stats(
                icu_cumulative)

            icu_needs = pd.DataFrame(
                np.vstack([
                    incidence_dates,
                    icu_cumulative_median, icu_cumulative_range95, icu_cumulative_range90, icu_cumulative_range75,
                    icu_cumulative_max, icu_cumulative_min
                ]).transpose())
            icu_needs.columns = [
                'date',
                'median', 'lower_2.5%', 'upper_97.5%', 'lower_5%',
                'upper_95%', 'lower_25%', 'upper_75%', 'max', 'min'
            ]
            icu_needs = self.add_scenario_indicator_column(icu_needs, cr)
            icu_needs_list.append(icu_needs)

            # ventilators
            vent_props = np.array([i[1] for i in self.vent_prop_icu])
            vent_by_age = icu_by_age * vent_props * self.vent_length / self.hosp_length
            vent_summed = vent_by_age.sum(axis=2)  # sum across ages
            vent_total = np.delete(vent_summed, self.zero_epidemics[cr], axis=1).transpose()
            vent_cumulative = np.cumsum(vent_total, axis=1)
            vent_cumulative_median, vent_cumulative_range95, vent_cumulative_range90, vent_cumulative_range75, vent_cumulative_max, vent_cumulative_min = summary_stats(
                vent_cumulative)

            vent_needs = pd.DataFrame(
                np.vstack([
                    incidence_dates,
                    vent_cumulative_median, vent_cumulative_range95, vent_cumulative_range90, vent_cumulative_range75,
                    vent_cumulative_max, vent_cumulative_min
                ]).transpose())
            vent_needs.columns = [
                'date',
                'median', 'lower_2.5%', 'upper_97.5%', 'lower_5%',
                'upper_95%', 'lower_25%', 'upper_75%', 'max', 'min'
            ]
            vent_needs = self.add_scenario_indicator_column(vent_needs, cr)
            vent_needs_list.append(vent_needs)

        return pd.concat(icu_needs_list), pd.concat(vent_needs_list)

    def icu_vent_daily(self):

        icu_needs_list = []
        vent_needs_list = []

        for cr in self.cr_scenarios:

            # daily hospitalizatoins
            daily = self.stack_slice_xarray('Ih', cr)

            # get the dates
            daily_dates = [self.start_date + timedelta(days=t) for t in range(0, self.config['total_time'])]

            # sum all the risk categories
            daily_across_risk = daily.sum(axis=3)  # (time, n_sim, age, risk)

            # ICU beds
            icu_props = np.array([i[1] for i in self.icu_prop_hosp])
            icu_by_age = daily_across_risk * icu_props * self.icu_length/self.hosp_length
            icu_summed = icu_by_age.sum(axis=2)  # sum across ages
            icu_reshape = icu_summed[range(0, self.config['total_time'] * self.config['interval_per_day'], self.config['interval_per_day'])]  # one point per day
            icu_total = np.delete(icu_reshape, self.zero_epidemics[cr], axis=1).transpose()
            icu_total_median, icu_total_range95, icu_total_range90, icu_total_range75, icu_total_max, icu_total_min = summary_stats(icu_total)

            icu_needs = pd.DataFrame(
                np.vstack([
                    daily_dates,
                    icu_total_median, icu_total_range95, icu_total_range90, icu_total_range75,
                    icu_total_max, icu_total_min,
                ]).transpose())
            icu_needs.columns = [
                'date',
                'median', 'lower_2.5%', 'upper_97.5%', 'lower_5%', 'upper_95%', 'lower_25%', 'upper_75%', 'max', 'min'
            ]

            icu_needs = self.add_scenario_indicator_column(icu_needs, cr)
            icu_needs_list.append(icu_needs)

            # ventilators
            vent_props = np.array([i[1] for i in self.vent_prop_icu])
            vent_by_age = icu_by_age * vent_props * self.vent_length/self.hosp_length
            vent_summed = vent_by_age.sum(axis=2)  # sum across ages and
            vent_reshape = vent_summed[range(0, self.config['total_time'] * self.config['interval_per_day'], self.config['interval_per_day'])] # grab one point per day
            vent_total = np.delete(vent_reshape, self.zero_epidemics[cr], axis=1).transpose()
            vent_total_median, vent_total_range95, vent_total_range90, vent_total_range75, vent_total_max, vent_total_min = summary_stats(vent_total)

            vent_needs = pd.DataFrame(
                np.vstack([
                    daily_dates,
                    vent_total_median, vent_total_range95, vent_total_range90, vent_total_range75, vent_total_max, vent_total_min,
                ]).transpose())
            vent_needs.columns = [
                'date',
                'median', 'lower_2.5%', 'upper_97.5%', 'lower_5%', 'upper_95%', 'lower_25%', 'upper_75%', 'max', 'min'
            ]

            vent_needs = self.add_scenario_indicator_column(vent_needs, cr)
            vent_needs_list.append(vent_needs)

        return pd.concat(icu_needs_list), pd.concat(vent_needs_list)


    def aggregate_compartment(self, compartment, resolution, is_incidence, rm_zeros=True, incl_raw=False, cumulative=False):
        """
        General method for organizing aggregations of compartment population counts for various reporting purposes.

        Available compartments:
        * Total Count Compartments
            - S = susceptible
            - E = exposed
            - Pa = pre-asymptomatic
            - Py = pre-symptomatic
            - Ia = infected, asymptomatic
            - Iy = infected, symptomatic
            - Ih = infected, hospitalized
            - R = recovered
            - D = dead
        * Incident Count Compartments
            - E2P = exposed to infected asymptomatic or symptomatic
            - E2Py = exposed to infected symptomatic
            - P2I = pre-symptomatic + pre-asymptomatic to infected symptomatic + infected asymptomatic
            - Pa2Ia = pre-asymptomatic to infected asymptomatic
            - Py2Iy = pre-symptomatic to infected symptomatic
            - Iy2Ih = infected symptomatic to hospitalized
            - H2D = hospitalized to dead

        :param compartment: The xarray coordinate of the model compartment to aggregate.
        :param resolution: The time scale at which to aggregate. Supported values are "daily_sum", "weekly_sum" or "daily_point".
        :param is_incidence: True/False; does this compartment contain incidence data?
        :param rm_zeros: True/False; should simulations without epidemics be removed?
        :param incl_raw: True/False; should raw simulation output be returned along with summary statistics?
        :param cumulative: True/False; should incidence data be summed to generate cumulative time series?
        :return:
        """

        scenario_summaries = []
        for cr in self.cr_scenarios:

            # -- extract a numpy array from the x-array
            incidence_by_replicate = self.compartment_stack(
                compartment=compartment,
                cr_scenario=cr,
                resolution=resolution)

            # -- optionally filter zeros
            if rm_zeros:
                final_incidence = np.delete(incidence_by_replicate, self.zero_epidemics[cr], axis=1).transpose()
            else:
                final_incidence = incidence_by_replicate.transpose()

            # -- organize date axis based on aggregation resolution
            if resolution == 'weekly_sum':
                n_weeks = math.floor(self.config['total_time'] / 7)
                dates = [self.start_date + timedelta(weeks=t) for t in range(0, n_weeks)]
            elif (resolution == 'daily_sum') or (resolution == 'daily_point'):
                dates = [self.start_date + timedelta(days=t) for t in range(0, self.config['total_time'])]
            elif resolution == 'point':
                dates = [self.start_date + timedelta(days=t/self.config['interval_per_day']) for t in range(0, self.config['total_time'] * self.config['interval_per_day'])]

            # -- get cumulative sum for incidence data
            if (resolution in ['weekly_sum', 'daily_sum']) and is_incidence and cumulative:
                final_incidence = np.cumsum(final_incidence, axis=1)

            elif cumulative:
                raise ValueError('Cannot do a cumulative sum of daily cases. Cumulative sums are only valid for indident cases.')

            # -- get summary stats
            inc_median, inc_range95, inc_range90, inc_range75, inc_max, inc_min = summary_stats(final_incidence)

            # -- build dataframes
            if incl_raw:
                summary = pd.DataFrame(np.vstack([dates, final_incidence, inc_median, inc_range95, inc_range90, inc_range75, inc_max, inc_min]).transpose())
                summary.columns = ['date'] + \
                    ['sto_idx_{}'.format(i) for i in range(final_incidence.shape[0])] + \
                    ['median',  'lower_2.5%', 'upper_97.5%', 'lower_5%', 'upper_95%', 'lower_25%', 'upper_75%', 'max', 'min']

            else:
                summary = pd.DataFrame(np.vstack([dates, inc_median, inc_range95, inc_range90, inc_range75, inc_max, inc_min]).transpose())
                summary.columns = ['date'] + ['median', 'lower_2.5%', 'upper_97.5%', 'lower_5%', 'upper_95%', 'lower_25%', 'upper_75%', 'max', 'min']

            summary = self.add_scenario_indicator_column(summary, cr)
            scenario_summaries.append(summary)

        # -- assemble full dataset and return
        scenarios_df = pd.concat(scenario_summaries)

        return scenarios_df


def setrac_excel(new_data, intervention_dates='../data/Hosp and others/Intervention_Dates_per_Texas_MSA.csv'):

    new_data_df = pd.read_csv(new_data)
    intervention_df = pd.read_csv(intervention_dates)

    new_data_df['hospitalized'] = new_data_df['Confirmed in \nGen/Iso Beds'] + new_data_df['Confirmed \nin ICU']

    intervention_df = intervention_df[['Metro', 'County', 'Social Distancing Stay at Home']]

    raw_msa = pd.merge(new_data_df, intervention_df, on='County', how='left')
    agg_msa = raw_msa.groupby(['Date', 'Metro']).agg(
        {
            'hospitalized': sum,
            'Social Distancing Stay at Home': min
        }
    ).reset_index()
    agg_msa.columns = ['date', 'Metro', 'hospitalized', 'stay_home']

    agg_msa['date'] = [datetime.strftime(datetime.strptime(i, '%m/%d/%y'), '%Y-%m-%d') for i in agg_msa['date']]
    agg_msa['stay_home_str'] = [datetime.strftime(datetime.strptime(i, '%Y-%m-%d'), '%Y%m%d') for i in
                                agg_msa['stay_home']]

    agg_msa['datetime'] = [datetime.strptime(i, '%Y-%m-%d') for i in agg_msa['date']]
    agg_msa['hour'] = [i.hour for i in agg_msa['datetime']]

    return agg_msa
