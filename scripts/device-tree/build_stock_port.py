#!/usr/bin/env python3
"""Build isolated SM-A022F DT sources; compare every merged FDT with official firmware.

Run inside Linux/WSL with cpp, dtc and fdtoverlay available. Inputs are read only;
all compiler outputs and logs stay below this script's build/ directory.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from build_candidates import compare_properties, read_fdt  # noqa: E402


REVISIONS = {
    "r00": ("a02_eur_open_w00_r00.dts", "dtbo-0.dtb", "a02-eur-open-00-merged.dtb"),
    "r01": ("a02_eur_open_w00_r01.dts", "dtbo-1.dtb", "a02-eur-open-01-merged.dtb"),
    "r06": ("a02_eur_open_w00_r06.dts", "dtbo-2.dtb", "a02-eur-open-01b-merged.dtb"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, log):
    result = subprocess.run(command, capture_output=True, text=True)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}; see {log}")


def compare(left_path, right_path):
    left, left_stats = read_fdt(left_path)
    right, right_stats = read_fdt(right_path)
    return {
        "left_nodes": left_stats["node_count"],
        "right_nodes": right_stats["node_count"],
        "left_properties": left_stats["property_count"],
        "right_properties": right_stats["property_count"],
        "memreserve_equal": left_stats["memreserve"] == right_stats["memreserve"],
        "missing_nodes": sorted(set(left) - set(right)),
        "extra_nodes": sorted(set(right) - set(left)),
        "changed_properties": compare_properties(left, right),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-source", type=Path, required=True,
                        help="Read-only Samsung kernel-source tree for headers/config")
    parser.add_argument("--firmware-analysis", type=Path, required=True,
                        help="Read-only extracted official DTB/DTBO directory")
    parser.add_argument("--stage", type=Path, required=True,
                        help="Separate writable staging directory previously prepared by prepare_stock_port.py")
    args = parser.parse_args()
    stage = args.stage.resolve()
    source = stage / "src/arch/arm64/boot/dts"
    mediatek = source / "mediatek"
    build = stage / "build"
    firmware = args.firmware_analysis.resolve()
    kernel = args.kernel_source.resolve()
    if any(root == other or root in other.parents or other in root.parents
           for root in (stage,) for other in (firmware, kernel)):
        parser.error("stage must not overlap read-only kernel source or firmware inputs")
    if not (stage / "sources-manifest.json").is_file():
        parser.error("stage must be a prepared staging tree with sources-manifest.json")
    if build.exists() and any(build.iterdir()):
        parser.error("stage/build is non-empty; choose a new staging directory to preserve prior results")
    build.mkdir(parents=True, exist_ok=True)
    base = mediatek / "mt6739-sm-a022f-stock.dts"
    inputs = [base, *mediatek.glob("*.dtsi"), *mediatek.joinpath("a02").glob("*.dts"),
              *source.glob("*.dts"), *source.joinpath("k39tv1_bsp_titan_hamster").glob("*.dtsi")]
    before = {str(path): sha(path) for path in inputs}
    firmware_inputs = [firmware / "boot-dtb-0.dtb"] + [
        firmware / name for _, official_overlay, official_merged in REVISIONS.values()
        for name in (official_overlay, official_merged)
    ]
    before.update({str(path): sha(path) for path in firmware_inputs})

    def preprocess(path, name):
        output = build / f"{name}.pp.dts"
        run(["cpp", "-nostdinc", "-I", str(kernel / "out/include"),
             "-I", str(kernel / "include"), "-I", str(source),
             "-I", str(mediatek), "-undef", "-D__DTS__",
             "-x", "assembler-with-cpp", str(path), "-o", str(output)],
            build / f"{name}-cpp.log")
        return output

    def dtc(path, name):
        output = build / f"{name}.dtb"
        run(["dtc", "-@", "-I", "dts", "-O", "dtb", "-o", str(output), str(path)],
            build / f"{name}-dtc.log")
        return output

    base_dtb = dtc(preprocess(base, "mt6739-sm-a022f-stock"), "mt6739-sm-a022f-stock")
    audit = {
        "description": "ARM32 Samsung MT6739 source base copied to ARM64 staging; PMU compatible changed only",
        "base_vs_official": compare(firmware / "boot-dtb-0.dtb", base_dtb),
        "revisions": {},
    }
    for revision, (board_name, overlay_name, merged_name) in REVISIONS.items():
        overlay = dtc(preprocess(mediatek / "a02" / board_name, revision), revision)
        merged = build / f"{revision}-merged.dtb"
        run(["fdtoverlay", "-i", str(base_dtb), "-o", str(merged), str(overlay)],
            build / f"{revision}-merge.log")
        audit["revisions"][revision] = {
            "source_overlay_sha256": sha(overlay),
            "official_overlay_sha256": sha(firmware / overlay_name),
            "overlay_byte_equal": overlay.read_bytes() == (firmware / overlay_name).read_bytes(),
            "merged_vs_official": compare(firmware / merged_name, merged),
        }
        print(f"{revision}: overlay exact={audit['revisions'][revision]['overlay_byte_equal']}; "
              f"merged changed properties={len(audit['revisions'][revision]['merged_vs_official']['changed_properties'])}")

    after = {name: sha(Path(name)) for name in before}
    if before != after:
        raise RuntimeError("A source or firmware input changed unexpectedly")
    (build / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
