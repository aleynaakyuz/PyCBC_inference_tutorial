#!/bin/bash

## This script creates the plot.

OMP_NUM_THREADS=1 

pycbc_inference_plot_posterior \
--input-file marginalized_model.hdf \
--output-file marginalized.png \
--parameters \
 mass1 mass2 inclination coa_phase \
--z-arg snr --plot-injection-parameters
