#!/bin/sh
# Read-only local Docker verification of this repository's committed history.
set -eu
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
scanner_image=ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f
exec docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --cpus 1 --memory 256m \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$repo_root,dst=/repo,readonly" \
  "$scanner_image" git --redact --no-banner --log-opts=--all /repo
