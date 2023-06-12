# Template Service

The service receives a simulation template and pulls information about valid
models for the required simulation time. The process determine valid models and
create simulation instructions for each group of valid models.

## MQTT

The MQTT Topic is: `dw/services/template`

The services answers with a MQTT response.

## Expected Input Payload

A json Template file with name, type and connection specification. 

```json
{
    "template": "<json-string>"
}
```

*Note: JSON requires to have the `"` symbol for surrounding keywords and strings. Therefore, it is needed to escape the `"` symbol by `\"` in the `<json-string>`.*

## Expected Output Payload

A JSON with a XML string according to the SSP Standard with FTP links in the model source
attribute.

```json
{
    "simulationConfigs": [
        "<sim_1 as json-string>",
        "<sim_2 as json-string>",
        "<sim_3 as json-string>",
        ...
    ]
}
```
