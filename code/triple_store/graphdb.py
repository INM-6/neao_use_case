import io
import logging
from multipledispatch import dispatch

import requests
from gastrodon import RemoteEndpoint, inline
from alpaca.ontology import ALPACA
from pathlib import Path
import rdflib


# Create logger and set configuration
logger = logging.getLogger(__file__)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter("[%(asctime)s] triple_store -"
                                           " %(levelname)s: %(message)s"))
logger.addHandler(log_handler)
logger.propagate = False


class GraphDBInterface:

    HEADERS = {
        "GET": {"Accept": "application/json"},
        "POST": {"Content-Type": "application/json"},
        "DELETE": {},
    }

    METHODS = {
        "GET": requests.get,
        "POST": requests.post,
        "DELETE": requests.delete
    }

    REPO_CONFIG = Path(__file__).parents[0] / "config" / "repo_config.ttl"

    def __init__(self, *, host="http://localhost:7200", repository=None,
                 clear=False, create=False, prefixes=None):
        self.host = host
        self.repository = None
        self.sparql_endpoint = None

        if repository is not None:
            repositories = self.get_repositories()
            all_repos = [repo['id'] for repo in repositories]
            if not repository in all_repos:
                if not create:
                    raise ValueError(f"Repository {repository} not found")
                self.add_repository(repository)
                repositories = self.get_repositories()
                all_repos = [repo['id'] for repo in repositories]

            repo_data = repositories[all_repos.index(repository)]

            if not clear:
                self.repository = repo_data
                self.init_sparql_endpoint(repo_data['uri'], prefixes=prefixes)
            else:
                self.delete_repository(repo_data['id'])

    def init_sparql_endpoint(self, repo_uri, prefixes=None):
        all_prefixes = {'alpaca': str(ALPACA)}
        if prefixes is not None:
            all_prefixes.update(prefixes)
        prefixes_list = [f"@prefix {prefix}: <{uri}> ."
                         for prefix, uri in all_prefixes.items()]

        prefixes_graph = inline("\n".join(prefixes_list)).graph

        self.sparql_endpoint = RemoteEndpoint(repo_uri,
                                              prefixes=prefixes_graph)

    def _make_rest_request(self, method, endpoint, headers=None,
                           expected_response=200, **kwargs):
        # Performs the HTTP request to the endpoint, and returns the Response
        # object
        url = f"{self.host}{endpoint}"

        request_header = self.HEADERS.get(method, {})
        if headers is not None:
            request_header.update(headers)

        request_fn = self.METHODS.get(method)
        kwargs['headers'] = headers
        response = request_fn(url, **kwargs)

        if response.status_code != expected_response and \
                expected_response is not None:
            logger.debug(f"Wrong response! Code {response.status_code}:\n"
                         f"headers = {response.headers}\n"
                         f"content = {response.content}")
            raise ValueError(str(response))

        return response

    def _get_repository(self, name):
        if name is None:
            if self.repository is None:
                raise ValueError("Must define the repository or define the"
                                 "repository when instantiating the class.")
            return self.repository['id']
        return name

    def delete_repository(self, repository=None, allow_non_existent=True):
        repository = self._get_repository(repository)
        endpoint = f"/rest/repositories/{repository}"
        expected_response = None if allow_non_existent else 200
        self._make_rest_request("DELETE", endpoint,
                                expected_response=expected_response)

    def get_repositories(self):
        response = self._make_rest_request("GET", "/rest/repositories")
        return response.json()

    def add_repository(self, repository):
        config = rdflib.Graph()
        config.parse(self.REPO_CONFIG, format='turtle')
        ns_rep = None
        for prefix, namespace in config.namespace_manager.namespaces():
           if prefix == "rep":
               ns_rep = rdflib.Namespace(namespace)

        # Replace repositoryID triple
        rep_node = next(config.subjects(rdflib.RDF.type, ns_rep.Repository))
        config.remove((rep_node, ns_rep.repositoryID, None))
        config.add((rep_node, ns_rep.repositoryID, rdflib.Literal(repository)))

        with io.BytesIO() as stream:
            config.serialize(stream, format='turtle')
            self._make_rest_request("POST", "/rest/repositories",
                                    files={'config': stream.getvalue()},
                                    expected_response=201)

    def _import_from_io(self, stream, repository, format):
        endpoint = f"/repositories/{repository}/rdf-graphs/service?default"
        with stream as data:
            content_type = {'turtle': 'text/turtle'}[format]

            self._make_rest_request("POST", endpoint,
                                    headers={'Content-Type': content_type,
                                             'Accept': 'application/json'},
                                    expected_response=204,
                                    data=data)

    def import_url(self, url, repository=None, format='turtle'):
        repository = self._get_repository(repository)
        logger.info(f"Importing URL '{url}' into '{repository}'")
        response = requests.get(url)
        stream = io.BytesIO(response.content)
        self._import_from_io(stream, repository, format)

    def import_file(self, file_name, repository=None, format='turtle'):
        file_name = Path(file_name).expanduser().absolute()
        repository = self._get_repository(repository)
        logger.info(f"Importing file '{file_name}' into '{repository}'")
        stream = open(file_name, 'rb')
        self._import_from_io(stream, repository, format)

    def import_files(self, directory, file_pattern, repository=None,
                     format='turtle'):
        directory = Path(directory).expanduser().absolute()
        for file in directory.rglob(file_pattern):
            self.import_file(file, repository=repository, format=format)

    @dispatch(Path)
    def execute_select_query(self, query):
        with open(query, 'r') as query_file:
            query_str = query_file.read()
        return self.execute_select_query(query_str)

    @dispatch(str)
    def execute_select_query(self, query):
        if self.sparql_endpoint is None:
            raise ValueError("SPARQL endpoint not initialized.")
        result = self.sparql_endpoint.select(query)
        return result
