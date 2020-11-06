#!/usr/bin/env python

import yaml, logging, os
logger = logging.getLogger(__name__)

def load(yaml_file, validate=False):
    # Load default values
    dyaml = os.path.join(os.path.dirname(__file__),'configs','default.yaml')
    if not os.path.exists(yaml_file):
        logger.error("config not found at %s"%(yaml_file))
        raise EnvironmentError
    if not os.path.exists(dyaml):
        logger.error("Default config not found at %s"%(dyaml))
        raise EnvironmentError
    with open(dyaml, 'r') as f:
        default = yaml.load(f, Loader=yaml.FullLoader)
    with open(yaml_file, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    if validate:
        ERROR = check_config(data, default)
        if ERROR:
            sys.exit("Encountered %i errors in configuration file: %s"%(ERROR, yaml_file))
    return data

def check_config(data, default):
    ERROR = 0
    age_keys = {5:('0-4', '5-17', '18-49', '50-64', '65+'), \
        3:('0-4', '5-17', '18+')}
    range_keys = ('0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+')
    # These can be evaluated in any order
    ERROR += check(data, 'age_groups', int, default=default)
    ERROR += check(data, 'R0', float, default=default)
    ERROR += check(data, 'DOUBLE_TIME', dict, ctype=float, keys=('low','high'), default=default)
    ERROR += check(data, 'T_EXPOSED_DIST', str, default=default)
    ERROR += check(data, 'T_Y_TO_R_PARA', list, size=3, ctype=float, default=default)
    ERROR += check(data, 'T_Y_TO_R_DIST', str, default=default)
    ERROR += check(data, 'T_H_TO_R', float, default=default)
    ERROR += check(data, 'ASYMP_RATE', float, default=default)
    ERROR += check(data, 'PROP_TRANS_IN_E', float, default=default)
    ERROR += check(data, 'T_ONSET_TO_H', float, default=default)
    ERROR += check(data, 'T_H_TO_D', float, default=default)
    ERROR += check(data, 'H_RELATIVE_RISK_IN_HIGH', int, default=default)
    ERROR += check(data, 'D_RELATIVE_RISK_IN_HIGH', int, default=default)
    ERROR += check(data, 'HIGH_RISK_RATIO', dict, ctype=float, keys=age_keys[data['age_groups']], default=default)
    ERROR += check(data, 'H_FATALITY_RATIO', dict, ctype=float, keys=range_keys, default=default)
    ERROR += check(data, 'INFECTION_FATALITY_RATIO', dict, ctype=float, keys=range_keys, default=default)
    ERROR += check(data, 'OVERALL_H_RATIO', dict, ctype=float, keys=range_keys, default=default)
    return ERROR

def check(d, name, vtype, size=0, ctype=False, keys=False, default=False):
    ERROR = 0
    if default:
        if name not in d and name in default:
            dv = default[name]
            logger.warn("%s not present in provided config. Using default value: %s"%(name, str(dv)))
            d[name] = dv
    # ERROR += check_key(d, name, 'config')
    vtname = vtype.__name__
    cname = 'config.'+name
    if vtname in ('float','int','str'):
        ERROR += check_val(d, name, cname, vtype)
    elif vtname == 'list':
        ERROR += check_list(d[name], cname, list, size, ctype)
    elif vtname == 'dict':
        ERROR += check_dict(d[name], cname, dict, keys, ctype)
    else:
        raise ValueError("Unhandled type")
    return ERROR


def check_val(d, key, name, vtype):
    if vtype.__name__ == 'float' and isinstance(d[key], int):
        logger.info("Converting %s:%s from int to float"%(name, d[key]))
        d[key] = float(d[key])
        return 0
    v = d[key]
    return _check_inst(v, name, vtype)

def check_dict(v, name, vtype, keys, ctype):
    ERROR = 0
    if _check_inst(v, name, vtype): return 1
    for k in keys:
        ERROR += check_key(v, k, name, ctype)
    return ERROR

def check_list(v, name, vtype, size, ctype):
    if _check_inst(v, name, vtype): return 1
    if not len(v) == size:
        logger.error("Expected list of length %i for %s. Got %i: %s"%(size, name, len(v), str(v)))
        return 1
    ERROR = 0
    for i in range(size):
        ERROR += check_val(v, i, '%s[%i]'%(name, i), ctype)
    return ERROR

def check_key(d, key, name, vtype=False):
    if _check_inst(d, name, ()): return 1
    if not key in d:
        key_str = str(d.keys())
        logger.error("Expected key %s in dict %s. Got the following: %s"%(str(key), name, key_str))
        return 1
    if vtype:
        return check_val(d, key, name, vtype)
    return 0

def _check_inst(v, name, vtype):
    if not isinstance(v, vtype):
        logger.error("Expected %s for %s. Got: %s"%(vtype.__name__, name, type(v).__name__))
        return 1
    return 0
