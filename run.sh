#!/bin/bash

## This script runs the sampler.

OMP_NUM_THREADS=1

export PYCBC_DETECTOR_CONFIG=detectors.ini ## This adds the detector custom detectors.

pycbc_inference \
--config-file config.ini \
--nprocesses 6 \
--processing-scheme cpu \
--output-file marginalized_model.hdf \
--seed 0 \
--force \
--verbose