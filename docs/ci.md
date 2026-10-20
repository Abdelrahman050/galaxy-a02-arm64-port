# Safe CI Proposal

`.github/workflows/quality.yml` is a draft read-only workflow. It runs repository integrity checks and Python syntax checks only. It does not download Samsung source or firmware, build kernel images, run a device tool, or request secrets.

The workflow uses `pull_request`, `push`, and manual dispatch, grants only `contents: read`, disables persisted checkout credentials, and pins `actions/checkout` to commit `3d3c42e5aac5ba805825da76410c181273ba90b1` (release v7.0.1 as checked on 2026-10-20). The action reference and current release should be rechecked before publication. This workflow has not been run on GitHub; no badge or successful remote CI claim is made.

The kernel build is intentionally not in CI: Samsung source and firmware are external, large inputs, and a clean-room environment would need controlled provenance, licensing, toolchain provisioning, and a much larger runner. Future CI can add source-free synthetic tests and patch parsing after review.

References: [actions/checkout releases](https://github.com/actions/checkout/releases) and [GitHub Actions workflow syntax and permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
