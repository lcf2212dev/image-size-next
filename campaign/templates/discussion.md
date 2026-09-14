## Context

This package depends on npm **`image-size`** at **{{DECLARED_RANGE}}** ({{API_NOTE}}).

Upstream is **archived**. **`image-size@{{UPSTREAM_VERSION}}`** remains affected by:

- **CVE-2025-71329** / [GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq) — DoS via infinite loop (JXL/HEIF/JP2 zero-size boxes)
- **CVE-2025-71330** / [GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) — DoS via infinite loop (ICNS zero entry length)

`npm audit fix` will **not** switch package names. **Do not** replace a 1.x tree (Metro / React Native) with the 2.x fork, or a 2.x tree with the 1.x fork.

## Maintained drop-in (this major only)

Community MIT fork with the same public API as `image-size@{{UPSTREAM_VERSION}}`:

- **npm:** https://www.npmjs.com/package/image-size-next (`image-size-next@{{FORK_VERSION}}`, dist-tag `{{DIST_TAG}}`)
- **GitHub:** https://github.com/lcf2212dev/image-size-next
- **Compare:** {{COMPARE_URL}}
- **Hub:** {{HUB_DISCUSSION_URL}}
- **Announcement:** {{X_ANNOUNCE_URL}}

Not affiliated with the original `image-size` maintainer — honest community fork only.

## Migration

**A — Direct dependency**

```bash
npm install image-size-next@{{FORK_VERSION}}
```

**B — Force transitive resolution (npm 8.3+)**

```json
{
  "overrides": {
    "image-size": "npm:image-size-next@{{FORK_VERSION}}"
  }
}
```

## Ask

Happy to open a PR if that helps. Flagging this so maintainers of **`{{PACKAGE_NAME}}`** can patch on their schedule.

Thanks for maintaining open source.
