"""
This script inserts RDF files with ontologies in OWL/Turtle format, and all
RDF files saved as Turtle files that are present in a directory.

The intended use is to load all provenance generated from multiple analyses,
captured using Alpaca, together with the Neuroelectrophysiology Analysis
Ontology used to annotate the provenance.

Once the triple store database is loaded with the data, the queries
demonstrating the use of the ontology can be run.
"""

import argparse
import logging
from triple_store import graphdb
import yaml
from pathlib import Path


ALPACA_NEAO_MAPPING = Path(__file__).parents[2] / "neao_to_alpaca.ttl"


logging.basicConfig(level=logging.DEBUG)


def load_data(repository, ontologies, prov_dir=None, prefixes=None,
              create_repo=False, neao_mapping=True):

    # Get the prefixes from a file
    if prefixes:
        with open(Path(prefixes).expanduser().absolute()) as stream:
            prefixes = yaml.safe_load(stream)

    # Create the interface to the triple store
    db_interface = graphdb.GraphDBInterface(repository=repository,
                                            create=create_repo,
                                            prefixes=prefixes)

    # Load ontologies into the database
    for ontology in ontologies:
        db_interface.import_file(ontology, format='turtle')

    # Load NEAO to Alpaca mapping into the database
    if neao_mapping:
        db_interface.import_file(ALPACA_NEAO_MAPPING)

    # Insert provenance files into the database
    if prov_dir:
        db_interface.import_files(prov_dir, "*.ttl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=str, required=True)
    parser.add_argument('--ontologies', type=str, required=True, nargs="+")
    parser.add_argument('--prov-dir', metavar="prov_dir", type=str,
                        required=False, nargs="?", default=None)
    parser.add_argument('--prefixes', type=str, required=False, default=None)
    parser.add_argument('--create-repo', metavar="create_repo", type=bool,
                        required=False, default=False)
    parser.add_argument('--neao_mapping', type=bool, required=False,
                        default=True)
    args = parser.parse_args()

    load_data(repository=args.repository, ontologies=args.ontologies,
              prov_dir=args.prov_dir, prefixes=args.prefixes,
              create_repo=args.create_repo, neao_mapping=args.neao_mapping)
