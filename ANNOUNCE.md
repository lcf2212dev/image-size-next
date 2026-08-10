# Announcement kit (English only)

Use these copy blocks for X, Hacker News, Reddit, and dependent outreach.
Do **not** use Portuguese or other languages for public posts about this package.

## X / Twitter — post 1 (main)

```
image-size (npm, tens of millions of weekly downloads) is archived and still vulnerable to CVE-2025-71329 / CVE-2025-71330 (DoS infinite loops).

Community drop-in fork with fixes:

npm: image-size-next@2.1.0
https://github.com/lcf2212dev/image-size-next
https://www.npmjs.com/package/image-size-next

MIT · same API · overrides-friendly
```

**Compose link:**  
https://twitter.com/intent/tweet?text=image-size%20%28npm%2C%20tens%20of%20millions%20of%20weekly%20downloads%29%20is%20archived%20and%20still%20vulnerable%20to%20CVE-2025-71329%20/%20CVE-2025-71330%20%28DoS%20infinite%20loops%29.%0A%0ACommunity%20drop-in%20fork%20with%20fixes%3A%0A%0Anpm%3A%20image-size-next%402.1.0%0Ahttps%3A//github.com/lcf2212dev/image-size-next%0Ahttps%3A//www.npmjs.com/package/image-size-next%0A%0AMIT%20%C2%B7%20same%20API%20%C2%B7%20overrides-friendly

## X / Twitter — post 2 (reply / thread)

```
Quick migrate:

npm i image-size-next

// force transitive deps (npm 8.3+):
"overrides": {
  "image-size": "npm:image-size-next@2.1.0"
}

Import path: image-size → image-size-next
fromFile: image-size/fromFile → image-size-next/fromFile

npm audit fix will NOT rename the package automatically.
```

## X / Twitter — post 3 (reply / thread)

```
Not affiliated with the original maintainer.
Upstream repo archived; 2.0.2 is still the latest release and remains open to event-loop DoS on crafted images.

If you depend on image-size (directly or transitively), run:
npm ls image-size
and patch via override or dependency swap.
```

## Hacker News

**Title:**  
`image-size-next: maintained fork of image-size fixing CVE-2025-71329/71330 (upstream archived)`

**URL:**  
https://github.com/lcf2212dev/image-size-next

**Optional text:**  
Upstream `image-size` (~tens of millions of weekly downloads) is archived at 2.0.2 with open DoS CVEs. `image-size-next@2.1.0` is a MIT drop-in with those fixes. Use `overrides` for transitive deps — `npm audit fix` will not switch package names.

## Reddit (r/node, r/javascript, r/netsec, r/webdev)

**Title:**  
Maintained drop-in fork for vulnerable image-size (CVE-2025-71329 / CVE-2025-71330) — upstream archived

**Body:**

```
## Context

The npm package `image-size` is widely used and still at **2.0.2**. The GitHub repo is **archived**. Two high-severity DoS issues remain open:

- CVE-2025-71329 (JXL/HEIF/JP2 zero-size boxes → infinite loop)
- CVE-2025-71330 (ICNS zero entry length → infinite loop)

## What we shipped

Community-maintained drop-in: **image-size-next@2.1.0**

- https://www.npmjs.com/package/image-size-next
- https://github.com/lcf2212dev/image-size-next

Same public API as `image-size@2.0.2`, MIT, Node 18+.

## Migration

```bash
npm install image-size-next
```

```json
{
  "overrides": {
    "image-size": "npm:image-size-next@2.1.0"
  }
}
```

**Important:** `npm audit fix` will not rename the package. You need an override or an explicit dependency change.

Not affiliated with the original maintainer — honest community fork only.
```

## Dependent issue / PR comment template

```
A community-maintained drop-in fork fixes CVE-2025-71329 and CVE-2025-71330 while preserving the image-size@2.0.2 API:

- npm: https://www.npmjs.com/package/image-size-next
- GitHub: https://github.com/lcf2212dev/image-size-next

```json
{
  "overrides": {
    "image-size": "npm:image-size-next@2.1.0"
  }
}
```

`npm audit fix` will not switch package names automatically.
Not affiliated with the original maintainer. Happy to open a PR if helpful.
```

## High-value dependents to contact first (manual / PRs)

Priority targets already depending on vulnerable `image-size` (from public search + known issues):

| Package / repo | Signal |
|----------------|--------|
| mastra-ai/mastra (`@mastra/memory`) | Open security issue #17975 |
| webpack/image-minimizer-webpack-plugin | Depends on `image-size@^2.0.2` |
| jantimon/favicons-webpack-plugin | Depends on `image-size` |
| heavysixer/node-pptx | Depends on `image-size@^2.0.2` |
| alfonsusac/check-site-meta | Depends on `image-size@^2.0.1` |
| transitive-bullshit/puppeteer-lottie | Depends on `image-size` |
| AlenVelocity/wa-sticker-formatter | Depends on `image-size` |

Expand with npm “Dependents” of `image-size` sorted by downloads before mass PRs.

## Language policy

All public docs, posts, issues, PRs, and release notes for this campaign: **English only**.
