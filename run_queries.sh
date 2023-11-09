#!/bin/bash

# This script executes the queries that are presented in the manuscript,
# saving the raw result tables as CSV files.
#
# The default behavior is to instantiate the GraphDB server app and kill the
# process at the end. An argument "running" can be passed to avoid this and
# control the server instance manually.
#
# GraphDB desktop must be already installed according to the README.md file
# in `code/triple_store`.
#
# Outputs will be stored into the `query_results` subfolder in the `outputs`
# folder with respect to the root of the repository. To change, please modify
# the $RESULTS_PATH variable below.
#
# The SPARQL code for each query is stored into the `queries` subfolder in
# the `code` folder with respect to the root of the repository.


# Query execution helper function
# Args: sparql_file, output_csv_file
run_query() {
    SPARQL_FILE="$SPARQL_PATH/$1"
    OUTPUT_FILE="$RESULTS_PATH/$2"
    python ./code/triple_store/scripts/query_data.py \
       --query_file="$SPARQL_FILE" \
       --output_file="$OUTPUT_FILE" --repository=provenance
}


# Specific output subfolders
RESULTS_PATH=./outputs/query_results

# SPARQL queries source folder
SPARQL_PATH=./code/queries


# Setup PYTHONPATH

PYTHONPATH=./code
export PYTHONPATH


# Clean-up

mkdir -p $RESULTS_PATH
rm -rf $RESULTS_PATH/*.*


# Launch GraphDB if not in manual mode (kill any running process)

if [ "$1" != "running" ]
then
   killall -q -w graphdb-desktop
   cd ./code/triple_store
   ./launch.sh
   cd ../..
fi


# Run queries
# Here, each command will produce one output presented in the paper.
# Check the README.md for details.

run_query "file_overview_input_datasets.sparql" "table_file_overview_input_datasets_raw.csv"
run_query "file_overview_files_written.sparql" "table_file_overview_files_written_raw.csv"


# Terminate GraphDB if not in manual mode

if [ "$1" != "running" ]
then
   killall graphdb-desktop
fi

echo "All queries executed "
