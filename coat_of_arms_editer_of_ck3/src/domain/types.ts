export type Severity = 'error' | 'warning' | 'info'

export interface Diagnostic {
  severity: Severity
  message: string
  line?: number
  column?: number
}

export interface CoatOfArmsInstance {
  position: [number, number]
  scale: [number, number]
  rotation: number
  depth: number
}

export interface ColoredEmblem {
  texture: string
  colors: [string, string, string]
  mask: number[]
  instances: CoatOfArmsInstance[]
}

export interface TexturedEmblem {
  texture: string
}

export interface CoatOfArms {
  outerKey: string
  pattern: string
  colors: [string, string, string]
  coloredEmblems: ColoredEmblem[]
  texturedEmblems: TexturedEmblem[]
}

export interface ImportResult {
  coatOfArms: CoatOfArms
  diagnostics: Diagnostic[]
}

export const createInstance = (): CoatOfArmsInstance => ({
  position: [0.5, 0.5],
  scale: [0.7, 0.7],
  rotation: 0,
  depth: 1,
})
export const createColoredEmblem = (): ColoredEmblem => ({
  texture: 'ce_martlet.dds',
  colors: ['yellow', 'red', 'white'],
  mask: [1],
  instances: [createInstance()],
})
export const createTexturedEmblem = (): TexturedEmblem => ({
  texture: '_default.dds',
})

export const createCoatOfArms = (): CoatOfArms => ({
  outerKey: 'coa',
  pattern: 'pattern_solid.dds',
  colors: ['blue', 'white', 'red'],
  coloredEmblems: [createColoredEmblem()],
  texturedEmblems: [],
})
