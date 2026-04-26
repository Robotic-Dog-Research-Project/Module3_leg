#!/usr/bin/env python3
# MQTT-driven robot dog leg controller.
# Subscribes to robosense/left_leg and robosense/right_leg. Payloads:
#   "10" -> up    (continuously increase that leg's angle until it hits max)
#   "01" -> down  (continuously decrease that leg's angle until it hits min)
#   "00" -> nothing (hold current angle)
# Values mirror Raspberry_Master_CLI: leg range is initial_angle +/- 60 degrees.

import os
import time
import threading

import paho.mqtt.client as mqtt

try:
    import smbus
except Exception:
    smbus = None


MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC_LEFT_LEG = "robosense/left_leg"
TOPIC_RIGHT_LEG = "robosense/right_leg"

STATE_BY_CODE = {
    "00": "nothing",
    "10": "up",
    "01": "down",
}

START_LEG_ANGLE = 90.0
MAX_ = 150
MIN_ = 15
LEG_RANGE = 60.0          # +/- degrees around initial
STEP_DEG = 0.5            # degrees per tick
TICK_INTERVAL = 0.1       # seconds between ticks (~10 Hz)
I2C_ADDRESS = 0x08
I2C_BUS_NUM = 1


class LegController:
    def __init__(self, i2c_addr=I2C_ADDRESS, bus_num=I2C_BUS_NUM):
        self.left_leg = 0.0
        self.left_joint = START_LEG_ANGLE
        self.right_leg = 0.0
        self.right_joint = START_LEG_ANGLE
        self.left_initial = START_LEG_ANGLE
        self.right_initial = START_LEG_ANGLE

        # Commanded direction per leg: "up", "down", or "nothing".
        self.left_cmd = "nothing"
        self.right_cmd = "nothing"

        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        self.address = i2c_addr
        if smbus:
            try:
                self.bus = smbus.SMBus(bus_num)
                time.sleep(1)
            except Exception:
                self.bus = None
        else:
            self.bus = None

    def set_command(self, side, state):
        with self.lock:
            if side == "left":
                self.left_cmd = state
            else:
                self.right_cmd = state

    def _step(self, angle, initial, cmd):
        if cmd == "up":
            new_angle = angle - STEP_DEG
            return max(new_angle, MIN_)  # clamp to minimum
        if cmd == "down":
            new_angle = angle + STEP_DEG
            return min(new_angle, MAX_)  # clamp to maximum
        return angle

    def run(self):
        while not self.stop_event.is_set():
            with self.lock:
                new_left = self._step(self.left_joint, self.left_initial, self.left_cmd)
                new_right = self._step(self.right_joint, self.right_initial, self.right_cmd)
                changed = (new_left != self.left_joint) or (new_right != self.right_joint)
                self.left_joint = new_left
                self.right_joint = new_right
            if changed:
                self.send_data()
            time.sleep(TICK_INTERVAL)

    def format_send_string(self):
        left_joint = int(round(self.left_joint))
        left_leg = int(round(self.left_leg))
        right_joint = int(round(180 - self.right_joint))  # mirror for reversed install
        right_leg = int(round(self.right_leg))
        return f"{left_joint:3}/{left_leg:3}/{right_joint:3}/{right_leg:3}"

    def send_data(self):
        s = self.format_send_string()
        print("SEND:", s)
        if self.bus:
            try:
                self.bus.write_i2c_block_data(self.address, 0, list(s.encode("utf-8")))
            except Exception as e:
                print("I2C write failed:", e)

    def stop(self):
        self.stop_event.set()


def decode(code: str) -> str:
    return STATE_BY_CODE.get(code.zfill(2), "nothing")


def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker rc={rc}")
    client.subscribe(TOPIC_LEFT_LEG)
    client.subscribe(TOPIC_RIGHT_LEG)


def on_message(client, userdata, msg):
    controller = userdata
    code = msg.payload.decode().strip()
    state = decode(code)
    if msg.topic == TOPIC_LEFT_LEG:
        controller.set_command("left", state)
        print(f"leg=left code={code} state={state}")
    elif msg.topic == TOPIC_RIGHT_LEG:
        controller.set_command("right", state)
        print(f"leg=right code={code} state={state}")


def main():
    controller = LegController()

    worker = threading.Thread(target=controller.run, daemon=True)
    worker.start()

    client = mqtt.Client(userdata=controller)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    print(f"Listening on {MQTT_HOST}:{MQTT_PORT} ...")

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        worker.join(timeout=1.0)


if __name__ == "__main__":
    main()
