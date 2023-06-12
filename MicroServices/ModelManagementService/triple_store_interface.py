import http.client
import logging

from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from graph_helper import generate_addition_graph


def add_graph_to_store(path_to_metadata_file: str, inputs_outputs: dict, ontology_url: str, ontology_uri: str,
                       path_to_fmu_file: str, triple_store_username: str, triple_store_password: str):
    logging.info("TSI:        : Adding nodes of \"" + path_to_metadata_file + "\" to store")
    addition_graph = generate_addition_graph(inputs_outputs, ontology_uri, path_to_metadata_file, path_to_fmu_file)
    update_remote_triple_store(addition_graph, ontology_url, triple_store_username, triple_store_password)


def generate_graph_ttl_file(ontology_url: str):
    g = Graph()
    g.parse(ontology_url)
    g.serialize(destination="/app/logs/ont.ttl", format="ttl")


def open_store(ontology_url: str, triple_store_username: str, triple_store_password: str):
    return SPARQLUpdateStore(auth=(triple_store_username, triple_store_password),
                             query_endpoint=ontology_url + "/query", update_endpoint=ontology_url + "/update")


def close_store(store: SPARQLUpdateStore):
    store.close()


def write_graph_to_store(store: SPARQLUpdateStore, g: Graph):
    for n in g:
        store.add(n)


def update_remote_triple_store(addition_graph, ontology_url, triple_store_username: str, triple_store_password: str):
    triple_store = SPARQLUpdateStore(auth=(triple_store_username, triple_store_password),
                                     query_endpoint=ontology_url + "/query", update_endpoint=ontology_url + "/update")
    for i in addition_graph:
        triple_store.add(i)
    triple_store.close()
    logging.info('TSI:        : Added nodes to store')


class SparqlHelper:

    def __init__(self, sparql_server_name: str, sparql_server_port: str, dataset_name: str, _logging: int):
        sparql_endpoint = "http://" + sparql_server_name + ":" + \
                          sparql_server_port + "/" + dataset_name
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
        logging.basicConfig(format="%(asctime)s: %(message)s", level=_logging,
                            datefmt="%H:%M:%S")
        logging.info("SparqlHelper: Using " + sparql_endpoint + " as SPARQL-Endpoint")

    def get_node(self, fmu_name):
        query = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX ont: <http://tuwien.ac.at/digiwind/DigiWindOnt#>
            ASK WHERE {
                ont:FMU_""" + fmu_name + """ a ont:FMU
            }
        """
        self.sparql.setQuery(query)
        results = self.sparql.queryAndConvert()
        if results['boolean']:
            return True
        return False

    def remove_fmu(self, fmu_name):
        self.sparql.setMethod('POST')
        query = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX ont: <http://tuwien.ac.at/digiwind/DigiWindOnt#>
            DELETE {
              ?a ?b ?c .
            }
            WHERE {
              SELECT ?a ?b ?c 
              WHERE {
                ?a ?b ?c .
              filter contains (str(?a), "FMU_"""+fmu_name+"""")
              }
            }
        """
        self.sparql.setQuery(query)
        self.sparql.query()
        query = """
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX ont: <http://tuwien.ac.at/digiwind/DigiWindOnt#>
                    DELETE {
                      ont:FMU_""" + fmu_name + """ ?b ?c .
                    }
                    WHERE {
                      SELECT ?a ?b ?c 
                      WHERE {
                        ont:FMU_""" + fmu_name + """ ?b ?c .
                      }
                    }
                """
        self.sparql.setQuery(query)
        self.sparql.query()
        logging.info("TSI:        : Removed \"" + fmu_name + "\" from triple store")

    def remove_all_nodes(self):
        self.sparql.setQuery("""
                    DELETE {
                      ?a ?b ?c .
                    }
                    WHERE {
                      ?a ?b ?c .
                    }
                """)
        self.sparql.setMethod('POST')
        self.sparql.query()

    def init_ontology(self, ontology_file_name: str):
        self.remove_all_nodes()
        with open("/app/ontology/" + ontology_file_name, 'r') as owl_file:
            g = Graph()
            g.parse(owl_file, format='xml')
            return g

    def connected(self):
        self.sparql.setQuery("""
            SELECT ?subject ?predicate ?object
            WHERE {
              ?subject ?predicate ?object
            }
            LIMIT 1
        """)
        try:
            self.sparql.queryAndConvert()
        except (OSError, ConnectionRefusedError, http.client.RemoteDisconnected):
            return False
        return True
