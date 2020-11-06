import os
import sys
import pytest
import numpy as np
import pandas as pd
from .pytest_utils import fp, md5sum
from SEIRcity import utils


def test_can_import():
    """"""
    assert hasattr(utils, "get_dt64_coords")


@pytest.mark.parametrize("kwargs,expected", [
    ({
        'time_begin_sim': 20200216,
        'total_time': 364,
        'shift_week': 0,
        'interval_per_day': 10
    },
     pd.date_range(start='2020-02-16', end='2021-02-14',
                   periods=3640))
])
def test_get_dt64_coords(kwargs, expected):
    """"""
    # need a freq interval_per_day per day, not evenly spaced
    r = utils.get_dt64_coords(**kwargs)
    # print(r)
    assert isinstance(r, pd.DatetimeIndex)
    assert all([a == e for a, e in zip(r, expected)])
