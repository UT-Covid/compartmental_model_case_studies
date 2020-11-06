import os
import sys
import pytest
import pickle
import numpy as np
import pandas as pd
import xarray as xr
from attrdict import AttrDict
from .pytest_utils import fp, md5sum, call_with_legacy_params, assert_objects_equal
from SEIRcity.outcome_handler import OutcomeHandler
from SEIRcity.scenario import BaseScenario
from SEIRcity.utils import all_same, all_unique


@pytest.fixture()
def oh():
    dims = ('param1', 'param2', 'param3')
    yield OutcomeHandler(param_dims=dims)


@pytest.fixture()
def outcome_w_ages():
    """A simplified outcome, with 4 compartments reported
    over 10 timepoints. Mostly for understanding how xarray
    works.
    """
    arr = np.arange(40).reshape((4, 10))
    dims = ('compartment', 'time')
    yield AttrDict({
        "arr": arr,
        "dims": dims
    })


@pytest.fixture()
def simpler_outcome():
    """A simplified 1D outcome in the time dimension. Represents
    total population of an arbitraty compartment over 10 timepoints.
    """
    arr = np.arange(10)
    dims = ('time')
    yield AttrDict({
        "arr": arr,
        "dims": dims
    })


@pytest.fixture()
def single_scenario_outcome():
    """Outcome from single_scenario0.yaml on commit
    e1e1da5c874405062804b1bac19378680d65205d
    """
    with open(fp("tests/data/example_outcome_single_scenario3.pckl"),
              'rb') as f:
        arr = pickle.load(f)
    assert isinstance(arr, np.ndarray)
    dims = ('compartment', 'time')
    yield AttrDict({
        "arr": arr,
        "dims": dims
    })


@pytest.fixture()
def outcome(simpler_outcome, outcome_w_ages, single_scenario_outcome):
    # yield simpler_outcome
    yield outcome_w_ages
    # yield single_scenario_outcome


def scenario():
    return BaseScenario({
        "NUM_SIM": 3,
        "param1": np.random.randint(3),
        "param2": "constant value",
        "param3": np.random.randint(10),
    })


@pytest.fixture()
def oh_w_outcomes(oh, outcome):
    for i in range(3):
        oh.add_outcome(scenario(), outcome.arr * i,
                       dims=outcome.dims)
    yield oh


@pytest.fixture()
def oh_w_replicates(oh, outcome):
    s = scenario()
    for i in range(3):
        oh.add_outcome(s, outcome.arr * i,
                       dims=outcome.dims)
    yield oh


def test_init(oh):
    """"""
    assert isinstance(oh, OutcomeHandler)


def test_can_add_outcome(oh_w_outcomes):
    """add_outcome method can generate a list of
    xr.DataArrays, where all the dims are the same.
    """
    flat_lst = oh_w_outcomes._outcomes_flat_lst
    assert isinstance(flat_lst, list)
    assert all([isinstance(da, xr.DataArray) for da in flat_lst])
    assert all_same([da.dims for da in flat_lst])
    # has time dims
    assert all(['time' in da.dims for da in flat_lst])


def test_flat_to_da(oh_w_outcomes):
    """Hidden method _flat_to_da can convert the _outcomes_flat_lst
    from a list of DataArrays to a DataArray that preserves
    """
    oh = oh_w_outcomes
    flat_lst = oh_w_outcomes._outcomes_flat_lst
    flat_da = oh._flat_to_da(flat_lst)
    dims = flat_lst[0].dims
    assert isinstance(flat_da, xr.DataArray)
    assert flat_da.dims == tuple(['task_index'] + list(dims))
    # can load coords when generating flat DataArray
    assert all([dim in flat_da.coords for dim in flat_da.dims]), flat_da.coords
    assert all([x == exp for x, exp in zip(flat_da.coords['task_index'],
                                           range(3))])
    assert all([x == exp for x, exp in zip(flat_da.coords['time'], range(10))])


def test_outcomes_flat(oh_w_outcomes):
    """Test property outcomes_flat that passes _outcomes_flat_lst to
    _flat_to_da (see above)
    """
    oh = oh_w_outcomes
    dims = oh._outcomes_flat_lst[0].dims
    flat_da = oh.outcomes_flat
    assert isinstance(flat_da, xr.DataArray)
    assert flat_da.dims == tuple(['task_index'] + list(dims))


# @pytest.mark.skip
def test_can_compile(oh_w_replicates):
    # print(oh_w_replicates.outcomes_flat)
    compiled = oh_w_replicates._compile()
    # print("compiled: ", compiled)
    # assert 0, compiled
    # print(compiled)


@pytest.mark.skip
@pytest.mark.parametrize("legacy_pickle", [
    fp("tests/data/single_scenario_flat_to_da_result0.pckl"),
    # (fp("tests/data/single_scenario_main_result3.pckl"),
    #  fp('tests/data/configs/single_scenario3.yaml')),
    # (fp("tests/data/multiple_scenario_main_result0.pckl"),
    #  fp('tests/data/configs/multiple_scenario0.yaml')),
])
def test_flat_to_da_legacy(legacy_pickle, outcome_w_ages):
    """For testing performance of _flat_to_da
    """
    oh = outcome_w_ages
    assert os.path.isfile(legacy_pickle)
    legacy_result, new_result = call_with_legacy_params(
        legacy_pickle=legacy_pickle,
        func=oh._flat_to_da)
    assert isinstance(legacy_result, xr.DataArray)
    assert isinstance(new_result, xr.DataArray)
    assert_objects_equal(legacy_result, new_result, verbose=False)
