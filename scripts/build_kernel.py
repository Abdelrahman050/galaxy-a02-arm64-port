#!/usr/bin/env python3
"""Build the recorded ARM64 kernel into a new, separate output directory.

The helper never cleans, packages, or flashes anything. Use only a writable
copy of Samsung source; keep the original source archive and firmware read-only.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def overlaps(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Required environment variable is unset: {name}")
    return value


def main() -> int:
    try:
        source = Path(require_env("KERNEL_SRC")).expanduser().resolve(strict=True)
        output = Path(require_env("KERNEL_OUT")).expanduser().resolve(strict=False)
        toolchain = Path(require_env("TOOLCHAIN_ROOT")).expanduser().resolve(strict=True)
        repo = Path(__file__).resolve().parents[1]
        config = Path(os.environ.get("KERNEL_CONFIG", repo / "config/a02-arm64.config")).expanduser().resolve(strict=True)
        make = os.environ.get("MAKE", "make")
        clang = Path(os.environ.get("CLANG", toolchain / "clang/bin/clang")).expanduser()
        lld = Path(os.environ.get("LD_LLD", toolchain / "clang/bin/ld.lld")).expanduser()
        cross = os.environ.get("CROSS_COMPILE", str(toolchain / "aarch64-linux-android-"))
        jobs = int(os.environ.get("JOBS", "4"))

        if not (source / "Makefile").is_file():
            raise ValueError(f"KERNEL_SRC is not a kernel source root: {source}")
        if overlaps(source, output):
            raise ValueError("KERNEL_OUT must be separate from KERNEL_SRC")
        if output.exists() and any(output.iterdir()):
            raise ValueError("KERNEL_OUT is non-empty; choose a new directory to preserve prior outputs")
        if jobs < 1:
            raise ValueError("JOBS must be a positive integer")
        for label, path in (("CLANG", clang), ("LD_LLD", lld)):
            resolved = path.expanduser().resolve(strict=True)
            if not resolved.is_file() or not os.access(resolved, os.X_OK):
                raise ValueError(f"{label} is not an executable file: {resolved}")
        clang, lld = clang.resolve(), lld.resolve()
        if not config.is_file():
            raise ValueError(f"Kernel config not found: {config}")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config, output / ".config")
    common = [
        "ARCH=arm64",
        "ANDROID_MAJOR_VERSION=r",
        "MTK_PLATFORM=mt6739",
        "CLANG_TRIPLE=aarch64-linux-gnu-",
        f"CROSS_COMPILE={cross}",
        f"CC={clang}",
        f"LD={lld}",
    ]
    log_path = output / "build.log"
    commands = [
        [make, "-C", str(source), f"O={output}", *common, "olddefconfig"],
        [make, "-C", str(source), f"O={output}", *common, f"-j{jobs}", "Image"],
    ]
    try:
        with log_path.open("w", encoding="utf-8") as log:
            for command in commands:
                print("Running:", " ".join(command))
                log.write("$ " + " ".join(command) + "\n")
                log.flush()
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        check=False, text=True)
                if result.returncode:
                    print(f"Build failed with exit code {result.returncode}; see {log_path}",
                          file=sys.stderr)
                    return result.returncode
    except OSError as exc:
        print(f"ERROR: could not run build command: {exc}; see {log_path}", file=sys.stderr)
        return 2

    print(f"Build complete; log: {log_path}")
    print("Compile/link evidence only. This does not establish device boot or flash readiness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
