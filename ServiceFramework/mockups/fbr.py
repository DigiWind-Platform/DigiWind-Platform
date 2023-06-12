import random
import time
import paho.mqtt.client as mqtt

sensor_topic = "5dit/fbr/sensors"
print("Starting mockup of smart data service...")


def on_connect(client, userdata, flags, rc):
    print("Connected to broker with result code " + str(rc))


mqtt_client = mqtt.Client()
# mqtt_client.username_pw_set("daniel", "daniel_password")

mqtt_client.on_connect = on_connect

mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

while True:
    value = random.randint(50, 250) + random.randint(0,100)/100
    mqtt_client.publish(sensor_topic, value)
    print("publishing value: " + str(value) + " on topic " + sensor_topic)
    time.sleep(30)
