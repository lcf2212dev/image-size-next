# Publish checklist

GitHub: [lcf2212dev/image-size-next](https://github.com/lcf2212dev/image-size-next)  
npm: [lcf2212dev](https://www.npmjs.com/~lcf2212dev) → package `image-size-next`

## 1. Create the GitHub repository

```bash
cd image-size-next
```

If the remote is not set yet:

```bash
gh auth login
gh repo create image-size-next --public --source=. --remote=origin --push
```

or manually:

```bash
git remote add origin https://github.com/lcf2212dev/image-size-next.git
git branch -M main
git push -u origin main
```

## 2. Publish to npm

```bash
npm login
# log in as lcf2212dev
npm whoami
npm run prepublishOnly
npm publish --access public
```

## 3. Tag the release

```bash
git tag v2.1.0
git push origin v2.1.0
gh release create v2.1.0 --title "v2.1.0" --notes-file CHANGELOG.md
```

## 4. Verify

```bash
npm view image-size-next
npx image-size-next path/to/image.png
```
