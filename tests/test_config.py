"""Check camera selection boundaries without opening hardware."""

import argparse
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import morph_robot_lerobot
from morph_robot_lerobot import config


class CameraArgumentTests(unittest.TestCase):
    def test_numeric_index_is_passed_to_opencv_as_an_integer(self):
        self.assertEqual(config.camera_source("2"), 2)

    def test_video_symlink_resolves_to_its_character_device(self):
        with tempfile.TemporaryDirectory() as directory:
            alias = Path(directory) / "camera"
            alias.symlink_to("/dev/video2")
            with patch.object(Path, "is_char_device", return_value=True):
                self.assertEqual(config.camera_source(str(alias)), "/dev/video2")

    def test_network_sources_and_non_camera_paths_are_rejected(self):
        for value in ("https://example.test/camera", "rtsp://example.test/live", "/dev/null", "-1", "movie.mp4"):
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    config.camera_source(value)

    def test_frame_output_requires_png_extension(self):
        self.assertEqual(config.image_output(".runtime/frame.png"), Path(".runtime/frame.png"))
        with self.assertRaises(argparse.ArgumentTypeError):
            config.image_output("frame.mp4")

    def test_camera_selection_is_required(self):
        with patch("sys.argv", ["morph-robot-lerobot", "camera-check"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exit_error:
                    config.parse_args()
        self.assertEqual(exit_error.exception.code, 2)

    def test_camera_cli_does_not_enumerate_or_probe_serial_devices(self):
        args = ["morph-robot-lerobot", "camera-check", "--camera", "0"]
        with patch("sys.argv", args), patch.object(morph_robot_lerobot, "comports") as ports:
            with patch("morph_robot_lerobot.cameras.check_camera", return_value={"ok": True}) as check:
                with contextlib.redirect_stdout(io.StringIO()):
                    morph_robot_lerobot.main()
                check.assert_called_once_with(0, None)
                ports.assert_not_called()


if __name__ == "__main__":
    unittest.main()
