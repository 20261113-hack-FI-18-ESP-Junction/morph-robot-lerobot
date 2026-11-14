"""Configuration for the local connection-check CLI."""

import argparse
import os
import re
from pathlib import Path


def camera_source(value: str) -> int | str:
    if value.isdecimal():
        return int(value)
    path = Path(value).resolve()
    if re.fullmatch(r"/dev/video\d+", str(path)) and path.is_char_device():
        return str(path)
    raise argparse.ArgumentTypeError("Use a camera index or an existing /dev/video device or its symlink.")


def image_output(value: str) -> Path:
    path = Path(value)
    if path.suffix.lower() != ".png":
        raise argparse.ArgumentTypeError("The optional frame output must be a .png file.")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SO-101 USB discovery, read-only motor checks, and camera checks.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("ports", help="List connected USB serial adapters without opening them.")
    commands.add_parser("cameras", help="List Linux video device candidates without opening them.")
    camera = commands.add_parser("camera-check", help="Read one frame from the selected camera and release it.")
    camera.add_argument("--camera", required=True, type=camera_source, help="Camera index or Linux video device.")
    camera.add_argument("--output", type=image_output, help="Optional local PNG path, such as .runtime/camera.png.")
    probe = commands.add_parser("probe", help="Read six motor identities and raw positions; no movement.")
    probe.add_argument("--port", default=os.environ.get("SO101_PORT"), help="USB serial port; defaults to SO101_PORT.")
    args = parser.parse_args()
    if args.command == "probe" and not args.port:
        parser.error("probe requires --port or the SO101_PORT environment variable")
    return args
