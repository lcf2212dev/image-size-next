import type { IImage, ISize } from './interface'
import { findBox, readUInt32BE, toUTF8String } from './utils'

const brandMap = {
  avif: 'avif',
  mif1: 'heif',
  msf1: 'heif',
  heic: 'heic',
  heix: 'heic',
  hevc: 'heic',
  hevx: 'heic',
}

export const HEIF: IImage = {
  validate(input) {
    const boxType = toUTF8String(input, 4, 8)
    if (boxType !== 'ftyp') return false

    const ftypBox = findBox(input, 'ftyp', 0)
    if (!ftypBox) return false

    const brand = toUTF8String(input, ftypBox.offset + 8, ftypBox.offset + 12)
    return brand in brandMap
  },

  calculate(input) {
    const metaBox = findBox(input, 'meta', 0)
    const iprpBox = metaBox && findBox(input, 'iprp', metaBox.offset + 12)
    const ipcoBox = iprpBox && findBox(input, 'ipco', iprpBox.offset + 8)

    if (!ipcoBox) {
      throw new TypeError('Invalid HEIF, no ipco box found')
    }

    const type = toUTF8String(input, 8, 12)

    const images: ISize[] = []
    let currentOffset = ipcoBox.offset + 8
    const ipcoEnd = ipcoBox.offset + ipcoBox.size

    while (currentOffset < ipcoEnd) {
      const ispeBox = findBox(input, 'ispe', currentOffset)
      if (!ispeBox) break
      if (ispeBox.size < 8) break
      if (ispeBox.offset + ispeBox.size > ipcoEnd) break

      const rawWidth = readUInt32BE(input, ispeBox.offset + 12)
      const rawHeight = readUInt32BE(input, ispeBox.offset + 16)

      const clapBox = findBox(input, 'clap', currentOffset)
      let width = rawWidth
      const height = rawHeight
      if (clapBox && clapBox.offset < ipcoEnd && clapBox.size >= 8) {
        const cropRight = readUInt32BE(input, clapBox.offset + 12)
        width = rawWidth - cropRight
      }

      images.push({ height, width })

      const nextOffset = ispeBox.offset + ispeBox.size
      if (nextOffset <= currentOffset) break
      currentOffset = nextOffset
    }

    if (images.length === 0) {
      throw new TypeError('Invalid HEIF, no sizes found')
    }

    return {
      width: images[0].width,
      height: images[0].height,
      type,
      ...(images.length > 1 ? { images } : {}),
    }
  },
}
