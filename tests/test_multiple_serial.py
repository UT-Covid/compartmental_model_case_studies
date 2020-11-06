import os
import sys
import pytest
import pickle
import numpy as np
import xarray as xr
from .pytest_utils import fp, md5sum, call_with_legacy_params, assert_objects_equal
from SEIRcity.simulate.multiple_pool import multiple_pool
from SEIRcity.simulate.multiple_serial import multiple_serial
from SEIRcity.param import aggregate_params_and_data


@pytest.mark.skip
class TestSerial(object):

    @pytest.mark.parametrize("legacy_pickle, yaml_fp", [
        (fp("tests/data/multiple_serial_result1.pckl"),
         fp("tests/data/configs/multiple_reps_single_scenario5.yaml")),
    ])
    def test_serial_can_return_xarray(self, legacy_pickle, yaml_fp, tmp_path):
        assert os.path.isfile(legacy_pickle)
        assert os.path.isfile(yaml_fp)
        config = aggregate_params_and_data(yaml_fp=yaml_fp)
        kwargs = {
            'legacy_pickle': legacy_pickle,
            'func': multiple_serial,
            'override_args': [config]
        }
        legacy_result, new_result = call_with_legacy_params(**kwargs)
        assert isinstance(legacy_result.outcomes, xr.DataArray)
        assert isinstance(new_result.outcomes, xr.DataArray)
        assert legacy_result.outcomes.dims == new_result.outcomes.dims
        # print("legacy: ", legacy_result.outcomes)
        # print("new: ", new_result.outcomes)
        # print("legacy coords: ", legacy_result.outcomes.coords)
        # print("new coords: ", new_result.outcomes.coords)

    @pytest.mark.parametrize("legacy_pickle,yaml_fp", [
        (fp("tests/data/multiple_serial_result6.pckl"),
         fp("tests/data/configs/multiple_scenario2.yaml"))
    ])
    def test_serial_can_return_xarray_slow(self, legacy_pickle, yaml_fp):
        """same as above but slow"""
        assert os.path.isfile(legacy_pickle)
        assert os.path.isfile(yaml_fp)
        config = aggregate_params_and_data(yaml_fp=yaml_fp)
        kwargs = {
            'legacy_pickle': legacy_pickle,
            'func': multiple_serial,
            'override_args': [config]
        }
        legacy_result, new_result = call_with_legacy_params(**kwargs)
        # assert 0
        assert isinstance(legacy_result.outcomes, xr.DataArray)
        assert isinstance(new_result.outcomes, xr.DataArray)
        assert legacy_result.outcomes.dims == new_result.outcomes.dims
        # print("legacy: ", legacy_result.outcomes)
        # print("new: ", new_result.outcomes)
        # print("legacy coords: ", legacy_result.outcomes.coords)
        # print("new coords: ", new_result.outcomes.coords)
