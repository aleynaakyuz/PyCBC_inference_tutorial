#!/usr/bin/env

python BBH_work.py --detectors CE40 CE20 --injections /home/aakyuz/tutorial/injections/* \
 --workflow-name test --config-files /home/aakyuz/tutorial/workflow.ini \
 --inference-config /home/aakyuz/tutorial/margtime.ini \
 --output-dir /home/aakyuz/tutorial/workflow_outputs --submit-now \
 --psd-paths /home/aakyuz/runs7/ce_strain/cosmic_explorer_strain.txt /home/aakyuz/runs7/ce_strain/cosmic_explorer_20km_strain.txt
