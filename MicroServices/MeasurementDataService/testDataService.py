import datetime
from pathlib import Path
from dataService import read_csv, fpath


if __name__ == "__main__":
    
    timerange = {
        "start": datetime.datetime(2021, 1, 1, 6, 0, 0),
        "end": datetime.datetime(2021, 1, 1, 12, 0, 0)
    }

    variables = [
        "windSpeed",
    ]
    print(Path(fpath).absolute)

    # Delete comment for testing purpose
    data = read_csv(fpath, timerange, variables)
    print(data)
