# Changelog (1.x line)

## [1.2.2] - 2026-08-13

### Security

- Fixed CVE-2025-71329 (DoS infinite loops on zero-size ISO BMFF boxes in JXL / HEIF / JP2).
- Fixed CVE-2025-71330 (DoS infinite loop on zero-length ICNS entries).
- Reject JPEG segments with length &lt; 2.

### Changed

- Published as **image-size-next@1.2.2** for Metro and other `image-size@^1.x` consumers.
- Git history is based on upstream `image-size@v1.2.1`.
- Compare: https://github.com/lcf2212dev/image-size-next/compare/v1.2.1...v1.2.2

This line is **not** npm `latest` (`latest` remains 2.1.x). Install with `image-size-next@1.2.2` or the `1.x` dist-tag.
