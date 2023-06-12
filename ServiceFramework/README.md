# service_framework

Contains the docker-compose file and related configuration files

# MQTT Topics

## Topic description
### Topic prefix
**Service topics**: dw/services\
**Message topic**: dw/message
### Normal services
- **Template Service**: template
- **Model Assembly Service**: mas
- **CoSimulation Service**: cosim
- **Operational Planning Service**: operationalPlanningCalculation

As these services are called by the BPMN-Service, they will wait for a message on the corresponding request topic.\
Therefore, each of these services has to listen for the correct topic, which composes of the prefix + servicename + /request/"ID".\
The "ID" is used to correlate requests and responses together, and has to be appended to the response topic.\
The input and output payload of each service is described within the service folder (e.g. [MicroServices/ModelAssemblyService/readme.md](../MicroServices/ModelAssemblyService/readme.md))

**Example** - Request for MAS: dw/services/mas/request/123456789\
**Example** - Response from MAS: dw/services/mas/response/123456789\

### Utility services:
- **Remaining Useful Liftime**: remainingUsefulLifetime
- **Operational Planning**: operationalPlanning

These service compose of different "normal" services and therefore start a BPMN-Process within the BPMN-Service as soon as a message arrives on the corresponding topic.\
**Example** - Request for MAS: dw/services/remainingUsefulLifetime\
Their payload is defined in: TODO



# HowTo

For starting the framework, navigate to the root folder of this repository (where the `docker-compose.yml` file is located). This is necessary, as the later command requires an input file, in which all services and the configuration is defined.
\
Then open a terminal/commando window in this root folder and type the following code for starting the framework:
 \
 `docker-compose up -d` (attach --build if starting for the first time or if changes were made to any service requiring the --build command (MMS, WebVOWL), e.g.  `docker-compose up -d --build`)
 \
This starts the framework in detached (-d) mode, meaning you can savely close the terminal and the containers will still be running.
\
Some configuration variables are within the .env file, which is necessary for the project name and some port definitions for a less error prone deployment.
\
For stopping the whole framework use this command (again, terminal in this root folder):
 \
 `docker-compose down`
 \
By using `docker ps` it is possible to view all running containers and see the names of them. With this, after starting the framework, all within the .yml file defined containers (services) should be up and running. Other commands may be of relevance:
- `docker stop <container_name>` stops the container
- `docker start <container_name>` start the container
- `docker restart <container_name>` restarts the container
- `docker logs <container_name>` outputs the log of container (append `-f` to get a continuous log output)

# Service
### Operate
[http://localhost:8080/](http://localhost:8080/)\
Allows to manage BPMN processes and see current states.
### ModelManagementService (MMS)
Before starting the service, it is important to copy the most recent DigiWindOnt.owl file in the "ServiceFramework/services/modelmanagementservice/ontology"-folder. This ontology file will be used to initialise the DigiWindOntology after starting the service. (This file was intentionally omitted to prevent multiple versions of this file from existing in the repository. Will get fixed at a later stage.) \
After starting this service generates a "ont.ttl" file in "ServiceFramework/services/modelmanagementservice/logs" which can be loaded into the WebVOWL webpage.\
The FMU-Models are provided by an integrated FTP server, reachable on port 2121 with username "digiwind" and password "digiwind_pw".\
### WebVOWL
[http://localhost:8081/](http://localhost:8081/)\
On the bottom of this site there is a menu entry called "Ontology", there you can click on the last entry "Select ontology file" and go to the logs folder of the ModelManagementService and choose "ont.ttl" and hit upload.\
Then you can browse the current ontology of DigiWind.
### Fuseki
[http://localhost:3030/](http://localhost:3030/)\
Username: admin\
Password: digiwind_pw

# MQTT
### Generation of Username/Password

In order to generate username/password for the MQTT broker, one way would be to start the broker with a customized entrypoint:\
docker run -it --entrypoint sh -v c:/dockershare/broker:/pwd eclipse-mosquitto
\
this will start a shell within the container, in which we can generate username/password:
\
cd /path
\
mosquitto_passwd -b -c passwd "username" "password"
\
cat passwd
\
Afterwards, a file called passwd should be created in the shared docker folder

Note: everytime a username/password combination is created, the file will be overwritten
