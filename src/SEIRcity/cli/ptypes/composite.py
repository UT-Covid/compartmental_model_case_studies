from .param import (Param, String, Float, Integer, ListStrings, ListFloats,
                    ListInts)
EPI_DEMOGRAPHIC_COHORTS = 5
EPI_SCENARIOS = 7

__all__ = ['MatlabIntDate', 'ListMatlabIntDates', 'Triangular', 'IntDateRange']


class Triangular(ListFloats):
    help = 'Triangular Distribution'
    MINLEN = 3
    MAXLEN = 3


class MatlabIntDate(Integer):
    # YYYYMMDD expressed as an integer
    help = 'Integer Date'

    @classmethod
    def validate(cls, value):
        # TODO - validate that the int represents a realistic date
        if len(str(value)) != 8:
            raise ValueError('{0} must be 8 digits in length'.format(value))
        return True


class ListMatlabIntDates(ListInts):
    help = 'List of Integer Dates'
    MINLEN = 1
    PTYPE = MatlabIntDate


class IntDateRange(ListMatlabIntDates):
    help = 'Start / End Date'
    MINLEN = 2
    MAXLEN = 3


class MatlabTriangular(String):

    help = 'Matlab Triangular'

    @classmethod
    def validate(cls, value):
        super().validate(value)
        if not value.startswith('Triangular'):
            raise ValueError(
                '{} does not appear to be a Triangular'.format(value))
        return True


class Demographics(ListFloats):

    help = 'Comma-separated Demographic Variables (Float)'

    # D,D,D,D, ...
    @classmethod
    def validate(cls, value):
        super().validate(value)
        if len(value) != EPI_DEMOGRAPHIC_COHORTS:
            raise ValueError('{} must contain {} values'.format(
                value, EPI_DEMOGRAPHIC_COHORTS))
        return True


class Scenarios(ListFloats):

    help = 'Comma-separated Scenario Variables (Float)'

    # S,S,S,S, ...
    @classmethod
    def validate(cls, value):
        super().validate(value)
        if len(value) != EPI_SCENARIOS:
            raise ValueError('{} must contain {} values'.format(
                value, EPI_SCENARIOS))
        return True


class DemographicsString(Demographics):
    help = 'Stringified Comma-separated Demographic Variables (Float)'

    @classmethod
    def cast(cls, value):
        value = super().cast(value)
        value = ','.join([str(v) for v in value])
        return value

    @classmethod
    def validate(cls, value):
        tval = ListFloats(value).value
        if len(tval) != EPI_DEMOGRAPHIC_COHORTS:
            raise ValueError('{} must contain {} values'.format(
                value, EPI_DEMOGRAPHIC_COHORTS))
        else:
            return True


class DemographicsStringByScenarios(Param):
    # D,D,D,D,D; D,D,D,D,D; ...
    help = 'Semicolon-separated Scenario Variables (Comma-separated Demographics Variables)'

    @classmethod
    def cast(cls, value, delim=';'):
        try:
            if isinstance(value, str):
                # Split on commas
                temp = [i.strip() for i in value.split(delim)]
            elif isinstance(value, list):
                temp = value
            temp2 = [DemographicsString(i).value for i in temp]
            return temp2
        except Exception:
            raise TypeError(
                'Unable to cast {0} to DemographicsStringByScenarios'.format(
                    value))

    @classmethod
    def validate(cls, value):
        super().validate(value)
        # type
        if not isinstance(value, list):
            raise TypeError('Must be a list')
        # length
        if len(value) != EPI_SCENARIOS:
            raise ValueError('{} must contain {} values'.format(
                value, EPI_SCENARIOS))
        # interior contents
        for v in value:
            Demographics(v)
        return True
