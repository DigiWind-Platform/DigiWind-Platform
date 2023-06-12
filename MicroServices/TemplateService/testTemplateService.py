import json
import os
import pprint
from pathlib import Path

from templateService import SparqlHelper
from templateService import resolveTemplate
from templateService import obj2dict

SPARQL_SERVER_NAME = os.environ.get('SPARQL_SERVER_NAME')
SPARQL_SERVER_PORT = os.environ.get('SPARQL_SERVER_PORT')
SPARQL_DATASET_NAME = os.environ.get('SPARQL_DATASET_NAME')


if __name__ == "__main__":

    pp = pprint.PrettyPrinter(indent=4)

    basePath = Path(__file__).parent

    templatePath = Path(
        #basePath, r"Template_MAS_Small_General_MetaInfo_Input.json"
        basePath, r"DummyModelTest.json"
    )

    # load simulation template
    with open(templatePath.absolute(), "r", encoding="utf-8") as file:
        template = json.load(file)

    spqlHelper = SparqlHelper(
        SPARQL_SERVER_NAME,
        SPARQL_SERVER_PORT,
        SPARQL_DATASET_NAME
    )
    resolvedTemplates = resolveTemplate(template, spqlHelper)
    """
    for i, ss in enumerate(resolvedTemplates):
        with open(f"template_{i}.json", "w") as fp:
            json.dump(my_dict(ss), fp)
    for t in resolvedTemplates:
        print(t)
    """
    listOfSimConfigs = []
    for temp in resolvedTemplates:
        jsonString = json.dumps(obj2dict(temp)).replace('"', "'")
        listOfSimConfigs.append(jsonString)

    payload = f'{{"simulationConfigs": {listOfSimConfigs}}}'
    with open("response.json", "w", encoding="utf-8") as fp:
        fp.write(payload)
