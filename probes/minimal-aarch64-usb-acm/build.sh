#!/usr/bin/env bash
set -euo pipefail

here=$(cd -- "$(dirname -- "$0")" && pwd)
kernel_work_root=${KERNEL_WORK_ROOT:-}
: "${kernel_work_root:?Set KERNEL_WORK_ROOT to the existing local Galaxy A02 workspace}"
clang=${CLANG:-$kernel_work_root/prebuilts/clang/host/linux-x86/clang-r383902/bin/clang}
gen_init_cpio=${GEN_INIT_CPIO:-$kernel_work_root/kernel-source-arm64-exp/out-arm64-a02/usr/gen_init_cpio}
out="$here/build"
mkdir -p "$out"

"$clang" --target=aarch64-linux-gnu -fuse-ld=lld \
    -O2 -Wall -Wextra -Werror -ffreestanding -fno-stack-protector -fno-pic \
    -nostdlib -static -Wl,-e,_start -Wl,--build-id=none \
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
