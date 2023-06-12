import paho.mqtt.client as mqtt
import json
import time

request_topic = "5dit/fbr/services/smartdataservice/request/#"
response_topic = "5dit/fbr/services/smartdataservice/response/#"
sensor_topic = "5dit/fbr/sensors/#"
topic_list = [request_topic, response_topic, sensor_topic]
print("Starting logger of smart data service...")


def on_connect(client, userdata, flags, rc):
    print("Connected to broker with result code " + str(rc))
    subscribe_to_topics(client)


def subscribe_to_topics(client):
    for topic in topic_list:
        client.subscribe(topic)


def on_message(client, userdata, msg):
    if msg.topic == sensor_topic:
        print("received message on " + msg.topic + " with data " + msg.payload)
    else:
        #data = json.loads(str(msg.payload.decode("utf-8", "ignore")))
        print("received message on " + msg.topic)


mqtt_client = mqtt.Client()
# mqtt_client.username_pw_set("daniel", "daniel_password")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_forever()