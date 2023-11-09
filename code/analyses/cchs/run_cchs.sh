#!/bin/bash

# This script runs all the CCH analyses for the ontology use case, generating
# annotated provenance records with Alpaca. The scripts in this folder require
# MPI parallelization. This bash script must be submitted via SLURM in a
# cluster with MPI properly configured.
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


DATA_I=../../../data/i140703-001_no_raw.nix

OUTPUT_FOLDER=../../../outputs/analyses


# Setup PYTHONPATH
PYTHONPATH=$(pwd)/../..
export PYTHONPATH


CCH_OUTPUT_1=$OUTPUT_FOLDER/reach2grasp/cchs_1
rm -rf $CCH_OUTPUT_1
mkdir $CCH_OUTPUT_1
mpiexec -n 20 python ./surrogate_1/compute_cchs.py --output_path=$CCH_OUTPUT_1 $DATA_I

CCH_OUTPUT_2=$OUTPUT_FOLDER/reach2grasp/cchs_2
rm -rf $CCH_OUTPUT_2
mkdir $CCH_OUTPUT_2
mpiexec -n 20 python ./surrogate_2/compute_cchs.py --output_path=$CCH_OUTPUT_2 $DATA_I
