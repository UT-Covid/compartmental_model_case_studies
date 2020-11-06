import os
import types
import functools
import pickle
from attrdict import AttrDict
import inspect
import time
# import git
from pprint import pprint as pp

# --------------------------Module Parameters------------------------- #

# whether to allow this module to do anything
# False will decorate with empty functions
ENABLE_DEV_UTILS = os.environ.get("ENABLE_DEV_UTILS", False)
# whether to allow overwrite of pickled results/args
DEV_UTILS_ALLOW_OVERWRITE = os.environ.get("DEV_UTILS_ALLOW_OVERWRITE", False)
# in the format <module.__name__>.<function.__name__>, a function
# to decorate with dev_utils.result_to_pickle
PICKLE_RESULTS_FROM = os.environ.get(
    "PICKLE_RESULTS_FROM", "")
# where to write pickled args/results. Formatted with function.__name__
# in args_to_pickle
PICKLED_ARGS_FP = os.environ.get(
    "PICKLED_ARGS_FP", "./outputs/{}_args{}.pckl")
PICKLED_RESULT_FP = os.environ.get(
    "PICKLED_RESULT_FP", "./outputs/{}_result{}.pckl")

# turn on ENABLE_DEV_UTILS if PICKLE_RESULTS_FROM is defined
if PICKLE_RESULTS_FROM:
    ENABLE_DEV_UTILS = True
    print("PICKLE_RESULTS_FROM == {}. ".format(PICKLE_RESULTS_FROM) +
          "Setting ENABLE_DEV_UTILS=1")
if ENABLE_DEV_UTILS:
    print("ENABLE_DEV_UTILS == True")

# -----------------------Decorator Extensions------------------------- #


def before_call_example(f, *args, **kwargs):
    """before_call decorators must always accept f, *args, **kwargs"""
    print("This is function before_call_example")


def after_call_example(f, result, *args, **kwargs):
    """after_call decorators must always accept f, result, *args, **kwargs"""
    print("This is function after_call_example")


def die(f, *args, **kwargs):
    raise Exception("intentional exception before or after running function " +
                    "{}".format(f.__name__))


def print_args(f, *args, **kwargs):
    """Decorator extension that prints function name, args, and kwargs"""
    print("Calling function '{}' with args:".format(f))
    arg_names = inspect.getfullargspec(f).args
    for k, v in zip(arg_names, args):
        print("\t{}: {}".format(k, v))
    if kwargs:
        print("kwargs:")
        pp(kwargs, indent=4)


def tick_counter(f, *args, **kwargs):
    try:
        CALL_COUNTER[f.__name__] += 1
    except KeyError:
        pass


def args_to_pickle(f, *args, **kwargs):
    """Pickles function args, and kwargs in dict format."""
    out_fp = PICKLED_ARGS_FP.format(f.__name__)
    data = dict({
        "args": args,
        "kwargs": kwargs})
    print("Writing pickled (kw)args for function {} to {}".format(f, out_fp))
    if os.path.exists(out_fp) and not DEV_UTILS_ALLOW_OVERWRITE:
        raise FileExistsError("File at '{}' already exists".format(out_fp))
    with open(out_fp, 'wb') as f:
        pickle.dump(data, f)


def result_to_pickle(f, result, *args, **kwargs):
    """Pickles function args, kwargs, and result in dict format."""
    out_fp = PICKLED_RESULT_FP.format(f.__name__, 0)
    data = dict({
        "fname": f.__name__,
        "commit": HEAD_commit_from_env(),
        "args": args,
        "kwargs": kwargs,
        "result": result})
    for i in range(100):
        if os.path.exists(out_fp) and not DEV_UTILS_ALLOW_OVERWRITE:
            out_fp = PICKLED_RESULT_FP.format(f.__name__, i)
        elif i == 100:
            raise FileExistsError("File at '{}' already exists".format(out_fp))
        else:
            break
    print("Writing pickled (kw)args and result for function {} to {}".format(f, out_fp))
    with open(out_fp, 'wb') as f:
        pickle.dump(data, f)

# ------------------------------Helpers------------------------------- #


def HEAD_commit():
    """Return commit ref for HEAD. Tries env GITREF_FULL if invalid git repo"""
    try:
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
    except git.exc.InvalidGitRepositoryError as invalid_err:
        sha = HEAD_commit_from_env()
    return sha


def HEAD_commit_from_env():
    """Return commit ref for HEAD. Passed to container as env GITREF_FULL"""
    return os.getenv("GITREF_FULL", "")


def parse_decorator_key(k):
    """Parses a string `k` formatted like
    <module.__name__>.<function.__name__> and returns tuple
    (<module.__name__>, <function.__name__>)
    """
    parsed = k.split(".")
    if len(parsed) == 1:
        return ("*", parsed[0])
    elif len(parsed) == 2:
        return parsed
    else:
        raise Exception("Invalid key '{}' in DECORATE_FUNCS".format(k))

# ------------Define which decorators on which functions-------------- #

# "<module.__name__>.<function.__name__>": {"before_call":
# [first_decorator_to_call_before_func, second_decorator_to_call_before],
# "after_call":
# [first_decorator_to_call_after_func, second_decorator_to_call_after]}
DECORATE_FUNCS = {
    # example
    "module.func": {
        "before_call": [before_call_example],
        "after_call": [after_call_example]},
    # function named func in any module
    "*.func": {
        "before_call": [],
        "after_call": []},
    # another way to specify function named func in any module
    "fit_to_data": {
        "before_call": [],
        "after_call": []},
    "_legacy_simulate_multiple": {
        "before_call": [],
        "after_call": [result_to_pickle]},
    "multiple_serial": {
        "before_call": [],
        "after_call": []},
    "multiple_pool": {
        "before_call": [],
        "after_call": []}
}

# add env PICKLE_RESULTS_FROM to decorator dict
if PICKLE_RESULTS_FROM:
    DECORATE_FUNCS[PICKLE_RESULTS_FROM] = {
        "before_call": [print_args],
        "after_call": [result_to_pickle]}

# dict of ints keyed by function.__name__ that tracks number of times
# each function has been called. Written to by tick_counter
CALL_COUNTER = {
    "function_that_was_called": 0
}

# ------------Base decorator and the function to add it--------------- #


def decorate_all_in_module(module, decorator):
    """Checkout from Łukasz Rogalski's answer on SO post
    https://stackoverflow.com/questions/39184338/how-can-i-decorate-all-functions-imported-from-a-file
    """
    # list of functions to decorate from DECORATE_FUNCS
    funcs_to_decorate = list([
        parse_decorator_key(k)[1] for k in DECORATE_FUNCS.keys()
        if parse_decorator_key(k)[0] in ("*", module.__name__)])
    if not ENABLE_DEV_UTILS:
        # not enabled, return
        return None
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, types.FunctionType):
            if getattr(obj, "__name__", None) in funcs_to_decorate:
                setattr(module, name, decorator(obj))


def base_decorator(f):
    """Decorator on all functions in all modules."""
    def exec_decorators(when, f, *args, **kwargs):
        assert when in ("before_call", "after_call")
        decorators = DECORATE_FUNCS.get(
            f.__name__, dict()).get(when, list())
        for d in decorators:
            assert isinstance(d, types.FunctionType), \
                "{} is not a function".format(d)
            d(f, *args, **kwargs)
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        # run before_call decorators
        exec_decorators("before_call", f, *args, **kwargs)
        # call the function
        result = f(*args, **kwargs)
        print("function {} took {:0.2f} seconds".format(
            f.__name__, time.time() - start))
        # run after_call decorators
        exec_decorators("after_call", f, result, *args, **kwargs)
        # return function result
        return result
    return wrapper
