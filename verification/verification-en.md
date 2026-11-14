---
id: verification-en
lang: en
type: verification
owner: repository
status: verified
sources: ["local-verification"]
---

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

The tracked GitHub Actions workflow runs this history scan on pushes to `main`, every Monday at 04:17 UTC, and on manual dispatch. It checks out all history with read-only repository permission and no persisted checkout credential. The scanner image and checkout action are pinned. Review scanner updates periodically so the scheduled check benefits from new detection rules. Local checks have passed; the delivery ledger records whether a hosted run was observed. A new clone needs the local hook configuration shown above because Git does not transfer local config.

[Español](verification-es.md)
