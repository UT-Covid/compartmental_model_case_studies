__all__ = [
    'BoolBuilder', 'StrBuilder', 'IntBuilder', 'FloatBuilder',
    'StrEnumBuilder', 'DictEnumBuilder', 'FileBuilder', 'TapisProperties'
]


class TapisProperties:
    UNDEFINED = None
    INPUTS = 'inputs'
    PARAMETERS = 'parameters'

    @classmethod
    def tapis_properties(cls, properties):
        if properties is None:
            properties = {'inputs': [], 'parameters': []}
        if 'inputs' not in properties:
            properties['inputs'] = []
        if 'parameters' not in properties:
            properties['parameters'] = []
        return properties


class TypeBuilder(TapisProperties):
    # Implements argparse builder and Tapis app builder functions
    TAPIS_PROPERTY_TYPE = TapisProperties.UNDEFINED

    @classmethod
    def extend_desc_default(cls, desc, val):
        default = val.get('default', None)
        if default is not None:
            desc = desc + ' <Default: {0}>'.format(default)
        return desc

    @classmethod
    def build_desc(cls, key, val):
        desc = val.get('longdesc')
        if desc is None or desc == '':
            meta = val.get('meta', None)
            if meta is not None and meta != '':
                desc = 'Format: {}'.format(val.get('meta'))
        return desc

    @classmethod
    def extend_parser(cls, parser, key, val):
        return parser

    @classmethod
    def extend_tapis_properties(cls, key, val, properties=None):
        properties = TapisProperties.tapis_properties(properties)
        return properties

    @classmethod
    def extend_tapis_shellvars(cls, key, val, shellvars=None):
        if shellvars is None:
            shellvars = []
        shellvars.append(key)
        return shellvars


class BoolBuilder(TypeBuilder):

    TAPIS_PROPERTY_TYPE = TapisProperties.PARAMETERS

    @classmethod
    def extend_parser(cls, parser, key, val):
        phelp = '{0}'.format(val['desc'])
        if val.get('default', None) is False:
            action = 'store_true'
        else:
            action = 'store_false'
        parser.add_argument(val['arg'], dest=key, action=action, help=phelp)
        return parser

    @classmethod
    def extend_tapis_properties(cls, key, val, properties=None):
        properties = cls.tapis_properties(properties)
        param = {}
        param['id'] = key
        param['value'] = {
            'visible': val.get('visible', True),
            'required': val.get('required', False),
            'type': 'flag',
            'enquote': False,
            'validator': None,
            'default': val.get('default', False)
        }
        param['details'] = {
            'label': val['desc'],
            'description': val.get('longdesc', None),
            'showArgument': True,
            'repeatArgument': False,
            'argument': val['arg'] + ' '
        }
        param['semantics'] = {
            'minCardinality': 1,
            'maxCardinality': 1,
            'ontology': []
        }
        properties[cls.TAPIS_PROPERTY_TYPE].append(param)
        return properties


class StrBuilder(TypeBuilder):
    TAPIS_PROPERTY_TYPE = TapisProperties.PARAMETERS

    @classmethod
    def extend_parser(cls, parser, key, val):
        phelp = '{0} - {1}'.format(val['desc'], val['type'].help)
        phelp = cls.extend_desc_default(phelp, val)
        parser.add_argument(val['arg'],
                            dest=key,
                            default=val.get('default',
                                            val.get('example', None)),
                            metavar=val.get('meta', 'str'),
                            help=phelp)
        return parser

    @classmethod
    def extend_tapis_properties(cls, key, val, properties=None):
        properties = cls.tapis_properties(properties)
        param = {}
        param['id'] = key
        param['value'] = {
            'visible': val.get('visible', True),
            'required': val.get('required', False),
            'type': 'string',
            'enquote': True,
            'validator': None,
            'default': val.get('default', None)
        }
        param['details'] = {
            'label': val['desc'],
            'description': cls.build_desc(key, val),
            'showArgument': True,
            'repeatArgument': False,
            'argument': val['arg'] + ' '
        }
        param['semantics'] = {
            'minCardinality': 1,
            'maxCardinality': 1,
            'ontology': []
        }
        properties[cls.TAPIS_PROPERTY_TYPE].append(param)
        return properties


class FloatBuilder(StrBuilder):
    @classmethod
    def extend_tapis_properties(cls, key, val, properties=None):
        properties = cls.tapis_properties(properties)
        param = {}
        param['id'] = key
        param['value'] = {
            'visible': val.get('visible', True),
            'required': val.get('required', False),
            'type': 'number',
            'enquote': True,
            'validator': None,
            'default': val.get('default', None)
        }
        param['details'] = {
            'label': val['desc'],
            'description': cls.build_desc(key, val),
            'showArgument': True,
            'repeatArgument': False,
            'argument': val['arg'] + ' '
        }
        param['semantics'] = {
            'minCardinality': 1,
            'maxCardinality': 1,
            'ontology': []
        }
        properties[cls.TAPIS_PROPERTY_TYPE].append(param)
        return properties


class IntBuilder(StrBuilder):
    @classmethod
    def extend_tapis_properties(cls, key, val, properties=None):
        properties = cls.tapis_properties(properties)
        param = {}
        param['id'] = key
        param['value'] = {
            'visible': val.get('visible', True),
            'required': val.get('required', False),
            'type': 'number',
            'enquote': True,
            'validator': None,
            'default': val.get('default', None)
        }
        param['details'] = {
            'label': val['desc'],
            'description': cls.build_desc(key, val),
            'showArgument': True,
            'repeatArgument': False,
            'argument': val['arg'] + ' '
        }
        param['semantics'] = {
            'minCardinality': 1,
            'maxCardinality': 1,
            'ontology': []
        }
        properties[cls.TAPIS_PROPERTY_TYPE].append(param)
        return properties


class StrEnumBuilder(TypeBuilder):
    TAPIS_PROPERTY_TYPE = TapisProperties.PARAMETERS

    # Choices are list of enumeration values
    @classmethod
    def extend_parser(cls, parser, key, val):
        phelp = '{0}'.format(val['desc'])
        phelp = cls.extend_desc_default(phelp, val)
        choices = val.get('choices', [])
        metavar = None
        parser.add_argument(val['arg'],
                            dest=key,
                            default=val.get('default',
                                            val.get('example', None)),
                            metavar=metavar,
                            choices=choices,
                            help=phelp)
        return parser

    @classmethod
    def extend_tapis_properties(cls, key, val, properties=None):
        properties = cls.tapis_properties(properties)
        param = {}
        param['id'] = key
        param['value'] = {
            'visible': val.get('visible', True),
            'required': val.get('required', False),
            'type': 'enumeration',
            'enquote': False,
            'default': val.get('default', None),
            'enumValues': val['choices']
        }
        param['details'] = {
            'label': val['desc'],
            'description': cls.build_desc(key, val),
            'showArgument': True,
            'repeatArgument': False,
            'argument': val['arg'] + ' '
        }
        param['semantics'] = {
            'minCardinality': 1,
            'maxCardinality': 1,
            'ontology': []
        }
        properties[cls.TAPIS_PROPERTY_TYPE].append(param)
        return properties


class DictEnumBuilder(StrBuilder):
    TAPIS_PROPERTY_TYPE = TapisProperties.PARAMETERS

    # Choices are list of key/val dicts
    # key is enum and val is a description

    @classmethod
    def extend_parser(cls, parser, key, val):
        phelp = '{0}'.format(val['desc'])
        phelp = cls.extend_desc_default(phelp, val)
        choices = val.get('choices', [])
        choices = [list(c.keys())[0] for c in choices]
        metavar = None
        parser.add_argument(val['arg'],
                            dest=key,
                            default=val.get('default',
                                            val.get('example', None)),
                            metavar=metavar,
                            choices=choices,
                            help=phelp)
        return parser

    @classmethod
    def extend_tapis_properties(cls, key, val, properties=None):
        properties = cls.tapis_properties(properties)
        param = {}
        param['id'] = key
        param['value'] = {
            'visible': val.get('visible', True),
            'required': val.get('required', False),
            'type': 'enumeration',
            'enquote': False,
            'default': val.get('default', None),
            'enumValues': val['choices']
        }
        param['details'] = {
            'label': val['desc'],
            'description': cls.build_desc(key, val),
            'showArgument': True,
            'repeatArgument': False,
            'argument': val['arg'] + ' '
        }
        param['semantics'] = {
            'minCardinality': 1,
            'maxCardinality': 1,
            'ontology': []
        }
        properties[cls.TAPIS_PROPERTY_TYPE].append(param)
        return properties


class FileBuilder(StrBuilder):
    TAPIS_PROPERTY_TYPE = TapisProperties.INPUTS

    @classmethod
    def extend_tapis_properties(cls, key, val, properties=None):
        properties = cls.tapis_properties(properties)
        param = {}
        param['id'] = key
        param['value'] = {
            'visible': val.get('visible', True),
            'required': val.get('required', False),
            'validator': None,
            'default': val.get('example', None)
        }
        param['details'] = {
            'label': val['desc'],
            'description': cls.build_desc(key, val),
            'showArgument': True,
            'repeatArgument': False,
            'argument': val['arg'] + ' '
        }
        param['semantics'] = {
            'minCardinality': 1,
            'maxCardinality': 1,
            'ontology': []
        }
        properties[cls.TAPIS_PROPERTY_TYPE].append(param)
        return properties
