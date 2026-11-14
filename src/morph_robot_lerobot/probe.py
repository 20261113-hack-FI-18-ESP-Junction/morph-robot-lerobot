"""Read SO-101 motor identities and uncalibrated encoder positions."""

import rustypot
from lerobot.motors import Motor, MotorNormMode, SerialMotorsBus

MOTOR_NAMES = (
    "shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper",
)


def read_motor(bus: SerialMotorsBus, name: str, motor_id: int, expected_model: int) -> dict:
    result = {"id": motor_id, "model": None, "position": None, "error": None}
    try:
        result["model"] = bus.ping(name, num_retry=1)
        if result["model"] is None:
            result["error"] = "No response; check motor power, wiring, IDs, and baud rate."
        elif result["model"] != expected_model:
            result["error"] = f"Expected STS3215 model number {expected_model}."
        else:
            result["position"] = bus.read("Present_Position", name, normalize=False, num_retry=1)
    except (OSError, RuntimeError) as error:
        result["error"] = str(error)
    return result


def probe(port: str) -> dict:
    motors = {
        name: Motor(index, "sts3215", MotorNormMode.RANGE_M100_100)
        for index, name in enumerate(MOTOR_NAMES, start=1)
    }
    bus = SerialMotorsBus(port=port, motors=motors)
    expected_model = rustypot.find_model("sts3215")[0]
    try:
        bus.connect(handshake=False)
        readings = {
            name: read_motor(bus, name, motor.id, expected_model)
            for name, motor in motors.items()
        }
    finally:
        # LeRobot's default disconnect disables torque; a diagnostic must not change it.
        bus.disconnect(disable_torque=False)
    return {"port": port, "ok": all(item["error"] is None for item in readings.values()), "motors": readings}
