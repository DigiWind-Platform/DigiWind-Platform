# FMU Manager GUI

This GUI in explorer style can be run by executing the DigiWind_GUI_main.py file. It can be used to make the upload and management of your FMU models easier. 

Per default the path on your local system used to upload FMUs is set to your Desktop. If you want to change it to a specific location where your FMUs are stored please provide the path when running the GUI file:

> `python .\DigiWind_GUI_main.py 'C:\Users\username\FMUFolder'`

Following validations are included in the GUI:
- valid JSON when uploading a new FMU
- no mandatory fields undefined
- correct date format for start of validity 
- unique FMU name otherwise it is recommended to use the update form
- correct file extension: .fmu

The GUI handles the versioning of the models automatically. If you are not using the GUI, please update the version numbers manually whenever you are creating or updating a model. 


## Metadata JSON Description

The metadata is defined in json files with separate parts for general model description and interface data.
First, the model type and name, and type from the ontology must be specified.
For the automated versioning, the user provides a "start of validity" timestamp. Additionally, the user can add a reference id for further model management.

```json
{
	"metaInformation": {
		"type": "WindTurbineFMU",
		"name": "MyWindTurbine",
		"startOfValidity": "2023-01-01T00:00:00",
		"referenceID": "1.0"
	},
```

Then all signal or power bonds are defined.
They get a individual name, and a specific type type from the ontology.
Currently, all signals must be combined into some bond.
Available types are general signal bond or power bonds.

```json
	"signalBonds": {
		"controllerConnector": {
			"type": "SignalBond",
			"binds": [
				"generatorSpeed",
				"collectivePitchAngle",
				"electroMagneticTorque",
			]
		},
		"electricalPort": {
			"type": "Electrical",
			"asFlow": "generatorCurrent",
			"asEffort": "generatorVoltage"
		},
	},
```

In the end, the user must assign ontology class names to all signals from the FMU.
```json
	"signals": {
        "generatorSpeed": "GeneratorSpeed",
        "collectivePitchAngle": "PitchAngleSetpoint",
        "electroMagneticTorque": "TorqueSet",
        "generatorVoltage": "Voltage",
        "generatorCurrent": "Current",
	}
}

```