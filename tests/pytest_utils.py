import os
import hashlib
import pickle
from functools import partial
from pprint import pprint as pp

# class definitions for *_objects_equal functions
from collections.abc import Iterable
from numbers import Number

SEIR_HOME = os.environ['SEIR_HOME']


def md5sum(filename):
    """Credit to Raymond Hettinger's reply on SO post
    https://stackoverflow.com/questions/7829499/using-hashlib-to-compute-md5-digest-of-a-file-in-python-3
    """
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()
    # print(md5sum('utils.py'))


def fp(path):
    """Prepends SEIR_HOME to path and returns full path."""
    return os.path.join(SEIR_HOME, path)


def obj_to_pickle(obj, fp):
    """Pickle dumps Python `obj` to path `fp`"""
    with open(fp, 'wb') as f:
        pickle.dump(obj, f)
    assert os.path.isfile(fp)


def compare_dicts(old_d, new_d, show_diff=False):
    """Compares dictionaries by key and prints in sane format
    """
    if old_d.keys() != new_d.keys():
        print("\tkeys are different between old len({}) and new len({})".format(
            len(old_d.keys()), len(new_d.keys())))
    all_okay = True
    for k in sorted(set(list(old_d.keys()) + list(new_d.keys()))):
        print("   {}".format(k))
        if k not in new_d:
            print("*    new dict has no attr ")
            continue
        elif k not in old_d:
            print("*     old dict has no attr ")
            continue
        are_equal = are_objects_equal(old_d[k], new_d[k])
        if are_equal:
            print("    is same between legacy and new")
        else:
            print("*    is **DIFFERENT** between legacy and new")
            all_okay = False
            if show_diff:
                print("     old: ", old_d[k])
                print("     new: ", new_d[k])
    return all_okay


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
        assert o1 == o2, "values differ"
    except AssertionError as ass_err:
        pp(o1)
        print("versus")
        pp(o2)
        raise ass_err
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
        return bool(o1 == o2)
    except ValueError as val_err:
        if type(o1) is not type(o2):
            return False
        elif both_inst_of((Number, str)):
            # have to catch type str to prevent RecursionError
            # (strings are Iterable)
            return bool(o1 == o2)
        elif both_inst_of(dict):
            if o1.keys() != o2.keys():
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


def call_with_legacy_params(func, legacy_pickle,
                            override_args=None, override_kwargs=None,
                            verbose=False):
    """Given a file path `legacy_pickle` containing an encoded Python
    dictionary, run function `func` with the same args encoded in
    `legacy_pickle`, and pickle the returned value. Returns tuple
    with filepath to pickled legacy return value, filepath to pickled
    new return value, the legacy return value object, and the new return
    value object, respectively. The dictionary encoded in `legacy_pickle`
    must be type dict and minimally contain keys args, kwargs, and result.
    Specify keyword arguments `override_args` or `override_kwargs` to
    override pickled args/kwargs. For instance, specifying both will call
    func(*override_args, **override_kwargs).
    """
    assert os.path.isfile(legacy_pickle)
    with open(legacy_pickle, 'rb') as f:
        unpickled = pickle.load(f)
    assert isinstance(unpickled, dict)
    assert "args" in unpickled
    assert "kwargs" in unpickled
    assert "result" in unpickled

    # print function name and commit sha
    if verbose:
        if "fname" in unpickled:
            print("function name (fname):", unpickled['fname'])
        if "commit" in unpickled:
            print("'{}' was pickled on commit: {}".format(
                legacy_pickle, unpickled['commit']))
        print("'{}' was run with args: {}".format(
            legacy_pickle, unpickled['args']))
        print("'{}'  was run with kwargs: {}".format(
            legacy_pickle, unpickled['kwargs']))

    # add override args and kwargs if they were specified
    if override_args is None:
        args = unpickled['args']
    else:
        args = override_args
    if override_kwargs is None:
        kwargs = unpickled['kwargs']
    else:
        kwargs = override_kwargs

    # run same function using the same params
    result = func(*args, **kwargs)
    return (unpickled['result'], result)
