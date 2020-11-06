import os
import sys
import pytest
import pickle
import glob
from .pytest_utils import fp, md5sum, call_with_legacy_params, assert_objects_equal
import SEIRcity as main


def test_main_can_import():
    """Can import function main from SEIR_main_publish"""
    assert hasattr(main, "main")


@pytest.mark.slow
@pytest.mark.parametrize("yaml_fp", [
    # YAML for a fitting workflow
    fp("tests/data/configs/fit_to_data0.yaml"),
    # YAML for a sim workflow with 3 replicates and a param sweep
    fp("tests/data/configs/multiple_scenario1.yaml")] +

    # Single scenario deterministic simulation for each of 22 cities
    list(glob.glob(fp("tests/data/configs/22cities/*.yaml")))
)
def test_main(yaml_fp):
    """Run __init__.main
    """
    assert os.path.isfile(yaml_fp)
    result = main.main(config_yaml=yaml_fp,
                       out_fp="./outputs/22cities.pckl", threads=48)
