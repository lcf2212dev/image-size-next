# Contributing

Thanks for helping maintain **image-size-next**.

## Setup

```bash
git clone https://github.com/lcf2212dev/image-size-next.git
cd image-size-next
npm install
npm test
npm run build
```

## Development

- Source lives in `lib/`.
- Tests live in `specs/` (`node:test` + TypeScript via `ts-node`).
- Build output is produced by `tsup` into `dist/`.

```bash
npm test
npm run lint
npm run build
```

## Code style

- All user-facing documentation and commit messages must be in **English**.
- **Do not add comments** in source (`lib/`, `bin/`, `specs/`). Prefer clear names and structure; put explanations in docs when needed.
- Keep the public API drop-in compatible with `image-size@2.0.2` unless a major version bump is intentional.

## Pull requests

1. Fork the repository and create a feature branch.
2. Add or update tests for behavior changes, especially security-related paths.
3. Ensure `npm test` and `npm run build` pass.
4. Open a PR with a clear description of the problem and solution.

## Security issues

See [SECURITY.md](./SECURITY.md). Do not disclose security issues in public PRs before coordinated disclosure.
