import os
import sys
import pytest
import pickle
import numpy as np
from .pytest_utils import fp, md5sum, call_with_legacy_params, assert_objects_equal
from SEIRcity.simulate.simulate_one import simulate_one
from SEIRcity.get_scenarios import get_scenarios
from SEIRcity.param import aggregate_params_and_data


@pytest.mark.parametrize("legacy_pickle,yaml_fp", [
    (fp("tests/data/single_scenario_main_result0.pckl"),
     fp('tests/data/configs/single_scenario0.yaml')),
    (fp("tests/data/single_scenario_main_result3.pckl"),
     fp('tests/data/configs/single_scenario3.yaml')),
    (fp("tests/data/multiple_scenario_main_result0.pckl"),
     fp('tests/data/configs/multiple_scenario0.yaml')),
])
def test_return_shape(legacy_pickle, yaml_fp):
    """"""
    config = aggregate_params_and_data(yaml_fp=yaml_fp)
    scenario = get_scenarios(config=config)[0]
    scenario['config'] = config
    result = simulate_one(scenario)
    assert isinstance(result, np.ndarray)
    assert len(result.shape) == 4
