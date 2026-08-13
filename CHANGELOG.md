# Changelog

All notable changes to this project will be documented in this file.

## [2.1.1] - 2026-08-11

### Security

- Same DoS fixes as 2.1.0 (CVE-2025-71329 / CVE-2025-71330).

### Changed

- Git history is now based on upstream `image-size@v2.0.2`, so this release is a real descendant of the original repository.
- Restored upstream comments and format-spec documentation in source.
- Restored fixture globs (`specs/images/valid/**/*.*` and `invalid/**/*.*`) and fail CI if they match nothing.
- Compare: https://github.com/lcf2212dev/image-size-next/compare/v2.0.2...v2.1.1


## [2.1.0] - 2026-08-10

### Security

- Fixed denial-of-service infinite loops when parsing crafted ISO BMFF boxes with a size of zero in JXL, HEIF, and JP2 handlers (**CVE-2025-71329**).
- Fixed denial-of-service infinite loop when parsing ICNS entries with a zero entry length (**CVE-2025-71330**).
- Hardened `readBox` / `findBox` to reject invalid box sizes and normalize ISO BMFF size `0` (extends to end of file) so callers always advance.
- Added progress guards at HEIF, JXL, and JP2 call sites.
- Reject JPEG segments with invalid length (`< 2`) instead of looping on corrupt input.

### Changed

- First release of **image-size-next**, a community-maintained fork of [`image-size@2.0.2`](https://www.npmjs.com/package/image-size).
- Drop-in API compatible with `image-size@2.0.2` (package name and CLI binary differ).
- Requires Node.js **18+**.
- CLI binary renamed to `image-size-next`.

### Credits

- Original library by [Aditya Yadav (netroy)](https://github.com/netroy) and contributors.
- Vulnerability research published by [Joshua Rogers](https://joshua.hu/image-size-infinite-loop-dos-vulnerabilities) and others in public advisories.
