#!/bin/bash

# This scripts instantiates the GraphDB server and run all the unit tests
# to check the functionality for querying the captured provenance data.
# The server is closed at the end.
# Tests are run using `pytest`.

./launch.sh

export PYTHONPATH=$(pwd)/../
pytest ./test

killall graphdb-desktop