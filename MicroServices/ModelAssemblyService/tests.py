from modelAssembly import URI
from modelAssembly import ssd2xml
from modelAssembly import writeXMLTree
from modelAssembly import Connection
from modelAssembly import createBaseSSD
from ssdToolbox import Annotation
from ssdToolbox import SimulationSettings
from ssdToolbox import InputData
from ssdToolbox import Signal
from fmpy.ssp.ssd import read_ssd
from ftplib import FTP

from fmpy.ssp.ssd import (
    SystemStructureDescription,
    Component,
    System,
    Connector,
    Connection,
    ns,
)


def createSSDExample():
    con = Connector(name="system", kind="input")

    con2 = Connector(name="system", kind="output")
    connectors = [con, con, con2]

    component = Component(name="system", source="fmu/test.fmu", connectors=connectors)

    components = [component, component]

    connection = Connection(
        startElement="a",
        startConnector="a",
        endElement="b",
        endConnector="b",
    )
    connections = [connection, connection]

    ssd = createBaseSSD()
    ssd.system.connections = connections
    ssd.system.elements = components
    a = Annotation(type="SimulationSettings")
    s = SimulationSettings(1.0, 1.0)
    a.append(s)
    b = Annotation(type="InputData")
    s1 = Signal("test")
    s2 = Signal("test2")
    s3 = Signal("test3")
    s = InputData("123", "123", [s1, s2, s3])
    b.append(s)
    ssd.annotations = [a, b]

    return ssd


def testXMLConversion():
    ssd = createSSDExample()
    ssdXML = ssd2xml(ssd)
    writeXMLTree("test.ssd", ssdXML)

    ssdFile = read_ssd("Schablone_v0.ssp")
    ssdXML = ssd2xml(ssdFile)
    writeXMLTree("extremeTest.ssd", ssdXML)


if __name__ == "__main__":
    # ftp = FTP()
    # ftp.connect("localhost", 2121)
    # ftp.login(user="digiwind", passwd="digiwind_pw")
    # ftp.dir()
    # ftp.quit()

    print(
        URI(
            "http://tuwien.ac.at/digiwind/DigiWindOnt#FMU/windTurbine/PowerBond/aerodynamicPort"
        ).stem
    )
    print(
        URI(
            "http://tuwien.ac.at/digiwind/DigiWindOnt#FMU/windTurbine/PowerBond/aerodynamicPort"
        ).leave
    )
    print(
        URI(
            "http://tuwien.ac.at/digiwind/DigiWindOnt#FMU/windTurbine/PowerBond/aerodynamicPort"
        ).base
    )
    print(
        URI(
            "http://tuwien.ac.at/digiwind/DigiWindOnt#FMU/windTurbine/PowerBond/aerodynamicPort"
        ).endswith("Port")
    )
    print(URI("http://tuwien.ac.at/digiwind/DigiWindOnt#AerodynamicPort").leave)

    testXMLConversion()
