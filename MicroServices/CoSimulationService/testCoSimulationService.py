import pprint
from pathlib import Path

from coSimulationService import main


if __name__ == "__main__":

    pp = pprint.PrettyPrinter(indent=4)

    basePath = Path(__file__).parent

    # load simulation template
    listOfSSDs = []
    for i in range(2):
        p = Path(basePath, f"../../ssd_res_{i}.ssd")
        print(p)
        listOfSSDs.append(p.read_text())

    print(listOfSSDs)
    df = main(listOfSSDStrings=listOfSSDs)

    df.to_csv("result.csv")
