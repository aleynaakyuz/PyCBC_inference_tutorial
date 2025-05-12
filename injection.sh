#!/bin/bash

## This script created the injection

OMP_NUM_THREADS=1

pycbc_create_injections --verbose --config-files injection.ini --ninjections 1 --seed 10 --output-file injection.hdf --force