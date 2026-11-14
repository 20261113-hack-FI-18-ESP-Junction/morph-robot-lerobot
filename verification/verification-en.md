# Local secret verification

This repository uses Gitleaks 8.30.1 for staged changes and a digest-pinned container for committed history. Install Gitleaks and Docker, then enable the tracked hook in a new clone:

```sh
git config core.hooksPath .githooks
```

The hook scans staged content and rejects findings or a missing scanner. Run the independent local check from this repository:

```sh
./tools/scan-secrets.sh
```

The container is temporary, has no network, reads the repository only, redacts findings and returns a failing exit code for a leak. The pinned image must already be available locally; retrieve the matching `ghcr.io/gitleaks/gitleaks:v8.30.1` image before running offline. This is local verification, not a production deployment. No service environment variables are needed.

Run after commits and regularly when reviewing history; no recurring automation is installed by this document. A new clone needs the local hook configuration shown above because Git does not transfer local config.

[Español](verification-es.md)
