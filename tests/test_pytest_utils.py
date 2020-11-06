import os
import sys
import pytest
from . import pytest_utils

HERE = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('o1,o2', [
    (1, 2),
    (3, 3.),
    ({'inject_test': 'foo bar{{inject_me}}', 'inject_me': 'beezbooz'},
     {'inject_test': 'foo barbeezbooz', 'inject_me': 'beezbooz'}),
])
def test_assert_objects_equal_throws_assertion(o1, o2):
    # match=r".* 123 .*"
    with pytest.raises(AssertionError):
        pytest_utils.assert_objects_equal(o1, o2)
