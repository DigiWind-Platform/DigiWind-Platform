
from dataclasses import dataclass
from lxml import builder
from lxml import etree
from typing import List

from pathlib import Path

from fmpy.ssp.ssd import (
    SystemStructureDescription,
    Component,
    System,
    Connector,
    Connection,
    ns,
)

ns["dgw"] = "http://digiwind.de"


class Annotation(list):
    def __init__(self, *args, type=None):
        list.__init__(self, *args)
        self.type = type


@dataclass
class SimulationSettings:
    timeStep: float
    stopTime: float


@dataclass
class Signal:
    variableName: str


@dataclass
class InputData:
    startDate: str
    endDate: str
    signals: List[Signal]


# Define element maker
E = builder.ElementMaker(
    nsmap=ns,
    namespace=ns["ssd"]
)

elementMakerSSC = builder.ElementMaker(
    nsmap=ns,
    namespace=ns["ssc"]
)

elementMakerDGW = builder.ElementMaker(
    nsmap=ns,
    namespace=ns["dgw"]
)

# define sub tags for this element // this returns a partial function with the attribute name as the tag
SystemStructureDescriptionXML = E.SystemStructureDescription
SystemXML = E.System
ElementsXML = E.Elements
ComponentXML = E.Component
ConnectionsXML = E.Connections
ConnectionXML = E.Connection
ConnectorXML = E.Connector
ConnectorsXML = E.Connectors

AnnotationsXML = E.Annotations
AnnotationXML = elementMakerSSC.Annotation

# could this be automated?
elementFactoryMapping = {
    SystemStructureDescription: SystemStructureDescriptionXML,
    System: SystemXML,
    "Elements": ElementsXML,
    Component: ComponentXML,
    "Connections": ConnectionsXML,
    Connection: ConnectionXML,
    "Connectors": ConnectorsXML,
    Connector: ConnectorXML,
    "Annotations": AnnotationsXML,
    "Signals": elementMakerDGW.Signals
}


digiWindElements = builder.ElementMaker(namespace=ns["dgw"])


def getFTPLocation(server, modelName):
    return f"ftp://{server}/{modelName}/{modelName}.fmu"


def createComponent(modelName, modelData, signalSet, server=""):

    # this could be read from the ontology later

    cons = []
    writtenVars = []
    for signalQuery in modelData.signalInterfaces:
        varName = signalQuery.variable.leave

        if varName not in signalSet:
            pass

        if varName in writtenVars:
            continue

        variableCausality = signalQuery.variableCausality.leave
        if variableCausality == "hasInputSignal":
            causality = "input"
        elif variableCausality == "hasOutputSignal":
            causality = "output"
        else:
            continue

        con = Connector(name=varName, kind=causality)
        writtenVars.append(varName)
        cons.append(con)

    if server:
        modelPath = getFTPLocation(
            server, modelData.description["identifier"][4:])
    else:
        modelPath = f"resource\\{modelName}.fmu"

    component = Component(
        name=modelName,
        source=modelPath,
        connectors=cons,
        type="application/x-fmu-sharedlibrary"
    )

    return component


def createBaseSSD():

    system = System(
        name="System",
    )

    ssd = SystemStructureDescription(
        system=system,
        name="SystemStructureDescription",
        version="1.0"
    )
    return ssd


def writeXMLTree(filename, xmlTree):

    xmlStr = str(
        etree.tostring(
            xmlTree,
            pretty_print=True,
            xml_declaration=True,
            method="xml",
            encoding="utf-8"
        ),
        "utf-8"
    )

    with open(filename, "w") as xmlFile:
        xmlFile.write(xmlStr)


def ssd2xml(ssd):

    # filter attributes
    elements = {}
    for k, v in ssd.__dict__.items():
        if k == "parent":
            continue
        if type(v) in elementFactoryMapping:
            elements[k] = v
            continue

        if isinstance(v, list):
            if len(v) == 0:
                continue

            elements[k.capitalize()] = v

    # filter attributes
    attributes = {}
    for k, v in ssd.__dict__.items():
        if v is None:
            continue

        if type(v) in elementFactoryMapping:
            continue

        if isinstance(v, list):
            continue

        if isinstance(v, Path):
            v = str(v)

        if isinstance(v, float):
            v = str(v)

        attributes[k] = v

    # create base elmenet and set all attributes
    try:
        factory = elementFactoryMapping[type(ssd)]
        xmlTree = factory(**attributes)
    except KeyError:
        # this could be used to generalize all factories here

        # create the factory with specific namespace
        # create xml tags from class names and collected attributes
        xmlTree = digiWindElements(ssd.__class__.__name__, **attributes)

    # create child elements recursively and append them to their parent element
    for k, el in elements.items():
        if isinstance(el, list):
            factory = elementFactoryMapping[k]

            xmlSubtree = factory()
            for listEL in el:
                if isinstance(listEL, Annotation):
                    xmlChild = AnnotationXML(type=listEL.type)
                    for an in listEL:
                        anElement = ssd2xml(an)
                        xmlChild.append(anElement)
                else:
                    xmlChild = ssd2xml(listEL)
                xmlSubtree.append(xmlChild)
            xmlTree.append(xmlSubtree)
        else:
            xmlChild = ssd2xml(el)
            xmlTree.append(xmlChild)

    return xmlTree
