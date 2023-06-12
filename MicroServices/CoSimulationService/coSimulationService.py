import json
import os
import shutil
import zipfile
from dataclasses import dataclass
from ftplib import FTP
from io import StringIO
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import paho.mqtt.client as mqtt
import pandas as pd
from fmpy.ssp.simulation import add_path
from fmpy.ssp.simulation import do_step
from fmpy.ssp.simulation import extract
from fmpy.ssp.simulation import find_components
from fmpy.ssp.simulation import find_connectors
from fmpy.ssp.simulation import free_fmu
from fmpy.ssp.simulation import get_connections

# from fmpy.ssp.simulation import instantiate_fmu
from fmpy.ssp.simulation import set_parameters
from fmpy import read_model_description
from fmpy.fmi1 import FMU1Slave
from fmpy.fmi2 import FMU2Slave
from fmpy.ssp.ssd import ParameterSet
from fmpy.ssp.ssd import Parameter
from fmpy.ssp.ssd import System
from fmpy.ssp.ssd import SystemStructureDescription
from fmpy.ssp.ssd import Unit
from fmpy.ssp.ssd import add_tree_info
from fmpy.ssp.ssd import handle_system
from fmpy.ssp.ssd import validate_tree
from lxml import etree

from ssdToolbox import Annotation
from ssdToolbox import InputData
from ssdToolbox import Signal
from ssdToolbox import SimulationSettings
from ssdToolbox import ns
from ssdToolbox import ssd2xml
from ssdToolbox import writeXMLTree

MQTT_TOPIC = os.environ.get("MQTT_TOPIC")
MQTT_TOPIC_DATA = os.environ.get("MQTT_TOPIC_DATA")
FTP_SERVER = os.environ.get("FTP_SERVER")
FTP_PORT = int(os.environ.get("FTP_PORT"))


@dataclass
class ExperimentSettings:
    stopTime: float
    macroStepSize: float
    parameterSet: ParameterSet = None


def handleAnnotations(ssd):
    """create all objects to represent all annotation settings"""
    annos = []
    for c in ssd.findall("ssd:Annotations/ssc:Annotation", namespaces=ns):
        annoType = c.get("type")
        if annoType == "SimulationSettings":
            s = c.find("dgw:SimulationSettings", namespaces=ns)
            simSettings = SimulationSettings(
                timeStep=float(s.get("timeStep")), stopTime=float(s.get("stopTime"))
            )
            annos.append(Annotation([simSettings], type="SimulationSettings"))
        elif annoType == "InputData":
            inEl = c.find("dgw:InputData", namespaces=ns)

            signals = inEl.findall("dgw:Signals/dgw:Signal", namespaces=ns)

            signalList = []
            for s in signals:
                signalList.append(Signal(s.get("variableName")))

            inData = InputData(inEl.get("startDate"), inEl.get("endDate"), signalList)
            annos.append(Annotation([inData], type="InputData"))

    return annos


def read_ssd(filename, validate=True):
    with open(filename, "r", encoding="utf-8") as f:
        tree = etree.parse(f)

    root = tree.getroot()

    if validate:
        validate_tree(root, "SystemStructureDescription.xsd")

    ssd = SystemStructureDescription()

    ssd.version = root.get("version")
    ssd.name = root.get("name")

    # Units
    for u in root.findall("ssd:Units/ssc:Unit", namespaces=ns):
        attr = dict(u.attrib)
        bu = u.find("ssc:BaseUnit", namespaces=ns)
        attr.update(bu.attrib)
        ssd.units.append(Unit(**attr))
    ssd.system = System()

    system = root.find("ssd:System", namespaces=ns)

    ssd.system = handle_system(system, filename=filename)

    # add parent elements
    add_tree_info(ssd.system)
    ssd.system.parent = None

    annotations = handleAnnotations(root)
    ssd.annotations = annotations

    return ssd


def createSSPPackage(ssdFilepath):
    if not isinstance(ssdFilepath, Path):
        ssdFilepath = Path(ssdFilepath)

    workDir = Path.cwd()

    tempSSD = workDir / "SystemStructure.ssd"

    shutil.copy(ssdFilepath, tempSSD)

    ssdFile = read_ssd(tempSSD)

    components = ssdFile.system.elements

    filelist = {}

    # download files
    with FTP() as ftp:
        ftp.connect(FTP_SERVER, FTP_PORT)
        ftp.login(user="digiwind", passwd="digiwind_pw")
        ftp.encoding = "utf-8"

        for comp in components:
            sourceUrl = urlparse(comp.source).path[1:]
            sourcePath = Path(sourceUrl)

            # maybe check if anchor is ftp

            pathElements = sourcePath.parts[:-1]
            ftpFile = sourcePath.name

            for p in pathElements:
                ftp.cwd(p)

            filename = workDir / sourcePath
            filename.parent.mkdir(exist_ok=True)

            # Write file in binary mode
            with open(filename, "wb") as file:
                # Command for Downloading the file "RETR filename"
                ftp.retrbinary(f"RETR {ftpFile}", file.write)
            ftp.cwd("/")

            # update paths in ssd object
            comp.source = filename.relative_to(workDir)
            filelist[comp.name] = comp.source

    # Update paths in system structure file
    xmlData = ssd2xml(ssdFile)
    writeXMLTree(tempSSD, xmlData)

    # create zip file
    zipFilepath = workDir / "System.ssp"
    with zipfile.ZipFile(zipFilepath, "w") as zp:
        zp.write(tempSSD.relative_to(workDir))

        for fmuPath in filelist.values():
            zp.write(fmuPath)

    # delete temporary files from workDir
    os.remove(tempSSD)
    for fmuPath in filelist.values():
        shutil.rmtree(fmuPath.parent)

    return zipFilepath, ssdFile


def instantiate_fmu(
    component, ssp_unzipdir, start_time, stop_time=None, parameter_set=None
):
    """Instantiate an FMU"""

    fmu_filename = os.path.join(ssp_unzipdir, component.source)

    component.unzipdir = extract(fmu_filename)

    # read the model description
    model_description = read_model_description(fmu_filename, validate=False)

    if model_description.coSimulation is None:
        raise Exception("%s does not support co-simulation." % component.source)

    # collect the value references
    component.variables = {}
    for variable in model_description.modelVariables:
        # component.vrs[variable.name] = variable.valueReference
        component.variables[variable.name] = variable

    fmu_kwargs = {
        "guid": model_description.guid,
        "unzipDirectory": component.unzipdir,
        "modelIdentifier": model_description.coSimulation.modelIdentifier,
        "instanceName": component.name,
    }

    if model_description.fmiVersion == "1.0":
        component.fmu = FMU1Slave(**fmu_kwargs)
        component.fmu.instantiate()
        if parameter_set is not None:
            set_parameters(component, parameter_set)
        component.fmu.initialize(stopTime=stop_time)
    else:
        component.fmu = FMU2Slave(**fmu_kwargs)
        component.fmu.instantiate()
        component.fmu.setupExperiment(startTime=start_time)
        if parameter_set is not None:
            set_parameters(component, parameter_set)
        """
        component.fmu.enterInitializationMode()
        component.fmu.exitInitializationMode()
        """


def simulate_ssp(
    ssp_filename,
    start_time=0.0,
    stop_time=None,
    step_size=None,
    parameter_set=None,
    input={},
    fmuStates=None,
):
    """Simulate a system of FMUs"""
    initialValueMapping = {
        "damageBladeFlapwise": "initialDamageBladeFlapwise",
        "damageBladeEdgewise": "initialDamageBladeEdgewise",
        "damageHubMx": "initialDamageHubMx",
        "damageHubMy": "initialDamageHubMy",
        "damageHubMz": "initialDamageHubMz",
        "damageTowerForeAft": "initialDamageTowerForeAft",
        "damageTowerSideSide": "initialDamageTowerSideSide",
    }

    if stop_time is None:
        stop_time = 1.0

    if step_size is None:
        step_size = stop_time * 1e-2

    with zipfile.ZipFile(ssp_filename, "r") as zf:
        xml = zf.open("SystemStructure.ssd").read()

    # this must be unified with other functions; currently this causes a lot of file writing
    ssd_filename = "temp.ssd"
    with open(ssd_filename, "w", encoding="utf-8") as f:
        f.write(xml.decode("utf-8"))

    ssd = read_ssd(ssd_filename)

    add_path(ssd.system)

    components = find_components(ssd.system)
    connectors = find_connectors(ssd.system)
    connections = get_connections(ssd.system)

    # resolve connections
    connections_reversed = {}

    for a, b in connections:
        connections_reversed[b] = a

    new_connections = []

    # trace connections back to the actual start connector
    for a, b in connections:
        while isinstance(a.parent, System) and a.parent.parent is not None:
            a = connections_reversed[a]

        new_connections.append((a, b))

    connections = new_connections

    # extract the SSP
    ssp_unzipdir = extract(ssp_filename)

    # initialize the connectors
    for connector in connectors:
        connector.value = 0.0

    # instantiate the FMUs
    for component in components:
        instantiate_fmu(component, ssp_unzipdir, start_time, stop_time, parameter_set)

    # set states from previous simulation
    for component in components:
        if fmuStates:
            for varName, var in component.variables.items():
                value = fmuStates[component.name][varName]

                # set_value(component, varName, value)

        component.fmu.enterInitializationMode()
        component.fmu.exitInitializationMode()

    time = start_time

    rows = []  # list to record the results

    # simulation loop
    while time < stop_time:
        # apply input
        for connector in ssd.system.connectors:
            if connector.kind == "input" and connector.name in input:
                connector.value = input[connector.name](time)

        # perform one step
        for component in components:
            do_step(component, time, step_size)

        # apply connections
        for start_connector, end_connector in connections:
            end_connector.value = start_connector.value

        # get the results
        row = [time]

        for connector in connectors:
            row.append(connector.value)

        # append the results
        rows.append(tuple(row))  # TODO track all connectors and all outputs!

        # advance the time
        time += step_size

    # free the FMUs
    stateDict = {}
    for component in components:
        vr = []
        vrMapping = {}
        for i, (name, var) in enumerate(component.variables.items()):
            vrMapping[i] = name
            vr.append(var.valueReference)

        values = component.fmu.getReal(vr)
        stateDict[component.name] = {v: values[k] for k, v in vrMapping.items()}

        free_fmu(component)

    # save output variables for initialization parameters
    initialParamList = []
    for component in components:
        for varName, var in component.variables.items():
            if varName not in initialValueMapping:
                continue

            if component.name == "AD8_Damage":
                continue

            initParam = initialValueMapping[varName]

            value = stateDict[component.name][varName]

            p = Parameter(name=f"{component.name}.Parameters.{initParam}", value=value)
            initialParamList.append(p)
    initSet = ParameterSet(parameters=initialParamList)

    # clean up
    shutil.rmtree(ssp_unzipdir)

    dtype = [("time", np.float64)]

    for connector, value in zip(connectors, rows[0][1:]):
        if type(value) == bool:
            dtype.append((connector.path, np.bool_))
        elif type(value) == int:
            dtype.append((connector.path, np.int32))
        else:
            dtype.append((connector.path, np.float64))

    # convert the results to a structured NumPy array
    return np.array(rows, dtype=np.dtype(dtype)), stateDict, initSet


def loadInputData(inputData: InputData):
    payload = {
        "timerange": {"start": inputData.startDate, "end": inputData.endDate},
        "variables": [s.variableName for s in inputData.signals],
    }

    userdata = {"waiting": True}

    def dataReceivedCallback(client, userdata, msg):
        # write data to input.csv file
        inputPath = Path.cwd() / "input.csv"

        with open(inputPath, "w", encoding="utf-8") as f:
            measurementData = msg.payload.decode("utf-8")
            f.write(measurementData)

        client._userdata["waiting"] = False

    mqttClient = mqtt.Client("CoSimulationService_DataRequest", userdata=userdata)
    mqttListenData = MQTT_TOPIC_DATA + "/response/#"
    mqttClient.connect("mqttbroker", 1883)

    mqttClient.subscribe(mqttListenData)

    mqttClient.on_message = dataReceivedCallback
    mqttClient.publish(
        "dw/services/dataservice/request/1", str(payload).replace("'", '"')
    )

    mqttClient.loop_start()

    while mqttClient._userdata["waiting"]:
        continue

    mqttClient.loop_stop()


def main(listOfSSDStrings):
    stateDict = None
    initSet = None
    listOfResults = []
    timeStep = 0.1
    print(f"got simulation request for {len(listOfSSDStrings)} simulations")
    for i, ssdString in enumerate(listOfSSDStrings):
        ssdFilePath = Path(f"payload_{i}.ssd")

        with open(ssdFilePath.absolute(), "w", encoding="utf-8") as file:
            file.write(ssdString)

        sspFilePath, ssdObject = createSSPPackage(ssdFilePath)

        # handle input data (pull from measurement service)
        inputData = filter(
            lambda x: x.type == "InputData", ssdObject.annotations
        ).__next__()[0]

        loadInputData(inputData)

        experimentSettings = filter(
            lambda x: x.type == "SimulationSettings", ssdObject.annotations
        ).__next__()[0]

        # this ssp file is not correctly written!

        print(
            f"Start simulation {i} (stopTime: {experimentSettings.stopTime}, comInterval: {experimentSettings.timeStep}"
        )
        result, stateDict, initSet = simulate_ssp(
            sspFilePath,
            stop_time=experimentSettings.stopTime,
            step_size=experimentSettings.timeStep,
            parameter_set=initSet,
            fmuStates=stateDict,
        )
        print(f"Simulation {i} finished")
        df = pd.DataFrame(data=result, columns=result.dtype.names)
        listOfResults.append(df)

    endTime = listOfResults[0]["time"].iloc[-1]

    for df in listOfResults[1:]:
        df["time"] += endTime + timeStep

    resultDf = pd.concat(listOfResults, ignore_index=True)

    return resultDf


def on_message(client, userdata, msg):
    responseTopic = MQTT_TOPIC + "/response/" + msg.topic.split("/")[-1]

    incomingPayload = msg.payload.decode("utf-8")

    data = json.loads(incomingPayload)
    # this string conversion does not work because the xml string has also strings inside which break the json
    data["simulationDefinitionsString"] = data["simulationDefinitionsString"].replace(
        "'", '"'
    )
    data["simulationDefinitionsString"] = data["simulationDefinitionsString"].replace(
        '\\\\"', "'"
    )
    # remove newline characters
    data["simulationDefinitionsString"] = data["simulationDefinitionsString"].replace(
        "\n", ""
    )

    simulationDefinitions = json.loads(data["simulationDefinitionsString"])
    listOfSSDStrings = simulationDefinitions.get("simulationDefinitions")

    df = main(listOfSSDStrings)

    textStream = StringIO()
    df.to_csv(textStream, index=False)

    payload = {"coSimulationResult": textStream.getvalue()}
    client.publish(responseTopic, str(payload))


if __name__ == "__main__":
    mqttClient = mqtt.Client("CoSimulationService")
    mqttListen = MQTT_TOPIC + "/request/#"
    mqttClient.connect("mqttbroker", 1883)

    mqttClient.subscribe(mqttListen)

    mqttClient.on_message = on_message
    mqttClient.loop_forever()
