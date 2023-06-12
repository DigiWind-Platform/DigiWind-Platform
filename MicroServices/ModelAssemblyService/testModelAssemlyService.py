import json
import pprint
from pathlib import Path

from modelAssembly import convertSimConfigs


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)

    basePath = Path(__file__).parent.parent.parent

    templatePath = Path(basePath, "response.json")

    # load simulation template
    with open(templatePath.absolute(), "r", encoding="utf-8") as file:
        template = json.load(file)
    print(template)

    ssdList = convertSimConfigs(template["simulationConfigs"])
    for i, ssdString in enumerate(ssdList):
        with open(f"ssd_res_{i}.ssd", "w", encoding="utf-8") as file:
            file.write(ssdString)
