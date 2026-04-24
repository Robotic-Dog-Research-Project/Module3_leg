import os
import paho.mqtt.client as mqtt


MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC_LEFT_LEG = "robosense/left_leg"
TOPIC_RIGHT_LEG = "robosense/right_leg"

STATE_BY_CODE = {
    "00": "nothing",
    "10": "up",
    "01": "down",
}


def decode(code: str) -> str:
    return STATE_BY_CODE.get(code.zfill(2), "nothing")


def handle_leg(leg: str, code: str) -> None:
    state = decode(code)
    print(f"leg={leg} code={code} state={state}")
    # TODO: drive leg motor/servo based on state


def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker rc={rc}")
    client.subscribe(TOPIC_LEFT_LEG)
    client.subscribe(TOPIC_RIGHT_LEG)


def on_message(client, userdata, msg):
    code = msg.payload.decode().strip()
    if msg.topic == TOPIC_LEFT_LEG:
        handle_leg("left", code)
    elif msg.topic == TOPIC_RIGHT_LEG:
        handle_leg("right", code)


def main() -> None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    print(f"Listening on {MQTT_HOST}:{MQTT_PORT} ...")
    client.loop_forever()


if __name__ == "__main__":
    main()
