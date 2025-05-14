#!/bin/bash

## This script creates the plot.

OMP_NUM_THREADS=1 

pycbc_inference_plot_posterior \
--input-file demarg.hdf \
--output-file demarg.png \
--parameters \
 mchirp q ra dec tc inclination coa_phase polarization distance \
--z-arg snr --plot-injection-parameters