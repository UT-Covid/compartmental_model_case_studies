"""Build argparse.args and Tapis app.params

First attempt at a generalized way to build argparse and 
Tapis app parameters from a shared codebase.
"""

# TODO - implement an ArgDef class that provides some validation and utility


class VarsBuilder(object):
    TOPIC = 'General'
    ARGDEFS = {}

    @classmethod
    def extend_parser(cls, parser):
        """Helper: Automatically populates an argparse Parser
        """
        g = parser.add_argument_group('{0}'.format(cls.TOPIC))
        for key, val in cls.ARGDEFS.items():
            g = val.get('type').extend_parser(g, key, val)
        return parser

    @classmethod
    def build_tapis_properties(cls, properties=None):
        for key, val in cls.ARGDEFS.items():
            properties = val.get('type').extend_tapis_properties(
                key, val, properties)
        return properties

    @classmethod
    def extend_tapis_shellvars(cls, shellvars=None):
        if shellvars is None:
            shellvars = []
        for key, val in cls.ARGDEFS.items():
            shellvars = val.get('type').extend_tapis_shellvars(
                key, val, shellvars)
        return shellvars

    @classmethod
    def param_class(cls, name):
        return cls.ARGDEFS[name]['type']

    @classmethod
    def param_get(cls, name, value):
        # Cast and validate value
        cl = cls.param_class(name)
        val = cl(value).value
        # NOTE - I don't know why I was forcing a list here
        # if not isinstance(val, list):
        #     val = [val]
        return val

    @classmethod
    def to_dict(cls, parsed_args):
        data = {}
        for pname, _ in cls.ARGDEFS.items():
            passed_val = getattr(parsed_args, pname, None)
            if passed_val is not None:
                data[pname] = cls.param_get(pname, passed_val)
            else:
                data[pname] = None
        return data

    @classmethod
    def extend_dict(cls, vars_dict):
        """Extend an argparse-derived variables dict with dynamically-computed values
        """
        return vars_dict
