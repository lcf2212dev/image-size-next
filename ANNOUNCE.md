# Announcement kit (English only)

Use these copy blocks for X, Hacker News, Reddit, and dependent outreach.
Do **not** use Portuguese or other languages for public posts about this package.

Two lines — never mix:

| Tree | Upstream | Fork | Dist-tag |
| --- | --- | --- | --- |
| Metro / RN / `image-size@^1` | 1.2.1 | **image-size-next@1.2.2** | `legacy` |
| `image-size@^2` | 2.0.2 | **image-size-next@2.1.1** | `latest` |

## X / Twitter — post 1 (main)

```
image-size (npm, tens of millions of weekly downloads) is archived and still vulnerable to CVE-2025-71329 / CVE-2025-71330 (DoS infinite loops) on both 1.2.1 and 2.0.2.

Community drop-in fork:

1.x / Metro:  npm i image-size-next@1.2.2   (dist-tag legacy)
2.x:          npm i image-size-next@2.1.1

https://github.com/lcf2212dev/image-size-next
Do not replace Metro 1.x with 2.x.
```

**Compose link:**  
https://twitter.com/intent/tweet?text=image-size%20(npm)%20is%20archived%20and%20still%20vulnerable%20to%20CVE-2025-71329%20/%20CVE-2025-71330%20on%20both%201.2.1%20and%202.0.2.%0A%0ACommunity%20drop-in%3A%0A1.x%20%2F%20Metro%3A%20image-size-next%401.2.2%20(legacy)%0A2.x%3A%20image-size-next%402.1.1%0Ahttps%3A%2F%2Fgithub.com%2Flcf2212dev%2Fimage-size-next

## X / Twitter — post 2 (reply / thread)

```
Quick migrate — pick the major you already use.

// Metro / image-size@^1
"overrides": { "image-size": "npm:image-size-next@1.2.2" }

// image-size@^2
"overrides": { "image-size": "npm:image-size-next@2.1.1" }

npm audit fix will NOT rename the package or jump 1.x → 2.x.
```

## X / Twitter — post 3 (reply / thread)

```
Not affiliated with the original maintainer.
Upstream repo archived; 1.2.1 and 2.0.2 remain open to event-loop DoS on crafted images.

If you depend on image-size (directly or transitively), run:
npm ls image-size
and patch via override for that major.
```

## Hacker News

**Title:**  
`image-size-next: maintained fork of image-size fixing CVE-2025-71329/71330 (1.2.1 Metro + 2.0.2)`

**URL:**  
https://github.com/lcf2212dev/image-size-next

**Optional text:**  
Upstream `image-size` is archived. Both **1.2.1** (what Metro `^1.0.2` resolved to) and **2.0.2** stay open to the DoS CVEs; `npm audit fix` cannot rename the package. `image-size-next@1.2.2` (`legacy`) is the 1.x drop-in; `@2.1.1` is the 2.x drop-in. Do not override Metro onto 2.x.

## Reddit (r/node, r/javascript, r/netsec, r/webdev)

**Title:**  
Maintained drop-in fork for vulnerable image-size 1.2.1 (Metro) and 2.0.2 — CVE-2025-71329 / CVE-2025-71330

**Body:**

```
## Context

The npm package `image-size` is archived. Two high-severity DoS issues remain open on **both** published lines:

- CVE-2025-71329 (JXL/HEIF/JP2 zero-size boxes → infinite loop)
- CVE-2025-71330 (ICNS zero entry length → infinite loop)

`image-size@1.2.1` is what Metro (`^1.0.2`) and many React Native / Babel-bundler trees still resolve. `2.0.2` is latest 2.x. Neither is patched upstream.

## What we shipped

Community-maintained drop-in: **image-size-next**

- 1.x / Metro: `image-size-next@1.2.2` (npm dist-tag `legacy`)
- 2.x: `image-size-next@2.1.1` (`latest`)
- https://www.npmjs.com/package/image-size-next
- https://github.com/lcf2212dev/image-size-next

## Migration

```json
{
  "overrides": {
    "image-size": "npm:image-size-next@1.2.2"
  }
}
```

or `@2.1.1` if your tree is already on image-size 2.x. **Do not mix majors.**

`npm audit fix` will not rename the package.

Not affiliated with the original maintainer — honest community fork only.
```

## Dependent issue / PR comment template

Prefer the files in `campaign/templates/` (`issue.md`, `discussion.md`, `maintainer_comment.md`). They fill `{{FORK_VERSION}}` from `resolved_major`. Do not paste a 2.x override into a Metro repo.

## High-value dependents to contact first (manual / PRs)

Contact **T0/T1 after `classify_major.py`**, with the matching major. Metro latest vendored parsers (0.84.5 / 0.83.8); older Metro on npm still pulls 1.2.1 — comment existing security threads, do not open a duplicate blast issue.

## Language policy

All public docs, posts, issues, PRs, and release notes for this campaign: **English only**.
