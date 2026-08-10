import type { IImage, ISize } from './interface'
import { readUInt16LE } from './utils'

const TYPE_ICON = 1
const SIZE_HEADER = 6
const SIZE_IMAGE_ENTRY = 16

function getSizeFromOffset(input: Uint8Array, offset: number): number {
  const value = input[offset]
  return value === 0 ? 256 : value
}

function getImageSize(input: Uint8Array, imageIndex: number): ISize {
  const offset = SIZE_HEADER + imageIndex * SIZE_IMAGE_ENTRY
  return {
    height: getSizeFromOffset(input, offset + 1),
    width: getSizeFromOffset(input, offset),
  }
}

export const ICO: IImage = {
  validate(input) {
    const reserved = readUInt16LE(input, 0)
    const imageCount = readUInt16LE(input, 4)
    if (reserved !== 0 || imageCount === 0) return false

    const imageType = readUInt16LE(input, 2)
    return imageType === TYPE_ICON
  },

  calculate(input) {
    const nbImages = readUInt16LE(input, 4)
    const imageSize = getImageSize(input, 0)

    if (nbImages === 1) return imageSize

    const images: ISize[] = []
    for (let imageIndex = 0; imageIndex < nbImages; imageIndex += 1) {
      images.push(getImageSize(input, imageIndex))
    }

    return {
      width: imageSize.width,
      height: imageSize.height,
      images: images,
    }
  },
}
