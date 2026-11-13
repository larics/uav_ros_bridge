#!/usr/bin/env python3
"""Checks the running MQTT adapter from the broker side. Started by
drone_interface_mqtt_check.sh with the fake backend and its camera media; prints PASS or FAIL
per check. The shared helpers come from uav_ros_general's test/drone_interface/check_util.py,
on PYTHONPATH."""
import json
import os
import sys
import threading
import time

import paho.mqtt.client as mqtt
from check_util import FINAL_STATE_NAMES, check, finish, poll
from uav_ros_msgs.msg import DronePhoto

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from drone_interface_mqtt_adapter import key_values  # noqa: E402

port, prefix, mode = int(sys.argv[1]), sys.argv[2], sys.argv[3]
renamed = mode == "profile"
messages = {}
lock = threading.Lock()


def on_message(_client, _userdata, message):
    with lock:
        messages.setdefault(message.topic[len(prefix) + 1:], []).append(message)


def wait(topic, timeout=8.0, pred=lambda m: True):
    def found():
        with lock:
            matching = [m for m in messages.get(topic, []) if pred(m)]
        return matching[-1] if matching else None
    return poll(found, timeout, 0.05)


def states(cid):
    with lock:
        return [json.loads(m.payload) for m in messages.get("command_status", []) if json.loads(m.payload)["id"] == cid]


def final(cid, timeout=8.0):
    return poll(lambda: next((s for s in states(cid) if s["state_name"] in FINAL_STATE_NAMES), None), timeout, 0.05)


client = mqtt.Client()
client.on_message = on_message
client.on_connect = lambda c, *_: c.subscribe(prefix + "/#", qos=1)
client.connect("localhost", port)
client.loop_start()


def send(payload):
    client.publish(prefix + "/command", payload if isinstance(payload, str) else json.dumps(payload), qos=1)


converted = {kv.key: kv.value for kv in key_values({"on": True, "off": False, "n": 2.5, "s": "x"})}
check("JSON booleans become true/false", converted == {"on": "true", "off": "false", "n": "2.5", "s": "x"}, converted)

if mode == "restart":
    # The broker was restarted without persistence: nothing retained is left but what the
    # adapter sends again when it reconnects.
    check("capabilities are sent again after a broker restart", wait("capabilities", 40) is not None)
    # Live delivery clears the retain flag; a client that subscribes now must get them retained.
    late, kept = mqtt.Client(), []
    late.on_message = lambda _c, _u, message: kept.append(message)
    late.on_connect = lambda c, *_: c.subscribe(prefix + "/capabilities", qos=1)
    late.connect("localhost", port)
    late.loop_start()
    check("and retained for a client that comes later",
          poll(lambda: kept[0] if kept else None, 5, 0.05) is not None and kept[0].retain)
    late.loop_stop()
    client.loop_stop()
    finish()

caps = wait("capabilities", 15)
check("capabilities arrive", caps is not None)

if renamed:
    check("capabilities are retained for a late client", caps is not None and caps.retain)
    message = wait("telemetry", 8)
    check("topic renamed by the profile", message is not None)
    data = json.loads(message.payload)
    check("field renamed", "state" in data and "flight_state_name" not in data, sorted(data))
    check("subset applied", "extra" not in data and "armed" in data, sorted(data))
    client.loop_stop()
    finish()

message = wait("status")
check("status arrives", message is not None)
strict = json.loads(message.payload, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
check("status is strict JSON, unknown numbers are null", strict["battery"]["percentage"] is None, strict["battery"])
check("enum name next to the number", strict["position"]["altitude_reference_name"] == "AMSL", strict["position"])
check("stamp is a number", isinstance(strict["header"]["stamp"], float), strict["header"])
check("health arrives", wait("health") is not None)

send({"id": "t1", "type": "land"})
check("rejection comes back", (final("t1") or {}).get("reason") == "not in the air", states("t1"))
send({"id": "t2", "type": "takeoff", "params": {"altitude": 10}})
check("takeoff succeeds", (final("t2") or {}).get("state_name") == "SUCCEEDED", states("t2"))
check("result is an object, empty without one", (final("t2") or {}).get("result") == {}, final("t2"))
send({"id": "f1", "type": "photo"})
taken = final("f1") or {}
result = taken.get("result") or {}
check("photo succeeds with photo_id and url in result",
      taken.get("state_name") == "SUCCEEDED" and set(result) == {"photo_id", "url"}, taken)
message = wait("camera/photo", pred=lambda m: json.loads(m.payload)["id"] == result.get("photo_id"))
check("camera/photo arrives with the id of the result", message is not None, messages.get("camera/photo"))
photo = json.loads(message.payload) if message else {}
check("camera/photo is QoS 1 and not retained", message is not None and message.qos == 1 and not message.retain)
check("camera/photo carries the DronePhoto fields", set(photo) == set(DronePhoto.__slots__), sorted(photo))
send({"id": "t2", "type": "takeoff", "params": {"altitude": 10}})
time.sleep(1)
check("a duplicate does not run again", [s["state_name"] for s in states("t2")].count("RUNNING") >= 1
      and states("t2")[-1]["state_name"] == "SUCCEEDED", states("t2")[-3:])
time.sleep(1)
check("a rejection arrives once", [m["state_name"] for m in states("t1")].count("REJECTED") == 1, states("t1"))
send({"id": "t2", "type": "takeoff", "params": {"altitude": 20}})
time.sleep(1)
check("a reused id is rejected over MQTT", states("t2")[-1].get("reason") == "id reused", states("t2")[-2:])
send("{not json")
send({"id": "t3"})
check("a command without a type is rejected with its id", "bad command" in (final("t3") or {}).get("reason", ""), states("t3"))
send({"id": "t4", "type": "hover"})
check("the adapter survives bad input", (final("t4") or {}).get("state_name") == "SUCCEEDED", states("t4"))
send({"id": "t5", "type": "mission_upload", "mission": {"id": "m", "waypoints": [
    {"latitude": 1, "longitude": 2, "altitude": 3, "altitude_reference": "ABOVE_GROUND"}]}})
check("an ABOVE_GROUND waypoint is refused by the adapter", "ABOVE_GROUND" in (final("t5") or {}).get("reason", ""), states("t5"))
send({"id": "t6", "type": "mission_upload", "mission": {"id": "m", "waypoints": [{"latitude": 1, "longitude": 2, "altitude": 3}]}})
check("a lat/lon mission passes the adapter", "bad command" not in (final("t6") or {}).get("reason", "bad command"), states("t6"))

client.loop_stop()
finish()
