#!/bin/bash

# This script runs all the analyses for the ontology use case, generating
# annotated provenance records with Alpaca.
#
# When experimental data is used, the reduced Reach2Grasp datasets in NIX
# must be present. The `i140703-001_no_raw.nix` file must be downloaded
# according to the `README.md` file. The path to the dataset is defined in the
# variable $DATA_I below. The script can be run directly if the dataset is
# copied to the `data` folder with respect to the repository root or the
# symbolic link was created. If using the dataset by providing the path to the
# local GIN repository folder, please change $DATA_I accordingly.
#
# Outputs will be stored into the `analyses` subfolder in the `outputs` folder
# with respect to the root of the repository. To change, please modify the
# $OUTPUT_FOLDER variable below.
#
# The analyses where cross-correlation histograms are computed require MPI for
# parallelization.


DATA_I=./data/i140703-001_no_raw.nix

OUTPUT_FOLDER=./outputs/analyses

# Specific output subfolders
PSD_OUTPUT=$OUTPUT_FOLDER/reach2grasp
CCH_OUTPUT=$OUTPUT_FOLDER/reach2grasp
ISI_OUTPUT=$OUTPUT_FOLDER/isi_histograms


# Clean-up
rm -rf $OUTPUT_FOLDER
mkdir $OUTPUT_FOLDER
mkdir $PSD_OUTPUT
mkdir $CCH_OUTPUT
mkdir $ISI_OUTPUT


# Store information on the environment
(python --version && pip list && pip freeze) > $OUTPUT_FOLDER/environment.txt


# Code path
ANALYSES_CODE=./code/analyses


# Setup PYTHONPATH
PYTHONPATH=$(pwd)/code
export PYTHONPATH


# Run PSD analyses
echo "1. PSD analyses"

PSD_OUTPUT_1=$PSD_OUTPUT/psd_by_trial
mkdir $PSD_OUTPUT_1
mpiexec -n 1 python $ANALYSES_CODE/psd_by_trial/elephant_welch/psd_by_trial.py --output_path=$PSD_OUTPUT_1 $DATA_I

PSD_OUTPUT_2=$PSD_OUTPUT/psd_by_trial_2
mkdir $PSD_OUTPUT_2
mpiexec -n 1 python $ANALYSES_CODE/psd_by_trial/elephant_multitaper/psd_by_trial.py --output_path=$PSD_OUTPUT_2 $DATA_I

PSD_OUTPUT_3=$PSD_OUTPUT/psd_by_trial_3
mkdir $PSD_OUTPUT_3
mpiexec -n 1 python $ANALYSES_CODE/psd_by_trial/scipy/psd_by_trial.py --output_path=$PSD_OUTPUT_3 $DATA_I


# Run CCH analyses
echo "2. CCH analyses"

CCH_OUTPUT_1=$CCH_OUTPUT/cchs_1
mkdir $CCH_OUTPUT_1
mpiexec -n 20 python $ANALYSES_CODE/cchs/surrogate_1/compute_cchs.py --output_path=$CCH_OUTPUT_1 $DATA_I

CCH_OUTPUT_2=$CCH_OUTPUT/cchs_2
mkdir $CCH_OUTPUT_2
mpiexec -n 20 python $ANALYSES_CODE/cchs/surrogate_2/compute_cchs.py --output_path=$CCH_OUTPUT_2 $DATA_I


# Run ISI histograms
echo "3. ISI analyses"

mpiexec -n 1 python $ANALYSES_CODE/isi_histograms/isi_analysis.py --output_path=$ISI_OUTPUT

echo "All done"
