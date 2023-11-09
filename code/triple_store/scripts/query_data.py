"""
This script provides a generic interface to execute specific SPARQL SELECT
queries on the triple store.

The script parses command line arguments, performs the query based on a SPARQL
query stored in a file, and saves the result as a CSV file. These are used
later for the tables in the manuscript.
"""

from pathlib import Path
import argparse
from triple_store.graphdb import GraphDBInterface


def main(query_file, output_file, repository):
    # Create interface
    graphdb = GraphDBInterface(repository=repository)

    # Execute query
    query_results = graphdb.execute_select_query(query_file)

    # Save results table to CSV
    query_results.to_csv(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=str, required=True)
    parser.add_argument('--query_file', type=str, required=True)
    parser.add_argument('--output_file', type=str, required=True)
    args = parser.parse_args()

    query_file = Path(args.query_file).expanduser().absolute()
    output_file = Path(args.output_file).expanduser().absolute()

    main(query_file, output_file, args.repository)
