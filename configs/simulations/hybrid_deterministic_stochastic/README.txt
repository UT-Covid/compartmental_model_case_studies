Hybrid runs need two steps:

1. Deterministic run: this runs a deterministic model to get estimates for compartment population sizes in the early epidemic. The deterministic run will always produce an epidemic under the parameters fitted to observed epidemics.

2. Stochastic run: this will take the output of the deterministic run as its initial condition input. A method in the stochastic workflow will identify the time point in the deterministic run and identify the time point at which a threshold number of cases is met. The population sizes in each compartment at that time will be used to initialize stochastic simulations.

Houston and Beaumont therefore each have two configuration files, one for each part of the workflow.

PLEASE NOTE that the results of deterministic runs are not distributed with this code. If you would like to reproduce the results from our paper, please run the deterministic configurations and update the stochastic configuration "I0" entry with the path to your deterministic results.

