import pickle
from attrdict import AttrDict
import os
import sys
import pytest
from pprint import pprint as pp
from .pytest_utils import fp, md5sum, call_with_legacy_params, assert_objects_equal
from SEIRcity import param

HERE = os.path.dirname(os.path.abspath(__file__))
CWD = os.getcwd()


def test_param_can_import():
    """Can import the two functions in SEIR_main_publish
    """
    assert hasattr(param, "SEIR_get_data")
    assert hasattr(param, "SEIR_get_param")


@pytest.mark.parametrize("legacy_pickle,yaml_fp", [
    (fp("tests/data/SEIR_get_data_result0.pckl"),
     fp("tests/data/configs/single_scenario0.yaml"))
])
def test_get_data_legacy(legacy_pickle, yaml_fp):
    """Compare results of legacy run of param.SEIR_get_data
    with results from a new run. Args, kwargs, and results were written
    to file path `legacy_pickle` by dev_utils.result_to_pickle. Can the
    same function yield exactly the same outputs as the legacy run using
    exactly the same inputs. Equality is determined by
    pytest_utils.assert_objects_equal.
    """
    assert os.path.isfile(legacy_pickle)
    assert os.path.isfile(yaml_fp)
    config = param.aggregate_params_and_data(yaml_fp=yaml_fp)
    kwargs = {
        'legacy_pickle': legacy_pickle,
        'func': param.SEIR_get_data,
        'override_args': list(),
        'override_kwargs': {"config": config}
    }
    legacy_result, new_result = call_with_legacy_params(**kwargs)
    assert isinstance(legacy_result, tuple)
    assert isinstance(new_result, tuple)
    assert_objects_equal(legacy_result, new_result, verbose=False)


@pytest.mark.parametrize("legacy_pickle,yaml_fp", [
    (fp("tests/data/SEIR_get_param_result0.pckl"),
     fp("tests/data/configs/single_scenario0.yaml"))
])
def test_get_param_legacy(legacy_pickle, yaml_fp):
    """Compare results of legacy run of param.SEIR_get_data
    with results from a new run. Args, kwargs, and results were written
    to file path `legacy_pickle` by dev_utils.result_to_pickle. Can the
    same function yield exactly the same outputs as the legacy run using
    exactly the same inputs. Equality is determined by
    pytest_utils.assert_objects_equal.
    """
    assert os.path.isfile(legacy_pickle)
    assert os.path.isfile(yaml_fp)
    config = param.aggregate_params_and_data(yaml_fp=yaml_fp)
    kwargs = {
        'legacy_pickle': legacy_pickle,
        'func': param.SEIR_get_param,
        'override_args': list(),
        'override_kwargs': {"config": config}
    }
    legacy_result, new_result = call_with_legacy_params(**kwargs)
    assert isinstance(legacy_result, dict)
    assert isinstance(new_result, dict)
    assert_objects_equal(legacy_result, new_result, verbose=False)
