import os
import sys
import pytest
import pickle
import numpy as np
from .pytest_utils import fp, md5sum, call_with_legacy_params, assert_objects_equal
from SEIRcity.simulate import legacy

# pickle results from legacy._legacy_simulate_multiple
from SEIRcity.dev_utils import decorate_all_in_module, base_decorator
decorate_all_in_module(legacy, base_decorator)


@pytest.mark.parametrize("legacy_pickle,yaml_fp", [
    (fp("tests/data/simulate_multiple_result2.pckl"),
       fp("tests/data/configs/single_scenario0.yaml"))
])
def test_simulate_multiple_legacy(legacy_pickle, yaml_fp):
    """Compare results of legacy run of simulate_multiple
    with results from a new run. Args, kwargs, and results were written
    to file path `legacy_pickle` by dev_utils.result_to_pickle. Can the
    same function yield exactly the same outputs as the legacy run using
    exactly the same inputs. Equality is determined by
    pytest_utils.assert_objects_equal.
    """
    assert os.path.isfile(legacy_pickle)
    assert os.path.isfile(yaml_fp)
    kwargs = {
        'legacy_pickle': legacy_pickle,
        'func': legacy._legacy_simulate_multiple,
        'override_args': list(),
        'override_kwargs': {"yaml_fp": yaml_fp},
        'verbose': True
    }
    legacy_result, new_result = call_with_legacy_params(**kwargs)
    assert isinstance(legacy_result, dict)
    assert isinstance(new_result, dict)
    assert legacy_result, "legacy_result is an empty dict"
    assert new_result, "new_result is an empty dict"
    assert_objects_equal(legacy_result, new_result, verbose=False)
