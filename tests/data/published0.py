#!/usr/bin/env python
import numpy as np

# Used in param.SEIR_get_data
H_RELATIVE_RISK_IN_HIGH = 10.
D_RELATIVE_RISK_IN_HIGH = 10.
HIGH_RISK_RATIO = {'0-4': 8.2825, '5-17': 14.1121, '18-49': 16.5298, '50-64': 32.9912, '65+': 47.0568}  # in %
# unused
H_FATALITY_RATIO = {'0-9': 0., '10-19': 0.2, '20-29': 0.2, '30-39': 0.2, '40-49': 0.4, \
                       '50-59': 1.3, '60-69': 3.6, '70-79': 8, '80+': 14.8}  # in %
INFECTION_FATALITY_RATIO = {'0-9': 0.0016, '10-19': 0.007, '20-29': 0.031, '30-39': 0.084, '40-49': 0.16, \
                       '50-59': 0.6, '60-69': 1.9, '70-79': 4.3, '80+': 7.8}  # in %
OVERALL_H_RATIO = {'0-9': 0.04, '10-19': 0.04, '20-29': 1.1, '30-39': 3.4, '40-49': 4.3, \
                       '50-59': 8.2, '60-69': 11.8, '70-79': 16.6, '80+': 18.4}  # in %
age_group_dict = {3: ['0-4', '5-17', '18+'], 5: ['0-4', '5-17', '18-49', '50-64', '65+']}

# Used in param.SEIR_get_param
# T_Y_TO_R_DIST = lambda x: np.random.triangular(*x)
# T_EXPOSED_DIST = lambda x: np.random.triangular(*x)
PROP_TRANS_IN_E = 0.126
T_ONSET_TO_H = 5.9
T_H_TO_D = 11.2
T_EXPOSED_PARA = [5.6, 7, 8.2]
T_Y_TO_R_PARA = [21.1, 22.6, 24.4]
T_H_TO_R = 11.5
R0 = 2.2
# unused, either here or in main
DOUBLE_TIME = {'high': 4., 'low': 7.2}

# Used in both functions
ASYMP_RATE = 0.179

# misc
age_groups = n_age = 5
