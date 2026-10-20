from pathlib import Path
import csv
import re


HERE = Path(__file__).resolve().parent
SOURCES = {
    "stock_arm32": HERE / "stock-arm32-last-reboot-reason-fields.txt",
    "arm64_fallback": HERE / "arm64-last-reboot-reason-fields.txt",
    "arm64_sec_header": HERE / "arm64-last-reboot-reason-fields.txt",
}


def parse_structs(path):
    text = path.read_text()
    structs = []
    for body in re.split(r"\n0x[0-9a-f]+:\s+NULL\s*\n", text):
        if 'DW_AT_name\t("last_reboot_reason")' not in body:
            continue
        size = int(re.search(r"DW_AT_byte_size\s*\(0x([0-9a-f]+)\)", body).group(1), 16)
        members = {}
        for item in re.split(r"\n0x[0-9a-f]+:\s+DW_TAG_member", body)[1:]:
            name = re.search(r"DW_AT_name\s*\(\"([^\"]+)\"\)", item)
            offset = re.search(r"DW_AT_data_member_location\s*\(0x([0-9a-f]+)\)", item)
            typename = re.search(r"DW_AT_type\s*\(0x[0-9a-f]+ \"([^\"]+)\"\)", item)
            if name and offset:
                members[name.group(1)] = (int(offset.group(1), 16), typename.group(1) if typename else "")
        structs.append((size, members))
    return structs


stock = parse_structs(SOURCES["stock_arm32"])[0]
arm64_fallback, arm64_sec_header = parse_structs(SOURCES["arm64_fallback"])
models = {"stock_arm32": stock, "arm64_fallback": arm64_fallback, "arm64_sec_header": arm64_sec_header}

with (HERE / "last-reboot-reason-abi.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["field", "stock_arm32_offset", "stock_arm32_type", "arm64_fallback_offset", "arm64_fallback_type", "arm64_sec_header_offset", "arm64_sec_header_type"])
    for name in sorted(stock[1] | arm64_fallback[1] | arm64_sec_header[1]):
        writer.writerow([name, *stock[1].get(name, ("", "")), *arm64_fallback[1].get(name, ("", "")), *arm64_sec_header[1].get(name, ("", ""))])

print("struct sizes:", {name: model[0] for name, model in models.items()})
print("field counts:", {name: len(model[1]) for name, model in models.items()})
print("stock/fallback differing shared offsets:", [name for name in stock[1].keys() & arm64_fallback[1].keys() if stock[1][name][0] != arm64_fallback[1][name][0]])
print("stock/sec-header differing shared offsets:", [name for name in stock[1].keys() & arm64_sec_header[1].keys() if stock[1][name][0] != arm64_sec_header[1][name][0]])
print("stock-only fields:", list(stock[1].keys() - arm64_fallback[1].keys()))
