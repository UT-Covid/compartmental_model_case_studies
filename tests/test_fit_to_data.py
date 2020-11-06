import os
import sys
import pytest
import numpy as np
from pprint import pprint as pp
from .pytest_utils import fp, md5sum, assert_objects_equal, \
    call_with_legacy_params, are_objects_equal, compare_dicts
from SEIRcity import fit_to_data
from SEIRcity.param import aggregate_params_and_data


def test_can_import():
    """"""
    assert hasattr(fit_to_data, "fitting_workflow")


@pytest.mark.slow
class TestFittingWorkflow(object):

    @pytest.mark.parametrize("yaml_fp", [
        fp("tests/data/configs/fit_to_data0.yaml"),
    ])
    def test_can_fit_beta_cred(self, yaml_fp):
        """
        issue #29
        https://github.com/UT-Covid/SEIR-city/issues/29#issuecomment-612205441
        """
        def percent_diff(v1, v2):
            return 100 * abs(v2 - v1) / float(v2 + v1)
        assert os.path.isfile(yaml_fp)
        config = aggregate_params_and_data(yaml_fp)
        soln = fit_to_data.fitting_workflow(config)
        assert isinstance(soln, dict)
        # print("solution dictionary: ", soln)
        # allow a 1e-6% difference between values
        diff_allowed = 1e-8
        assert diff_allowed > percent_diff(soln['beta0'], 0.035311161044565095)
        assert diff_allowed > percent_diff(soln['c_reduction'], 0.9999999999999999)
        assert diff_allowed > percent_diff(soln['final_nrmsd_t'], 0.054442533850151076)

    @pytest.mark.parametrize("yaml_fp", [
        fp("tests/data/configs/fit_to_data1.yaml"),
    ])
    def test_can_fit_beta(self, yaml_fp):
        """Can fit only beta with constant c_reduction"""
        def percent_diff(v1, v2):
            return 100 * abs(v2 - v1) / float(v2 + v1)
        assert os.path.isfile(yaml_fp)
        config = aggregate_params_and_data(yaml_fp)
        soln = fit_to_data.fitting_workflow(config)
        assert isinstance(soln, dict)
        # print("solution dictionary: ", soln)
        # allow a 1e-6% difference between values
        diff_allowed = 1e-8
        assert diff_allowed > percent_diff(soln['beta0'], 0.032852938571626515)
        assert diff_allowed > percent_diff(soln['final_nrmsd_t'], 1.4016486264974712)

    @pytest.mark.parametrize("yaml_fp", [
        fp("tests/data/configs/fit_to_data2.yaml"),
    ])
    def test_can_fit_cred(self, yaml_fp):
        """Can fit c_reduction with constant beta0"""
        def percent_diff(v1, v2):
            return 100 * abs(v2 - v1) / float(v2 + v1)
        assert os.path.isfile(yaml_fp)
        config = aggregate_params_and_data(yaml_fp)
        soln = fit_to_data.fitting_workflow(config)
        assert isinstance(soln, dict)
        # print("solution dictionary: ", soln)
        # allow a 1e-6% difference between values
        diff_allowed = 1e-8
        assert diff_allowed > percent_diff(soln['c_reduction'], 0.8497231717065995)
        assert diff_allowed > percent_diff(soln['final_nrmsd_t'], 0.22376477708630133)
