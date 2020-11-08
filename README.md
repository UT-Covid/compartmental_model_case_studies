# COVID-19 SEIR Single-City Model

## Overview

This repository accompanies the manuscript "Early COVID-19 pandemic modeling: Three compartmental model case studies from Texas, USA".

## Contact

Please contact Kelly Pierce (kpierce -at- tacc.utexas.edu) or Ethan Ho (eho -at- tacc.utexas.edu) for questions or support.

This software is not actively maintained and is presented to accompany our manuscript for record keeping purposes. **If you wish to model COVID-19 transmission dynamics** please reach out to us -- we can share more updated models upon request.

## Reproducibility

All paths are relative to the `compartmental_model_case_studies` directory, or should be user-specified when reproducing results.

### Austin Analysis

1. Estimate the transmission rate and transmission rate reduction

	The following bash script runs a single call to `python -m src.SEIRcity` that jointly estimates baseline transmission rate and transmission rate reduction after implementation of social distancing measures. The resulting parameters are written to a `csv` file. The header `beta0` indicates the baseline transmission rate; the header `c_reduction` indicates the transmission rate reduction.
	
	```bash
	python3 -m src.SEIRcity --config-yaml configs/transmission_rate_and_reduction/austin_fit_trans_rate_and_reduction.yaml --out-fp </path/to/output.csv>
	```

2. Simulate the healthcare burden under the estimated parameters

	```bash
	python3 -m src.SEIRcity --config-yaml configs/simulations/stochastic/Austin_transmission_reduction_0.94_config.yaml --out-fp </path/to/sim_out.pckl>
	```

### Houston Analysis

1. Estimate the epidemic emergence date and transmission rate reduction

	The following bash script runs a set of calls to `python -m src.SEIRcity` for different potential epidemic emergence dates, fits the corresponding transmission rate reduction assuming that emergence date, and report the fitted transmission rate reduction and its associated root mean squared error to a `csv` file.
	
	```bash
	./fit_start_houston.sh
	```
	
	The output files are saved in `outputs/houston_fit/` and are manually reviewed to identify the transmission rate reduction corresponding to the lowest `final_rmsd`.
	
	For Houston, our estimated transmission rate reduction was almost 99.99% (repeating) for the best fitting epidemic emergence date of Feburary 10, 2020. We truncated this value for our projections in this manuscript to 99%.
	
2. Generate a deterministic run under the estimated parameters

	```bash
	python3 -m src.SEIRcity --config-yaml configs/simulations/hybrid_deterministic_stochastic/deterministic_houston_transmission_reduction_0.99_config.yaml --out-fp </path/to/determ_out.pckl>
	```
	
3. Simulate the healthcare burden under estimated parameters using the deterministic result to set initial conditions.

	First, edit `configs/simulations/hybrid_deterministic_stochastic/stochastic_houston_transmission_reduction_0.99_config.yaml` to include your `/path/to/determ_out.pckl` under the `I0` heading.
	
	Next, run the following command to produce the simulations:

	```bash
	python3 -m src.SEIRcity --config-yaml configs/simulations/hybrid_deterministic_stochastic/stochastic_houston_transmission_reduction_0.99_config.yaml --out-fp </path/to/sim_out.pckl>
	```

### Beaumont Analysis

1. Estimate the epidemic emergence date and transmission rate reduction

	The following bash script runs a set of calls to `python -m src.SEIRcity` for different potential epidemic emergence dates, fits the corresponding transmission rate reduction assuming that emergence date, and report the fitted transmission rate reduction and its associated root mean squared error to a `csv` file.
	
	```bash
	./fit_start_beaumont.sh
	```
	
	The output files are saved in `outputs/beaumont_fit/` and are manually reviewed to identify the transmission rate reduction corresponding to the lowest `final_rmsd`.
	
	For Beaumont, our estimated transmission rate reduction was almost 85% for the best fitting epidemic emergence date of February 27, 2020. 	
2. Generate a deterministic run under the estimated parameters

	```bash
	python3 -m src.SEIRcity --config-yaml configs/simulations/hybrid_deterministic_stochastic/deterministic_houston_transmission_reduction_0.99_config.yaml --out-fp </path/to/determ_out.pckl>
	```
	
3. Simulate the healthcare burden under estimated parameters using the deterministic result to set initial conditions

	First, edit `configs/simulations/hybrid_deterministic_stochastic/stochastic_beaumont_transmission_reduction_0.85_config.yaml` to include your `/path/to/determ_out.pckl` under the `I0` heading.
	
	Next, run the following command to produce the simulations:

	```bash
	python3 -m src.SEIRcity --config-yaml configs/simulations/hybrid_deterministic_stochastic/stochastic_beaumont_transmission_reduction_0.85_config.yaml --out-fp </path/to/sim_out.pckl>
	```
*Note: The [Austin](https://cid.utexas.edu/sites/default/files/cid/files/covid-19_analysis_for_austin_april_20_2020.pdf?m=1587474298), [Houston](https://sites.cns.utexas.edu/sites/default/files/cid/files/houston_covid-19_healthcare_demand_projections.pdf?m=1588108988), and [Beaumont](https://sites.cns.utexas.edu/sites/default/files/cid/files/beaumont_healthcare_demand_projections.pdf?m=1588251994) reports referenced in our paper all report the baseline Austin transmission rate as 0.035. The model parameterization in the configurations uses more significant figures. The Austin configuration files use a transmission rate of 0.035107; the Houston and Beaumont configurations, which borrow the Austin transmission rate, use an updated transmission rate of 0.0351655. This value takes into account new Austin hospital census data available after the Austin report was released.*

### Inventory of outputs included in this repository.

Full simulation outputs are too large to upload to GitHub repositories, but we have included the smaller output files in the subdirectory `outputs/reproducibility/`:

- `houston_fit/` and `beaumont_fit/` contain the estimated transmission rate reduction and epidemic emergence date data. Dates are encoded in file names; file contents report parameter estimates (heading `c_reduction` for contact reduction, synonymous in our model framework with transmission rate reduction) and error (heading `final_rmsd`).

- 'austin_fit/' contains a single `csv` file with the estimated transmission rate (heading `beta0`) and transmission rate reduction (heading `c_reduction`).

We also include a Jupyter Notebook, Final_CiSE_Images.ipynb, in the top level of the repository. This notebook requires the large output files that are not included in the repository, but demonstrates how those data were processed. Output files for the simulations represented are available upon request.

## Quick Start

This software runs a pre-set compartmental model with user specified parameters. A successful run of the model will produce either a `csv` of fitted transmission-related parameters, or a pickled array object containing the compartment populations for each time step of a model run.

1. Install Python package dependencies:

```bash
pip install -r requirements.txt
```

2. Set simulation parameters by writing a configuration YAML file. Start by copying and modifying one of the files in `configs/` and editing in your favorite text editor.

There are also example config YAML files for [simulating multiple scenarios, each with multiple replicates][6], and [fitting the SEIR model to existing data][7] (such as hospitalization data) in order to obtain a fitted value for `beta0` (transmission coefficient).

3. Run the `SEIRcity` module as an executable:

```bash
python3 -m src.SEIRcity --config-yaml ./inputs/my_config.yaml --out-fp ./outputs/my_xarray_dataarray.pckl --threads 48
```

## Installation

Running SEIR-city requires [Python 3](https://www.python.org/). SEIR-city officially supports Python versions 3.6 and newer.

### 1. Install Python package dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up environment

#### Option A. Install in [Poetry](https://python-poetry.org/) Virtual Environment

```bash
poetry install
```

#### Option B. Build [Docker](https://www.docker.com/) Image

```bash
docker build --build-arg REQUIREMENTS=requirements.txt -t covid-seir:1.1.0 -f Dockerfile .
# or more succinctly...
IMAGE_ORG=$MY_DOCKERHUB_ORG make image
```

#### Option C. Install in Python `virtualenv`

```bash
python3 -m virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
