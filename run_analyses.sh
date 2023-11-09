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


DATA_I=./data/i140703-001_no_raw.nix

OUTPUT_FOLDER=./outputs/analyses


# Specific output subfolders

PSD_OUTPUT=$OUTPUT_FOLDER/reach2grasp
SURROGATE_OUTPUT=$OUTPUT_FOLDER/reach2grasp
ISI_OUTPUT=$OUTPUT_FOLDER/isi_histograms


# Clean-up
rm -rf $OUTPUT_FOLDER
mkdir $OUTPUT_FOLDER
mkdir $PSD_OUTPUT
mkdir $SURROGATE_OUTPUT
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

PSD_CODE_ROOT=$ANALYSES_CODE/psd_by_trial
PSD_SCRIPT=psd_by_trial.py

PSD_OUTPUT_1=$PSD_OUTPUT/psd_by_trial
mkdir $PSD_OUTPUT_1
python $PSD_CODE_ROOT/elephant_welch/$PSD_SCRIPT --output_path=$PSD_OUTPUT_1 $DATA_I

PSD_OUTPUT_2=$PSD_OUTPUT/psd_by_trial_2
mkdir $PSD_OUTPUT_2
python $PSD_CODE_ROOT/elephant_multitaper/$PSD_SCRIPT --output_path=$PSD_OUTPUT_2 $DATA_I

PSD_OUTPUT_3=$PSD_OUTPUT/psd_by_trial_3
mkdir $PSD_OUTPUT_3
python $PSD_CODE_ROOT/scipy/$PSD_SCRIPT --output_path=$PSD_OUTPUT_3 $DATA_I


# Run CCH analyses
echo "2. CCH analyses"

SURROGATE_CODE_ROOT=$ANALYSES_CODE/surrogate_isih
SURROGATE_SCRIPT=compute_isis.py

SURROGATE_OUTPUT_1=$SURROGATE_OUTPUT/surrogate_isih_1
mkdir $SURROGATE_OUTPUT_1
python $SURROGATE_CODE_ROOT/surrogate_1/$SURROGATE_SCRIPT --output_path=$SURROGATE_OUTPUT_1 $DATA_I

SURROGATE_OUTPUT_2=$SURROGATE_OUTPUT/surrogate_isih_2
mkdir $SURROGATE_OUTPUT_2
python $SURROGATE_CODE_ROOT/surrogate_2/$SURROGATE_SCRIPT --output_path=$SURROGATE_OUTPUT_2 $DATA_I


# Run ISI histograms
echo "3. ISI analyses"

python $ANALYSES_CODE/isi_histograms/isi_analysis.py --output_path=$ISI_OUTPUT

echo "All done"
