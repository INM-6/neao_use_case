"""
This script provides a generic interface to execute specific SPARQL update
(INSERT/DELETE) queries on the triple store.

The script parses command line arguments and performs the query based on a
SPARQL query stored in a file. Multiple files can be passed.
"""

from pathlib import Path
import argparse
from triple_store.graphdb import GraphDBInterface


def main(query_files, repository):
    # Create interface
    graphdb = GraphDBInterface(repository=repository)

    # Execute query(ies)
    for file in query_files:
        graphdb.execute_update_query(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=str, required=True)
    parser.add_argument('query_files', type=str, nargs="+")
    args = parser.parse_args()

    query_files = [Path(query_file).expanduser().absolute()
                   for query_file in args.query_files]

    main(query_files, args.repository)
