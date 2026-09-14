# Suggested GHSA notes (English, factual)

Submit via “Suggest improvements for this vulnerability” on:

- https://github.com/advisories/GHSA-5p2g-fcmc-qvqq
- https://github.com/advisories/GHSA-w3rx-r6r6-pgpr

Do **not** ask GitHub to list a different npm package as `patched_versions` of `image-size`. Ask only for notes + references.

## Details / notes to add

```
Workaround (community fork; not affiliated with the original maintainer):

image-size 1.x (Metro, React Native, CJS sync API — including 1.2.1) remains affected. Do not jump to 2.x.

  npm overrides:  "image-size": "npm:image-size-next@1.2.2"
  compare: https://github.com/lcf2212dev/image-size-next/compare/v1.2.1...v1.2.2
  dist-tag: legacy

image-size 2.x (including 2.0.2):

  npm overrides:  "image-size": "npm:image-size-next@2.1.1"
  compare: https://github.com/lcf2212dev/image-size-next/compare/v2.0.2...v2.1.1
  dist-tag: latest

npm audit fix will not rename the package. Mixing majors breaks Metro (v2 dropped the sync API).
```

## References to add

- https://www.npmjs.com/package/image-size-next
- https://github.com/lcf2212dev/image-size-next
- https://github.com/lcf2212dev/image-size-next/compare/v1.2.1...v1.2.2
- https://github.com/lcf2212dev/image-size-next/compare/v2.0.2...v2.1.1
