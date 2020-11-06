#!/usr/bin/env python

import os
from attrdict import AttrDict
import numpy as np
import datetime
import pickle
import yaml
from time import time
from . import utils
import numpy as np
import pandas as pd
import xarray as xr
from .dev_utils import base_decorator


class OutcomeHandler(object):
    """Base class for OutcomeHandler. The OutcomeHandler's purpose is
    to take a list of numpy arrays returned from simulate_one runs
    (one of these "outcomes" for each Scenario), and "compile" these
    outcomes into parameter space. The data structure used for
    representing parameter space is an xarray.DataArray. OutcomeHandler
    can also convert this N-dimensional DataArray to more familiar data
    structures, such as pandas DataFrame (to_dataframe method) or the
    legacy dictionary format (to_legacy_dict method).
    """

    # each of these params gets an axis, or dimension, in the
    # numpy array. In other words, these are the attributes that
    # change between different Scenarios, the ones that can uniquely
    # define a specific Scenario.
    DEFAULT_PARAM_DIMS = ('close_trigger', 'reopen_trigger', 'g_rate',
                          'c_reduction', 'beta0')

    def __init__(self, param_dims=None, verbosity=2):
        if param_dims is None:
            self.param_dims = self.DEFAULT_PARAM_DIMS
        else:
            self.param_dims = param_dims
        # validation
        assert utils.all_unique(self.param_dims)
        self._outcomes_flat_lst = list()
        self.scenarios = list()
        self.verbosity = verbosity

    def log(self, *args, level=1, **kwargs):
        if self.verbosity >= level:
            print(*args, **kwargs)

    # ------------------- Getters and setters --------------------------

    @property
    def outcomes_flat(self, force_recalc=False):
        if hasattr(self, '_outcomes_flat') and not force_recalc:
            return self._outcomes_flat
        else:
            return self._flat_to_da(self._outcomes_flat_lst)

    @property
    def n_sim(self):
        assert len(self.scenarios) > 0, "OutcomeHandler has no scenarios"
        assert all([s.get("NUM_SIM", None) for s in self.scenarios]), \
            "all Scenarios must have attr NUM_SIM"
        assert utils.all_same([s.get("NUM_SIM", None) for s in self.scenarios]), \
            "attribute NUM_SIM must be the same for all Scenarios"
        return self.scenarios[0]['NUM_SIM']

    @property
    def coords(self):
        self._precompile_check()
        return self._get_param_coords()

    @property
    def outcomes(self, force_recalc=False):
        if hasattr(self, '_outcomes') and not force_recalc:
            return self._outcomes
        else:
            return self._compile()

    # ------------------ Load outcomes to flat list --------------------

    def add_outcome(self, scenario, outcome, dims, coords=None):
        """"""
        # TODO: validate that shape of array matches dims
        # TODO: support lists and other sequences
        assert isinstance(outcome, np.ndarray)
        if isinstance(dims, str):
            dims = list([dims])
        if len(dims) != len(outcome.shape):
            raise ValueError("len(dims) == {} but ".format(len(dims)) +
                             "len(outcome.shape) == {}. ".format(len(outcome.shape)) +
                             "Must be same length. Shape of passed outcome " +
                             "is : {}".format(outcome.shape))
        try:
            self._add_outcome_arr(scenario, outcome, dims, coords)
        except ValueError as val_err:
            print('dims is probably not consistent with array shape. ' +
                  'len(dims) should equal len(shape)')
            raise val_err

    def _add_outcome_arr(self, scenario, outcome, dims, coords=None):
        """"""
        assert len(self._outcomes_flat_lst) == len(self.scenarios)
        da_kwargs = dict({'dims': dims})
        if coords is not None:
            da_kwargs['coords'] = coords
        outcome_da = xr.DataArray(outcome, **da_kwargs)
        self._outcomes_flat_lst.append(outcome_da)
        self.scenarios.append(scenario)

    # ----------- Compile flat DataArray to N-D DataArray --------------

    def _flat_to_da(self, flat_lst):
        """Given `flat_lst`, which should be a list of
        outcomes (xr.DataArray instances that all have the same dims),
        stack along a new axis 'task_index': the integer task_index of the
        simulation outcome. Note that task_index is different from the
        scenario_index, succinctly `index`. We expect (actually, assert)
        that NUM_SIM * len(index) == task_index
        """
        # TODO: we dont need to manually assemble dims and coords here
        # concat does that already

        # type assertions
        assert flat_lst and isinstance(flat_lst, list)
        assert all([isinstance(da, xr.DataArray) for da in flat_lst])
        # get list of dims and coords for each outcome DataArray
        flat_dims = [da.dims for da in flat_lst]
        flat_coords = [dict(da.coords) for da in flat_lst]
        # get the dims and coords of just the first outcome DataArray
        first_dims = flat_dims[0]
        first_coords = flat_coords[0]
        # make sure dims and coords for all other outcome
        # DataArrays are equal
        # start = time()
        try:
            for d, c in zip(flat_dims, flat_coords):
                utils.assert_objects_equal(first_dims, d)
                utils.assert_objects_equal(first_coords, c)
        except ValueError as val_err:
            self.log("dims: ", d, level=0)
            self.log("coords: ", c, level=0)
            raise val_err
        # print("dim/coord validation took {:0.2f} s".format(time() - start))
        # avoid edge case
        assert 'task_index' not in first_dims
        # return as stacked DataArray
        da = xr.concat(flat_lst, 'task_index')
        # get integer index (pandas.RangeIndex) for all dims without coords
        # notably, this includes task_index, time, age group, risk group
        for dim_without_coords in da.dims:
            idx = da.get_index(dim_without_coords)
            da.coords[dim_without_coords] = idx
        self._outcomes_flat = da
        return da

    def _get_param_coords(self, dim):
        """Given a dimension `dim`, return the list of unique Scenario[dim]
        values for each Scenario.
        """
        return list(set([s[dim] for s in self.scenarios]))

    def _get_unique_scenarios(self):
        """Returns list of unique Scenarios. Unique is defined as
        having a unique combination of attrs whose names are stored in
        self.param_dims. Returns what you would want set(scenarios_list)
        to do.
        """
        raise DeprecationWarning()
        use_keys = self.param_dims
        assert self.scenarios
        first = self.scenarios[0]
        unique = list()
        for scenario in self.scenarios:
            if not utils.are_objects_equal(first, scenario):
                unique.append(scenario)

    def _get_expected_shape(self, dims, coords):
        """"""
        return tuple([len(coords.get(dim, list())) for dim in dims])

    def _get_outcomes_nan(self):
        """"""
        # copy outcomes_flat. Ends up calling _flat_to_da
        flat_da = self.outcomes_flat
        # start with the dims and coords from the flat DataArray
        dims = list(flat_da.dims)
        coords = dict(flat_da.coords)
        # remove task index. was useful in the flattened array
        # but not here
        dims.remove('task_index')
        coords.pop('task_index', None)
        # add replicate and (scenario) index axes first, with coords
        dims.insert(0, 'replicate')
        # dims.insert(0, 'index')
        coords['replicate'] = list(range(self.n_sim))
        # n_unique_scenarios = len([self._get_unique_scenarios()])
        # coords['index'] = list(range(num_unique_scenarios))
        # add each parameter dimension, starting with the
        # highest dims at the end of the self.params_dims list
        for param_dim in reversed(self.param_dims):
            # insert dimension at axis=0
            dims.insert(0, param_dim)
            # get coords for the added dimension. coords are a list of
            # the unique values of the dim across all Scenarios
            coords[param_dim] = self._get_param_coords(dim=param_dim)
        # get the expected shape of the array, given coordinates
        shape = self._get_expected_shape(dims, coords)
        try:
            outcomes_nan = xr.DataArray(np.full(shape, np.nan, dtype=float),
                                        dims=dims, coords=coords)
        except Exception as err:
            self.log("shape: ", shape)
            self.log("dims: ", dims)
            self.log("coords: ", coords)
            self.log("flat_da: ", flat_da)
            self.log("flat_da.shape: ", flat_da.shape)
            self.log("flat_da.dims: ", flat_da.dims)
            self.log("flat_da.coords: ", flat_da.coords)
            raise err
        return outcomes_nan

    def _compile(self):
        """Compiles flat integer-indexed outcomes in self.outcomes_flat
        to an N-D xarray.DataArray, where N is the number of parameters
        that change between Scenarios.
        """
        # TODO: load Scenario as dict to DataArray metadata
        outcomes = self._get_outcomes_nan()
        # WARNING: current assumption is that replicates of the same
        # scenario were added via adjacent calls to add_outcome.
        # TODO
        replicate_ct = 0
        # populate empty nan outcomes DataArray with the outcome,
        # at a point in matrix space specified by the Scenario attributes.
        # start1 = time()
        for i in range(len(self.scenarios)):
            scenario = self.scenarios[i]
            outcome = self.outcomes_flat[i]
            # get the location in parameter space that we want to change
            point = dict({dim: scenario[dim] for dim in self.param_dims})
            # if replicate at point is already populated,
            # increment replicate and try again. Error if
            # replicate >= self.n_sim
            # TODO: we assume here that replicates are adjacent
            # in self.outcomes_flat
            point['replicate'] = i % self.n_sim
            # point['index'] = i
            # check to make sure this point in space is not occupied
            # (AKA assert is is nan, as we initialized the array)
            is_nan = bool(np.all(np.isnan(outcomes.loc[point])))
            if not is_nan:
                raise ValueError("OutcomeHandler._compile: matrix point " +
                                 "{} already contains at ".format(point) +
                                 "least one value that is not NaN. " +
                                 "Continuing with this operation would " +
                                 "overwrite existing data.")
            # start2 = time()
            try:
                outcomes.loc[point] = outcome
            except Exception as err:
                self.log("point: ", point)
                self.log("outcomes: ", outcomes)
                raise err
            # print("iterating over scenarios took {:0.2f} s".format(time() - start2))
        # print("iterating over scenarios took {:0.2f} s".format(time() - start1))
        self._outcomes = outcomes
        return outcomes

    # ---------------- Common slicing/output formats -------------------

    def to_slice(self, how=None):
        raise NotImplemented()

    def to_pickle(self, out_fp):
        """Writes compiled xarray.DataArray as a pickle file to
        output filepath `out_fp`.
        """
        da = self.outcomes
        print("Writing outcomes as pickled xarray.DataArray to: {}".format(out_fp))
        with open(out_fp, 'wb') as f:
            pickle.dump(da, f)

    def to_dataframe(self, out_fp):
        """Writes compiled xarray.DataArray as a pandas DataFrame to
        output filepath `out_fp`.
        """
        da = self.outcomes
        df = da.to_dataframe(name='value').reset_index()
        print("Writing xarray to pandas DataFrame at: {}".format(out_fp))
        df.to_csv(out_fp)

    def to_legacy_dict(self):
        legacy = dict()
        # TODO
        raise NotImplementedError("cannot yet generate legacy dictionary")
        # Ensure that the every attribute in consistent_attrs
        # is the same between all Scenarios
        outcomes = self.outcomes
        dims = outcomes.dims
        coords = outcomes.coords
        consistent_attrs = ('CITY', 'time_begin_sim', 'beta0')
        all_s = self.scenarios
        first_s = all_s[0]
        for attr in consistent_attrs:
            assert utils.all_same([s.get(attr, None) for s in self.scenarios])

        # pull some useful Scenario attrs that are consistent between
        # Scenarios
        CITY = first_s['CITY']
        n_age = first_s['n_age']
        beta0 = first_s['beta0'] * np.ones(np.arange(n_age))
        time_begin_sim = first_s['time_begin_sim']
        Para = first_s['Para']
        metro_pop = first_s['metro_pop']
        CLOSE_TRIGGER_LIST = list(set([
            s.close_trigger for s in all_s]))
        REOPEN_TRIGGER_LIST = list(set([
            s.reopen_trigger for s in all_s]))

        for g_rate_da in coords['g_rate']:
            g_rate = str(g_rate_da.values)
            legacy[g_rate] = dict()
            # fill top level dict
            legacy[g_rate]['CITY'] = beta0
            legacy[g_rate]['CITY'] = CITY
            legacy[g_rate]['time_begin_sim'] = time_begin_sim
            legacy[g_rate]['CLOSE_TRIGGER_LIST'] = CLOSE_TRIGGER_LIST
            legacy[g_rate]['REOPEN_TRIGGER_LIST'] = REOPEN_TRIGGER_LIST
            legacy[g_rate]['Para'] = Para
            legacy[g_rate]['metro_pop'] = metro_pop
            for c_red_da in list(coords['c_reduction']):
                c_red = float(c_red_da.values)
                print("c_red: ", c_red)
                legacy[g_rate][c_red] = dict()
                for c_trig_da in list(coords['close_trigger']):
                    for r_trig_da in list(coords['reopen_trigger']):
                        c_trig = str(c_trig_da.values)
                        r_trig = str(r_trig_da.values)
                        print("c_trig / r_trig: ", c_trig + "/" + r_trig)
                        legacy[g_rate][c_red][c_trig + "/" + r_trig] = dict()



        # legacy['GROWTH_RATE'] =
        # legacy['CONTACT_REDUCTION'] =
        # legacy['beta0'] =
        # legacy['Para'] =
        # legacy['metro_pop'] =
        # legacy['time_begin_sim'] =
        # legacy['time_begin_sim'] =
        # legacy['time_begin_sim'] =


        return legacy

        # result_stack = list()
        # result_dict = {
        #     # params that are consistent between scenarios
        #     # 'CITY': CITY,
        #     # 'time_begin_sim': time_begin_sim,
        # CLOSE_TRIGGER_LIST same as below
        # REOPEN_TRIGGER_LIST = list(set([r_trigger for r in sc]))
        #
        #     # params that are unique to each scenario
        #     # 'GROWTH_RATE': g_rate,
        #     # 'CONTACT_REDUCTION': CONTACT_REDUCTION,
        #     # 'beta0': beta0,
        #     # 'Para': Para,
        #     # 'metro_pop': metro_pop,
        #     # close trigger
        #     # reopen trigger
        #
        #     # results
        #     # 'E2Iy_dict': E2Iy_dict,
        #     # 'E2I_dict': E2I_dict,
        #     # 'Ia_dict': Ia_dict,
        #     # 'Iy_dict': Iy_dict,
        #     # 'Ih_dict': Ih_dict,
        #     # 'R_dict': R_dict,
        #     # 'Iy2Ih_dict': Iy2Ih_dict,
        #     # 'Ih2D_dict': Ih2D_dict,
        #     # 'CloseDate_dict': CloseDate_dict,
        #     # 'ReopenDate_dict': ReopenDate_dict,
        #     # 'R0_baseline': R0_baseline
        # }
