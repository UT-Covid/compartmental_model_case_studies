import random
from .builder import (TypeBuilder, IntBuilder, FloatBuilder, StrBuilder,
                      BoolBuilder, DictEnumBuilder)

__all__ = [
    'Boolean', 'Integer', 'Float', 'String', 'PositiveInt', 'PositiveFloat',
    'PositiveOrRandomInt', 'BooleanInt', 'List', 'ListInts', 'ListFloats',
    'ListStrings', 'ListThreeFloats', 'ListFiveFloats', 'ListNineFloats',
    'KeyValString', 'KeyValDict', 'KeyFloatDict', 'ListKeyFloats',
    'DictKeyFloats', 'StringDictEnum', 'Proportion', 'Rate', 'ListKeyStrings',
    'DictKeyStrings'
]


class Param(TypeBuilder):

    help = 'Undefined'

    def __init__(self, value):
        value = self.cast(value)
        if self.validate(value):
            self.value = value

    @classmethod
    def cast(cls, value):
        return value

    @classmethod
    def validate(cls, value):
        return True


class Boolean(Param, BoolBuilder):
    help = 'Boolean'

    @classmethod
    def cast(self, value):
        cval = False
        if isinstance(value, bool):
            cval = value
        elif isinstance(value, (float, int)):
            value = int(value)
            if value > 0:
                cval = True
            else:
                cval = False
        elif isinstance(value, str):
            if value.lower() in ('y', 'yes', 'true', '1'):
                cval = True
            else:
                cval = False
        return cval


class String(Param, StrBuilder):

    help = 'String'

    @classmethod
    def cast(cls, value):
        if isinstance(value, str):
            return value
        elif isinstance(value, (bool, int, float)):
            return str(value)
        else:
            return TypeError('Unable to cast to Str')

    @classmethod
    def validate(cls, value):
        super().validate(value)
        if not isinstance(value, str):
            raise ValueError('{} must be an <str>'.format(value))
        return True


class Float(Param, FloatBuilder):

    help = 'Float'

    @classmethod
    def cast(cls, value):
        if isinstance(value, float):
            return value
        elif isinstance(value, (int, str)):
            return float(value)
        else:
            return TypeError('Unable to cast to Float')

    @classmethod
    def validate(cls, value):
        super().validate(value)
        if not isinstance(value, float):
            raise ValueError('{} must be a <float>'.format(value))
        return True


class Integer(Param, IntBuilder):

    help = 'Integer'

    @classmethod
    def cast(cls, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, (str)):
            return int(value)
        else:
            return TypeError('Unable to cast to Integer')

    @classmethod
    def validate(cls, value):
        super().validate(value)
        if not isinstance(value, int):
            raise ValueError('{} must be an <int>'.format(value))
        return True


class PositiveInt(Integer):
    help = 'Positive Integer'

    @classmethod
    def validate(cls, value):
        val = super().cast(value)
        if val < 0:
            raise ValueError('{0} was not >= 0'.format(value))
        else:
            return True


class PositiveFloat(Float):
    help = 'Positive Float'

    @classmethod
    def validate(cls, value):
        val = super().cast(value)
        if val < 0:
            raise ValueError('{0} was not >= 0.0'.format(value))
        else:
            return True


class Rate(PositiveFloat):
    help = 'Rate'


class Proportion(PositiveFloat):
    help = 'Proportion (0-1)'

    @classmethod
    def validate(cls, value):
        super().validate(value)
        if value < 0.0 or value > 1.0:
            raise ValueError('{0} not between 0.0 and 1.0'.format(value))
        else:
            return True


class PositiveOrRandomInt(Integer):
    help = 'Random Positive Integer'
    # Generates a random int if passed a negative - useful for setting a random seed

    @classmethod
    def cast(cls, value):
        cvalue = super().cast(value)
        if cvalue < 0:
            cvalue = int(random.random() * 2147483647)
        return cvalue


class BooleanInt(Param, BoolBuilder):
    help = 'Boolean Integer'

    @classmethod
    def cast(cls, value):
        cval = 0
        if isinstance(value, bool):
            if value is True:
                cval = 1
            else:
                cval = 0
        elif isinstance(value, int):
            if value > 0:
                cval = 1
            else:
                cval = 0
        elif isinstance(value, str):
            if value.lower() in ('y', 'yes', 'true', '1'):
                cval = 1
            else:
                cval = 0
        return cval


class List(Param, StrBuilder):
    help = 'List'

    DELIMITER = ','
    MINLEN = None
    MAXLEN = None
    PTYPE = None

    # F, F, F, F, ...
    @classmethod
    def cast(cls, value, delim=None):
        if delim is None:
            delim = cls.DELIMITER

        try:
            if isinstance(value, str):
                # Split on commas
                temp = [i.strip() for i in value.split(delim)]
            elif isinstance(value, list):
                temp = value

            if cls.PTYPE is not None:
                c = cls.PTYPE
                temp2 = [c(i).value for i in temp]
                return temp2
            else:
                return temp

        except Exception:
            raise

    @classmethod
    def validate(cls, value):
        super().validate(value)

        if not isinstance(value, list):
            raise ValueError('{} must be a list'.format(value))

        if cls.MINLEN is not None:
            if len(value) < cls.MINLEN:
                raise ValueError('List must have at least {0} elements'.format(
                    cls.MINLEN))
        if cls.MAXLEN is not None:
            if len(value) > cls.MAXLEN:
                raise ValueError(
                    'List must have no more than {0} elements'.format(
                        cls.MAXLEN))
        return True


class ListFloats(List):
    PTYPE = Float


class ListInts(List):
    PTYPE = Integer


class ListStrings(List):
    PTYPE = String


class ListThreeFloats(ListFloats):
    MINLEN = 3
    MAXLEN = 3


class ListFiveFloats(ListFloats):
    MINLEN = 5
    MAXLEN = 5


class ListNineFloats(ListFloats):
    MINLEN = 9
    MAXLEN = 9


class KeyValString(String):
    help = 'Key:Value String'
    DELIMITER = ':'

    @classmethod
    def cast(cls, value):
        vals = str(value).split(cls.DELIMITER, 1)
        if not len(vals) in (2, 2):
            raise ValueError('Unable to find key:val pair')
        return value


class KeyValDict(KeyValString):

    help = 'Key:Value Dict'
    # Type for the Value in Key: Value
    PTYPE = None

    @classmethod
    def cast(cls, value):
        vals = str(value).split(cls.DELIMITER, 1)
        if not len(vals) in (2, 2):
            raise ValueError('Unable to find key:val pair')
        k = vals[0]
        if cls.PTYPE is None:
            v = vals[1]
        else:
            c = cls.PTYPE
            v = c(vals[1]).value

        return {k: v}

    @classmethod
    def validate(cls, value):
        if not isinstance(value, dict):
            raise TypeError('{0} must be a <dict>'.format(value))
        else:
            return True


class KeyFloatDict(KeyValDict):
    help = 'Key:Float Dict'
    PTYPE = Float


class ListKeyFloats(List):
    help = 'List of Key:Floats'
    PTYPE = KeyFloatDict


class ListKeyStrings(List):
    help = 'List of Key:Strings'
    PTYPE = KeyValDict


class DictKeyFloats(ListKeyFloats):
    @classmethod
    def cast(cls, value):
        vals = super().cast(value)
        d = {}
        for v in vals:
            d = {**d, **v}
        return d

    @classmethod
    def validate(cls, value):
        if not isinstance(value, dict):
            raise TypeError('{0} must be a <dict>'.format(value))
        else:
            return True


class DictKeyStrings(ListKeyStrings):
    @classmethod
    def cast(cls, value):
        vals = super().cast(value)
        d = {}
        for v in vals:
            d = {**d, **v}
        return d

    @classmethod
    def validate(cls, value):
        if not isinstance(value, dict):
            raise TypeError('{0} must be a <dict>'.format(value))
        else:
            return True


class StringDictEnum(DictEnumBuilder, String):
    # TODO - Figure out how to safely get choices from ARGDEFS.choices
    help = 'Enumerated String'
