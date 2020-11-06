#!/usr/bin/env python
import os
import sys

# singularity clobbers the PYTHONPATH
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SEIR_HOME = os.path.join(HERE, "..")
SEIR_HOME = os.environ.get('SEIR_HOME', DEFAULT_SEIR_HOME)
sys.path.append(os.path.join(SEIR_HOME, "src"))
