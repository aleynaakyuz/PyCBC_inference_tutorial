#!/usr/bin/env

import h5py
import numpy as np
import pycbc.workflow as wf
import pycbc
import argparse
import pycbc.workflow.pegasus_workflow as wdax
from pycbc.conversions import mchirp_from_mass1_mass2, q_from_mass1_mass2
from pycbc.psd.read import from_txt
from pycbc.waveform import get_waveform_filter_length_in_time
from pycbc.detector import Detector
from pycbc.waveform import get_fd_waveform
from pycbc.filter import sigma

## Define command line input options
parser = argparse.ArgumentParser()
parser.add_argument("--injections", nargs='*')
parser.add_argument("--inference-config")
parser.add_argument("--detectors", nargs='*')
parser.add_argument("--psd-paths", nargs='*')

pycbc.init_logging(True) ## adds verbosity
wf.add_workflow_command_line_group(parser) ## adds command line input options
wf.add_workflow_settings_cli(parser) ## Adds workflow options to an argument parser
opts = parser.parse_args() ## get options

workflow = wf.Workflow(opts, "gw") ## define workflow name
wf.makedir(opts.output_dir) ## create output directory
infhand = wf.resolve_url_to_file(opts.inference_config) ## read the common inference config file

## You can define any function you need.
def get_proj_strain(det, param): 
    """
	Calculates the projected signal.
    """
    ra = param['ra']
    dec = param['dec']
    pol = param['polarization']
    tc = param['tc']
    
    detec = Detector(det)
    hp, hc = get_fd_waveform(**param)
    f_plus, f_cross = detec.antenna_pattern(ra, dec, pol, tc)
    
    proj_strain = f_plus * hp + f_cross * hc
    return proj_strain

def calculate_snr(det, psd, param, low_freq, high_freq=None):
    """
	Calculates the snr
    """
    proj_strain = get_proj_strain(det, param)
    amp = sigma(proj_strain, psd=psd, low_frequency_cutoff=low_freq, high_frequency_cutoff=high_freq)
    return amp

def get_net_snr(params):
	"""
	Calculates the network snr
	"""
	df = 0.001
	net_snr_sq = 0
	for k, det in enumerate(opts.detectors):
		psd = from_txt(opts.psd_paths[k], low_freq_cutoff=5.1, length=int(4000/df), delta_f=df)
		snr = calculate_snr(det, psd, params, 5.1)
		net_snr_sq += snr**2
	return np.sqrt(net_snr_sq)

## Define executables
inference_exe = wf.Executable(workflow.cp, "inference", ifos=workflow.ifos,
                              out_dir=opts.output_dir)

demarg_exe = wf.Executable(workflow.cp, "demarg", ifos=workflow.ifos,
                              out_dir=opts.output_dir)

plot_exe = wf.Executable(workflow.cp, "plot", ifos=workflow.ifos,
                              out_dir=opts.output_dir)

df = 0.001
for i, inj in enumerate(opts.injections): ## Loop over different injections
	params2 = h5py.File(inj)
	params = {key:params2[key][:][0] for key in list(params2.keys())}
	att = {key:params2.attrs[key] for key in list(params2.attrs.keys())}
	params.update(att)

	params.update({'delta_f':df})
	net_snr = get_net_snr(params)

	## calculates the length of the signal
	time = get_waveform_filter_length_in_time(**params) 

	tc = params['tc']
	ra = params['ra']
	dec = params['dec']
	dist = params['distance']
	mass1 = params['mass1']
	mass2 = params['mass2']
	mchirp = mchirp_from_mass1_mass2(mass1, mass2)
	q = q_from_mass1_mass2(mass1, mass2)

	path = opts.output_dir + '/inj_%s.ini' % i # define the path of the individual inference config file
	f = open(path, 'w') ## open and write the file
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

	## Create a node for every executable
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
