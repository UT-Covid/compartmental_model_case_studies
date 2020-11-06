#!/usr/bin/env python
import os
import sys
import numpy as np
import pickle
import datetime as dt

from SEIRcity.scenario import BaseScenario as Scenario
from SEIRcity.get_scenarios import get_scenarios
from .simulate_one import simulate_one
from SEIRcity import param_parser, utils
from SEIRcity import param as SEIR_param_publish
from SEIRcity.outcome_handler import OutcomeHandler

# DEV
from SEIRcity import dev_utils


def multiple_serial(config):
    """Simulate multiple scenarios serially on a single thread. Given
    path to config YAML file `yaml_fp`, retrieves a list of unique
    scenarios from get_scenarios. Serially generates a list of outcomes
    (each outcome is a numpy array returned by simulate_one), which is
    passed to the OutcomeHandler for "compilation" into parameter space.
    Returns the OutcomeHandler instance.
    """

    # get scenarios from yaml_fp
    scenarios_tup = get_scenarios(config)

    # For now, for the sake of output formatting, assert NUM_SIM is
    # same for all Scenarios. This is checked later by OutcomeHandler
    # pull this from Scenario attr, just like OutcomeHandler does
    n_sims_lst = [s.get("NUM_SIM", None) for s in scenarios_tup]
    assert len(set(n_sims_lst)) == 1
    n_sim = n_sims_lst[0]

    # get datetime64 coords for 'time' dimension
    first_s = scenarios_tup[0]
    time_coords = utils.get_dt64_coords(
        time_begin_sim=first_s['time_begin_sim'],
        total_time=first_s['total_time'],
        shift_week=first_s['shift_week'],
        interval_per_day=first_s['interval_per_day'])

    # New OutcomeHandler
    oh = OutcomeHandler()

    for scenario in scenarios_tup:
        for replicate in range(n_sim):
            outcome = simulate_one(scenario)
            dims = ('compartment', 'time', 'age_group', 'risk_group')
            coords = dict({
                'compartment': ['S', 'E2Iy', 'E2I', 'Iy2Ih', 'H2D', 'Ia',
                                'Iy', 'Ih', 'R', 'E', 'D', 'SchoolReopenArr',
                                'SchoolCloseArr', 'R0_baseline'],
                'age_group': ['0-4', '5-17', '18-49', '50-64', '65+'],
                'time': time_coords
            })
            oh.add_outcome(scenario, outcome, dims=dims, coords=coords)
    compiled = oh._compile()
    return oh
