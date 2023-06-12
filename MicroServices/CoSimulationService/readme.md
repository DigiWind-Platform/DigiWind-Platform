# Co-Simulation Service

## MQTT

The MQTT Topic is: `dw/services/cosim`

The services answers with...

## Expected Input Payload

A json Template file with an SSD description for the simulation and further instructions e.g. simulation time and step size.

```json
{
    "simulationConfigs": [
        "<sim_1 as ssd-xml-string>",
        "<sim_2 as ssd-xml-string>",
        "<sim_3 as ssd-xml-string>",
        ...
    ]
}
```

## Expected Output Payload

One CSV file with continues simulation results from all inputs files:

|time|generator.rotationSpeed|generator.emTorque|windTurbine.windSpeed|
|----|-----------------------|------------------|---------------------|
|0.0 |0.0                    |0.0               |0.0                  |
|0.1 |0.0                    |0.0               |0.0                  |


The result is send also via mqtt message with payload as:
```json
{
    "coSimulationResult": "<csv-string>"
}
```