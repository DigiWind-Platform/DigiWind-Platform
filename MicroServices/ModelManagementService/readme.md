# Model Management Service

This service manages FMI models and their metadata by adding the path to each FMI and the respective metadata into the DigiWind ontology.

For this, the fmu folder has to follow a strict folder structure. Each folder only has to have one FMI and one metadata file.
For example:

fmu-folder\
| - generatorV1.0\
| - | generatorV1.0.fmu\
| - | metadata.json\
| - windTurbineV1.0\
| - | windTurbineV1.0.fmu\
| - | metadata.json\

The ontology folder has to contain the specified ontology file, which is used to populate the triple store with the basic ontological concepts.

Important:
- identifier-metadata field has to have the same value as the folder which contains the coresponding metadata file and FMI file
- only one FMI file and one metadata (name is configurable) file is allowed per folder, otherwise their information will not be included into the ontology
- FMIs have to comply to FMI standard 2.0
- The service has various configuration parameters, which can be specified either as environmental parameters or within the compose file

      - SPARQL_SERVER_NAME: Name of the triple store server (url, IP)
      - SPARQL_SERVER_PORT: Port of the triple store server endpoint
      - SPARQL_DATASET_NAME: name of the dataset of the triple store
      - SPARQL_USER: username of the triple store server
      - SPARQL_PASSWORD: username of the triple store server
      - LOGGING_LEVEL: defines the output level of the logging, values are = NONE, DEBUG, INFO
      - METADATA_FILE_NAME: the name of the metadata file
      - FTP_PASSIVE_PORT_RANGE: the range of passive ftp ports used (used for clients to receive a port)
      - FTP_USER: username of the ftp server
      - FTP_PASSWORD: password of the ftp server
      - ONTOLOGY_URL: The URL of the ontology (e.g.: "http://tuwien.ac.at/digiwind/DigiWindOnt#") with Apostrophes for parsing
      - ONTOLOGY_FILE_NAME: name of the ontology file in the ontology folder