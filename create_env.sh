#!/bin/bash

# Newer conda versions use --yes to force environment creation
CONDA_VERSION=$(conda --version)
VERSION_MATCH="^conda ([0-9]+)\..+$"

if [[ $CONDA_VERSION =~ $VERSION_MATCH ]]
then
   version="${BASH_REMATCH[1]}"
   if [ ${version} -lt 23 ]
   then
      command="--force"
   else
      command="--yes"
   fi
else
   command="--yes"
fi

conda env create "${command}" -f ./environment/environment.yaml
