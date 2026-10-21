#!/usr/bin/env python3
"""Run bounded, read-only integrity and hygiene checks on this repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN_SUFFIXES = {
    ".img", ".bin", ".elf", ".ko", ".so", ".dtb", ".dtbo", ".cpio",
    ".apk", ".pit", ".tar", ".tgz", ".zip", ".7z", ".lz4", ".pem",
    ".p12", ".keystore",
}
SECRET_PATTERNS = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
LOCAL_PATH_PATTERNS = [
    re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+\\"),
    re.compile(r"/home/[A-Za-z0-9_.-]+(?:/|\b)"),
    re.compile(r"/local/" r"user/[A-Za-z0-9_.-]+(?:/|\b)"),
]
REQUIRED = [
    "README.md", "ROADMAP.md", "STATUS.md", "SECURITY.md", "NOTICE.md",
    "LICENSE", ".gitignore", "config/a02-arm64.config", "patches/README.md",
    "scripts/build_kernel.py", "scripts/repo_audit.py", "docs/flash-readiness.md",
]
MAX_FILE_BYTES = 5 * 1024 * 1024
LOCAL_ONLY_FILES = {
    "PRE-PUBLISH-REVIEW.md",
    "patches/device-tree/0001-a02-arm64-pmu-compat.patch",
}


def is_git_root(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
    except OSError:
        return False
    return result.returncode == 0 and Path(result.stdout.strip()).resolve() == root.resolve()


def tracked_paths(root: Path) -> set[str]:
    """Return indexed paths when root is a Git worktree; support plain test trees."""
    if not is_git_root(root):
        return set()
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "-z"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except OSError:
        return set()
    if result.returncode != 0:
        return set()
    return {item.decode("utf-8", errors="surrogateescape")
            for item in result.stdout.split(b"\0") if item}


def repo_files(root: Path) -> list[Path]:
    tracked = tracked_paths(root)
    if not is_git_root(root):
        return sorted(
            p for p in root.rglob("*")
            if p.is_file()
            and ".git" not in p.parts
            and p.relative_to(root).as_posix() not in LOCAL_ONLY_FILES
        )
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others",
             "--exclude-standard", "-z"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0:
        paths = [root / item.decode("utf-8", errors="surrogateescape")
                 for item in result.stdout.split(b"\0") if item]
        return sorted(
            p for p in paths
            if p.is_file()
            and (p.relative_to(root).as_posix() not in LOCAL_ONLY_FILES
                 or p.relative_to(root).as_posix() in tracked)
        )
    return sorted(
        p for p in root.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and (p.relative_to(root).as_posix() not in LOCAL_ONLY_FILES
             or p.relative_to(root).as_posix() in tracked)
    )


def content_violations(root: Path) -> list[str]:
    problems: list[str] = []
    indexed_local_only = LOCAL_ONLY_FILES & tracked_paths(root)
    problems.extend(f"local-only path is tracked: {rel}"
                    for rel in sorted(indexed_local_only))
    for path in repo_files(root):
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            problems.append(f"forbidden file type: {rel}")
        if path.stat().st_size > MAX_FILE_BYTES:
            problems.append(f"file exceeds {MAX_FILE_BYTES} bytes: {rel}")
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            problems.append(f"non-text or unreadable file: {rel}")
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                problems.append(f"possible secret pattern in: {rel}")
        for pattern in LOCAL_PATH_PATTERNS:
            if pattern.search(text):
                problems.append(f"possible local user path in: {rel}")
    return problems


def checksum_violations(root: Path) -> list[str]:
    manifest = root / "SHA256SUMS"
    if not manifest.is_file():
        return ["missing SHA256SUMS"]
    problems: list[str] = []
    seen: set[str] = set()
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("  ", 1)
        if len(fields) != 2 or not re.fullmatch(r"[0-9a-f]{64}", fields[0]):
            problems.append(f"malformed SHA256SUMS line {line_number}")
            continue
        digest, rel = fields
        if rel in seen:
            problems.append(f"duplicate SHA256SUMS entry: {rel}")
            continue
        seen.add(rel)
        path = root / rel
        if not path.is_file() or root not in path.resolve().parents:
            problems.append(f"missing or unsafe SHA256SUMS path: {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            problems.append(f"SHA-256 mismatch: {rel}")
    expected = {
        p.relative_to(root).as_posix()
        for p in repo_files(root)
        if p.name != "SHA256SUMS"
    }
    for rel in sorted(expected - seen):
        problems.append(f"file missing from SHA256SUMS: {rel}")
    for rel in sorted(seen - expected):
        problems.append(f"SHA256SUMS entry has no repository file: {rel}")
    return problems


def audit(root: Path) -> dict[str, object]:
    root = root.resolve()
    problems = [f"missing required file: {rel}" for rel in REQUIRED if not (root / rel).is_file()]
    problems.extend(content_violations(root))
    problems.extend(checksum_violations(root))
    files = repo_files(root)
    return {
        "status": "PASS" if not problems else "FAIL",
        "file_count_including_manifest": len(files),
        "total_bytes_including_manifest": sum(p.stat().st_size for p in files),
        "sha256_verified_entries": len((root / "SHA256SUMS").read_text(encoding="utf-8").splitlines())
        if (root / "SHA256SUMS").is_file() else 0,
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    result = audit(args.root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['status']}: {result['file_count_including_manifest']} files, "
              f"{result['total_bytes_including_manifest']} bytes")
        for problem in result["problems"]:
            print(f"FAIL: {problem}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
