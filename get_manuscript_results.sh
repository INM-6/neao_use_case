#!/bin/bash

# This script produces all the results presented in the manuscript, after
# provenance data was inserted into the GraphDB repository 'provenance'.

# It first executes all queries, and saves the raw results as CSV files.
# This is implemented in the script `run_queries.sh`. Please, see that script
# for additional details.

# Once the CSV files are generated, a second script is run to generate the
# LaTeX code used for the tables in the manuscript. This is implemented in
# the script `generate_manuscript_tables.sh`.

./run_queries.sh

./generate_manuscript_tables.sh
