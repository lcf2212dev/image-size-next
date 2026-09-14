Heads-up for maintainers: a community drop-in fork fixes CVE-2025-71329 / CVE-2025-71330 for the **same major** this repo already uses (`image-size` {{DECLARED_RANGE}} → `image-size-next@{{FORK_VERSION}}`).

- npm: https://www.npmjs.com/package/image-size-next (`{{DIST_TAG}}`)
- GitHub: https://github.com/lcf2212dev/image-size-next
- Compare: {{COMPARE_URL}}
- Hub: {{HUB_DISCUSSION_URL}}
- Announcement: {{X_ANNOUNCE_URL}}

{{API_NOTE}}

```json
{
  "overrides": {
    "image-size": "npm:image-size-next@{{FORK_VERSION}}"
  }
}
```

`npm audit fix` will not rename the package. Not affiliated with the original maintainer. Happy to open a PR if helpful.
