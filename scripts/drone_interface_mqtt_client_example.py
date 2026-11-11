#!/usr/bin/env python3
"""A drone client over MQTT: reads the capabilities and the status, takes off, flies to a point,
flies a short lat/lon mission and comes home. Needs only paho-mqtt, not ROS, so it runs on any
machine that reaches the broker.

    drone_interface_mqtt_client_example.py --host localhost --prefix drone/vehicle
"""
import argparse
import json
import math
import sys
import threading
import time
import uuid

import paho.mqtt.client as mqtt

METRES_PER_DEGREE = 111320.0
RETRY_AFTER = 5.0  # [s] without an answer: send the same id again, the drone runs it only once
FINAL_STATES = ("SUCCEEDED", "FAILED", "CANCELLED", "REJECTED")


class Drone:
    def __init__(self, host, port, prefix):
        self.prefix = prefix
        self.status = None
        self.capabilities = None
        self.commands = {}
        self.changed = threading.Condition()

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(host, port)
        self.client.loop_start()

    def on_connect(self, client, _userdata, _flags, _result):
        client.subscribe(self.prefix + "/status")
        client.subscribe(self.prefix + "/capabilities")
        client.subscribe(self.prefix + "/command_status", qos=1)

    def on_message(self, _client, _userdata, message):
        data = json.loads(message.payload)
        with self.changed:
            if message.topic.endswith("/status") and not message.topic.endswith("command_status"):
                self.status = data
            elif message.topic.endswith("/capabilities"):
                self.capabilities = data
            else:
                self.commands.setdefault(data["id"], []).append(data)
                print("  %s: %s %s" % (data.get("type") or data["id"], data["state_name"], data["reason"]), flush=True)
            self.changed.notify_all()

    def wait_for(self, predicate, timeout):
        with self.changed:
            return self.changed.wait_for(predicate, timeout)

    def run(self, kind, timeout, params=None, mission=None):
        """Sends a command and follows it by id to its final state. True when it succeeded."""
        command = {"id": str(uuid.uuid4()), "client": "mqtt-example", "type": kind, "params": params or {}}
        if mission:
            command["mission"] = mission
        payload = json.dumps(command)
        self.client.publish(self.prefix + "/command", payload, qos=1)

        ended = lambda: any(s["state_name"] in FINAL_STATES for s in self.commands.get(command["id"], []))
        if not self.wait_for(lambda: command["id"] in self.commands, RETRY_AFTER):
            print("  no answer, sending the same id again", flush=True)
            self.client.publish(self.prefix + "/command", payload, qos=1)
        if not self.wait_for(ended, timeout):
            print("%s did not end in %d s" % (kind, timeout), file=sys.stderr)
            return False
        final = [s for s in self.commands[command["id"]] if s["state_name"] in FINAL_STATES][-1]
        if final["state_name"] != "SUCCEEDED":
            print("%s %s: %s" % (kind, final["state_name"], final["reason"]), file=sys.stderr)
        return final["state_name"] == "SUCCEEDED"


def offset(home, north, east):
    return (home["latitude"] + north / METRES_PER_DEGREE,
            home["longitude"] + east / (METRES_PER_DEGREE * math.cos(math.radians(home["latitude"]))))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--prefix", default="drone/vehicle")
    args = parser.parse_args()

    drone = Drone(args.host, args.port, args.prefix)
    if not drone.wait_for(lambda: drone.capabilities, 30):
        sys.exit("no capabilities from %s" % args.prefix)
    print("commands:", ", ".join(drone.capabilities["commands"]), flush=True)

    ready = lambda: drone.status and drone.status["ready_to_fly"] and drone.status["home"]["latitude"] is not None
    if not drone.wait_for(ready, 300):
        sys.exit("not ready to fly: %s" % [w["name"] for w in (drone.status or {}).get("warnings", [])])
    status = drone.status
    print("state %s, battery %s %%" % (status["flight_state_name"], status["battery"]["percentage"]), flush=True)
    home = status["home"]

    latitude, longitude = offset(home, 15, 0)
    goal = {"latitude": latitude, "longitude": longitude, "altitude": 10, "altitude_reference": "ABOVE_TAKEOFF"}
    corners = [offset(home, north, east) for north, east in ((15, 15), (0, 15), (0, 0))]
    mission = {"id": "mqtt-example", "name": "mqtt example", "waypoints": [
        {"latitude": la, "longitude": lo, "altitude": 10, "altitude_reference": "ABOVE_TAKEOFF"} for la, lo in corners]}

    steps = (("takeoff", 150, {"altitude": 10}, None),
             ("goto", 90, goal, None),
             ("mission_upload", 15, None, mission),
             ("mission_start", 150, {"mission_id": "mqtt-example"}, None),
             ("return_home", 240, None, None))
    for kind, timeout, params, flight in steps:
        print(kind, flush=True)
        if not drone.run(kind, timeout, params, flight):
            sys.exit(1)
    print("done", flush=True)
    drone.client.loop_stop()


if __name__ == "__main__":
    main()
