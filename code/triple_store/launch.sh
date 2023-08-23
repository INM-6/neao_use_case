#!/bin/bash

# This script instantiates a GraphDB server
#
# GraphDB Desktop must be already installed according to the README.md file,
# and the path provided in the $GRAPH_DB_PATH variable below.
#
# Any log outputs will be written to the subfolder `graphdb_logs` inside
# the folder `outputs` in the root of the repository. To change, edit the
# variable $LOG_PATH below.

GRAPH_DB_PATH=/opt/graphdb-desktop/bin/graphdb-desktop
LOG_PATH=../../outputs/graphdb_logs

# Clean log outputs
rm $LOG_PATH/*.*

# Start GraphDB Desktop
($GRAPH_DB_PATH >$LOG_PATH/graphdb.log 2>&1 &)

# Wait
sleep 20

# Check connectivity
GRAPH_DB=$(curl -Is http://localhost:7200)

if [ "$GRAPH_DB" == "" ]
then
  echo "Could not initialize GraphDB. Check that it is installed and" \
       "available on '$GRAPH_DB_PATH'."
  exit
fi

# Save version information
echo "$GRAPH_DB" >$LOG_PATH/graphdb_version.txt