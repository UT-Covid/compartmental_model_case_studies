import os
import sys
import pytest
import pickle
import numpy as np
import datetime as dt
from attrdict import AttrDict
from .pytest_utils import fp, assert_objects_equal, call_with_legacy_params
from SEIRcity import model, utils

HERE = os.path.dirname(os.path.abspath(__file__))


def test_model_can_import():
    """Can import the two functions in SEIR_main_publish
    """
    assert hasattr(model, "SEIR_model_publish_w_risk")
    assert hasattr(model, "compute_R0")


@pytest.mark.skip
@pytest.mark.parametrize("legacy_pickle", [
    # Call from SEIR_main_publish.main on commit on commit eca0e3b4222476b87d45
    fp("tests/data/SEIR_model_publish_w_risk_result0.pckl")
])
def test_model_publish_w_risk_legacy(legacy_pickle, tmp_path):
    """Compare results of legacy run of model.SEIR_model_publish_w_risk
    with results from a new run. Args, kwargs, and results were written
    to file path `legacy_pickle` by dev_utils.result_to_pickle. Can the
    same function yield exactly the same outputs as the legacy run using
    exactly the same inputs. Equality is determined by
    pytest_utils.assert_objects_equal.
    """
    assert os.path.isfile(legacy_pickle)
    legacy_result, new_result = call_with_legacy_params(
        legacy_pickle=legacy_pickle, func=model.SEIR_model_publish_w_risk)
    assert isinstance(legacy_result, tuple)
    assert isinstance(new_result, tuple)
    assert_objects_equal(legacy_result, new_result, verbose=False)


def test_dt_to_dt64arr_and_back():
    """Can convert from dt64 to dt and back.
    """
    # we use the legacy_reopen datetime from below test as fixture
    as_dt = dt.datetime(2020, 4, 2)
    print('as_dt: ', as_dt)
    as_dt64 = utils.dt_to_dt64(as_dt)
    print('as_dt64: ', as_dt64)
    back_again = utils.dt64_to_dt(as_dt64)
    assert back_again == as_dt


@pytest.mark.skip
@pytest.mark.parametrize("legacy_pickle", [
    # Call from SEIR_main_publish.main on commit on commit eca0e3b4222476b87d45
    fp("tests/data/SEIR_model_publish_w_risk_result0.pckl")
])
def test_model_can_return_dt64_array(legacy_pickle, tmp_path):
    """If the format of school event times returned by model is changed
    to an ndarray with dtype datetime64, can we recapitulate the old
    datetime.datetime return format?
    """
    # run model with same kwargs
    assert os.path.isfile(legacy_pickle)
    legacy_result, new_result = call_with_legacy_params(
        legacy_pickle=legacy_pickle,
        func=model.SEIR_model_publish_w_risk)

    legacy_reopen = legacy_result[-1]
    legacy_close = legacy_result[-2]
    print('legacy_reopen: ', legacy_reopen)
    print('legacy_close: ', legacy_close)

    new_reopen_arr = new_result[-1]
    new_close_arr = new_result[-2]
    assert isinstance(new_reopen_arr, np.ndarray)
    assert isinstance(new_close_arr, np.ndarray)
    assert new_reopen_arr.dtype == 'float64'
    assert new_close_arr.dtype == 'float64'

    new_reopen_dt = utils.bool_arr_to_dt(new_reopen_arr)
    new_close_dt = utils.bool_arr_to_dt(new_close_arr)

    assert new_reopen_dt == legacy_reopen
    assert new_close_dt == legacy_close
