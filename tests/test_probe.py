"""Exercise the motor probe without opening a serial port."""

import unittest
from unittest.mock import create_autospec, patch

import morph_robot_lerobot.probe as probe_module


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.port = "/dev/fake-so101"
        self.model = probe_module.rustypot.find_model("sts3215")[0]
        self.bus = create_autospec(probe_module.SerialMotorsBus, instance=True, spec_set=True)
        self.factory = self.enterContext(patch.object(probe_module, "SerialMotorsBus", return_value=self.bus))
        self.models = dict.fromkeys(probe_module.MOTOR_NAMES, self.model)
        self.positions = {
            name: 1200 + index * 100 for index, name in enumerate(probe_module.MOTOR_NAMES)
        }
        self.bus.ping.side_effect = lambda name, **kwargs: self.models[name]
        self.bus.read.side_effect = lambda register, name, **kwargs: self.positions[name]

    def assert_read_only_and_closed(self):
        self.bus.connect.assert_called_once_with(handshake=False)
        self.bus.disconnect.assert_called_once_with(disable_torque=False)
        allowed = {"connect", "ping", "read", "disconnect"}
        self.assertTrue(all(call[0] in allowed for call in self.bus.method_calls))
        for call in self.bus.read.call_args_list:
            self.assertEqual(call.args[0], "Present_Position")
            self.assertIs(call.kwargs.get("normalize"), False)
        self.assertEqual(self.bus.method_calls[-1][0], "disconnect")

    def test_six_motors_return_raw_positions_without_writes(self):
        result = probe_module.probe(self.port)

        self.assertTrue(result["ok"])
        self.assertEqual(result["port"], self.port)
        self.assertEqual(set(result["motors"]), set(probe_module.MOTOR_NAMES))
        for index, name in enumerate(probe_module.MOTOR_NAMES, start=1):
            self.assertEqual(result["motors"][name], {
                "id": index, "model": self.model, "position": self.positions[name], "error": None,
            })
        self.factory.assert_called_once()
        configuration = self.factory.call_args.kwargs
        self.assertEqual(configuration["port"], self.port)
        self.assertEqual([motor.id for motor in configuration["motors"].values()], list(range(1, 7)))
        self.assertTrue(all(motor.model == "sts3215" for motor in configuration["motors"].values()))
        self.assert_read_only_and_closed()

    def test_missing_motor_preserves_other_results_and_skips_its_position_read(self):
        self.models["elbow_flex"] = None

        result = probe_module.probe(self.port)

        self.assertFalse(result["ok"])
        self.assertIsNone(result["motors"]["elbow_flex"]["position"])
        self.assertIn("No response", result["motors"]["elbow_flex"]["error"])
        self.assertEqual(result["motors"]["gripper"]["position"], self.positions["gripper"])
        self.assertEqual(sum(item["error"] is None for item in result["motors"].values()), 5)
        self.assertNotIn("elbow_flex", [call.args[1] for call in self.bus.read.call_args_list])
        self.assert_read_only_and_closed()

    def test_wrong_model_is_reported_without_reading_its_position(self):
        self.models["wrist_flex"] = self.model + 1

        result = probe_module.probe(self.port)

        self.assertFalse(result["ok"])
        wrong = result["motors"]["wrist_flex"]
        self.assertEqual(wrong["model"], self.model + 1)
        self.assertIsNone(wrong["position"])
        self.assertIn(str(self.model), wrong["error"])
        self.assertNotIn("wrist_flex", [call.args[1] for call in self.bus.read.call_args_list])
        self.assert_read_only_and_closed()

    def test_position_failure_is_reported_and_remaining_motors_are_read(self):
        def read(register, name, **kwargs):
            if name == "shoulder_lift":
                raise ConnectionError("Position read timed out")
            return self.positions[name]

        self.bus.read.side_effect = read
        result = probe_module.probe(self.port)

        self.assertFalse(result["ok"])
        failed = result["motors"]["shoulder_lift"]
        self.assertEqual(failed["model"], self.model)
        self.assertIsNone(failed["position"])
        self.assertEqual(failed["error"], "Position read timed out")
        self.assertEqual(result["motors"]["gripper"]["position"], self.positions["gripper"])
        self.assert_read_only_and_closed()

    def test_motor_rejecting_a_read_is_reported(self):
        self.bus.read.side_effect = RuntimeError("Motor refused the read")

        result = probe_module.probe(self.port)

        self.assertFalse(result["ok"])
        self.assertTrue(all(item["error"] == "Motor refused the read" for item in result["motors"].values()))
        self.assert_read_only_and_closed()

    def test_no_motor_responses_never_reports_a_successful_probe(self):
        self.models = dict.fromkeys(probe_module.MOTOR_NAMES)

        result = probe_module.probe(self.port)

        self.assertFalse(result["ok"])
        self.assertEqual(len(result["motors"]), 6)
        self.assertTrue(all(item["error"] for item in result["motors"].values()))
        self.bus.read.assert_not_called()
        self.assert_read_only_and_closed()

    def test_connection_error_propagates_and_closes_without_torque_change(self):
        self.bus.connect.side_effect = ConnectionError("USB adapter disconnected")

        with self.assertRaisesRegex(ConnectionError, "USB adapter disconnected"):
            probe_module.probe(self.port)

        self.bus.ping.assert_not_called()
        self.bus.read.assert_not_called()
        self.assert_read_only_and_closed()

    def test_interrupt_during_read_closes_without_torque_change(self):
        self.bus.read.side_effect = KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            probe_module.probe(self.port)

        self.assert_read_only_and_closed()


if __name__ == "__main__":
    unittest.main()
