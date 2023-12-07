#!/bin/bash

# This script executes the Python scripts that generate the tables presented
# in the manuscript. It uses the raw query results stored as CSV files.
#
# Outputs will be stored into the `manuscript_tables` sub folder in the
# `outputs` folder with respect to the root of the repository. To change,
# please modify $RESULTS_PATH variable below.


# Specific output subfolders
RESULTS_PATH=./outputs/manuscript_tables

# Table scripts path
SCRIPTS=./code/manuscript_tables


# Setup PYTHONPATH

PYTHONPATH=./code
export PYTHONPATH


# Clean-up

mkdir -p $RESULTS_PATH
rm -rf $RESULTS_PATH/*.*


# Generate tables

python "$SCRIPTS/table_file_overview.py"
python "$SCRIPTS/table_steps.py"
python "$SCRIPTS/table_results.py"
python "$SCRIPTS/table_psd_results.py"
python "$SCRIPTS/table_filtering.py"
python "$SCRIPTS/table_surrogate_isih_results.py"
python "$SCRIPTS/table_artificial_isih_results.py"


echo "All manuscript tables generated"
