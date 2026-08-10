# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 2.1.x   | Yes       |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, report privately via one of:

1. GitHub Security Advisories on this repository (preferred).
2. Email the maintainer listed in `package.json`.

Include:

- A clear description of the issue
- Affected versions
- Steps to reproduce (minimal fixture preferred)
- Impact assessment (e.g. hang, crash, info leak)

You should receive an acknowledgment within a few business days when possible.

## Known Fixed Issues

This fork specifically addresses denial-of-service conditions present in `image-size` through 2.0.2:

| ID | Summary | Fixed in |
| -- | ------- | -------- |
| CVE-2025-71329 | Infinite loop on zero-size JXL/HEIF/JP2 boxes | 2.1.0 |
| CVE-2025-71330 | Infinite loop on zero-length ICNS entries | 2.1.0 |

Related historical advisory on the original package: [GHSA-m5qc-5hw7-8vg7](https://github.com/advisories/GHSA-m5qc-5hw7-8vg7) (partially fixed upstream in 2.0.2; residual issues remain there).

## Design Notes

Untrusted image buffers must never be able to hang the Node.js event loop. Length and size fields from parsers are validated so offsets always make forward progress or parsing aborts with an error.
