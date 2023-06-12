import json
import logging
import os
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from distutils.version import StrictVersion
from pathlib import Path
from typing import Dict
from typing import List

import paho.mqtt.client as mqtt
from SPARQLWrapper import JSON
from SPARQLWrapper import SPARQLWrapper

SPARQL_SERVER_NAME = os.environ.get("SPARQL_SERVER_NAME")
SPARQL_SERVER_PORT = os.environ.get("SPARQL_SERVER_PORT")
SPARQL_DATASET_NAME = os.environ.get("SPARQL_DATASET_NAME")


LOG_DIRECTORY = Path().absolute() / "app" / "logs"
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIRECTORY / "debug.log"


MQTT_TOPIC = os.environ.get("MQTT_TOPIC")

logging.basicConfig(
    handlers=[logging.FileHandler(LOG_FILE, mode="a"), logging.StreamHandler()],
    format="%(asctime)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
)


@dataclass
class QueryModelInfo:
    name: str
    identifier: str
    fmuType: str
    startOfValidity: datetime
    endOfValidity = None

    @property
    def version(self):
        vString = self.identifier.split("_V_")[1]
        return vString.replace("_", ".")


class URI(str):
    def __new__(cls, value):
        obj = str.__new__(cls, value)
        return obj

    def splitURI(self):
        parts = self.split("#")
        return parts[0], "".join(parts[1:])

    @property
    def base(self):
        base, _ = self.splitURI()
        return base

    @property
    def model(self):
        _, model = self.splitURI()
        return model


class SparqlHelper:
    resultConversions = {"uri": URI, "literal": str}

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
        logging.debug(f"Connecting to Sparql server {sparqlEndpoint}")
        self.sparql = SPARQLWrapper(sparqlEndpoint)
        self.sparql.setReturnFormat(JSON)

    def convertResult(self, queryResult, queryType):
        bindings = []

        for sparqlResult in queryResult["results"]["bindings"]:
            for var in sparqlResult:
                sparqlResult[var] = self.convertSparqlResult(**sparqlResult[var])

            bindings.append(queryType(**sparqlResult))
        return bindings

    def convertSparqlResult(self, type, value, datatype=""):
        if datatype == "http://www.w3.org/2001/XMLSchema#dateTime":
            return datetime.fromisoformat(value)

        return self.resultConversions[type](value)

    def getAllModelVersions(self, identifier, fmuType):
        query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX ont: <http://tuwien.ac.at/digiwind/DigiWindOnt#>

            SELECT ?identifier  ?name ?fmuType ?startOfValidity
            WHERE {{
                ?identifier rdf:type ?fmuType .

                FILTER(?fmuType = ont:{fmuType})

                ?identifier ont:hasName ?name .
                ?identifier ont:hasName "{identifier}" .

                ?identifier ont:startOfValidity ?startOfValidity .
            }}"""

        self.sparql.setQuery(query)
        res = self.sparql.queryAndConvert()

        return self.convertResult(res, QueryModelInfo)


def determineTimeFrame(simulationConfig: dict):
    startDate = datetime.strptime(simulationConfig["startDate"], "%Y-%m-%dT%H:%M:%SZ")
    startDate = startDate.replace(tzinfo=timezone.utc)
    endDate = datetime.strptime(simulationConfig["endDate"], "%Y-%m-%dT%H:%M:%SZ")
    endDate = endDate.replace(tzinfo=timezone.utc)
    return startDate, endDate


@dataclass
class SimulationSlice:
    startDate: datetime
    endDate: datetime
    models: Dict[str, QueryModelInfo]


@dataclass
class SimulationConfig:
    timeStepSize: float
    simulationTime: float


@dataclass
class InputData:
    startDate: str
    endDate: str
    signalList: List[str]


@dataclass
class SimulationModel:
    name: str
    type: str
    identifier: str
    connections: List
    inputs: List = field(default_factory=list)


@dataclass
class SimulationSetup:
    models: List[SimulationModel]
    inputs: InputData
    simulationConfiguration: SimulationConfig


def obj2dict(obj):
    if not hasattr(obj, "__dict__"):
        return obj
    result = {}
    for key, val in obj.__dict__.items():
        if key.startswith("_"):
            continue
        element = []
        if isinstance(val, list):
            for item in val:
                element.append(obj2dict(item))
        else:
            element = obj2dict(val)
        result[key] = element
    return result


def filterModelVersions(
    modelCollections: List[QueryModelInfo], startDate: datetime, endDate: datetime
) -> List[SimulationSlice]:
    # setup simulations slices
    simulationDateSlices = []
    for name, models in modelCollections.items():
        dates = [
            m.startOfValidity
            for m in models
            if m.startOfValidity >= startDate and m.startOfValidity < endDate
        ]
        simulationDateSlices += dates
    simulationDateSlices = sorted(list(set(simulationDateSlices)))
    if simulationDateSlices[0] != startDate:
        simulationDateSlices.insert(0, startDate)
    simulationDateSlices.append(endDate)

    simulationSlices = []
    for sliceStart, sliceEnd in zip(simulationDateSlices, simulationDateSlices[1:]):
        simulationModels = {}
        for name, models in modelCollections.items():
            modelsInSlice = [
                m
                for m in models
                if m.startOfValidity <= sliceStart and m.endOfValidity >= sliceEnd
            ]

            latestVersion = max(
                modelsInSlice,
                key=lambda x: StrictVersion(x.version),
                default=max(models, key=lambda x: StrictVersion(x.version)),
            )

            simulationModels[name] = latestVersion
        simulationSlices.append(SimulationSlice(sliceStart, sliceEnd, simulationModels))

    return simulationSlices


def determineEndDates(listOfModels: List[QueryModelInfo]):
    sortedModels = sorted(listOfModels, key=lambda x: StrictVersion(x.version))

    endDates = {}
    for model in sortedModels:
        majorVersion, _, _ = StrictVersion(model.version).version
        endDates[majorVersion] = model.startOfValidity

    maxDate = datetime.max.replace(tzinfo=timezone.utc)
    for model in sortedModels:
        majorVersion, _, _ = StrictVersion(model.version).version
        model.endOfValidity = endDates.get(majorVersion + 1, maxDate)

    return sortedModels


def resolveTemplate(template: dict, spqlHelper: SparqlHelper) -> List[dict]:
    startDate, endDate = determineTimeFrame(template["simulationConfiguration"])

    # simulaiton settings

    # external measurement data
    models = template["models"]
    signals = []
    for model in models:
        requiredSignals = model.get("inputs", [None])
        signals += requiredSignals
    signals = list(set(signals))

    # determine models
    modelCollections = {}
    for model in models:
        name = model["name"]
        fmuType = model["type"]

        # get all versions for specified model
        logging.debug(f"search model versions for {name} and {fmuType}")
        modelInfos = spqlHelper.getAllModelVersions(name, fmuType)
        modelInfos = determineEndDates(modelInfos)

        modelCollections[name] = modelInfos
        logging.debug(f"found models for {name}: {modelInfos}")

    simulationModels = filterModelVersions(modelCollections, startDate, endDate)

    # make simulations templates
    resolvedTemplates = []
    for sm in simulationModels:
        inputData = InputData(
            datetime.strftime(sm.startDate, "%Y-%m-%dT%H:%M:%SZ"),
            datetime.strftime(sm.endDate, "%Y-%m-%dT%H:%M:%SZ"),
            signals,
        )

        simSliceDuration = sm.endDate - sm.startDate
        simConfig = SimulationConfig(
            timeStepSize=template["simulationConfiguration"]["timeStepSize"],
            simulationTime=simSliceDuration.total_seconds(),
        )
        logging.debug(f"simulation config: {simConfig}")

        simModels = []
        for model in models:
            name = model["name"]
            fmuType = model["type"]
            connections = model["connections"]
            inputs = model["inputs"]

            simModel = SimulationModel(
                name=name,
                type=fmuType,
                identifier=sm.models[name].identifier.model,
                connections=connections,
                inputs=inputs,
            )
            simModels.append(simModel)

        simSetup = SimulationSetup(
            models=simModels, inputs=inputData, simulationConfiguration=simConfig
        )
        resolvedTemplates.append(simSetup)

    return resolvedTemplates


def on_message(client, userdata, msg):
    jsonData = msg.payload.decode("utf-8")
    responseTopic = MQTT_TOPIC + "/response/" + msg.topic.split("/")[-1]

    template = json.loads(jsonData)
    template = json.loads(template.get("template").replace("'", '"'))

    spqlHelper = SparqlHelper(
        SPARQL_SERVER_NAME, SPARQL_SERVER_PORT, SPARQL_DATASET_NAME
    )

    resolvedTemplates = resolveTemplate(template, spqlHelper)

    listOfSimConfigs = []
    for temp in resolvedTemplates:
        # jsonString = json.dumps(obj2dict(temp)).replace('"', "'")
        # listOfSimConfigs.append(jsonString)
        listOfSimConfigs.append(obj2dict(temp))
    print(
        f"received template and generated {len(listOfSimConfigs)} simulation specifications"
    )

    data = {"simulationConfigs": listOfSimConfigs}

    payload = f'{{"simulationConfigsString": "{data}"}}'

    client.publish(responseTopic, payload)


if __name__ == "__main__":
    mqttClient = mqtt.Client("TemplateService")
    subTopic = MQTT_TOPIC + "/request/#"
    mqttClient.connect("mqttbroker", 1883)

    mqttClient.subscribe(subTopic)

    mqttClient.on_message = on_message
    mqttClient.loop_forever()
