import os
import sys
import pytest
from pprint import pprint as pp
from .pytest_utils import fp, md5sum, call_with_legacy_params, assert_objects_equal
from SEIRcity.get_scenarios import get_scenarios
from SEIRcity.scenario import BaseScenario
from SEIRcity.param import aggregate_params_and_data


@pytest.mark.skip
@pytest.mark.parametrize('yaml_fp,legacy_pickle', [
    (fp("tests/data/configs/single_scenario0.yaml"),
     fp("tests/data/scenarios/single_scenario0.pckl")),
    (fp("tests/data/configs/single_scenario1.yaml"),
     fp("tests/data/scenarios/single_scenario1.pckl")),
    (fp("tests/data/configs/single_scenario2.yaml"),
     fp("tests/data/scenarios/single_scenario2.pckl")),
    (fp("tests/data/configs/multiple_scenario0.yaml"),
     fp("tests/data/scenarios/multiple_scenario0.pckl")),
])
def test_can_return_legacy(yaml_fp, legacy_pickle):
    """Given arg `yaml_fp`, can return Python object pickled in `legacy_pickle`.
    """
    assert os.path.isfile(legacy_pickle)
    assert os.path.isfile(yaml_fp)
    config = aggregate_params_and_data(yaml_fp=yaml_fp)
    override_args = [config]

    legacy_result, new_result = call_with_legacy_params(
        legacy_pickle=legacy_pickle,
        func=get_scenarios,
        override_args=override_args)

    assert isinstance(legacy_result, tuple)
    assert isinstance(new_result, tuple)
    assert all([isinstance(s, BaseScenario) for s in new_result])
    assert legacy_result, "legacy_result is an empty tuple"
    assert new_result, "new_result is an empty tuple"

    assert_objects_equal(legacy_result, new_result, verbose=False)
