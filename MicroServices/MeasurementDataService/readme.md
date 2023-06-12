# Measurement Data Service

The measurement data service can be used to stream data from a .csv file into another service. We provided random generated input data in the example_data.csv. If you want to use your own measurement data, please replace the file and define the fpath variable in dataService.py accordingly. 

## MQTT

The MQTT Topic is: `dw/services/dataservice`

## Expected Input Payload 

To use the service following input is required:
- timerange (JSON) with two keys:
    - start
    - end
- variables (Array) with the variables defined as Strings 

Example:

    {
        "timerange" : {
            "start": "2021-01-01T00:00:00Z",
            "end": "2021-01-31T00:00:00Z"
        },
        "variables" : [
            "windSpeed",
        ]
    }

## Expected Output Payload

For the example input with the given .csv the expected output is:

    timestamp,windSpeed

    2021-01-01 06:00:00,5.859955348650627

    2021-01-01 06:10:00,6.232952096525826

    [...]

    2021-01-01 11:50:00,4.473208376153272

    2021-01-01 12:00:00,4.51893443601923
