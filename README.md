# image-size-next

[![npm version](https://img.shields.io/npm/v/image-size-next.svg)](https://www.npmjs.com/package/image-size-next)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

**Community-maintained fork** of [`image-size`](https://github.com/image-size/image-size) — a fast, lightweight Node.js library to get the dimensions of image files and buffers.

> **Not affiliated** with the original `image-size` maintainer. The upstream GitHub repository was archived; this package continues maintenance and ships security fixes for open DoS issues.

## Why this package?

`image-size` through **2.0.2** is vulnerable to event-loop denial of service when parsing certain crafted image inputs:

| CVE | Issue | Status in this fork |
| --- | ----- | ------------------- |
| [CVE-2025-71329](https://nvd.nist.gov/vuln/detail/CVE-2025-71329) | Infinite loop on zero-size boxes (JXL / HEIF / JP2) | **Fixed** in 2.1.0 |
| [CVE-2025-71330](https://nvd.nist.gov/vuln/detail/CVE-2025-71330) | Infinite loop on zero-length ICNS entries | **Fixed** in 2.1.0 |

Use **`image-size-next`** as a drop-in replacement when you need a maintained, patched package.

## Features

- Zero runtime dependencies
- Supports major image formats (see below)
- Works with buffers and files
- Minimal memory footprint — reads image headers only
- ESM and CommonJS
- TypeScript types included

## Supported formats

BMP, CUR, DDS, GIF, HEIC/HEIF/AVIF, ICNS, ICO, J2C, JPEG-2000 (JP2), JPEG, JPEG-XL, KTX (1 and 2), PNG, PNM (PAM, PBM, PFM, PGM, PPM), PSD, SVG, TGA, TIFF, WebP

## Install

```bash
npm install image-size-next
# or
yarn add image-size-next
# or
pnpm add image-size-next
```

**Requirements:** Node.js **18+**

## Migration from `image-size`

```diff
- "image-size": "2.0.2"
+ "image-size-next": "2.1.0"
```

```diff
- import { imageSize } from 'image-size'
+ import { imageSize } from 'image-size-next'

- import { imageSizeFromFile } from 'image-size/fromFile'
+ import { imageSizeFromFile } from 'image-size-next/fromFile'
```

### Force transitive dependency replacement

When **other packages** in your project depend on vulnerable `image-size` (you do not import it yourself), force every resolution of `image-size` to this fork. The public API matches, so nested dependencies keep working without code changes.

Add the block below to the **root** `package.json`, then reinstall.

#### npm (8.3+)

```json
{
  "overrides": {
    "image-size": "npm:image-size-next@2.1.0"
  }
}
```

```bash
rm -rf node_modules package-lock.json
npm install
npm ls image-size
```

#### Yarn (Classic / Berry)

```json
{
  "resolutions": {
    "image-size": "npm:image-size-next@2.1.0"
  }
}
```

```bash
# Yarn Classic
rm -rf node_modules yarn.lock
yarn install
yarn why image-size

# Yarn Berry (v2+)
yarn install
yarn why image-size
```

#### pnpm

```json
{
  "pnpm": {
    "overrides": {
      "image-size": "npm:image-size-next@2.1.0"
    }
  }
}
```

```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
pnpm why image-size
```

After install, `npm ls image-size` / `yarn why` / `pnpm why` should show `image-size-next` (aliased as `image-size`), not the vulnerable `image-size@2.0.2` from the registry.

### Keep the `image-size` import path (alias)

If you want `import … from 'image-size'` (or nested `require('image-size')`) without renaming every import, install this package under the original name:

```bash
# npm
npm install image-size@npm:image-size-next@2.1.0

# Yarn
yarn add image-size@npm:image-size-next@2.1.0

# pnpm
pnpm add image-size@npm:image-size-next@2.1.0
```

That writes a dependency like:

```json
{
  "dependencies": {
    "image-size": "npm:image-size-next@2.1.0"
  }
}
```

For full coverage of **transitive** deps, still add the `overrides` / `resolutions` block from the previous section.

## Usage

### Buffer / Uint8Array

```js
import { imageSize } from 'image-size-next'
// or
const { imageSize } = require('image-size-next')

const dimensions = imageSize(buffer)
console.log(dimensions.width, dimensions.height)
```

### File (async)

```js
import { imageSizeFromFile } from 'image-size-next/fromFile'
// or
const { imageSizeFromFile } = require('image-size-next/fromFile')

const dimensions = await imageSizeFromFile('photos/image.jpg')
console.log(dimensions.width, dimensions.height)
```

Reading from files uses a default concurrency limit of **100**. Change it with:

```js
import { setConcurrency } from 'image-size-next/fromFile'

setConcurrency(50)
```

### Synchronous file read (not recommended)

Blocking the main thread reduces concurrency. Prefer `imageSizeFromFile`. If you must:

```js
import { readFileSync } from 'node:fs'
import { imageSize } from 'image-size-next'

const buffer = readFileSync('photos/image.jpg')
const dimensions = imageSize(buffer)
```

### Command line

```bash
npx image-size-next image1.jpg image2.png
```

### Multi-size images

For HEIF, ICO, or CUR files, `width` and `height` refer to the largest image. An `images` array lists all sizes when present.

```js
import { imageSizeFromFile } from 'image-size-next/fromFile'

const { images } = await imageSizeFromFile('icons/multi-size.ico')
for (const dimensions of images) {
  console.log(dimensions.width, dimensions.height)
}
```

### Disable certain types

```js
import { disableTypes } from 'image-size-next'

disableTypes(['tiff', 'ico'])
```

### JPEG orientation

When EXIF orientation is present, it is returned as a number from 1 to 8.

```js
const { width, height, orientation } = await imageSizeFromFile('photo.jpeg')
```

## Limitations

1. **Partial file reading** — only headers are read; some corrupted images may still report dimensions.
2. **SVG** — pixel dimensions and `viewBox` only; percentage values are not supported.
3. **File access** — default concurrency limit of 100 for `imageSizeFromFile`.
4. **Buffers** — some formats (e.g. TIFF) need enough of the header present in the buffer.

## API compatibility

Public API matches `image-size@2.0.2`:

| Export | Module |
| ------ | ------ |
| `imageSize`, `disableTypes`, `types` | `image-size-next` |
| `imageSizeFromFile`, `setConcurrency` | `image-size-next/fromFile` |
| CLI | `image-size-next` |

## Security

See [SECURITY.md](./SECURITY.md) for reporting vulnerabilities and the list of fixed CVEs.

## License

[MIT](./LICENSE)

- Original work: Copyright © 2013–2025 Aditya Yadav and contributors
- This fork: Copyright © 2026 lcf2212dev · [GitHub](https://github.com/lcf2212dev) · [X](https://x.com/lcf2212dev)

## Credits

- Original [`image-size`](https://github.com/image-size/image-size) by [Aditya Yadav (netroy)](https://github.com/netroy) and [contributors](https://github.com/image-size/image-size/blob/main/Contributors.md)
- Inspired by [dabble's imagesize](https://github.com/dabble/imagesize)
- Security research shared publicly by [Joshua Rogers](https://joshua.hu/image-size-infinite-loop-dos-vulnerabilities) and advisory databases

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).
