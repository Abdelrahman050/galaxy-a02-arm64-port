# PowerVR Gralloc and Handle Audit

An offline inspection of the stock 32-bit PowerVR graphics stack found a fixed native-handle envelope of 208 bytes with 49 integer slots. This is a limited structural observation from the inspected firmware build, not a complete public ABI specification.

The exact private field meanings and versioning, metadata encoding, allocation flags, plane layouts, cache maintenance, fences, protected buffers, ION/PowerVR interactions, and ownership rules remain unresolved. No ARM64 mapper or gralloc implementation has been built or validated.

Consequences for the port:

- The stock ELF32 mapper cannot be loaded inside a 64-bit framework process.
- A 32-bit allocator or composer service may be callable through Binder/HIDL only if the framework/vendor interface and transferred buffer handles are compatible; this is unverified.
- A new ARM64 mapper must correctly import, lock, unlock, describe, and release the stock-compatible buffer protocol. Matching the 208-byte size alone is insufficient.
- SwiftShader or another off-screen software renderer would not prove a usable phone UI; the rendered buffer must reach the panel through a validated composer/display path.

The proprietary graphics binaries and raw disassembly are excluded. See [`android-userspace-audit.md`](android-userspace-audit.md) for the userspace integration status. Graphics remains a critical blocker and is not proven by kernel compilation.
