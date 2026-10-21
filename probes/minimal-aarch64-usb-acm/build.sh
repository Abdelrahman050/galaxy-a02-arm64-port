#!/usr/bin/env bash
set -euo pipefail

here=$(cd -- "$(dirname -- "$0")" && pwd)
kernel_work_root=${KERNEL_WORK_ROOT:-}
: "${kernel_work_root:?Set KERNEL_WORK_ROOT to the existing local Galaxy A02 workspace}"
clang=${CLANG:-$kernel_work_root/prebuilts/clang/host/linux-x86/clang-r383902/bin/clang}
gen_init_cpio=${GEN_INIT_CPIO:-$kernel_work_root/kernel-source-arm64-exp/out-arm64-a02/usr/gen_init_cpio}
out=${PROBE_OUT:-$here/build}
: "${USB_VID:?Set USB_VID to a VID you own or are explicitly authorized to use}"
: "${USB_PID:?Set USB_PID to a product ID assigned for that VID}"
: "${USB_SERIAL:?Set USB_SERIAL to a unique USB serial string for this test image}"
usb_vid=${USB_VID^^}
usb_pid=${USB_PID^^}
usb_serial=$USB_SERIAL

if [[ ! "$usb_vid" =~ ^[[:xdigit:]]{4}$ || "$usb_vid" == "0000" || "$usb_vid" == "FFFF" ]]; then
    printf 'USB_VID must be four hex digits, excluding reserved values.\n' >&2
    exit 2
fi
if [[ ! "$usb_pid" =~ ^[[:xdigit:]]{4}$ || "$usb_pid" == "0000" || "$usb_pid" == "FFFF" ]]; then
    printf 'USB_PID must be four hex digits, excluding reserved values.\n' >&2
    exit 2
fi
if [[ ! "$usb_serial" =~ ^[A-Za-z0-9._-]{1,32}$ ]]; then
    printf 'USB_SERIAL must be 1-32 letters, digits, dots, underscores, or hyphens.\n' >&2
    exit 2
fi

[[ -x "$clang" ]] || { printf 'Clang not executable: %s\n' "$clang" >&2; exit 2; }
[[ -x "$gen_init_cpio" ]] || { printf 'gen_init_cpio not executable: %s\n' "$gen_init_cpio" >&2; exit 2; }
for tool in gzip sha256sum readelf touch; do
    command -v "$tool" >/dev/null 2>&1 || { printf 'Required tool not found: %s\n' "$tool" >&2; exit 2; }
done

if [[ -e "$out" ]]; then
    [[ -d "$out" ]] || { printf 'Output path is not a directory: %s\n' "$out" >&2; exit 2; }
    shopt -s nullglob dotglob
    existing=("$out"/*)
    shopt -u nullglob dotglob
    if (( ${#existing[@]} != 0 )); then
        printf 'Refusing to overwrite non-empty output directory: %s\n' "$out" >&2
        exit 2
    fi
fi
mkdir -p "$out"

printf '#define A02_USB_VID 0x%sU\n#define A02_USB_PID 0x%sU\n#define A02_USB_SERIAL "%s"\n' \
    "$usb_vid" "$usb_pid" "$usb_serial" > "$out/probe_identity.h"

"$clang" --target=aarch64-linux-gnu -fuse-ld=lld \
    -O2 -Wall -Wextra -Werror -ffreestanding -fno-stack-protector -fno-pic \
    -nostdlib -static -Wl,-e,_start -Wl,--build-id=none -I "$out" \
    "$here/init.c" -o "$out/init"
touch -d '@0' "$out/init"

cat > "$out/cpio.list" <<EOF
dir /dev 755 0 0
nod /dev/console 600 0 0 c 5 1
dir /sys 755 0 0
file /init init 755 0 0
EOF

(cd "$out" && "$gen_init_cpio" -t 0 cpio.list > initramfs.cpio)
gzip -n -9 -c "$out/initramfs.cpio" > "$out/initramfs.cpio.gz"
(cd "$out" && sha256sum init initramfs.cpio initramfs.cpio.gz > SHA256SUMS)
readelf -h -l "$out/init" > "$out/elf-readelf.txt"
cat "$out/SHA256SUMS"
