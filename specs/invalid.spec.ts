import * as assert from 'node:assert'
import { describe, it } from 'node:test'
import { sync as globSync } from 'glob'
import { imageSizeFromFile } from '../lib/fromFile'

// Test all invalid files
describe('Invalid Images', () => {
  const invalidFiles = globSync('specs/images/invalid/**/*.*')

  it('discovers invalid fixture images (glob must not be empty)', () => {
    assert.ok(
      invalidFiles.length > 0,
      'expected specs/images/invalid/**/*.* to match fixture files',
    )
  })

  for (const file of invalidFiles) {
    describe(file, () => {
      it('should callback with error when called asynchronously', async () => {
        await assert.rejects(
          async () => await imageSizeFromFile(file),
          (err: Error) => {
            assert.ok(err instanceof TypeError)
            assert.match(err.message, /^Invalid \w+$/)
            return true
          },
        )
      })
    })
  }

  describe('non-existent file', () => {
    const fakeFile = 'fakefile.jpg'

    it('should callback with error when called asynchronously', async () => {
      await assert.rejects(
        async () => await imageSizeFromFile(fakeFile),
        (err: Error) => {
          assert.ok(err instanceof Error)
          assert.match(err.message, /^ENOENT.*$/)
          return true
        },
      )
    })
  })
})
