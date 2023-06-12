import paho.mqtt.client as mqtt
import json
import time

smartdataservice_request = "5dit/fbr/services/smartdataservice/request/#"
smartdataservice_reply = "5dit/fbr/services/smartdataservice/response"
simulation_request = "5dit/fbr/services/simulation/request/#"
simulation_reply = "5dit/fbr/services/simulation/response"
deviationDetection_request = "5dit/fbr/services/deviationDetection/request/#"
deviationDetection_reply = "5dit/fbr/services/deviationDetection/response"
deviationDetected_request = "5dit/fbr/services/deviationDetected"
deviationDetected_reply = "5dit/fbr/services/deviationDetected"
deviationClassification_request = "5dit/fbr/services/deviationClassification/request/#"
deviationClassification_reply = "5dit/fbr/services/deviationClassification/response"
faultClassification_request = "5dit/fbr/services/faultClassification"
faultClassification_reply = "5dit/fbr/services/faultClassification"
faultClassificationService_request = "5dit/fbr/services/faultClassificationService/request/#"
faultClassificationService_reply = "5dit/fbr/services/faultClassificationService/response"
topic_list = [smartdataservice_request, simulation_request, deviationDetection_request, deviationDetected_request, deviationClassification_request, faultClassification_request, faultClassificationService_request]
print("Starting mockup of smart data service...")


def on_connect(client, userdata, flags, rc):
    print("Connected to broker with result code " + str(rc))
    subscribe_to_topics(client)


def subscribe_to_topics(client):
    for topic in topic_list:
        client.subscribe(topic)


def on_message(client, userdata, msg):
    print("received message on " + msg.topic)
    if msg.topic == smartdataservice_request:
        reply_to_topic_service(msg, smartdataservice_reply)
    elif msg.topic == simulation_request:
        reply_to_topic_service(msg, simulation_reply)
    elif msg.topic == deviationDetection_request:
        reply_to_topic_service(msg, deviationDetection_reply)
    elif msg.topic == deviationDetected_request:
        reply_to_topic_message(deviationDetected_reply)
    elif msg.topic == deviationClassification_request:
        reply_to_topic_service(msg, deviationClassification_reply)
    elif msg.topic == faultClassification_request:
        reply_to_topic_message(faultClassification_request)
    elif msg.topic == faultClassificationService_request:
        reply_to_topic_service(msg, faultClassificationService_reply)


def reply_to_topic_service(msg, topic):
    topic_parts = msg.topic.split('/')
    key = topic_parts[len(topic_parts) - 1]
    time.sleep(10)
    client.publish(topic + "/" + key, "")
    print("published message on " + topic + "/" + key)

def reply_to_topic_message(topic):
    time.sleep(10)
    client.publish(topic, "")
    print("published message on " + topic)


mqtt_client = mqtt.Client()
# mqtt_client.username_pw_set("daniel", "daniel_password")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_forever()
