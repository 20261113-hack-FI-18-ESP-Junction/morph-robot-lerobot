"""Configuration for the local connection-check CLI."""

import argparse
import os


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SO-101 USB discovery and read-only motor checks.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("ports", help="List connected USB serial adapters without opening them.")
    probe = commands.add_parser("probe", help="Read six motor identities and raw positions; no movement.")
    probe.add_argument("--port", default=os.environ.get("SO101_PORT"), help="USB serial port; defaults to SO101_PORT.")
    args = parser.parse_args()
    if args.command == "probe" and not args.port:
        parser.error("probe requires --port or the SO101_PORT environment variable")
    return args
