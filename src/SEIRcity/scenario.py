#!/usr/bin/env python

import os
from attrdict import AttrDict
from jinja2 import Template
import numbers
import numpy as np
import datetime
import yaml
from copy import deepcopy
from . import param_parser


class BaseScenario(AttrDict):
    """Base class for Scenarios. Inherits from attrdict.AttrDict."""

    # Jinja injection in Scenarios is supported for the same Python types
    # that are supported in pyyaml v5.3.1 (and NoneType, of course)
    _supported_types = (datetime.datetime, str, bool, complex, int,
                       float, list, tuple, set, dict)

    def __init__(self, *args, inject=True, yaml_fp=None, **kwargs):
        super(BaseScenario, self).__init__(*args, **kwargs)
        if yaml_fp is not None:
            self.update_from_yaml(yaml_fp)
        if inject:
            self.inject()

    def update_from_yaml(self, yaml_fp):
        """Update self with values in config YAML file `yaml_fp`, using
        SEIRcity.param_parser.load.
        """
        if not os.path.isfile(yaml_fp):
            raise FileNotFoundError("Could not find config YAML file " +
                                    " at yaml_fp == '{}'".format(yaml_fp))
        new_params = param_parser.load(yaml_fp)
        assert isinstance(new_params, dict), \
            "received non-dict type from SEIRcity.param_parser.load"
        self.update(new_params)
        return self

    def inject(self):
        """Inject Jinja2-formatted template strings with values from
        self. This is done recursively as the algorithm walks through
        dictionary and sequence objects.

        Example:

            Given self defined as:

            self.to_dict() == {
                "key1": "a value to inject",
                "key2": {
                    "irrelevant_key": "{{key1}} goes here"
                },
                "key3": "{{key4}}",
                "key4": "4.6"}

            calling self.inject() would use Jinja2 to inject self with
            values stored in self:

            self.to_dict() == {
                "key1": "a value to inject",
                "key2": {
                    "irrelevant_key": "a value to inject goes here"
                },
                "key3": 4.6,
                "key4": "4.6"}

            Note that injection will attempt to convert the value
            containing the template to the same type as the injected
            key, as demonstrated with key3 and key4 above.

        Returns modified self, but also modifies self in place.
        """
        try:
            return _inject(self, self.copy(), max_depth=10, inplace=True,
                    try_convert=True, verbose=False)
        except RecursionError as recur_err:
            raise recur_err

    def to_dict(self):
        """Returns self as 'vanilla' Python dictionary."""
        return dict(self)


def _inject(data, populate_with, max_depth=10, inplace=False,
            try_convert=False, verbose=False,
            only_convert_to=(numbers.Number)):
    """Recursively inject Jinja2-formatted templates in `data` with
    values in dictionary `populate_with` using Jinja2. Recursively walks
    through dictionaries and sequence types (up to `max_depth` times).

    Args:
        data (obj): Object in which to perform Jinja2 injection.
            Currently, only supported types are str, dict,
            tuple, list, and set.
        populate_with (dict): Dictionary containing data to inject into
            Jinja2 templated strings. For instance, `populate_with` ==
            {'key1': 'a value'} would convert `data` == '{{key1}}' to
            'a value'.
        max_depth (int): Maximum levels of recursion to allow before
            throwing RecursionError.
        inplace (bool): Whether to modify `data` in place. Only
            supported for dict-type `data`.
        try_convert (bool): Whether to attempt conversion after
            injection. For instance, `populate_with` ==
            {'key1': 6.8} would convert `data` == '{{key1}}' to
            float type 6.8. Only supported for conversions to types in
            `number.Number`.
        verbose (bool): Verbosity
        only_convert_to (tuple): Supported conversion types. See
            `try_convert`.

    Returns modified `data`. See example in scenario.BaseScenario.inject
    for details.
    """
    assert isinstance(populate_with, dict), \
        "arg `populate_with` must be a dictionary"
    if verbose:
        print("_inject was passed data: {}".format(data))
        print("_inject was passed populate_with: {}".format(populate_with))
    max_depth -= 1
    kwargs = {
        'max_depth': max_depth,
        'inplace': inplace,
        'try_convert': try_convert,
        'verbose': verbose}
    if max_depth <= 0:
        raise RecursionError("scenario._inject called itself >= " +
                             "max_depth times. Halting recursion.")
    elif isinstance(data, str):
        t = Template(data)
        pop_keys = [k for k in populate_with.keys() if k in data]
        pop_filtered = {k: populate_with[k] for k in pop_keys}
        injected = t.render(**pop_filtered)
        if try_convert and injected != data and len(pop_keys) == 1:
            pop_value = pop_filtered[pop_keys[0]]
            if not isinstance(pop_value, only_convert_to):
                return injected
            return _try_conversion(injected, type(pop_value))
        else:
            return injected
    elif isinstance(data, dict):
        if inplace:
            d = data
        else:
            d = data.copy()
        for k, v in d.items():
            d[k] = _inject(v, populate_with, **kwargs)
        return d
    elif isinstance(data, list):
        return list([_inject(v, populate_with, **kwargs) for v in data])
    elif isinstance(data, set):
        return set([_inject(v, populate_with, **kwargs) for v in data])
    elif isinstance(data, tuple):
        return tuple([_inject(v, populate_with, **kwargs) for v in data])
    else:
        return data


def _try_conversion(val, to_type, verbose=True):
    """Try to convert `val` to type `to_type` by calling
    `to_type`.__call__. Returns unaltered `val` if conversion fails.
    Refuses to try conversions to types not in `only_try`
    """
    if verbose:
        print("_try_conversion called with val " +
              "{} to_type {}".format(val, to_type))
    converter = getattr(to_type, "__call__", None)
    if converter is None:
        return val
    try:
        return converter(val)
    except ValueError as val_err:
        return val
    except Exception as err:
        raise err
