"""
This script clears a repository in the GraphDB triple store database.
It is intended as a cleanup step to reset the state of the repository.
"""

import argparse
from triple_store import graphdb

config = argparse.ArgumentParser()
config.add_argument("--repository", required=True, type=str)
args = config.parse_args()

graphdb = graphdb.GraphDBInterface()
graphdb.delete_repository(args.repository)
