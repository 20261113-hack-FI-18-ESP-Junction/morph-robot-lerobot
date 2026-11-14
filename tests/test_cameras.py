"""Verify camera diagnostics using synthetic frames and filesystem fixtures."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np

from morph_robot_lerobot import cameras


class CameraCheckTests(unittest.TestCase):
    def setUp(self):
        self.capture = Mock(spec_set=["open", "isOpened", "read", "release"])
        self.capture.open.return_value = True
        self.capture.isOpened.return_value = True
        self.frame = np.arange(36, dtype=np.uint8).reshape(3, 4, 3)
        self.capture.read.return_value = True, self.frame
        self.factory = self.enterContext(patch.object(cameras.cv2, "VideoCapture", return_value=self.capture))
        self.enterContext(patch.object(cameras.sys, "platform", "linux"))

    def assert_released_without_controls(self):
        self.capture.release.assert_called_once_with()
        self.assertEqual(self.capture.method_calls[-1][0], "release")
        self.assertTrue(all(call[0] in {"open", "isOpened", "read", "release"}
                            for call in self.capture.method_calls))

    def test_frame_is_read_without_setting_camera_controls(self):
        result = cameras.check_camera(0)

        self.capture.open.assert_called_once_with(0, cv2.CAP_V4L2)
        self.capture.read.assert_called_once_with()
        self.assertEqual(result, {
            "camera": 0, "ok": True, "width": 4, "height": 3, "channels": 3,
            "pixel_min": 0, "pixel_max": 35, "uniform_frame": False,
        })
        self.assert_released_without_controls()

    def test_saved_png_contains_the_captured_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "frames" / "camera.png"
            result = cameras.check_camera(0, output)
            self.assertEqual(result["image"], str(output.resolve()))
            self.assertTrue(np.array_equal(cv2.imread(str(output)), self.frame))
        self.assert_released_without_controls()

    def test_uniform_frame_is_reported_without_claiming_visual_quality(self):
        self.capture.read.return_value = True, np.zeros((2, 3), dtype=np.uint8)

        result = cameras.check_camera(0)

        self.assertTrue(result["uniform_frame"])
        self.assertEqual(result["channels"], 1)
        self.assert_released_without_controls()

    def test_open_failure_releases_camera_without_reading(self):
        self.capture.open.return_value = False

        with self.assertRaisesRegex(RuntimeError, "could not be opened"):
            cameras.check_camera(0)

        self.capture.read.assert_not_called()
        self.assert_released_without_controls()

    def test_missing_frame_releases_camera(self):
        self.capture.read.return_value = False, None

        with self.assertRaisesRegex(RuntimeError, "returned no frame"):
            cameras.check_camera(0)

        self.assert_released_without_controls()

    def test_opencv_error_releases_camera_and_returns_an_actionable_error(self):
        self.capture.read.side_effect = cv2.error("Backend failed")

        with self.assertRaisesRegex(RuntimeError, "OpenCV could not complete"):
            cameras.check_camera(0)

        self.assert_released_without_controls()

    def test_failed_image_write_releases_camera(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(cameras.cv2, "imwrite", return_value=False):
                with self.assertRaisesRegex(OSError, "Could not write"):
                    cameras.check_camera(0, Path(directory) / "frame.png")

        self.assert_released_without_controls()

    def test_interrupt_releases_camera(self):
        self.capture.read.side_effect = KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            cameras.check_camera(0)

        self.assert_released_without_controls()


class CameraDiscoveryTests(unittest.TestCase):
    def test_linux_listing_includes_device_names_and_aliases_without_opening(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            node = root / "sys" / "video0"
            node.mkdir(parents=True)
            (node / "name").write_text("USB Camera\n")
            alias_dir = root / "dev" / "v4l" / "by-id"
            alias_dir.mkdir(parents=True)
            alias = alias_dir / "usb-camera-video-index0"
            alias.symlink_to("../../video0")
            paths = {"/sys/class/video4linux": root / "sys", "/dev": root / "dev",
                     "/dev/v4l": root / "dev" / "v4l"}
            with patch.object(cameras, "Path", side_effect=lambda value: paths[value]):
                with patch.object(cameras.sys, "platform", "linux"):
                    with patch.object(cameras.cv2, "VideoCapture") as capture:
                        result = cameras.list_cameras()
                        capture.assert_not_called()
            self.assertEqual(result["devices"], [{
                "device": str(root / "dev" / "video0"), "name": "USB Camera", "aliases": [str(alias)],
            }])

    def test_other_platforms_explain_explicit_camera_selection(self):
        with patch.object(cameras.sys, "platform", "darwin"):
            with self.assertRaisesRegex(RuntimeError, "camera-check --camera INDEX"):
                cameras.list_cameras()


if __name__ == "__main__":
    unittest.main()
