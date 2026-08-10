import { detector } from './detector'
import type { imageType } from './types/index'
import { typeHandlers } from './types/index'
import type { ISizeCalculationResult } from './types/interface'

type Options = {
  disabledTypes: imageType[]
}

const globalOptions: Options = {
  disabledTypes: [],
}

export function imageSize(input: Uint8Array): ISizeCalculationResult {
  const type = detector(input)

  if (typeof type !== 'undefined') {
    if (globalOptions.disabledTypes.indexOf(type) > -1) {
      throw new TypeError(`disabled file type: ${type}`)
    }

    const handler = typeHandlers.get(type)
    const size = handler?.calculate(input)
    if (size !== undefined) {
      size.type = size.type ?? type

      if (size.images && size.images.length > 1) {
        const largestImage = size.images.reduce((largest, current) => {
          return current.width * current.height > largest.width * largest.height
            ? current
            : largest
        }, size.images[0])

        size.width = largestImage.width
        size.height = largestImage.height
      }

      return size
    }
  }

  throw new TypeError(`unsupported file type: ${type}`)
}

export const disableTypes = (types: imageType[]): void => {
  globalOptions.disabledTypes = types
}
