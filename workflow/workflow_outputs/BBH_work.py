#!/usr/bin/env

import h5py
import numpy as np
import pycbc.workflow as wf
import pycbc
import argparse, os
import configparser
from pycbc.workflow.configuration import WorkflowConfigParser
import pycbc.workflow.pegasus_workflow as wdax
from pycbc.conversions import mchirp_from_mass1_mass2, q_from_mass1_mass2
from pycbc.psd.read import from_txt
from ce_sens.utils import calculate_snr, get_parameter_list
from pycbc.waveform import get_waveform_filter_length_in_time

parser = argparse.ArgumentParser()
parser.add_argument("--injections", nargs='*')
parser.add_argument("--inference-config")
parser.add_argument("--detectors", nargs='*')
parser.add_argument("--psd-paths", nargs='*')

pycbc.init_logging(True)
wf.add_workflow_command_line_group(parser)
wf.add_workflow_settings_cli(parser)
opts = parser.parse_args()

workflow = wf.Workflow(opts, "gw")
wf.makedir(opts.output_dir)
infhand = wf.resolve_url_to_file(opts.inference_config)

def get_net_snr(params):
	df = 0.001
	net_snr_sq = 0
	for k, det in enumerate(opts.detectors):
		psd = from_txt(opts.psd_paths[k], low_freq_cutoff=5.1, length=int(4000/df), delta_f=df)
		snr = calculate_snr(det, psd, params, 5.1)
		net_snr_sq += snr**2
	return np.sqrt(net_snr_sq)

inference_exe = wf.Executable(workflow.cp, "inference", ifos=workflow.ifos,
                              out_dir=opts.output_dir)

demarg_exe = wf.Executable(workflow.cp, "demarg", ifos=workflow.ifos,
                              out_dir=opts.output_dir)

plot_exe = wf.Executable(workflow.cp, "plot", ifos=workflow.ifos,
                              out_dir=opts.output_dir)

df = 0.001
for i, inj in enumerate(opts.injections):
	params2 = h5py.File(inj)
	params = {key:params2[key][:][0] for key in list(params2.keys())}
	att = {key:params2.attrs[key] for key in list(params2.attrs.keys())}
	params.update(att)

	params.update({'delta_f':df})
	net_snr = get_net_snr(params)
	time = get_waveform_filter_length_in_time(**params)
	tc = params['tc']
	ra = params['ra']
	dec = params['dec']
	dist = params['distance']
	mass1 = params['mass1']
	mass2 = params['mass2']
	mchirp = mchirp_from_mass1_mass2(mass1, mass2)
	q = q_from_mass1_mass2(mass1, mass2)
	path = opts.output_dir + '/inj_%s.ini' % i
	f = open(path, 'w')
	f.write(f"""
[model]
marginalize_distance_snr_range = {max(net_snr - 20, 5)}, {net_snr + 20}

[data]
trigger-time = {tc}
injection-file = {inj}
analysis-start-time = {-(int(time) + 5)}
analysis-end-time = 5

[prior-tc]
name = uniform
min-tc = {tc - 0.05}
max-tc = {tc + 0.05}

[prior-mchirp]
name = uniform
min-mchirp = {max(mchirp - 50, 0.1)}
max-mchirp = {mchirp + 50}

[prior-q]
name = uniform
min-q = {max(q - 5, 1)}
max-q = {(q + 5)}

[prior-distance]
name = uniform_radius
min-distance = {dist/2}
max-distance = {dist*2}
""")
	f.close()
	fhand = wf.resolve_url_to_file(path)
	node = inference_exe.create_node()

	node.add_input_list_opt("--config-file", [infhand, fhand])

	inference_file = node.new_output_file_opt(workflow.analysis_time, '.hdf', '--output-file', tags=[str(inj)])

	workflow += node

	node = demarg_exe.create_node()
	node.add_input_opt("--input-file", inference_file)
	demarg_file = node.new_output_file_opt(workflow.analysis_time, ".hdf",
                                              "--output-file",
                                              tags=[str(inj) + 'demarg'])
	workflow += node


	node = plot_exe.create_node()
	node.add_input_opt("--input-file", demarg_file)
	plot_file = node.new_output_file_opt(workflow.analysis_time, ".png",
                                             "--output-file",
                                             tags=[str(inj) + 'demarg'])
	workflow += node

workflow.save()
