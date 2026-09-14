Hi — security heads-up about a dependency (not marketing spam).

Your package {{PACKAGE_NAME}} depends on npm `image-size` at {{DECLARED_RANGE}}. Upstream is archived; {{UPSTREAM_VERSION}} is still open to CVE-2025-71329 / CVE-2025-71330 (DoS infinite loops).

Community MIT drop-in for this major only:

• npm: image-size-next@{{FORK_VERSION}} (dist-tag {{DIST_TAG}})
• GitHub: https://github.com/lcf2212dev/image-size-next
• Compare: {{COMPARE_URL}}
• Post: {{X_ANNOUNCE_URL}}

"overrides": { "image-size": "npm:image-size-next@{{FORK_VERSION}}" }

Do not mix 1.x (Metro) with 2.x. npm audit fix will not rename the package.

Not affiliated with the original maintainer. Happy to open a PR on {{REPO}} if useful.
Thanks for maintaining open source.
