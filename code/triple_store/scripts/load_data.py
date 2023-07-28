"""
This scripts creates a repository in the GraphDB triple store, and inserts
an RDF file with the ontology in OWL format, and all RDF files saved as
Turtle files that are present in a directory.

The intended use is to load all provenance generated from multiple analyses,
captured using Alpaca, together with the Neuroelectrophysiology Analysis
Ontology used to annotate the provenance.

Once the triple store database is loaded with the data, the queries
demonstrating the use of the ontology can be run.
"""

import argparse
import logging
from triple_store import graphdb
from alpaca.ontology import ONTOLOGY_SOURCE as ALPACA_ONTOLOGY

logging.basicConfig(level=logging.DEBUG)


def load_provenance_data(repository, ontology, prov_dir):
    # Create the interface to the triple store
    db_interface = graphdb.GraphDBInterface(repository=repository, create=True)

    # Load Alpaca ontology into the database
    db_interface.import_file(ALPACA_ONTOLOGY)

    # Load ontology into the database
    #db_interface.import_file(ontology, format='turtle')


    # Insert provenance files into the database
    db_interface.import_files(prov_dir, "*.ttl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=str, required=True)
    parser.add_argument('--ontology', type=str, required=True)
    parser.add_argument('prov_dir', metavar='prov_dir', nargs="?")
    args = parser.parse_args()

    load_provenance_data(args.repository, args.ontology, args.prov_dir)
