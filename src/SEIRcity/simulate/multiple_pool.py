#!/usr/bin/env python
import os
import sys
import numpy as np
import pickle
import datetime as dt
from multiprocessing import Pool

from SEIRcity.scenario import BaseScenario as Scenario
from SEIRcity.get_scenarios import get_scenarios
from .simulate_one import simulate_one
from SEIRcity import param_parser, utils
from SEIRcity import param as SEIR_param_publish
from SEIRcity.outcome_handler import OutcomeHandler

# DEV
from SEIRcity import dev_utils


def multiple_pool(config, threads=48):
    """Simulate multiple scenarios with multiprocessing support. Given
    dictionary of parameters `config` from configuration YAML, retrieves
    a list of unique scenarios from get_scenarios. A multiprocessing.Pool
    instance with `threads` number of threads is used to generate a list
    of outcomes (each outcome is a numpy array returned by simulate_one),
    which is passed to the OutcomeHandler for "compilation" into
    parameter space. Returns the OutcomeHandler instance.
    """
    # TODO: validate that slicing by n_sim chunks produces
    # list of equivalent scenarios (same Scenario objects)

    # get scenarios from yaml_fp
    scenarios_tup = get_scenarios(config=config)

    # For now, for the sake of output formatting, assert NUM_SIM is
    # same for all Scenarios. This is checked later by OutcomeHandler
    n_sims_lst = [s.get("NUM_SIM", None) for s in scenarios_tup]
    assert len(set(n_sims_lst)) == 1
    n_sim = n_sims_lst[0]
    assert n_sim is not None

    # get datetime64 coords for 'time' dimension
    first_s = scenarios_tup[0]
    time_coords = utils.get_dt64_coords(
        time_begin_sim=first_s['time_begin_sim'],
        total_time=first_s['total_time'],
        shift_week=first_s['shift_week'],
        interval_per_day=first_s['interval_per_day'])

    # New OutcomeHandler
    oh = OutcomeHandler()

    # generate int64 seeds for each thread
    expected_n_tasks = n_sim * len(scenarios_tup)
    if expected_n_tasks < 4:
        pool_size = 4
    else:
        pool_size = expected_n_tasks
    seed_gen = np.random.SeedSequence(pool_size=pool_size)

    # generate list of tasks (Scenario objects with NUM_SIM replicates)
    tasks = list()
    task_idx = 0
    for unique_scenario in scenarios_tup:
        for replicate in range(n_sim):
            task = Scenario(unique_scenario.copy())
            task['config'] = config
            task['seed'] = seed_gen.pool[task_idx]
            tasks.append(task)
            task_idx += 1

    # assert that the number of tasks equals number of
    # unique scenarios times the number of replicates
    n_tasks = len(tasks)
    if expected_n_tasks != n_tasks:
        raise ValueError(
            "Assigned {} tasks but expected ".format(n_tasks) +
            "{} (number unique scenarios ".format(expected_n_tasks) +
            "* replicates (AKA NUM_SIM) = " +
            "{} * {} = {}).".format(len(scenarios_tup), n_sim, expected_n_tasks))

    # run simulate_one for each task
    with Pool(processes=threads) as pool:
        outcomes_flat_lst = pool.map(simulate_one, tasks)

    # load flat outcomes list into the OutcomeHandler
    assert len(tasks) == len(outcomes_flat_lst)
    for task_idx in range(len(tasks)):
        scenario = tasks[task_idx]
        outcome = outcomes_flat_lst[task_idx]
        dims = ('compartment', 'time', 'age_group', 'risk_group')
        coords = dict({
            # TODO: ingest these dynamically
            'compartment': ['S', 'E2Iy', 'E2I', 'Iy2Ih', 'H2D', 'Ia',
                            'Iy', 'Ih', 'R', 'E', 'D', 'SchoolReopenArr',
                            'SchoolCloseArr', 'R0_baseline'],
            'age_group': ['0-4', '5-17', '18-49', '50-64', '65+'],
            'time': time_coords
        })
        oh.add_outcome(scenario, outcome, dims=dims, coords=coords)
    oh._compile()
    return oh
