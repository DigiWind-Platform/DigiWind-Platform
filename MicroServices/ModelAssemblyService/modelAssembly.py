import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from typing import List

import paho.mqtt.client as mqtt
from fmpy.ssp.ssd import Connection
from SPARQLWrapper import JSON
from SPARQLWrapper import SPARQLWrapper

from ssdToolbox import createBaseSSD
from ssdToolbox import createComponent
from ssdToolbox import ssd2xml
from ssdToolbox import writeXMLTree
from ssdToolbox import Annotation
from ssdToolbox import SimulationSettings
from ssdToolbox import InputData
from ssdToolbox import Signal

FTP_SERVER = os.environ.get("FTP_SERVER")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")
SPARQL_SERVER_NAME = os.environ.get("SPARQL_SERVER_NAME")
SPARQL_SERVER_PORT = os.environ.get("SPARQL_SERVER_PORT")
SPARQL_DATASET_NAME = os.environ.get("SPARQL_DATASET_NAME")


# might be obsolete
@dataclass
class QuerySignalMapping:
    signalName: str
    signalType: str
    signalCausality: str


@dataclass
class QuerySignalInterface:
    signalBond: str
    signalBondType: str
    signalBondSegment: str
    variable: str
    variableType: str
    variableCausality: str


@dataclass
class SimulationModel:
    description: Dict
    signalMapping: Dict
    signalInterfaces: List


def makeSignalPath(parts):
    signalPath = parts[0]
    for p in parts[1:]:
        signalPath += "/" + p

    return signalPath


def assembleModel(filename: str, template: Dict, models: List[SimulationModel]):
    # determine single connections from port connections in the connection template
    templateConnections = []
    for model in template["models"]:
        startModel = model["name"]

        connections = model["connections"]
        for con in connections:
            endModel = con["destModelName"]

            startConModel = con["srcPortName"]
            endConModel = con["destPortName"]

            modelQuery = models[startModel]
            for signalInterface in modelQuery.signalInterfaces:
                # check the other connector model
                if not signalInterface.signalBond.endswith(startConModel):
                    continue

                # check if current variable is an output
                # Connections are only formulated from output to input

                # skip variable if it is an input
                if signalInterface.variableCausality.leave == "hasInputSignal":
                    continue
                if signalInterface.variableCausality.leave == "hasSignalBond":
                    continue

                startVar = makeSignalPath(
                    [startConModel, signalInterface.variableType.leave]
                )
                endVar = makeSignalPath(
                    [endConModel, signalInterface.variableType.leave]
                )

                # here the signal names from the ontology are used
                # they are separated later with the actual FMU signal names
                c = Connection(
                    startElement=startModel,
                    startConnector=startVar,
                    endElement=endModel,
                    endConnector=endVar,
                )

                templateConnections.append(c)

    # Only add signals to component description which are used in connections
    signalSet = set()

    # replace the signal path with the actual  signal name
    for tempCon in templateConnections:
        startMapping = models[tempCon.startElement].signalMapping
        endMapping = models[tempCon.endElement].signalMapping

        tempCon.startConnector = startMapping[tempCon.startConnector]
        tempCon.endConnector = endMapping[tempCon.endConnector]

        # obtain only the variable name

        signalSet.add(tempCon.startConnector)
        signalSet.add(tempCon.endConnector)

    # create base SSD
    ssdDoc = createBaseSSD()

    # add models (with only used I/O)
    for modelName, modelData in models.items():
        component = createComponent(modelName, modelData, signalSet, FTP_SERVER)
        ssdDoc.system.elements.append(component)

    ssdDoc.system.connections = templateConnections
    ssdDoc.annotations = []

    # add simulation settings
    if template.get("simulationConfiguration"):
        ssdSimSettings = Annotation(type="SimulationSettings")
        ssdSimSettings.append(
            SimulationSettings(
                timeStep=template["simulationConfiguration"]["timeStepSize"],
                stopTime=template["simulationConfiguration"]["simulationTime"],
            )
        )
        ssdDoc.annotations.append(ssdSimSettings)

    # add input data information
    if template.get("inputs"):
        signalList = []
        for signalName in template["inputs"]["signalList"]:
            signalList.append(Signal(signalName))
        ssdInputData = Annotation(type="InputData")
        ssdInputData.append(
            InputData(
                startDate=template["inputs"]["startDate"],
                endDate=template["inputs"]["endDate"],
                signals=signalList,
            )
        )
        ssdDoc.annotations.append(ssdInputData)

    # Write output
    ssdXML = ssd2xml(ssdDoc)
    writeXMLTree(filename, ssdXML)


class URI(str):
    def __new__(cls, value):
        obj = str.__new__(cls, value)
        return obj

    def splitURI(self):
        parts = self.split("#")
        return parts[0], "".join(parts[1:])

    @property
    def stem(self):
        _, parts = self.splitURI()
        return parts

    @property
    def leave(self):
        _, parts = self.splitURI()
        parts = parts.split("/")
        return parts[-1]

    @property
    def base(self):
        base, _ = self.splitURI()
        return base


def convertURI(value):
    return URI(value)


class SparqlHelper:
    resultConversions = {"uri": convertURI}

    def __init__(
        self, sparql_server_name: str, sparql_server_port: str, dataset_name: str
    ):
        sparqlEndpoint = (
            "http://"
            + sparql_server_name
            + ":"
            + sparql_server_port
            + "/"
            + dataset_name
        )
        self.sparql = SPARQLWrapper(sparqlEndpoint)
        self.sparql.setReturnFormat(JSON)

    def convertResult(self, queryResult, queryType):
        bindings = []

        for sparqlResult in queryResult["results"]["bindings"]:
            for var in sparqlResult:
                sparqlResult[var] = self.convertSparqlResult(**sparqlResult[var])

            bindings.append(queryType(**sparqlResult))
        return bindings

    def convertSparqlResult(self, type, value):
        return self.resultConversions[type](value)

    def getFMUSignals(self, fmuName):
        query = f"""PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX : <http://tuwien.ac.at/digiwind/DigiWindOnt#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?signalCausality ?signalName ?signalType WHERE {{
                :FMU.{fmuName} ?signalCausality ?signalName .
                ?signalCausality rdfs:subPropertyOf :has .

                ?signalName rdf:type ?signalType .
                ?signalType rdfs:subClassOf :Signal .
            }}"""
        self.sparql.setQuery(query)

        res = self.sparql.queryAndConvert()

        return self.convertResult(res, QuerySignalMapping)

    def getFMUSignalInterfaces(self, fmuIdentifier):
        query = f"""PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX : <http://tuwien.ac.at/digiwind/DigiWindOnt#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?signalBond ?signalBondType ?signalBondSegment ?variable ?variableType ?variableCausality  WHERE {{
                :{fmuIdentifier}  :hasSignalBond ?signalBond .

                ?variableCausality rdfs:subPropertyOf :has  .
                :{fmuIdentifier} ?variableCausality ?variable .
                {{
                    ?signalBond rdf:type ?signalBondType .
                    ?signalBondType rdfs:subClassOf :PowerBond.

                    ?signalBond ?signalBondSegment ?variable .
                    ?signalBondSegment rdfs:subPropertyOf :binds  .

                }}
                UNION
                {{
                    ?signalBond rdf:type ?signalBondType . # to fill the variable
                    ?signalBond rdf:type :SignalBond .
                    MINUS {{?signalBond rdf:type :PowerBond}} .

                    ?signalBond ?signalBondSegment ?variable .
                    ?signalBond :binds ?variable .
                }}
                ?variable rdf:type ?variableType .
                ?variableType rdfs:subClassOf :Signal.
            }}"""
        self.sparql.setQuery(query)

        res = self.sparql.queryAndConvert()

        return self.convertResult(res, QuerySignalInterface)


def convertSimConfigs(listOfSimConfigs):
    ssdList = []
    for simConfig in listOfSimConfigs:
        # get model I/Os from the ontology
        sparqlHelper = SparqlHelper(
            SPARQL_SERVER_NAME, SPARQL_SERVER_PORT, SPARQL_DATASET_NAME
        )

        models = {}

        for model in simConfig["models"]:
            interfaces = sparqlHelper.getFMUSignalInterfaces(model["identifier"])

            signalMapping = {}
            for signalQuery in interfaces:
                signalCon = signalQuery.signalBond.leave
                signalType = signalQuery.variableType.leave
                signalPath = makeSignalPath([signalCon, signalType])

                signalMapping[signalPath] = signalQuery.variable.leave

            models[model["name"]] = SimulationModel(model, signalMapping, interfaces)

        ssdFilepath = Path("system.ssd")
        assembleModel(ssdFilepath, simConfig, models)

        with open(ssdFilepath.absolute(), "r", encoding="utf-8") as file:
            ssdList.append(file.read().replace("'", '"').replace('"', "\\'"))

    return ssdList


def on_message(client, userdata, msg):
    responseTopic = MQTT_TOPIC + "/response/" + msg.topic.split("/")[-1]

    incomingPayload = msg.payload.decode("utf-8")

    data = json.loads(incomingPayload)
    simulationConfigs = json.loads(data["simulationConfigsString"].replace("'", '"'))

    print("Converting simulation configs into SSD description")
    ssdList = convertSimConfigs(simulationConfigs["simulationConfigs"])

    data = str({"simulationDefinitions": ssdList}).replace('"', "'")

    payload = f'{{"simulationDefinitionsString": "{data}"}}'

    client.publish(responseTopic, payload)


if __name__ == "__main__":
    mqttClient = mqtt.Client("ModelAssemblyService")
    mqttListen = MQTT_TOPIC + "/request/#"
    mqttClient.connect("mqttbroker", 1883)

    mqttClient.subscribe(mqttListen)

    mqttClient.on_message = on_message
    mqttClient.loop_forever()
