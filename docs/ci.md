# CI Record and Boundaries

The repository's read-only workflow `.github/workflows/quality.yml` has run on GitHub. Run 1 on `main`, commit `b08646591106073875a70963e16c9d6051dbccb9`, completed successfully on 2026-10-20. The single `checks` job passed repository-content/SHA-256 verification, Python syntax checking, and synthetic repository-audit tests. See the [run](https://github.com/Abdelrahman050/galaxy-a02-arm64-port/actions/runs/39474974322). A Bash syntax check for the experimental probe builder has since been added to the workflow; it is pending execution on the updated PR commit.

This is one successful CI run for that commit, not a claim that kernel builds, boot images, hardware, or Android are tested by CI. The workflow is triggered by `pull_request`, `push`, and manual dispatch; grants `contents: read`; disables persisted checkout credentials; and pins `actions/checkout` to `3d3c42e5aac5ba805825da76410c181273ba90b1`. Recheck the action pin before future workflow changes.

CI does not download Samsung source or firmware, build kernel images or the C probe, or access devices. The Bash step checks parsing only. Local review includes offline ELF/CPIO/gzip/image-layout validation, but the USB UDC, Windows COM enumeration, bootloader acceptance, and device execution remain outside CI.

References: [actions/checkout releases](https://github.com/actions/checkout/releases) and [GitHub Actions workflow syntax and permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
