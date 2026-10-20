#!/usr/bin/env python3
"""Parse project Python sources without writing bytecode or touching inputs."""

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
files = sorted((ROOT / "scripts").rglob("*.py")) + sorted((ROOT / "tests").rglob("*.py"))
errors = []
for path in files:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: {exc}")

if errors:
    print("FAIL: Python syntax errors detected", file=sys.stderr)
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

print(f"PASS: parsed {len(files)} Python source files")
