import * as assert from 'node:assert'
import { describe, it } from 'node:test'
import {
  findBox,
  readInt16LE,
  readInt32LE,
  readUInt,
  readUInt16BE,
  readUInt16LE,
  readUInt24LE,
  readUInt32BE,
  readUInt32LE,
  readUInt64,
  toHexString,
  toUTF8String,
} from '../lib/types/utils'

describe('Utils', () => {
  describe('toUTF8String', () => {
    it('should convert Uint8Array to UTF8 string', () => {
      const input = new Uint8Array([72, 101, 108, 108, 111])
      assert.equal(toUTF8String(input), 'Hello')
    })

    it('should handle substring conversion with start and end', () => {
      const input = new Uint8Array([72, 101, 108, 108, 111])
      assert.equal(toUTF8String(input, 1, 4), 'ell')
    })
  })

  describe('toHexString', () => {
    it('should convert Uint8Array to hex string', () => {
      const input = new Uint8Array([255, 0, 16])
      assert.equal(toHexString(input), 'ff0010')
    })

    it('should handle substring conversion with start and end', () => {
      const input = new Uint8Array([255, 0, 16])
      assert.equal(toHexString(input, 1, 2), '00')
    })
  })

  describe('Integer reading functions', () => {
    it('readInt16LE should read 16-bit signed integer (little-endian)', () => {
      const input = new Uint8Array([255, 255])
      assert.equal(readInt16LE(input), -1)
    })

    it('readUInt16BE should read 16-bit unsigned integer (big-endian)', () => {
      const input = new Uint8Array([1, 0])
      assert.equal(readUInt16BE(input), 256)
    })

    it('readUInt16LE should read 16-bit unsigned integer (little-endian)', () => {
      const input = new Uint8Array([0, 1])
      assert.equal(readUInt16LE(input), 256)
    })

    it('readUInt24LE should read 24-bit unsigned integer (little-endian)', () => {
      const input = new Uint8Array([1, 1, 1])
      assert.equal(readUInt24LE(input), 65793)
    })

    it('readInt32LE should read 32-bit signed integer (little-endian)', () => {
      const input = new Uint8Array([255, 255, 255, 255])
      assert.equal(readInt32LE(input), -1)
    })

    it('readUInt32BE should read 32-bit unsigned integer (big-endian)', () => {
      const input = new Uint8Array([0, 0, 1, 0])
      assert.equal(readUInt32BE(input), 256)
    })

    it('readUInt32LE should read 32-bit unsigned integer (little-endian)', () => {
      const input = new Uint8Array([0, 1, 0, 0])
      assert.equal(readUInt32LE(input), 256)
    })
  })

  describe('readUInt', () => {
    it('should read 16-bit unsigned integer with different endianness', () => {
      const input = new Uint8Array([1, 0])
      assert.equal(readUInt(input, 16, 0, true), 256)
      assert.equal(readUInt(input, 16, 0, false), 1)
    })

    it('should read 32-bit unsigned integer with different endianness', () => {
      const input = new Uint8Array([0, 0, 1, 0])
      assert.equal(readUInt(input, 32, 0, true), 256)
      assert.equal(readUInt(input, 32, 0, false), 65536)
    })
  })

  describe('readUInt64', () => {
    it('should read zero correctly in both endianness', () => {
      const input = new Uint8Array([0, 0, 0, 0, 0, 0, 0, 0])
      assert.equal(readUInt64(input, 0, true), 0n)
      assert.equal(readUInt64(input, 0, false), 0n)
    })

    it('should read 2^32 in big-endian', () => {
      const input = new Uint8Array([0, 0, 0, 1, 0, 0, 0, 0])
      assert.equal(readUInt64(input, 0, true), 4294967296n)
    })

    it('should read 2^32 in little-endian', () => {
      const input = new Uint8Array([0, 0, 0, 0, 1, 0, 0, 0])
      assert.equal(readUInt64(input, 0, false), 4294967296n)
    })

    it('should read max uint64 value in both endianness', () => {
      const input = new Uint8Array([255, 255, 255, 255, 255, 255, 255, 255])
      const expected = 18446744073709551615n
      assert.equal(readUInt64(input, 0, true), expected)
      assert.equal(readUInt64(input, 0, false), expected)
    })
  })

  describe('findBox', () => {
    it('should find box by name in Uint8Array', () => {
      const boxSize = new Uint8Array([0, 0, 0, 8])
      const boxName = new Uint8Array([116, 101, 115, 116])
      const input = new Uint8Array([...boxSize, ...boxName])

      const result = findBox(input, 'test', 0)
      assert.deepEqual(result, {
        name: 'test',
        offset: 0,
        size: 8,
      })
    })

    it('should return undefined when box is not found', () => {
      const input = new Uint8Array([0, 0, 0, 8, 116, 101, 115, 116])
      const result = findBox(input, 'none', 0)
      assert.equal(result, undefined)
    })

    it('should handle incomplete box data', () => {
      const input = new Uint8Array([0, 0])
      const result = findBox(input, 'test', 0)
      assert.equal(result, undefined)
    })

    it('should handle box size larger than remaining input', () => {
      const boxSize = new Uint8Array([0, 0, 0, 100])
      const boxName = new Uint8Array([116, 101, 115, 116])
      const input = new Uint8Array([...boxSize, ...boxName])

      const result = findBox(input, 'test', 0)
      assert.equal(result, undefined)
    })
  })
})
