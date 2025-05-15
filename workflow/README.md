This folder contains scripts to run a simple workflow that
runs two inference jobs. 

To run these scripts, you need to be set up an envirnoment
that has HTcondor and Pegasus.

To install Pegasus, run

wget https://download.pegasus.isi.edu/pegasus/5.0.8/pegasus-binary-5.0.8-x86_64_ubuntu_20.tar.gz

untar the file and add this line to your .bashrc file 

export PATH="/path/to/pegasus-5.0.6/bin:$PATH

by replacing /path/to/ with your path to untared folder.