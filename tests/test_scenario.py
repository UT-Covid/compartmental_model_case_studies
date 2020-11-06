import os
import sys
import pytest
import numpy as np
from attrdict import AttrDict
from copy import deepcopy
from .pytest_utils import fp, md5sum, assert_objects_equal
from SEIRcity.scenario import BaseScenario, _inject

HERE = os.path.dirname(os.path.abspath(__file__))
CWD = os.getcwd()


@pytest.fixture()
def base_scenario():
    base_scenario = BaseScenario({
        'foo': 'bar',
        '3': 7.8
    })
    yield base_scenario
    del base_scenario


class TestScenario(object):

    def test_can_shallow_copy(self, base_scenario):
        assert isinstance(base_scenario, AttrDict)
        # AttrDict has attribute _sequence_type
        # failure here indicates that parent class
        # AttrDict.__init__ was not called
        assert hasattr(base_scenario, "_sequence_type")
        shallow_copy = base_scenario.copy()
        as_dict = base_scenario.to_dict()
        assert type(as_dict) is dict
        assert_objects_equal(shallow_copy, as_dict)

    @pytest.mark.parametrize('yaml_fp', [
        fp("tests/data/configs/single_scenario0.yaml"),
    ])
    def test_can_read_yaml(self, base_scenario, yaml_fp):
        assert os.path.isfile(yaml_fp)
        base_scenario.update_from_yaml(yaml_fp)
        assert base_scenario.get('foo', None) == 'bar'
        assert base_scenario.get('3', None) == 7.8
        assert base_scenario.get('CONTACT_REDUCTION', None) == [0.75]

    @pytest.mark.parametrize('args,expected_args', [
        ({'foo': 'bar'}, {'foo': 'bar'}),
        ({'inject_test': 'foo bar{{inject_me}}', 'inject_me': 'beezbooz'},
         {'inject_test': 'foo barbeezbooz', 'inject_me': 'beezbooz'}),
        ({'inject_recursion': ['bar', 'baz {{ inject_me }}', 4.],
          'inject_me': 'beezbooz'},
         {'inject_recursion': ['bar', 'baz beezbooz', 4.],
          'inject_me': 'beezbooz'}),
        ({'inject_max_depth': [{'foo': {'baz': ['bar', 5, AttrDict({}), "{{ inject_me }}"]}}],
          'inject_me': 'beezbooz'},
         {'inject_max_depth': [{'foo': {'baz': ['bar', 5, AttrDict({}), "beezbooz"]}}],
          'inject_me': 'beezbooz'}),
        # really try to break it. extreme edge case. just for fun
        ({'inject_me': '{{inject_me}}'}, {'inject_me': '{{inject_me}}'})
    ])
    def test_can_inject(self, args, expected_args):
        scenario = BaseScenario(args, inject=True)
        expected_scenario = BaseScenario(expected_args, inject=False)
        assert_objects_equal(scenario, expected_scenario, verbose=False)

    @pytest.mark.parametrize('args,expected_args', [
        ({'foo': 'bar'}, {'foo': 'bar'}),
        ({'inject_test': 'foo bar{{inject_me}}', 'inject_me': 'beezbooz'},
         {'inject_test': 'foo barbeezbooz', 'inject_me': 'beezbooz'}),
    ])
    def test_can_preserve_attr_after_inject(self, args, expected_args):
        attr_name, attr_val = 'bar', 'foo'
        scenario = BaseScenario(args, inject=False)
        expected_scenario = BaseScenario(args, inject=False)
        setattr(scenario, attr_name, attr_val)
        setattr(expected_scenario, attr_name, attr_val)
        scenario.inject()
        assert getattr(scenario, attr_name) == getattr(scenario, attr_name, "dummy")


class TestHiddenInject(object):

    @pytest.mark.parametrize('data,populate_with,expected', [
        ("{{inject_me}}", {'inject_me': 'bar'}, "bar"),
        (set(["{{inject_me}}"]), {'inject_me': 'bar'}, set(["bar"])),
        (tuple(["{{inject_me}}"]), {'inject_me': 'bar'}, tuple(["bar"])),
        (list(["{{inject_me}}"]), {'inject_me': 'bar'}, list(["bar"])),
        ({"foo": "{{inject_me}}"}, {'inject_me': 'bar'}, {"foo": "bar"})
    ])
    def test_type_support(self, data, populate_with, expected):
        """Can support recursion in types str, set, tuple, list, and dict."""
        assert _inject(data, populate_with) == expected

    @pytest.mark.parametrize('data,expected', [
        ({'inject_test': 'foo bar{{inject_me}}', 'inject_me': 'beezbooz'},
         {'inject_test': 'foo barbeezbooz', 'inject_me': 'beezbooz'}),
    ])
    def test_populate_with_self(self, data, expected):
        """Can safely modify a dict `self` with `data` == self and
        `populate_with` == self.copy()
        """
        assert _inject(data, data.copy()) == expected

    @pytest.mark.parametrize('data,populate_with,expected', [
        ("foo{{inject_me}}bar", {'inject_me': 3.}, "foo3.0bar"),
        ("bar{{inject_me}}baz", {'inject_me': ['a list']}, "bar['a list']baz"),
    ])
    def test_can_populate_non_str(self, data, populate_with, expected):
        """Can use non-str value to populate str type field.
        """
        result = _inject(data, populate_with)
        assert result == expected
        assert type(result) == type(expected)

    @pytest.mark.parametrize('data,populate_with,expected', [
        # supported conversion types (number.Number by default)
        ("{{inject_me}}", {'inject_me': 3.}, 3.),
        ("{{inject_me}}", {'inject_me': 365}, 365),
        # Does not attempt to convert the below strings. Can prevent
        # attempted conversion to sequence types, or if multiple injections
        # occur in one field.
        ("{{inject_me}}", {'inject_me': ['a list']}, "['a list']"),
        ("{{inject_me}}", {'inject_me': ['a set']}, "['a set']"),
        ("{{inject_me}}", {'inject_me': ['a tuple']}, "['a tuple']"),
        ("{{inject_me}}fizz{{me_too}}", {'inject_me': 3., 'me_too': 78}, "3.0fizz78"),
        # really weird edge cases
        ("{{inject_me}}", {'inject_me': np.inf}, np.inf),
    ])
    def test_can_convert(self, data, populate_with, expected):
        """Can replace str type field '{{inject_me}}' with non-string type
        value populate_with['inject_me'].
        """
        result = _inject(data, populate_with, try_convert=True)
        assert result == expected
        assert type(result) == type(expected)
