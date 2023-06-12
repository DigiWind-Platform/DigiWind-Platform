# Model Assembly Service

## MQTT

The MQTT Topic is: `dw/services/mas`

The services answers with a MQTT response.

## Expected Input Payload

A json Template file with references to the model identifiers.

```json
{
    "ssdStrings": [
        "<sim_1 as json-string>",
        "<sim_2 as json-string>",
        "<sim_3 as json-string>",
        ...
    ]
}
```

*Note: JSON requires to have the `"` symbol for surrounding keywords and strings. Therefore, it is needed to escape the `"` symbol by `\"` in the `<json-string>`.*

## Expected Output Payload

A JSON with a XML string according to the SSP Standard with FTP links in the model source
attribute.

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