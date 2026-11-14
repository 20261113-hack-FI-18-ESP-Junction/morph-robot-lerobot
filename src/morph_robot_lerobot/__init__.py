"""Local connection checks using the official Hugging Face LeRobot package."""

import json
import sys

from serial.tools.list_ports import comports

from .config import parse_args


def serial_command(args) -> None:
    ports = sorted(port for port in comports() if port.vid is not None)
    if args.command == "ports":
        if not ports:
            print("No USB serial adapters detected. Connect an arm with a USB data cable.")
        for port in ports:
            usb_id = f"{port.vid:04x}:{port.pid:04x}" if port.pid is not None else "unknown"
            print(f"{port.device}\t{port.description}\tusb={usb_id}\tserial={port.serial_number or 'unknown'}")
        return
    if args.port not in {port.device for port in ports}:
        sys.exit("Selected port is not a detected USB serial adapter. Run the ports command first.")

    from .probe import probe

    try:
        result = probe(args.port)
    except (OSError, RuntimeError) as error:
        sys.exit(f"Connection check failed: {error}")
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        sys.exit(1)


def main() -> None:
    args = parse_args()
    if args.command in {"ports", "probe"}:
        serial_command(args)
        return

    from .cameras import check_camera, list_cameras

    try:
        result = list_cameras() if args.command == "cameras" else check_camera(args.camera, args.output)
    except (OSError, RuntimeError) as error:
        sys.exit(f"Camera check failed: {error}")
    print(json.dumps(result, indent=2))
