"""Discover Linux video devices and verify a selected camera's first frame."""

import sys
from pathlib import Path

import cv2


def list_cameras() -> dict:
    if sys.platform != "linux":
        raise RuntimeError("Device listing uses Linux sysfs; on this platform use camera-check --camera INDEX.")
    aliases = {}
    for path in Path("/dev/v4l").glob("by-*/*"):
        aliases.setdefault(str(path.resolve()), []).append(str(path))
    devices = []
    entries = [entry for entry in Path("/sys/class/video4linux").glob("video*") if entry.name[5:].isdecimal()]
    for entry in sorted(entries, key=lambda item: int(item.name[5:])):
        device = str(Path("/dev") / entry.name)
        try:
            name = (entry / "name").read_text().strip()
        except FileNotFoundError:
            continue
        devices.append({"device": device, "name": name, "aliases": sorted(aliases.get(device, []))})
    return {"devices": devices, "note": "Video nodes may contain metadata; camera-check verifies frame capture."}


def save_frame(output: Path, frame) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), frame):
        raise OSError("Could not write the camera frame to the requested PNG path.")
    return str(output.resolve())


def check_camera(camera: int | str, output: Path | None = None) -> dict:
    backend = cv2.CAP_V4L2 if sys.platform == "linux" else cv2.CAP_ANY
    capture = cv2.VideoCapture()
    try:
        if not capture.open(camera, backend) or not capture.isOpened():
            raise RuntimeError("Camera could not be opened; check the device, permissions, and other camera users.")
        success, frame = capture.read()
        if not success or frame is None or frame.size == 0:
            raise RuntimeError("Camera opened but returned no frame; check its capture node and other camera users.")
        result = {
            "camera": camera, "ok": True,
            "width": int(frame.shape[1]), "height": int(frame.shape[0]),
            "channels": int(frame.shape[2]) if frame.ndim == 3 else 1,
            "pixel_min": int(frame.min()), "pixel_max": int(frame.max()),
            "uniform_frame": bool(frame.min() == frame.max()),
        }
        if output is not None:
            result["image"] = save_frame(output, frame)
        return result
    except cv2.error as error:
        raise RuntimeError("OpenCV could not complete the camera check.") from error
    finally:
        capture.release()
