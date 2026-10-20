#!/usr/bin/env python3
"""Stage Samsung SM-A022F DT sources for an AArch64 build without touching inputs.

Copies the stock MT6739 base and active dependencies from arch/arm, and the
already supplied A02 board overlays from arch/arm64. Refuses to overwrite a
target directory. Only intentional content edit: ARMv8 PMU compatible.
"""

import argparse
import hashlib
import json
from pathlib import Path


ARM_FILES = [
    "mt6739.dts",
    "cust_mt6739_msdc.dtsi",
    "trusty.dtsi",
    "mt6357.dtsi",
    "modem-MT6739ap-pdata.dtsi",
    "k39tv1_bsp_titan_hamster.dts",
    "k39tv1_bsp_titan_hamster/gpio00.dtsi",
    "k39tv1_bsp_titan_hamster/gpio01.dtsi",
]
ROOT_COMPATIBLE = "mediatek,mt6739"
PMU_COMPATIBLE_BEFORE = "arm,cortex-a7-pmu"
PMU_COMPATIBLE_AFTER = "arm,armv8-pmuv3"
MAX_DTS_BYTES = 8 * 1024 * 1024
EXPECTED_A02_OVERLAYS = {
    "a02_eur_open_w00_r00.dts",
    "a02_eur_open_w00_r01.dts",
    "a02_eur_open_w00_r06.dts",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dts_tokens(text):
    """Tokenize enough DTS syntax to validate the root and PMU node safely."""
    tokens = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        if text.startswith("//", i):
            end = text.find("\n", i + 2)
            i = len(text) if end < 0 else end + 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated DTS block comment")
            i = end + 2
            continue
        if text[i] == '"':
            i += 1
            value = []
            while i < len(text) and text[i] != '"':
                if text[i] == "\\":
                    i += 1
                    if i >= len(text):
                        raise ValueError("unterminated escape in DTS string")
                value.append(text[i])
                i += 1
            if i >= len(text):
                raise ValueError("unterminated DTS string")
            tokens.append(("string", "".join(value)))
            i += 1
            continue
        if text[i] in "{};=/":
            tokens.append(("punct", text[i]))
            i += 1
            continue
        start = i
        while (i < len(text) and not text[i].isspace()
               and text[i] not in "{};=/\""
               and not text.startswith("//", i)
               and not text.startswith("/*", i)):
            i += 1
        if i == start:
            raise ValueError(f"unsupported DTS token at character {i}")
        tokens.append(("atom", text[start:i]))
    return tokens


def validate_stock_base(data, expected_pmu=PMU_COMPATIBLE_BEFORE):
    """Validate the expected source identity and single ARM32 PMU field.

    This intentionally is not a full Device Tree compiler. A DTC build is
    still required before integrating or shipping a compiled tree.
    """
    if not data or len(data) > MAX_DTS_BYTES:
        raise ValueError("MT6739 input is empty, oversized, or not DTS text")
    try:
        text = data.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ValueError("MT6739 input must be UTF-8 DTS text, not a DTB") from exc
    if "\0" in text:
        raise ValueError("MT6739 input contains NUL bytes and is not DTS text")
    tokens = dts_tokens(text)
    dts_header = [("punct", "/"), ("atom", "dts-v1"),
                  ("punct", "/"), ("punct", ";")]
    if not any(tokens[i:i + len(dts_header)] == dts_header
               for i in range(len(tokens) - len(dts_header) + 1)):
        raise ValueError("input is missing the DTS v1 header")
    depth_before = {}
    matching_brace = {}
    stack = []
    root_opens = []
    for index, token in enumerate(tokens):
        depth_before[index] = len(stack)
        if token == ("punct", "{"):
            if index > 0 and tokens[index - 1] == ("punct", "/") and not stack:
                root_opens.append(index)
            stack.append(index)
        elif token == ("punct", "}"):
            if not stack:
                raise ValueError("unmatched closing brace in DTS")
            matching_brace[stack.pop()] = index
    if stack:
        raise ValueError("unclosed brace in DTS")
    if len(root_opens) != 1:
        raise ValueError("expected exactly one top-level DTS root node")
    root_open = root_opens[0]
    root_close = matching_brace[root_open]

    def property_strings(start, end, property_name, expected_depth):
        values = []
        for i in range(start, end - 3):
            if (depth_before.get(i) == expected_depth
                    and tokens[i] == ("atom", property_name)
                    and tokens[i + 1] == ("punct", "=")
                    and tokens[i + 2][0] == "string"
                    and tokens[i + 3] == ("punct", ";")):
                values.append(tokens[i + 2][1])
        return values

    root_compatibles = property_strings(root_open + 1, root_close, "compatible", 1)
    if ROOT_COMPATIBLE not in root_compatibles:
        raise ValueError(f"input root does not identify {ROOT_COMPATIBLE}")
    pmu_opens = [i + 1 for i in range(root_open + 1, root_close)
                 if tokens[i] == ("atom", "pmu")
                 and i + 1 < len(tokens)
                 and tokens[i + 1] == ("punct", "{")
                 and depth_before.get(i + 1) == 1]
    if len(pmu_opens) != 1:
        raise ValueError("expected exactly one top-level pmu node")
    pmu_open = pmu_opens[0]
    pmu_close = matching_brace[pmu_open]
    pmu_compatibles = property_strings(pmu_open + 1, pmu_close, "compatible", 2)
    if pmu_compatibles != [expected_pmu]:
        raise ValueError(f"PMU compatible must be exactly {expected_pmu}")
    return {"root_compatible": root_compatibles,
            "pmu_compatible": pmu_compatibles[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-source", type=Path, required=True,
                        help="Read-only extracted Samsung kernel source root")
    parser.add_argument("--target", type=Path, required=True,
                        help="New, nonexistent output directory")
    args = parser.parse_args()
    kernel = args.kernel_source.resolve()
    target = args.target.resolve()
    if target.exists():
        parser.error(f"target already exists; refusing to overwrite: {target}")
    if target == kernel or target in kernel.parents or kernel in target.parents:
        parser.error("target must be separate from the read-only kernel source tree")
    source_arm = kernel / "arch/arm/boot/dts"
    source_arm64 = kernel / "arch/arm64/boot/dts/mediatek/a02"
    if not source_arm.is_dir() or not source_arm64.is_dir():
        parser.error("expected Samsung ARM32 DTS and A02 ARM64 overlay directories")
    overlay_sources = sorted(path for path in source_arm64.iterdir()
                             if path.suffix in {".dts", ".dtsi"})
    overlay_names = {path.name for path in overlay_sources}
    missing_overlays = sorted(EXPECTED_A02_OVERLAYS - overlay_names)
    if missing_overlays:
        parser.error(f"expected A02 revision overlays are missing: {', '.join(missing_overlays)}")
    source_files = [source_arm / relative for relative in ARM_FILES] + overlay_sources
    for source in source_files:
        if not source.is_file() or source.is_symlink():
            parser.error(f"required DTS input is missing or not a regular file: {source.relative_to(kernel)}")
        if kernel not in source.resolve().parents:
            parser.error("DTS input resolves outside the kernel source root")
    originals = {source: source.read_bytes() for source in source_files}
    try:
        validate_stock_base(originals[source_arm / "mt6739.dts"])
    except (ValueError, UnicodeError) as exc:
        parser.error(str(exc))
    for source, original in originals.items():
        if source.read_bytes() != original:
            parser.error(f"source input changed during preflight: {source.relative_to(kernel)}")
    dt_root = target / "src/arch/arm64/boot/dts"
    mt_dir = dt_root / "mediatek"
    manifest = {"description": "Isolated Samsung MT6739/A02 DTS copy with one ARMv8 PMU adaptation",
                "input_identity": ROOT_COMPATIBLE,
                "pmu_change": {"node": "/pmu", "property": "compatible",
                               "from": PMU_COMPATIBLE_BEFORE, "to": PMU_COMPATIBLE_AFTER},
                "files": []}

    for relative in ARM_FILES:
        source = source_arm / relative
        if relative == "mt6739.dts":
            destination = mt_dir / "mt6739-sm-a022f-stock.dts"
        elif relative.startswith("k39tv1_bsp_titan_hamster"):
            destination = dt_root / relative
        else:
            destination = mt_dir / relative
        original = originals[source]
        content = original
        if relative == "mt6739.dts":
            before = f'compatible = "{PMU_COMPATIBLE_BEFORE}";'.encode()
            after = f'compatible = "{PMU_COMPATIBLE_AFTER}";'.encode()
            if content.count(before) != 1:
                raise RuntimeError("Stock PMU property changed; inspect source manually")
            content = content.replace(before, after, 1)
            parsed = validate_stock_base(content, PMU_COMPATIBLE_AFTER)
            if parsed["pmu_compatible"] != PMU_COMPATIBLE_AFTER:
                raise RuntimeError("Post-edit PMU validation failed")
            if original.replace(before, after, 1) != content:
                raise RuntimeError("Unexpected change outside /pmu:compatible")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        manifest["files"].append({"origin": source.relative_to(kernel).as_posix(),
                                  "staged": destination.relative_to(target).as_posix(),
                                  "origin_sha256": digest(original),
                                  "staged_sha256": digest(content),
                                  "changed": content != original})

    for source in overlay_sources:
        content = originals[source]
        destination = mt_dir / "a02" / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        manifest["files"].append({"origin": source.relative_to(kernel).as_posix(),
                                  "staged": destination.relative_to(target).as_posix(),
                                  "origin_sha256": digest(content),
                                  "staged_sha256": digest(content),
                                  "changed": False})
    (target / "sources-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Staged {len(manifest['files'])} source files in {target}")


if __name__ == "__main__":
    main()
