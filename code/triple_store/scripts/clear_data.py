"""
This script clears a repository in the GraphDB triple store database.

It is intended as a clean up step after the analyses and queries are finished.
"""

import argparse
from triple_store import graphdb

config = argparse.ArgumentParser()
config.add_argument("--repository", required=True, type=str)
args = config.parse_args()

graphdb = graphdb.GraphDBInterface()
graphdb.delete_repository(args.repository)
