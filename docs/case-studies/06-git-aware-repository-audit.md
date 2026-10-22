# Making the Repository Audit Git-Aware

## Technical scope

This case covers repository hygiene checks for excluded local-only files and forbidden binary suffixes. It evaluates the audit code and its synthetic tests, not the general security of GitHub or every possible secret/binary format.

## Executive summary

The initial audit enumerated files with a recursive filesystem walk and excluded two local-only paths by filename. Its tests covered those files as untracked fixtures, but the implementation did not distinguish an untracked local file from one already present in Git's index. A tracked local-only patch or review document could therefore be silently omitted from the audit inventory. The revised audit asks Git for tracked and untracked non-ignored paths, treats tracked local-only paths as violations, and adds isolated Git-index tests. It also has a test that force-adds an ignored .img file and verifies the forbidden suffix is caught. The code now detects the specific bypass in a synthetic repository; it is not a complete security scanner.

## Repository and CI context

The project publishes source, patches, documentation, and safe analysis tools while excluding firmware, boot images, and local review artifacts. GitHub Actions runs a read-only job with the check name checks and limited contents:read permission. It verifies repository contents and SHA-256, Python syntax, Bash syntax where configured, and synthetic tests; it does not build the kernel or access the phone.

## Original problem and symptoms

The baseline repo_audit.py used Path.rglob and skipped paths in LOCAL_ONLY_FILES unconditionally. The original tests verified that an untracked local PRE-PUBLISH review and firmware-derived patch were ignored from the public inventory. That was intended for local working files, but the same filter also hid those names if they were staged or committed. A related gap was the difference between a file ignored by .gitignore and a file forcibly tracked with git add -f.

## Investigation and confirmed root cause

The scanner's source of truth was the working directory, with a name-based exclusion applied before asking whether Git tracked the path. Consequently, the audit could not distinguish “local file intentionally not part of the repository” from “prohibited path already staged for publication.” This is confirmed by the old implementation at baseline b086465 and the revised implementation and tests in commit 7c62f87.

## Applied fix

The revised code queries the Git index with git ls-files --cached and enumerates non-ignored untracked paths separately. It includes a local-only path when Git tracks it and emits an explicit “local-only path is tracked” violation. Tests create temporary repositories for the tracked local-only files and a force-tracked ignored boot.img placeholder. Plain untracked local-only files remain excluded from checksums and content scanning, as intended.

## Validation and verified results

The added unit cases exercise both sides of the policy: local-only untracked files are not treated as public repository files, but tracked copies fail; a force-tracked ignored firmware image is still enumerated and rejected by suffix. The repository's read-only Actions workflow passed on the current main commit c141938d02f2cc3e7ed6970ae96e1ab7f770cfd5 (run 8). That establishes the test suite and audit pass for the checked tree, not comprehensive detection of arbitrary credentials or binaries.

## Remaining limitations

The audit relies on a bounded list of secret patterns, file suffixes, and local path forms. It is not a substitute for a dedicated secret-scanning or license-review process. Files larger than the configured limit and non-text files are rejected, but an unknown binary format with an allowed suffix could still require human review. CI never processes firmware or kernel binaries.

## Lessons learned

- Before publishing, audit the Git index and staged content, not only a recursive directory walk.
- Tests must include tracked, untracked, ignored, and force-tracked states when policy depends on Git membership.
- A green read-only CI job is evidence for its named checks only; it says nothing about kernel builds or device behavior.

## Evidence references

Compare the baseline [repo_audit.py at b086465](https://github.com/Abdelrahman050/galaxy-a02-arm64-port/blob/b08646591106073875a70963e16c9d6051dbccb9/scripts/repo_audit.py) with the current [audit implementation](../../scripts/repo_audit.py), [synthetic tests](../../tests/test_repo_audit.py), and [CI record](../ci.md). The Git-aware correction and tracked-file fixtures are in [commit 7c62f87](https://github.com/Abdelrahman050/galaxy-a02-arm64-port/commit/7c62f8700a8b98f666efa068a8e86fcebb922291); the current main run is [Actions run 8](https://github.com/Abdelrahman050/galaxy-a02-arm64-port/actions/runs/39826275874).

## Current status

**RESOLVED — VERIFIED IN DEFINED SCOPE.** The tracked-file bypass and forced-tracked firmware suffix cases pass their synthetic tests and the repository workflow. Broader scanning coverage remains bounded by the implemented rules.
