import { expect } from 'chai'
import { imageSize } from '../lib'

const TIMEOUT_MS = 100

function assertCompletesQuickly(fn: () => void) {
  const start = Date.now()
  let threw: unknown
  try {
    fn()
  } catch (err) {
    threw = err
  }
  const elapsed = Date.now() - start
  expect(elapsed).to.be.lessThan(
    TIMEOUT_MS,
    `expected completion within ${TIMEOUT_MS}ms, took ${elapsed}ms`,
  )
  return threw
}

describe('security: denial of service via zero-size structures', () => {
  it('does not hang on JXL container with zero-size box', () => {
    const payload = new Uint8Array([
      0x00, 0x00, 0x00, 0x00, 0x4a, 0x58, 0x4c, 0x20,
    ])
    const err = assertCompletesQuickly(() => imageSize(payload))
    expect(err).to.be.instanceOf(Error)
  })

  it('does not hang on HEIF-like buffer with zero-size ispe box', () => {
    const payload = new Uint8Array([
      0x00, 0x00, 0x00, 0x10, 0x66, 0x74, 0x79, 0x70, 0x61, 0x76, 0x69, 0x66,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x24, 0x6d, 0x65, 0x74, 0x61,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x69, 0x70, 0x72, 0x70,
      0x00, 0x00, 0x00, 0x14, 0x69, 0x70, 0x63, 0x6f, 0x00, 0x00, 0x00, 0x00,
      0x69, 0x73, 0x70, 0x65, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ])
    const err = assertCompletesQuickly(() => imageSize(payload))
    expect(err).to.be.instanceOf(Error)
  })

  it('does not hang on JP2-like buffer with zero-size box', () => {
    const payload = new Uint8Array([
      0x00, 0x00, 0x00, 0x00, 0x6a, 0x50, 0x20, 0x20,
    ])
    const err = assertCompletesQuickly(() => imageSize(payload))
    expect(err).to.be.instanceOf(Error)
  })

  it('does not hang on ICNS with zero-length entry', () => {
    const payload = new Uint8Array([
      0x69, 0x63, 0x6e, 0x73, 0x00, 0x00, 0x00, 0x10, 0x69, 0x73, 0x33, 0x32,
      0x00, 0x00, 0x00, 0x00,
    ])
    const err = assertCompletesQuickly(() => imageSize(payload))
    expect(err).to.be.instanceOf(Error)
  })

  it('rejects ISO BMFF box size of one (64-bit largesize) without hanging', () => {
    const payload = new Uint8Array([
      0x00, 0x00, 0x00, 0x01, 0x66, 0x74, 0x79, 0x70, 0x61, 0x76, 0x69, 0x66,
      0x00, 0x00, 0x00, 0x00,
    ])
    const err = assertCompletesQuickly(() => imageSize(payload))
    expect(err).to.be.instanceOf(Error)
  })
})
