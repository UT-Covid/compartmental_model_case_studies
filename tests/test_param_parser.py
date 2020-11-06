#!/usr/bin/env python

import os
import pytest
import pickle
import importlib.util
from .pytest_utils import fp, md5sum, assert_objects_equal
from SEIRcity import param_parser

HERE = os.path.dirname(os.path.abspath(__file__))
CEW = set(('CRITICAL','ERROR','WARN'))

@pytest.mark.skip
def test_exact_match(caplog):
    pub_config = os.path.join(HERE, '..', 'SEIRcity', 'configs', 'published.yaml')
    assert os.path.isfile(pub_config)
    param_parser.load(pub_config)
    for record in caplog.records:
        assert record.levelname not in CEW
        #assert "wally" not in caplog.text

@pytest.mark.parametrize("yaml_fp,expected_fp", [
    (fp("tests/data/published0.yaml"), fp("tests/data/published0.py"))])
def test_can_convert_published(yaml_fp, expected_fp):
    """Function load can generate exactly the expected data given
    YAML file `yaml`
    """
    assert os.path.isfile(yaml_fp)
    assert os.path.isfile(expected_fp)

    # import expected_fp as module `expected`
    module_spec = importlib.util.spec_from_file_location("module.name", expected_fp)
    expected = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(expected)

    # run parser
    result = param_parser.load(yaml_fp)
    assert isinstance(result, dict)

    # compare with expected values
    for k in result.keys():
        assert hasattr(expected, k), \
            "{} has contains no var {}".format(expected_fp, k)
        try:
            assert_objects_equal(result[k], getattr(expected, k, None))
        except AssertionError as err:
            print(k)
            raise err
