import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
SEIR_HOME = os.path.dirname(PARENT)
sys.path.append(SEIR_HOME)


from .fitting_workflow import fitting_workflow
