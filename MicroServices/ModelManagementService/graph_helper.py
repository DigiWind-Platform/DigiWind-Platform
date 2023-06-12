import json
import logging
import os

import rdflib
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, XSD, XMLNS, RDFS


def graphiphy(structure, graph: Graph, count, ont: Namespace, prefix: str,
              caller_id: str, inputs_outputs: dict, relative_path: str):
    # (Collection of items, graph to parse them to, start the count at, namespace, path to file)
    for name, items in structure.items():
        precount = count

        if type(items) is dict:  # if type is a collection, execute recursive resolver
            count += 1
            graphiphy(items, graph, count, ont, prefix, name, inputs_outputs, relative_path)
            count = precount  # reset depth counter

        if type(items) is list:  # only bindings of controller signals come up as lists
            for subitem in items:
                graph.add((URIRef(prefix + '/SignalBond/' + caller_id), RDF.type, URIRef(ont + 'SignalBond')))
                graph.add((URIRef(prefix + '/SignalBond/' + caller_id), ont.binds, URIRef(prefix + '/Signal/' + subitem)))
                graph.add((URIRef(prefix), ont.has, URIRef(prefix + '/SignalBond/' + caller_id)))
                graph.add((URIRef(prefix), ont.hasSignalBond, URIRef(prefix + '/SignalBond/' + caller_id)))

        if type(items) is str:  # bottom structure level accessed (signals, bonds, metaInformation)
            if caller_id == 'signals':
                graph.add((URIRef(prefix + '/Signal/' + name), RDF.type, ont.Signal))
                graph.add((URIRef(prefix + '/Signal/' + name), RDF.type, ont.Interface))
                graph.add((URIRef(prefix + '/Signal/' + name), RDF.type, URIRef(ont + items)))  # Signal Subtype
                graph.add((URIRef(prefix), ont.has, URIRef(prefix + '/Signal/' + name)))
                # for direction in inputs_outputs:
                for _ in inputs_outputs["input"]:
                    if _ == name:
                        graph.add((URIRef(prefix), ont.hasInputSignal, URIRef(prefix + '/Signal/' + name)))
                for _ in inputs_outputs["output"]:
                    if _ == name:
                        graph.add((URIRef(prefix), ont.hasOutputSignal, URIRef(prefix + '/Signal/' + name)))

            if caller_id == 'aerodynamicPort' or caller_id == 'mechanicalPort' or caller_id == 'electricalPort':
                if name == 'type':
                    graph.add((URIRef(prefix + '/PowerBond/' + caller_id), RDF.type, ont.PowerBond))
                    graph.add((URIRef(prefix + '/PowerBond/' + caller_id), RDF.type, ont.SignalBond))
                    graph.add((URIRef(prefix + '/PowerBond/' + caller_id), RDF.type, ont.Interface))
                    graph.add((URIRef(prefix + '/PowerBond/' + caller_id), RDF.type, URIRef(ont + items)))
                    graph.add((URIRef(prefix), ont.hasSignalBond, URIRef(prefix + '/PowerBond/' + caller_id)))
                if name == 'asFlow' or name == 'asEffort':
                    graph.add(
                        (URIRef(prefix + '/PowerBond/' + caller_id), ont.binds, URIRef(prefix + '/Signal/' + items)))
                    graph.add((URIRef(prefix + '/PowerBond/' + caller_id), URIRef(ont + name),
                               URIRef(prefix + '/Signal/' + items)))

            if caller_id == 'metaInformation':
                if name == 'type':
                    graph.add((URIRef(prefix), RDF.type,  URIRef(ont + items)))
                if name == 'startOfValidity':
                    # 'http://tuwien.ac.at/digiwind/DigiWindOnt#FMU/generator/'
                    graph.add((URIRef(prefix), ont.startOfValidity, Literal(
                        rdflib.util.date_time(rdflib.util.parse_date_time(items)), datatype=XSD.dateTime)))
                if name == 'referenceID':
                    graph.add((URIRef(prefix), ont.hasReferenceID, Literal(items)))
                if name == 'name':
                    graph.add((URIRef(prefix), ont.hasName, Literal(items)))
# Filter for instances of fmus which are later than a given date
# PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
# PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX owl: <http://www.w3.org/2002/07/owl#>
# PREFIX digiWindOnt: <http://tuwien.ac.at/digiwind/DigiWindOnt#>
# PREFIX ontAnnot: <http://purl.org/net/ns/ontology-annot#>
# PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
# SELECT * WHERE {
#   ?a ?b ?c
#   FILTER(?c > "2022-07-23T12:22:45+00:00"^^xsd:dateTime)
# }


def generate_addition_graph(inputs_outputs, ontology_uri, path_to_metadata_file, path_to_fmu_file):
    ont = Namespace(ontology_uri)
    with open(path_to_metadata_file, "r") as read_file:
        fmu_meta_data_file = json.load(read_file)
    addition_graph = Graph()
    init_graph(addition_graph, ontology_uri)
    relative_path = path_to_metadata_file
    for i, c in enumerate(reversed(path_to_metadata_file)):
        if c == os.sep:
            relative_path = path_to_metadata_file[:len(path_to_metadata_file) - i]
            break
        if i == len(path_to_metadata_file) - 1:
            relative_path = path_to_metadata_file[:len(path_to_metadata_file) - i - 1]
            break
    identifier = fmu_meta_data_file.get('metaInformation').get('identifier')
    if identifier is None:
        print("No meta information for the identifier is available, did not include the " + path_to_metadata_file)
        return addition_graph
    prefix = ont + 'FMU_' + identifier
    addition_graph.add((URIRef(prefix), RDF.type, ont.FMU))
    addition_graph.add((URIRef(prefix), ont.Path, Literal(path_to_fmu_file)))
    logging.info("GH:         : Path to fmu: " + path_to_fmu_file)
    graphiphy(fmu_meta_data_file, addition_graph, 0, ont, prefix, '', inputs_outputs, relative_path)
    logging.info("GH:         : Added fmu to ontology (" + path_to_fmu_file + ")")
    return addition_graph


def init_graph(addition_graph, ontology_uri):
    addition_graph.namespace_manager.bind("ont", ontology_uri)
    addition_graph.namespace_manager.bind("rdf", RDF)
    addition_graph.namespace_manager.bind("xmlns", XMLNS)
    addition_graph.namespace_manager.bind("rdfs", RDFS)
    addition_graph.namespace_manager.bind("xsd", XSD)
