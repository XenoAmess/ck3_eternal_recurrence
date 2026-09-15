export const FIT_BUDGET_STRESS_CONTRACT = {
  contract: 'ck3-coa-real-fit-budget-stress-v1',
  budgets: [128, 1_024, 10_000] as const,
  searchResolution: 96,
  maximumDurationMs: {
    128: 15_000,
    1024: 45_000,
    10000: 180_000,
  },
  maximumCancellationLatencyMs: 1_000,
  maximumMeasuredJsHeapDeltaBytes: 384 * 1024 * 1024,
  memoryEvidenceScope: 'JavaScript heap delta only; excludes GPU and browser-process memory',
} as const
