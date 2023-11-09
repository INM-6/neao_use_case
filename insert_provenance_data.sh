#!/bin/bash

# This script inserts all the provenance files generated by the analyses and
# the ontology definitions into a GraphDB repository.

# To speed up the process, the files will be inserted offline, before the
# server is initialized. Any existing repository will be overwritten.
#
# GraphDB desktop must be already installed according to the README.md file
# in `code/triple_store`.


# Deletes the temp directory where ontologies were cloned/downloaded
function cleanup {
  rm -rf "$TMP_FOLDER"
}
trap cleanup EXIT


# Path where TTL files will be read from (saved by the analysis scripts)
PROV_PATH=./outputs/analyses

# URL to the Git repository with NEAO source
NEAO_REPO="/home/koehler/PycharmProjects/neuroephys_analysis_ontology"

# URL to get the W3C PROV-O OWL source
PROV_URL="http://www.w3.org/ns/prov-o-20130430"

# Path to the InsertRDF utility from GraphDB
IMPORT_RDF=/opt/graphdb-desktop/lib/app/bin/importrdf

# Path to the repository config file
REPO_CONFIG=./code/triple_store/config/repo_config.ttl


# Clone/download the ontology files into a temporary folder

TMP_FOLDER=$(mktemp -d)

NEAO_FOLDER="$TMP_FOLDER/neao"
#git clone $NEAO_REPO $NEAO_FOLDER
cp -r $NEAO_REPO "$NEAO_FOLDER"   # Temp: using local source

PROV_O_FILE="$TMP_FOLDER/provo.ttl"
wget $PROV_URL -O "$PROV_O_FILE"

ALPACA_FILE="$TMP_FOLDER/alpaca.ttl"
ALPACA_ONTOLOGY=$(python -c "from alpaca.ontology import ONTOLOGY_SOURCE; print(ONTOLOGY_SOURCE)")
cp "$ALPACA_ONTOLOGY" "$ALPACA_FILE"


# Rename files from OWL to TTL to allow using the import tool

find "$TMP_FOLDER" -type f -name '*.owl' -exec mv -- {} {}.ttl \;


# Create lists of TTL files with provenance information

PSD_FILES=$(find "$PROV_PATH" -name '*psd*.ttl' -print0 | xargs --null)
ISI_FILES=$(find "$PROV_PATH" -name '*isi*.ttl' -print0 | xargs --null)


# Loading is done offline, kill any running process

killall -q -w graphdb-desktop


# Insert the ontologies and the TTL files with provenance

$IMPORT_RDF -Dgraphdb.inference.concurrency=6 load -m parallel -f -c $REPO_CONFIG \
    "$PROV_O_FILE" "$ALPACA_FILE" \
    "$NEAO_FOLDER/base/base.owl.ttl" "$NEAO_FOLDER/steps/steps.owl.ttl" \
    "$NEAO_FOLDER/data/data.owl.ttl" "$NEAO_FOLDER/neao.owl.ttl" \
    ./code/neao_to_alpaca.ttl "$PSD_FILES" "$ISI_FILES"


echo "All data inserted into GraphDB"
