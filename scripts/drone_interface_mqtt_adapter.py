#!/usr/bin/env python3
"""The drone interface over MQTT: mirrors the ROS API one to one as JSON. It only maps names
and formats; what the drone can do is decided behind drone/command.

    <prefix>/status          out, throttled
    <prefix>/health          out
    <prefix>/capabilities    out, retained
    <prefix>/command_status  out, QoS 1
    <prefix>/camera/jpeg     out, raw JPEG bytes, retained
    <prefix>/command         in, QoS 1

A command is the DroneCommand message as JSON, with `params` as an object. Waypoints of its
mission are {latitude, longitude, altitude, altitude_reference, heading}, never poses: the
adapter passes them on in the mission manager's lat/lon frames, which converts them, and does
no geodesy of its own. MQTT can deliver a command twice, which is harmless: the core runs a
known id only once.
"""
import json
import math
from concurrent.futures import ThreadPoolExecutor

import paho.mqtt.client as mqtt
import rospy
import yaml
from diagnostic_msgs.msg import KeyValue
from sensor_msgs.msg import CompressedImage
from uav_ros_msgs.msg import (DiagnosticComponentArray, DroneCapabilities, DroneCommand,
                              DroneCommandStatus, DroneStatus, GeoPose, Mission, MissionAction,
                              MissionWaypoint)
from geometry_msgs.msg import PoseStamped, Quaternion
from uav_ros_msgs.srv import SendDroneCommand

QOS_FAST, QOS_RELIABLE = 0, 1
# Rejections the core answers without an entry, so drone/command_status never carries them
# (reasons in command_manager.cpp).
UNPUBLISHED_REJECTIONS = {"missing id", "id reused"}
ALTITUDE_REFERENCES = {"AMSL": GeoPose.AMSL, "ABOVE_TAKEOFF": GeoPose.ABOVE_TAKEOFF,
                       "ABOVE_GROUND": GeoPose.ABOVE_GROUND}
ALTITUDE_NAMES = {value: name for name, value in ALTITUDE_REFERENCES.items()}
# The mission manager's geodetic frames (uav_ros_lib geo_frame.hpp): x = latitude,
# y = longitude, z = altitude in the frame's reference.
WAYPOINT_FRAMES = {"AMSL": "latlon_origin", "ABOVE_TAKEOFF": "latlon_above_takeoff"}


def to_dict(message):
    """A ROS message as JSON-safe data: KeyValue lists become objects, unknown numbers null."""
    if hasattr(message, "to_sec"):
        return message.to_sec()
    if isinstance(message, float):
        return message if math.isfinite(message) else None
    if isinstance(message, (list, tuple)):
        if message and isinstance(message[0], KeyValue):
            return {kv.key: kv.value for kv in message}
        return [to_dict(item) for item in message]
    if not hasattr(message, "__slots__"):
        return message
    data = {slot: to_dict(getattr(message, slot)) for slot in message.__slots__}
    if isinstance(message, GeoPose):
        data["altitude_reference_name"] = ALTITUDE_NAMES.get(message.altitude_reference, "")
    return data


def text(value):
    """A JSON value as the drone interface reads it: booleans as true/false, not True/False."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def key_values(params):
    return [KeyValue(key=str(k), value=text(v)) for k, v in (params or {}).items()]


class Adapter:
    def __init__(self):
        config = rospy.get_param("~")
        self.prefix = config["prefix"] or "drone/" + config.get("vehicle_id", "vehicle")
        self.status_period = 1.0 / config["status_rate"]
        self.last_status = 0.0
        self.capabilities = None  # the latest, sent again on every (re)connect
        self.profile = self.load_profile(config.get("profile", ""))
        self.pool = ThreadPoolExecutor(max_workers=config["workers"])

        self.command = rospy.ServiceProxy("drone/command", SendDroneCommand)

        self.client = mqtt.Client(client_id=config.get("client_id", ""))
        if config.get("username"):
            self.client.username_pw_set(config["username"], config.get("password"))
        if config.get("tls"):
            self.client.tls_set(ca_certs=config.get("ca_certs") or None)
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = lambda *_: rospy.logwarn("[mqtt adapter] broker lost, retrying")
        self.client.on_message = self.on_message
        self.client.connect_async(config["host"], config["port"])
        self.client.loop_start()

        rospy.Subscriber("drone/status", DroneStatus, self.on_status, queue_size=1)
        rospy.Subscriber("drone/health", DiagnosticComponentArray, self.forward("health"), queue_size=1)
        rospy.Subscriber("drone/capabilities", DroneCapabilities, self.on_capabilities, queue_size=1)
        rospy.Subscriber("drone/command_status", DroneCommandStatus,
                         self.forward("command_status", qos=QOS_RELIABLE), queue_size=50)
        rospy.Subscriber("drone/camera/image", CompressedImage, self.on_image, queue_size=1, buff_size=2 ** 24)
        rospy.loginfo("[mqtt adapter] %s on %s:%d", self.prefix, config["host"], config["port"])

    @staticmethod
    def load_profile(path):
        """Topic renames, field renames and field subsets for a client with its own format."""
        if not path:
            return {}
        with open(path) as stream:
            return yaml.safe_load(stream) or {}

    def topic(self, name):
        return "%s/%s" % (self.prefix, self.profile.get("topics", {}).get(name, name))

    def shaped(self, name, data):
        """The data with the profile applied to its top level fields."""
        subset = self.profile.get("subsets", {}).get(name)
        if subset:
            data = {key: value for key, value in data.items() if key in subset}
        renames = self.profile.get("fields", {}).get(name, {})
        return {renames.get(key, key): value for key, value in data.items()}

    def publish(self, name, message, qos=QOS_FAST, retain=False):
        payload = json.dumps(self.shaped(name, to_dict(message)), allow_nan=False)
        self.client.publish(self.topic(name), payload, qos=qos, retain=retain)

    def forward(self, name, qos=QOS_FAST, retain=False):
        return lambda message: self.publish(name, message, qos, retain)

    def on_status(self, status):
        now = rospy.get_time()
        if now - self.last_status >= self.status_period:
            self.last_status = now
            self.publish("status", status)

    def on_capabilities(self, capabilities):
        self.capabilities = capabilities
        self.publish("capabilities", capabilities, retain=True)

    def on_image(self, image):
        self.client.publish(self.topic("camera/jpeg"), bytes(image.data), qos=QOS_FAST, retain=True)

    def on_connect(self, client, _userdata, _flags, result):
        if result != 0:
            rospy.logerr("[mqtt adapter] broker refused the connection: %d", result)
            return
        client.subscribe(self.topic("command"), qos=QOS_RELIABLE)
        # Retained, but a broker without persistence forgets it on a restart, and the first one
        # can arrive from ROS before the connection is up and be dropped.
        if self.capabilities is not None:
            self.publish("capabilities", self.capabilities, retain=True)
        rospy.loginfo("[mqtt adapter] connected")

    def on_message(self, _client, _userdata, message):
        # Never on the network thread: mission_upload takes as long as the upload does.
        self.pool.submit(self.handle_command, message.payload)

    def handle_command(self, payload):
        try:
            data = json.loads(payload)
            status = self.command(self.to_command(data)).status
        except (ValueError, TypeError, KeyError, AttributeError, rospy.ServiceException) as error:
            status = DroneCommandStatus(state=DroneCommandStatus.REJECTED, state_name="REJECTED",
                                        reason="bad command: %s" % error)
            if isinstance(payload, (bytes, str)):
                status.id = self.id_of(payload)
            self.publish("command_status", status, qos=QOS_RELIABLE)
            return
        # Every state, rejections included, reaches MQTT from drone/command_status, in order;
        # the service answer would arrive late and stale. The exceptions are rejections
        # without an entry, which only exist in the answer.
        if status.state == DroneCommandStatus.REJECTED and status.reason in UNPUBLISHED_REJECTIONS:
            self.publish("command_status", status, qos=QOS_RELIABLE)

    @staticmethod
    def id_of(payload):
        try:
            return str(json.loads(payload).get("id", ""))
        except (ValueError, AttributeError):
            return ""

    def to_command(self, data):
        command = DroneCommand(id=str(data["id"]), client=str(data.get("client", "mqtt")),
                               type=str(data["type"]), timeout=float(data.get("timeout", 0.0)),
                               params=key_values(data.get("params")))
        if data.get("mission"):
            command.mission = self.to_mission(data["mission"])
        return command

    def to_mission(self, data):
        waypoints = [MissionWaypoint(pose=self.to_waypoint_pose(w), speed=float(w.get("speed", 0.0)),
                                     connected=bool(w.get("connected", False)),
                                     actions=[self.to_action(a) for a in w.get("actions", [])])
                     for w in data["waypoints"]]
        return Mission(id=str(data["id"]), name=str(data.get("name", data["id"])), waypoints=waypoints)

    @staticmethod
    def to_waypoint_pose(data):
        """A lat/lon waypoint as a pose in a geodetic frame. Without a heading the orientation
        is all zero, which the mission manager turns into facing along the path."""
        if not all(key in data for key in ("latitude", "longitude", "altitude")):
            raise ValueError("every waypoint needs latitude, longitude and altitude")
        reference = data.get("altitude_reference", "ABOVE_TAKEOFF")
        if reference not in WAYPOINT_FRAMES:
            raise ValueError("altitude_reference %s is not supported in a mission" % reference)
        pose = PoseStamped()
        pose.header.frame_id = WAYPOINT_FRAMES[reference]
        pose.pose.position.x = float(data["latitude"])
        pose.pose.position.y = float(data["longitude"])
        pose.pose.position.z = float(data["altitude"])
        pose.pose.orientation = Quaternion(0, 0, 0, 0)
        if data.get("heading") is not None:
            yaw = math.radians(90.0 - float(data["heading"]))  # compass -> ENU
            pose.pose.orientation = Quaternion(0, 0, math.sin(yaw / 2), math.cos(yaw / 2))
        return pose

    @staticmethod
    def to_action(data):
        return MissionAction(type=str(data["type"]), params=key_values(data.get("params")),
                             timeout=float(data.get("timeout", 0.0)), on_failure=str(data.get("on_failure", "")))

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.pool.shutdown(wait=False)


def main():
    rospy.init_node("drone_interface_mqtt_adapter")
    adapter = Adapter()
    rospy.on_shutdown(adapter.stop)
    rospy.spin()


if __name__ == "__main__":
    main()
