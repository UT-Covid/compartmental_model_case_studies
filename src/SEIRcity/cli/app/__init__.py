import json
import os
from jinja2 import Template

HERE = os.path.dirname(os.path.abspath(__file__))

LABEL = 'TX Cities COVID-19 Model (Python)'
DESCRIPTION = 'Parameterizable SEIR model of COVID-19 supporting 22 Texas metropolitan areas'
APPID = 'seir-city-covid19'
APPVERSION = '1.1.1'


def build_app_def(app_properties):
    source = open(os.path.join(HERE, 'template.json.j2'), 'r').read()
    var = {}
    var['inputs'] = json.dumps(app_properties['inputs'])
    var['parameters'] = json.dumps(app_properties['parameters'])
    var['label'] = LABEL
    var['description'] = DESCRIPTION
    var['appid'] = APPID
    var['appversion'] = APPVERSION
    template = Template(source)
    rendered = template.render(**var)
    return json.loads(rendered)
