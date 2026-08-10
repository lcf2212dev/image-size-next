import type { IImage, ISize } from './interface'
import { readUInt32BE, toUTF8String } from './utils'

const SIZE_HEADER = 8
const FILE_LENGTH_OFFSET = 4
const ENTRY_LENGTH_OFFSET = 4
const MIN_ENTRY_LENGTH = 8

const ICON_TYPE_SIZE: Record<string, number> = {
  ICON: 32,
  'ICN#': 32,
  'icm#': 16,
  icm4: 16,
  icm8: 16,
  'ics#': 16,
  ics4: 16,
  ics8: 16,
  is32: 16,
  s8mk: 16,
  icp4: 16,
  icl4: 32,
  icl8: 32,
  il32: 32,
  l8mk: 32,
  icp5: 32,
  ic11: 32,
  ich4: 48,
  ich8: 48,
  ih32: 48,
  h8mk: 48,
  icp6: 64,
  ic12: 32,
  it32: 128,
  t8mk: 128,
  ic07: 128,
  ic08: 256,
  ic13: 256,
  ic09: 512,
  ic14: 512,
  ic10: 1024,
}

function readImageHeader(
  input: Uint8Array,
  imageOffset: number,
): [string, number] {
  const imageLengthOffset = imageOffset + ENTRY_LENGTH_OFFSET
  return [
    toUTF8String(input, imageOffset, imageLengthOffset),
    readUInt32BE(input, imageLengthOffset),
  ]
}

function getImageSize(type: string): ISize {
  const size = ICON_TYPE_SIZE[type]
  return { width: size, height: size, type }
}

export const ICNS: IImage = {
  validate: (input) => toUTF8String(input, 0, 4) === 'icns',

  calculate(input) {
    const inputLength = input.length
    const fileLength = readUInt32BE(input, FILE_LENGTH_OFFSET)
    let imageOffset = SIZE_HEADER

    const images: ISize[] = []

    while (imageOffset < fileLength && imageOffset < inputLength) {
      if (inputLength - imageOffset < MIN_ENTRY_LENGTH) break

      const imageHeader = readImageHeader(input, imageOffset)
      const entryLength = imageHeader[1]
      if (entryLength < MIN_ENTRY_LENGTH) break

      const imageSize = getImageSize(imageHeader[0])
      if (imageSize.width && imageSize.height) {
        images.push(imageSize)
      }

      const nextOffset = imageOffset + entryLength
      if (nextOffset <= imageOffset) break
      imageOffset = nextOffset
    }

    if (images.length === 0) {
      throw new TypeError('Invalid ICNS, no sizes found')
    }

    return {
      width: images[0].width,
      height: images[0].height,
      ...(images.length > 1 ? { images } : {}),
    }
  },
}
