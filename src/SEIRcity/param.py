# -*- coding: utf-8 -*-
"""
Get input data from Excel files, and calculate epidemiological parameters
"""
import os
import numpy as np
import pandas as pd
import datetime as dt
from . import param_parser
from .get_initial_state import InitialModelState
from datetime import datetime


def aggregate_params_and_data(yaml_fp):
    """Aggregates all run parameters. Reads from a config YAML file
    at `yaml_fp`, and calls SEIR_get_data to retrieve demographic data.
    Returns a dictionary of aggregated parameters.
    """

    config = param_parser.load(yaml_fp, validate=False)

    # -------------Get data/params from get_data/params ----------------

    # handling of legacy param names, formatted as:
    # [old name which is still supported, new name]
    legacy_conversions = tuple([
        ['sd_date', 'c_reduction_date'],
        ['DATA_FOLDER', 'data_folder'],
        ['CITY', 'city'],
    ])
    for conversion in legacy_conversions:
        old_name = conversion[0]
        new_name = conversion[1]
        if new_name not in config:
            assert old_name in config, "config YAML has no field " + \
                "`{}` (formerly known as `{}`)".format(new_name, old_name)
            config[new_name] = config[old_name]

    # get demographics, school calendar, and transmission data from Excel files
    AgeGroupDict, metro_pop, school_calendar, \
        time_begin, FallStartDate, Phi, symp_h_ratio_overall, \
        symp_h_ratio, hosp_f_ratio = SEIR_get_data(config=config)

    config.update({
        "AgeGroupDict": AgeGroupDict,
        'metro_pop': metro_pop,
        'school_calendar': school_calendar,
        'time_begin': time_begin,
        'FallStartDate': FallStartDate,
        'phi': Phi,
        #initial_state': config['initial_state'],
        'initial_i': config['I0'],
        'symp_h_ratio_overall': symp_h_ratio_overall,
        'symp_h_ratio': symp_h_ratio,
        'hosp_f_ratio': hosp_f_ratio
    })

    # -------------Get initial state of model --------------------------
    ## --  get initial state of compartments
    # todo: SEIR model should take a new arg "init_type" that explicitly states whether to initialize every compartment or just infected
    # todo: currently the type of initialization is inferred from the instance type of "initial_i" -- that is sure to break at some point
    init_state = InitialModelState(config['total_time'], config['interval_per_day'], config['n_age'], config['n_risk'],
                                   config['I0'], metro_pop)
    compartments = init_state.initialize()
    # todo: more graceful and transparent override of user config specified start date
    # todo: perhaps in param_parser we can check that time_begin_sim is None if a I0 is a file path
    if init_state.start_day:
        print('Start date as specified in the config file is overridden by initialization from a deterministic solution.')
        print('The new start date is {}'.format(init_state.start_day))
        date_begin = init_state.start_day
        config['time_begin_sim'] = datetime.strftime(date_begin, '%Y%m%d')  # return datetime to its expected string format
        # todo: we should re-save this config to reflect the updated start time

    # ------------- Update config with revised initial conditions -------
    config['initial_state'] = compartments
    config['t_offset'] = init_state.offset

    return config


def SEIR_get_data(config):
    """ Gets input data from Excel files. Takes a configuration
    dictionary `config` that must minimally contain the following keys:

    :data_folder: str, path of Excel files
    :city: str, name of city simulated
    :n_age: int, number of age groups
    :n_risk: int, number of risk groups
    """

    # ingest from configuration dictionary
    data_folder = config['data_folder']
    city = config['city']
    n_age = config['n_age']
    n_risk = config['n_risk']
    H_RELATIVE_RISK_IN_HIGH = config['H_RELATIVE_RISK_IN_HIGH']
    D_RELATIVE_RISK_IN_HIGH = config['D_RELATIVE_RISK_IN_HIGH']
    HIGH_RISK_RATIO = config['HIGH_RISK_RATIO']
    H_FATALITY_RATIO = config['H_FATALITY_RATIO']
    INFECTION_FATALITY_RATIO = config['INFECTION_FATALITY_RATIO']
    OVERALL_H_RATIO = config['OVERALL_H_RATIO']
    ASYMP_RATE = config['ASYMP_RATE']
    age_group_dict = config['age_group_dict']

    # ------------------------------

    us_population_filename = 'US_pop_UN.csv'
    population_filename = '{}_Population_{}_age_groups.csv'
    population_filename_dict = {}
    for key in age_group_dict.keys():
        population_filename_dict[key] = population_filename.format(city, str(key))

    school_calendar_filename = '{}_School_Calendar.csv'.format(city)

    contact_matrix_all_filename_dict = {5: 'ContactMatrixAll_5AgeGroups.csv',
                                         3: 'ContactMatrixAll_3AgeGroups.csv'}
    contact_matrix_school_filename_dict = {5: 'ContactMatrixSchool_5AgeGroups.csv',
                                          3: 'ContactMatrixSchool_3AgeGroups.csv'}
    contact_matrix_work_filename_dict = {5: 'ContactMatrixWork_5AgeGroups.csv',
                                           3: 'ContactMatrixWork_3AgeGroups.csv'}
    contact_matrix_home_filename_dict = {5: 'ContactMatrixHome_5AgeGroups.csv',
                                         3: 'ContactMatrixHome_3AgeGroups.csv'}

    ## Load data
    # Population in US
    df_US = pd.read_csv(data_folder + us_population_filename, index_col=False)
    GroupPaperPop = df_US.groupby('GroupPaper')['Value'].sum().reset_index(name='GroupPaperPop')
    GroupCOVIDPop = df_US.groupby('GroupCOVID')['Value'].sum().reset_index(name='GroupCOVIDPop')
    df_US = pd.merge(df_US, GroupPaperPop)
    df_US = pd.merge(df_US, GroupCOVIDPop)

    # Calculate age specific and risk group specific symptomatic hospitalization ratio
    df_US['Overall_H_Ratio'] = df_US['GroupPaper'].map(OVERALL_H_RATIO) / 100.
    df_US['YHR_paper'] = df_US['Overall_H_Ratio'] / (1 - ASYMP_RATE)
    df_US['YHN_1yr'] = df_US['YHR_paper'] * df_US['Value']
    GroupCOVID_YHN = df_US.groupby('GroupCOVID')['YHN_1yr'].sum().reset_index(name='GroupCOVID_YHN')
    df_US = pd.merge(df_US, GroupCOVID_YHN)
    df_US['YHR'] = df_US['GroupCOVID_YHN'] / df_US['GroupCOVIDPop']
    df_US['GroupCOVIDHighRiskRatio'] = df_US['GroupCOVID'].map(HIGH_RISK_RATIO) / 100.
    df_US['YHR_low'] = df_US['YHR'] /(1 - df_US['GroupCOVIDHighRiskRatio'] + \
                                      H_RELATIVE_RISK_IN_HIGH * df_US['GroupCOVIDHighRiskRatio'])
    df_US['YHR_high'] = H_RELATIVE_RISK_IN_HIGH * df_US['YHR_low']

    # Calculate age specific and risk group specific hospitalized fatality ratio
    df_US['I_Fatality_Ratio'] = df_US['GroupPaper'].map(INFECTION_FATALITY_RATIO) / 100.
    df_US['YFN_1yr'] = df_US['I_Fatality_Ratio'] * df_US['Value'] / (1 - ASYMP_RATE)
    GroupCOVID_YFN = df_US.groupby('GroupCOVID')['YFN_1yr'].sum().reset_index(name='GroupCOVID_YFN')
    df_US = pd.merge(df_US, GroupCOVID_YFN)
    df_US['YFR'] = df_US['GroupCOVID_YFN'] / df_US['GroupCOVIDPop']
    df_US['YFR_low'] = df_US['YFR'] / (1 - df_US['GroupCOVIDHighRiskRatio'] + \
                                       D_RELATIVE_RISK_IN_HIGH * df_US['GroupCOVIDHighRiskRatio'])
    df_US['YFR_high'] = D_RELATIVE_RISK_IN_HIGH * df_US['YFR_low']
    df_US['HFR'] = df_US['YFR'] / df_US['YHR']
    df_US['HFR_low'] = df_US['YFR_low'] / df_US['YHR_low']
    df_US['HFR_high'] = df_US['YFR_high'] / df_US['YHR_high']

    df_US_dict = df_US[['GroupCOVID', 'YHR', 'YHR_low', 'YHR_high', \
                        'HFR_low', 'HFR_high']].drop_duplicates().set_index('GroupCOVID').to_dict()
    Symp_H_Ratio_dict = df_US_dict['YHR']
    Symp_H_Ratio_L_dict = df_US_dict['YHR_low']
    Symp_H_Ratio_H_dict = df_US_dict['YHR_high']
    Hosp_F_Ratio_L_dict = df_US_dict['HFR_low']
    Hosp_F_Ratio_H_dict = df_US_dict['HFR_high']
    Symp_H_Ratio = np.array([Symp_H_Ratio_dict[i] for i in age_group_dict[n_age]])
    Symp_H_Ratio_w_risk = np.array([[Symp_H_Ratio_L_dict[i] for i in age_group_dict[n_age]], \
                            [Symp_H_Ratio_H_dict[i] for i in age_group_dict[n_age]]])
    Hosp_F_Ratio_w_risk = np.array([[Hosp_F_Ratio_L_dict[i] for i in age_group_dict[n_age]], \
                            [Hosp_F_Ratio_H_dict[i] for i in age_group_dict[n_age]]])

    df = pd.read_csv(data_folder + population_filename_dict[n_age], index_col=False)
    pop_metro = np.zeros(shape=(n_age, n_risk))
    for r in range(n_risk):
        pop_metro[:, r] = df.loc[df['RiskGroup'] == r, age_group_dict[n_age]].values.reshape(-1)

    # Transmission adjustment multiplier per day and per metropolitan area
    df_school_calendar = pd.read_csv(data_folder + school_calendar_filename, index_col=False)
    school_calendar = df_school_calendar['Calendar'].values.reshape(-1)
    school_calendar_start_date = dt.datetime.strptime(np.str(df_school_calendar['Date'][0]), '%m/%d/%y')

    df_school_calendar_aug = df_school_calendar[df_school_calendar['Date'].str[0].astype(int) >= 8]
    fall_start_date = df_school_calendar_aug[df_school_calendar_aug['Calendar'] == 1].Date.to_list()[0]
    fall_start_date = '20200' + fall_start_date.split('/')[0] + fall_start_date.split('/')[1]

    # Contact matrix
    phi_all = pd.read_csv(data_folder + contact_matrix_all_filename_dict[n_age], header=None).values
    phi_school = pd.read_csv(data_folder + contact_matrix_school_filename_dict[n_age], header=None).values
    phi_work = pd.read_csv(data_folder + contact_matrix_work_filename_dict[n_age], header=None).values
    phi_home = pd.read_csv(data_folder + contact_matrix_home_filename_dict[n_age], header=None).values
    phi = {'phi_all': phi_all, 'phi_school': phi_school, 'phi_work': phi_work, 'phi_home': phi_home}

    return age_group_dict, pop_metro, school_calendar, school_calendar_start_date, fall_start_date, phi, \
           Symp_H_Ratio, Symp_H_Ratio_w_risk, Hosp_F_Ratio_w_risk


def SEIR_get_param(config):
    """ Get epidemiological parameters from configuration dictionary
    `config`. `config` must minimally have the following keys:

    :symp_h_ratio_overall: np.array of shape (n_age, )
    :symp_h_ratio: np.array of shape (n_risk, n_age)
    :hosp_f_ratio: np.array of shape (n_age, )
    :n_age: int, number of age groups
    :n_risk: int, number of risk groups
    :deterministic: boolean, whether to remove parameter stochasticity
    """

    # ------------------------------
    # Read params from param_parser
    # ------------------------------
    symp_h_ratio_overall = config['symp_h_ratio_overall']
    symp_h_ratio = config['symp_h_ratio']
    hosp_f_ratio = config['hosp_f_ratio']
    n_age = config['n_age']
    n_risk = config['n_risk']
    deterministic = config['deterministic']
    H_RELATIVE_RISK_IN_HIGH = config['H_RELATIVE_RISK_IN_HIGH']
    PROP_TRANS_IN_E = config['PROP_TRANS_IN_E']
    T_ONSET_TO_H = config['T_ONSET_TO_H']
    T_H_TO_D = config['T_H_TO_D']
    T_EXPOSED_PARA = config['T_EXPOSED_PARA']
    T_Y_TO_R_PARA = config['T_Y_TO_R_PARA']
    T_H_TO_R = config['T_H_TO_R']
    R0 = config['R0']
    ASYMP_RATE = config['ASYMP_RATE']
    DOUBLE_TIME = config['DOUBLE_TIME']

    # delta functions
    T_Y_TO_R_DIST = lambda x: np.random.triangular(*x)
    T_EXPOSED_DIST = lambda x: np.random.triangular(*x)

    # ------------------------------------------------------------------

    r0 = R0
    double_time = DOUBLE_TIME

    gamma_h = 1 / T_H_TO_R
    gamma_y_c = 1 / np.median(T_Y_TO_R_PARA)
    if deterministic:
        gamma_y = gamma_y_c
    else:
        gamma_y = 1 / T_Y_TO_R_DIST(T_Y_TO_R_PARA)
    gamma_a = gamma_y
    gamma = np.array([gamma_a * np.ones(n_age), gamma_y * np.ones(n_age), gamma_h * np.ones(n_age)])

    sigma_c = 1 / np.median(T_EXPOSED_PARA) * np.ones(n_age)
    if deterministic:
        sigma = sigma_c
    else:
        sigma = 1 / T_EXPOSED_DIST(T_EXPOSED_PARA) * np.ones(n_age)
    # print("sigma: ", sigma)

    eta = 1 / T_ONSET_TO_H * np.ones(n_age)

    mu = 1 / T_H_TO_D * np.ones(n_age)

    nu = hosp_f_ratio * gamma_h / (mu + (gamma_h - mu) * hosp_f_ratio)

    pi = symp_h_ratio * gamma_y / (eta + (gamma_y - eta) * symp_h_ratio)

    tau = (1 - ASYMP_RATE) * np.ones(n_age)

    omega_y = 1.
    omega_h = 0.
    omega_e = ((symp_h_ratio_overall / eta) + ((1 - symp_h_ratio_overall) / gamma_y)) * \
              omega_y * sigma * PROP_TRANS_IN_E / (1 - PROP_TRANS_IN_E)
    omega_a = ((symp_h_ratio_overall / eta) + ((1 - symp_h_ratio_overall) / gamma_y_c)) * \
              omega_y * sigma_c * PROP_TRANS_IN_E / (1 - PROP_TRANS_IN_E)
    omega = np.array([omega_a, omega_y * np.ones(n_age), omega_h * np.ones(n_age), omega_e])

    para = {'r0': r0, 'double_time': double_time, 'gamma': gamma, 'sigma': sigma, 'eta': eta,
            'mu': mu, 'nu': nu, 'pi': pi, 'tau': tau, 'omega': omega}

    return para
