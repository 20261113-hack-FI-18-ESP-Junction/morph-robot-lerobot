# Morph LeRobot

Connect and test a pair of SO-101 leader/follower arms using the official
Hugging Face `lerobot[hardware,feetech]==0.7.0` package. The local
`morph-robot-lerobot` command adds USB discovery and a read-only motor check;
motor setup, calibration, and teleoperation use the upstream LeRobot commands.

## Install

Run commands from this directory:

```bash
uv sync --locked
export HF_LEROBOT_HOME="$PWD/.runtime/lerobot"
```

The project selects Python 3.12. LeRobot 0.7.0 requires NumPy below 2.3, whose
supported Python versions stop at 3.13, so the original Python 3.14 scaffold is
not compatible. `uv.lock` fixes the dependency versions, `.venv/` holds the
environment, and `uv.toml` keeps uv's package cache under `.runtime/uv-cache/`.
The export above keeps calibration and LeRobot files under `.runtime/lerobot/`.
Repeat that export in each new terminal before using the official commands.

## Connect and identify the two arms

Use each controller's USB data connection and the power supply matched to its
motors. SO-101 kits have different motor voltage variants; follow the labels
and supplier instructions. Secure the arms and leave the grippers empty.

```bash
uv run morph-robot-lerobot ports
```

This only enumerates USB serial adapters; it does not open a serial port. To
identify the leader, unplug only its USB cable, list ports again, and note
which entry disappeared. Reconnect it and repeat for the follower. Do not
assign the roles from the order of the port list.

Set the actual paths you identified, replacing these placeholders:

```bash
export LEADER_PORT='/dev/cu.REPLACE_WITH_LEADER'
export FOLLOWER_PORT='/dev/cu.REPLACE_WITH_FOLLOWER'
```

If no USB adapters appear on macOS, check that the cable supports data, try a
direct laptop connection, and accept an accessory connection prompt if one
appears. On a Waveshare controller, check the manufacturer's USB/B jumper
positions. Motor power and USB enumeration are separate checks.

The official interactive port finder is also available:

```bash
uv run lerobot-find-port
```

## Read the motors before changing anything

```bash
uv run morph-robot-lerobot probe --port "$LEADER_PORT"
uv run morph-robot-lerobot probe --port "$FOLLOWER_PORT"
```

Each probe reads the model number and raw encoder position for the six expected
STS3215 motor IDs at LeRobot's default 1,000,000 baud. It sends no goal-position,
torque, ID, or calibration writes, including when closing the port after an
error. It returns `"ok": true` and exit status 0 only when all six motors have
the expected model and their positions can be read. Other results include a
per-motor error and return a nonzero exit status.

The expected IDs are 1 shoulder pan, 2 shoulder lift, 3 elbow, 4 wrist flex,
5 wrist roll, and 6 gripper. A successful probe verifies communication with
those IDs; it does not verify which physical joint has each ID, calibration,
firmware consistency, or motion readiness. Check the mechanical mapping against
the official assembly guide before calibration.

The probe also accepts `SO101_PORT` as an environment variable. To use a local
file, copy `.env.example` to `.env`, fill in the port, then run:

```bash
uv run --env-file .env morph-robot-lerobot probe
```

## Assign motor IDs only if needed

An arm can arrive with IDs already assigned even though it has never been
calibrated. Missing replies can also mean a power, cable, or baud-rate problem;
do not automatically reassign IDs after a failed probe.

If IDs have not been assigned, follow the official SO-101 wiring/setup guide.
**The setup procedure requires one motor connected at a time**, following the
interactive prompts. Disconnect motor power before changing motor wiring.
Never start it on a fully connected chain of motors with duplicate IDs.

```bash
uv run lerobot-setup-motors \
  --teleop.type=so101_leader --teleop.port="$LEADER_PORT"

uv run lerobot-setup-motors \
  --robot.type=so101_follower --robot.port="$FOLLOWER_PORT"
```

Reconnect the chain as instructed in the guide and rerun both probes.

## Calibrate each arm

Once both motor checks pass and the joint IDs are correct, run these separately.
Follow the official guide's starting pose and the interactive prompts to move
each joint by hand through its range. Calibration writes motor settings and
calibration files; it is not a read-only diagnostic.

```bash
uv run lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id=morph_leader

uv run lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id=morph_follower
```

Reuse these same IDs for teleoperation so LeRobot loads the matching calibration.

## First movement test

After calibration, place the two arms in similar poses, clear their reachable
area, and keep the follower's power disconnect accessible. This command enables
the follower and makes it track the leader for ten seconds. Move the leader
gently; support the follower when the run ends and torque is released.

```bash
uv run lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id=morph_follower \
  --robot.max_relative_target=1 \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id=morph_leader \
  --fps=30 \
  --teleop_time_s=10 \
  --display_data=false
```

`max_relative_target` limits the target change per control step in LeRobot's
normalized units; it is not a speed guarantee or a collision detector. Press
Ctrl+C to stop the loop. No camera or trained policy is needed for this test.

## Verify the software

```bash
uv run python -m unittest discover -s tests -v
uv run morph-robot-lerobot --help
uv run lerobot-calibrate --help
uv run lerobot-teleoperate --help
```

The unit tests use a fake motor bus and never access hardware.

## Official references

- [Hugging Face LeRobot repository](https://github.com/huggingface/lerobot)
- [LeRobot installation](https://huggingface.co/docs/lerobot/installation)
- [SO-101 setup and calibration](https://huggingface.co/docs/lerobot/so101)
- [SO-101 hardware and assembly](https://github.com/TheRobotStudio/SO-ARM100)
- [LeRobot 0.7.0 motor-bus implementation](https://github.com/huggingface/lerobot/blob/v0.7.0/src/lerobot/motors/motors_bus.py)
- [NumPy 2.2.6 supported Python versions](https://github.com/numpy/numpy/blob/v2.2.6/doc/source/release/2.2.6-notes.rst)
