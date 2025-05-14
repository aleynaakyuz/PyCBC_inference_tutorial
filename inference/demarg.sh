#!/bin/bash

## This script performs demarginalization.

OMP_NUM_THREADS=1 

export PYCBC_DETECTOR_CONFIG=detectors.ini ## This adds the detector custom detectors.

pycbc_inference_model_stats \
--input-file marginalized_model.hdf \
--output-file demarg.hdf \
--nprocesses 1 \
--reconstruct-parameters \
--force \
--verbose