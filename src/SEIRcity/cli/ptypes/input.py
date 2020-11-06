import os
from .param import String
from .builder import (FileBuilder)

__all__ = ['File', 'CSVFile', 'ExcelFile']


class Input(FileBuilder, String):
    help = 'Input'
    check_exists = False

    @classmethod
    def cast(cls, value):
        value = super().cast(value)
        for scheme in ('http://', 'https:', 'ftp://', 'agave://'):
            if value.startswith(scheme):
                if value.endswith('/'):
                    value = value.split('/')[-2]
                else:
                    value = value.split('/')[-1]
                break
        return value

    @classmethod
    def validate(cls, value):
        value = cls.cast(value)
        if cls.check_exists:
            if os.path.exists(value):
                return True
            else:
                raise FileNotFoundError('{0} was not found'.format(value))
        else:
            return True


class File(Input):
    help = 'File'


class CSVFile(Input):
    help = 'CSV File'
    check_exists = False

    @classmethod
    def validate(cls, value):
        super().validate(value)
        if value.lower().endswith('.csv') or value.lower().endswith('.csv'):
            return True
        else:
            raise ValueError('{0} must be an CSV file (.csv)'.format(value))


class ExcelFile(Input):
    help = 'Excel File'
    check_exists = False

    @classmethod
    def validate(cls, value):
        super().validate(value)
        if value.lower().endswith('.xls') or value.lower().endswith('.xlsx'):
            return True
        else:
            raise ValueError(
                '{0} must be an Excel file (.xls, xlsx)'.format(value))
