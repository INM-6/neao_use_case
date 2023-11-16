import unittest
from pathlib import Path

import pandas as pd
import numpy as np
from triple_store.graphdb import GraphDBInterface


RES_PATH = Path(__file__).parents[0] / "res"


def _compare_data_frames(query, expected, uri_columns=None):
    if uri_columns is not None:
        for col in uri_columns:
            # Convert rdflib URIRef to string
            query[col] = query[col].apply(str)
    sort_column = query.columns[0]
    query = query.sort_values(sort_column)
    expected = expected.sort_values(sort_column)
    data_equal = np.array_equal(query.values, expected.values)
    columns_equal = np.array_equal(query.columns, expected.columns)
    return data_equal and columns_equal


class GraphDBInterfaceTestCase(unittest.TestCase):

    def setUp(self):
        # Clear all possible repositories before test
        for repository in ("test", "test_multiple", "test_file"):
            GraphDBInterface().delete_repository(repository,
                                                 allow_non_existent=True)

    def test_interface(self):
        graphdb = GraphDBInterface(repository="test", create=True)
        graphdb.import_file(RES_PATH / "input_output.ttl")
        test_query = """
PREFIX alpaca: <https://github.com/INM-6/alpaca/ontology/alpaca.owl#>
        
SELECT ?name ?value
WHERE {
    ?s a alpaca:FunctionExecution .
    ?s alpaca:hasParameter ?p .
    ?p alpaca:pairName ?name .
    ?p alpaca:pairValue ?value .
}
LIMIT 3
"""
        query_result = graphdb.execute_select_query(test_query)

        graphdb.delete_repository()

        expected_df_records = [
            {
                "name": "param_1",
                "value": "5"
            },

        ]
        expected_df = pd.DataFrame(expected_df_records)
        expected_df["value"] = expected_df["value"].astype("int64")
        self.assertTrue(_compare_data_frames(query_result, expected_df))

    def test_multiple_imports(self):
        graphdb = GraphDBInterface(repository="test_multiple", create=True)
        graphdb.import_files(RES_PATH, "*.ttl")

        test_query = """
PREFIX alpaca: <https://github.com/INM-6/alpaca/ontology/alpaca.owl#>

SELECT ?func ?name ?value
WHERE {
    ?func a alpaca:FunctionExecution .
    ?func alpaca:hasParameter ?p .
    ?p alpaca:pairName ?name .
    ?p alpaca:pairValue ?value .
}
LIMIT 3
"""
        query_result = graphdb.execute_select_query(test_query)

        graphdb.delete_repository()

        expected_df_records = [
            {
                "func": "urn:fz-juelich.de:alpaca:function_execution:Python:1111112:9999992:test.test_function#123452",
                "name": "param",
                "value": "10"
            },
            {
                "func": "urn:fz-juelich.de:alpaca:function_execution:Python:111111:999999:test.test_function#12345",
                "name": "param_1",
                "value": "5"
            },

        ]
        expected_df = pd.DataFrame(expected_df_records)
        expected_df["value"] = expected_df["value"].astype("int64")

        self.assertTrue(_compare_data_frames(query_result, expected_df,
                                             uri_columns=("func",)))

    def test_file_query(self):
        graphdb = GraphDBInterface(repository="test_file", create=True)
        graphdb.import_file(RES_PATH / "input_output.ttl")
        query_result = graphdb.execute_select_query(RES_PATH /
                                                    "test_query.sparql")
        graphdb.delete_repository()

        expected_df_records = [
            {
                "value": "5",
                "name": "param_1"
            },
        ]
        expected_df = pd.DataFrame(expected_df_records)
        expected_df["value"] = expected_df["value"].astype("int64")
        self.assertTrue(_compare_data_frames(query_result, expected_df))

    def test_update_query(self):
        graphdb = GraphDBInterface(repository="test_insert", create=True)
        graphdb.import_file(RES_PATH / "input_output.ttl")
        insert_query = """
PREFIX alpaca: <https://github.com/INM-6/alpaca/ontology/alpaca.owl#>

INSERT {
   ?func <http://example.org#predicate> ?value
}
WHERE {
    ?func a alpaca:FunctionExecution .
    ?func alpaca:hasParameter ?p .
    ?p alpaca:pairValue ?value .
}
"""
        graphdb.execute_update_query(insert_query)

        test_query = """
PREFIX alpaca: <https://github.com/INM-6/alpaca/ontology/alpaca.owl#>

SELECT ?value
WHERE {
    ?func <http://example.org#predicate> ?value .
}
"""
        query_result = graphdb.execute_select_query(test_query)

        graphdb.delete_repository()

        expected_df_records = [
            {
                "value": "5",
            },
        ]
        expected_df = pd.DataFrame(expected_df_records)
        expected_df["value"] = expected_df["value"].astype("int64")
        self.assertTrue(_compare_data_frames(query_result, expected_df))

    def test_file_update_query(self):
        graphdb = GraphDBInterface(repository="test_file_insert", create=True)
        graphdb.import_file(RES_PATH / "input_output.ttl")
        graphdb.execute_update_query(RES_PATH / "update_query.sparql")

        test_query = """
PREFIX alpaca: <https://github.com/INM-6/alpaca/ontology/alpaca.owl#>

SELECT ?value
WHERE {
    ?func <http://example.org#pred> ?value .
}
"""
        query_result = graphdb.execute_select_query(test_query)

        graphdb.delete_repository()

        expected_df_records = [
            {
                "value": "5",
            },
        ]
        expected_df = pd.DataFrame(expected_df_records)
        expected_df["value"] = expected_df["value"].astype("int64")
        self.assertTrue(_compare_data_frames(query_result, expected_df))


if __name__ == "__main__":
    unittest.main()
