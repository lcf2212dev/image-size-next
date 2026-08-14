# image-size-next (1.x)

Community-maintained **1.x** line of [`image-size`](https://github.com/image-size/image-size) for consumers such as **Metro** (`image-size@^1.0.2`).

Fixes **CVE-2025-71329** and **CVE-2025-71330**. Same 1.x API as `image-size@1.2.1`.

Not affiliated with the original maintainer.

## Diff vs upstream

This tag is a descendant of upstream [`v1.2.1`](https://github.com/image-size/image-size/releases/tag/v1.2.1):

https://github.com/lcf2212dev/image-size-next/compare/v1.2.1...v1.2.2

```bash
git fetch --tags
git diff v1.2.1..v1.2.2
```

## Install

```bash
npm install image-size-next@1.2.2
# or
npm install image-size-next@1.x
```

Do **not** use this line as npm `latest` — that remains **2.1.x**.

### Metro / Yarn resolution

```json
{
  "resolutions": {
    "image-size": "npm:image-size-next@1.2.2"
  }
}
```

### npm overrides

```json
{
  "overrides": {
    "image-size": "npm:image-size-next@1.2.2"
  }
}
```

## 2.x line

For `image-size@2.x` consumers use **`image-size-next@2.1.1`** (`latest`).

## License

MIT. Original work © Aditya Yadav and contributors. This line © 2026 lcf2212dev.
