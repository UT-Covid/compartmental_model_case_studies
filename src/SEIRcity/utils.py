#!/usr/bin/env python

import os
import numpy as np
import pandas as pd
import datetime as dt
from numbers import Number
from collections.abc import Sequence, Iterable


def assert_has_keys(d, required_keys, verbosity=0):
    """Asserts that dict `d` contains all keys in Sequence `required_keys`"""
    assert isinstance(d, dict), "arg `d` is a ".format(type(d)) + \
        ", not a dictionary"
    for k in required_keys:
        if k not in d.keys():
            if verbosity:
                print("dict d: ", d)
            raise IndexError("dictionary `d` does not have required " +
                             "key: {}".format(k))


def R0_arr_to_float(arr):
    """Converts 3D array with float dtype filled with the same float
    value, and returns that float value. Used as an adapter from new
    to legacy R0_baseline output.
    """
    assert isinstance(arr, np.ndarray), arr
    as_float = arr[0, 0, 0]
    assert isinstance(as_float, float), "type is {}".format(type(as_float))
    if np.all(np.isnan(arr)):
        return None
    return as_float


def get_dt64_coords(time_begin_sim, total_time, shift_week, interval_per_day):
    """Given int type args, return a pandas.DateIndex of evenly spaced
    timepoints.
    """
    date_begin = dt.datetime.strptime(np.str(
        time_begin_sim), '%Y%m%d') + dt.timedelta(weeks=shift_week)
    date_end = date_begin + dt.timedelta(days=total_time)
    n_timepoints = (total_time * interval_per_day)
    return pd.date_range(start=date_begin, end=date_end, periods=n_timepoints)


def bool_arr_to_dt(arr, interval_per_day, time_begin_sim, shift_week):
    """Converts a 3D float array containing zeroes and ones to
    a datetime.datetime object.
    """
    # for 2D currently
    t_slice = arr[:, 0, 0]
    assert len(t_slice.shape) == 1, t_slice.shape
    try:
        time_idx = np.where(t_slice == 1.)[0][0]
        time_idx = float(time_idx)
        assert isinstance(time_idx, float), time_idx
    except (KeyError, IndexError):
        # legacy result
        return "NA"
    print("time_idx: ", time_idx)

    # convert to datetime
    date_begin = dt.datetime.strptime(np.str(time_begin_sim), '%Y%m%d') + \
        dt.timedelta(weeks=shift_week)
    days_from_t0 = np.floor((time_idx + 0.1) / interval_per_day)
    t_date = date_begin + dt.timedelta(days=days_from_t0)
    return t_date


def dt64_arr_to_dt(as_dt64_arr):
    """Converts a 3D array of dtype np.datetime64[s]
    filled with the same np.datetime64 value to
    a datetime.datetime. Used as a converter to legacy datetime objects.
    """
    assert isinstance(as_dt64_arr, np.ndarray)
    assert as_dt64_arr.dtype == 'datetime64[s]'
    # return 'NA' if all are null
    if np.all(np.isnat(as_dt64_arr)):
        return "NA"
    as_dt64 = as_dt64_arr[0, 0, 0]
    return model.dt64_to_dt(as_dt64)


def dt_to_dt64(as_dt):
    """Converts a datetime.datetime to np.datetime64. Credit to
    https://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64
    """
    assert isinstance(as_dt, dt.datetime)
    return np.datetime64(as_dt)


def dt64_to_dt(as_dt64):
    """Converts a np.datetime64 to datetime.datetime. Credit to
    https://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64
    """
    assert isinstance(as_dt64, np.datetime64)
    ts = (as_dt64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
    return dt.datetime.utcfromtimestamp(ts)


def all_same(lst):
    """Returns True if all elements of Sequence `lst` are identical.
    False otherwise.
    """
    assert isinstance(lst, Sequence)
    return bool(len(set(lst)) <= 1)


def all_unique(lst):
    """Returns True if all elements of Sequence `lst` are unique.
    False otherwise.
    """
    assert isinstance(lst, Sequence)
    return bool(len(set(lst)) == len(lst))


def assert_objects_equal(o1, o2, max_depth=20, verbose=False):
    """Checkout from tests/pytest_utils.py on commit
    4d568cf938e06551fa9980e1071ddc4ec2b93ebc
    """
    def both_inst_of(otype):
        try:
            return isinstance(o1, otype) and isinstance(o2, otype)
        except RecursionError as recur_err:
            # raise Warning()
            raise recur_err

    max_depth -= 1
    if verbose:
        print("comparing objects:")
        pp(o1, indent=4)
        pp(o2, indent=4)
    assert type(o1) is type(o2), \
        "types differ: {} vs {}".format(type(o1), type(o2))
    if max_depth <= 0:
        print("comparing objects:")
        pp(o1, indent=4)
        pp(o2, indent=4)
        raise RecursionError("assert_objects_equal reached " +
                             "maximum levels searched. ".format(max_depth) +
                             "Recommended to call this function with " +
                             "verbose=True")
    try:
        assert o1 == o2, "values differ: {} vs {}".format(o1, o2)
    except ValueError as val_err:
        if both_inst_of((Number, str)):
            # have to catch type str to prevent RecursionError
            # (strings are Iterable)
            assert o1 == o2, "values differ: {} vs {}".format(o1, o2)
        elif both_inst_of(dict):
            assert len(o1.keys()) == len(o2.keys()), \
                "len(dict.keys()) differ: {} vs {}".format(o1.keys(), o2.keys())
            for k in o1.keys():
                assert_objects_equal(o1[k], o2[k], max_depth=max_depth,
                                     verbose=verbose)
        elif both_inst_of(Iterable):
            assert len(o1) == len(o2), \
                "lengths differ: {} vs {}".format(len(o1), len(o2))
            for k in range(len(o1)):
                assert_objects_equal(o1[k], o2[k], max_depth=max_depth,
                                     verbose=verbose)
        else:
            raise ValueError("assert_objects_equal does not support " +
                             "comparisions of type '{}'".format(type(o1)))


def are_objects_equal(o1, o2, max_depth=20, verbose=False):
    """Returns True if Python objects `o1` and `o2` are equal. Equality
    is defined as having the same type. If objects are lists or
    dictionaries, recursively call self on all keys. Same as
    assert_objects_equal but returns boolean.
    """
    def both_inst_of(otype):
        try:
            return isinstance(o1, otype) and isinstance(o2, otype)
        except RecursionError as recur_err:
            # raise Warning()
            raise recur_err
    max_depth -= 1
    kwargs = {
        'max_depth': max_depth,
        'verbose': verbose}
    if verbose:
        print("comparing objects:")
        pp(o1, indent=4)
        pp(o2, indent=4)
    if max_depth <= 0:
        print("comparing objects:")
        pp(o1, indent=4)
        pp(o2, indent=4)
        raise RecursionError("are_objects_equal reached " +
                             "maximum levels searched. ".format(max_depth) +
                             "Recommended to call this function with " +
                             "verbose=True")
    try:
        return o1 == o2
    except ValueError as val_err:
        if type(o1) is not type(o2):
            return False
        elif both_inst_of((Number, str)):
            # have to catch type str to prevent RecursionError
            # (strings are Iterable)
            return o1 == o2
        elif both_inst_of(dict):
            if len(o1.keys()) != len(o2.keys()):
                return False
            return all([are_objects_equal(o1[k], o2[k], **kwargs)
                       for k in o1.keys()])
        elif both_inst_of(Iterable):
            if len(o1) != len(o2):
                return False
            return all([are_objects_equal(o1[k], o2[k], **kwargs)
                       for k in range(len(o1))])
        else:
            raise ValueError("compare_objects does not support " +
                             "comparisions of type '{}'".format(type(o1)))
