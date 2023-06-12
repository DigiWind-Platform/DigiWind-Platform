import json
import datetime
import os
import pandas as pd
import paho.mqtt.client as mqtt
from io import StringIO
from pathlib import Path

MQTT_TOPIC = os.environ.get("MQTT_TOPIC")

fpath = Path(__file__).parent / "example_data.csv"


def read_csv(filepath, timerange=None, variables=None):
    df = pd.read_csv(filepath)
    colNames = df.columns
    df = df.rename(columns={n: n.strip() for n in colNames})

    # current fmu for measurement data needs csv data
    if variables is None:
        variables = df.columns
    else:
        variables = ["timestamp"] + variables
        df = df[variables]

    if timerange:
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%dT%H:%M:%SZ")
        df = df[
            (timerange["start"] <= df["timestamp"])
            & (df["timestamp"] <= timerange["end"])
        ]

    textStream = StringIO()
    df.to_csv(textStream, index=False)
    payload = textStream.getvalue()

    return payload


def on_message(client, userdata, msg):
    jsonData = msg.payload.decode("utf-8")
    payloadDict = json.loads(jsonData)

    timerange = payloadDict.get("timerange", None)
    timerange["start"] = datetime.datetime.strptime(
        timerange["start"], "%Y-%m-%dT%H:%M:%SZ"
    )
    timerange["end"] = datetime.datetime.strptime(
        timerange["end"], "%Y-%m-%dT%H:%M:%SZ"
    )
    variables = payloadDict.get("variables", None)

    print(f"Measurement data ({timerange}) request for {variables}")
    payload = read_csv(fpath, timerange, variables)

    responseTopic = MQTT_TOPIC + "/response/" + msg.topic.split("/")[-1]
    client.publish(responseTopic, payload)


if __name__ == "__main__":
    mqttClient = mqtt.Client("MeasurementDataService")
    mqttListen = MQTT_TOPIC + "/request/#"
    mqttClient.connect("mqttbroker", 1883)

    mqttClient.subscribe(mqttListen)

    mqttClient.on_message = on_message
    print(f"Start data service using data file ({fpath})")
    mqttClient.loop_forever()
