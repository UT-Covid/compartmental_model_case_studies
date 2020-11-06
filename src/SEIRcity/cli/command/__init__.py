CONFIG = 'python3 -B -m src.SEIRcity.cli'
CONFIG_CMD = CONFIG + ' -O config.yml'
RUN_CMD = 'python3 -B -m src.SEIRcity --threads 8 --out-fp outputs/output.pckl --config-yaml config.yml'
