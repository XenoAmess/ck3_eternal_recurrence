export const FIT_BUDGET_STRESS_CONTRACT = {
  contract: 'ck3-coa-real-fit-budget-stress-v2',
  performanceReference: 'maintainer-workstation-chromium-production-build',
  budgets: [128, 1_024, 10_000] as const,
  searchResolution: 96,
  maximumDurationMs: {
    128: 900_000,
    1024: 900_000,
    10000: 1_200_000,
  },
  maximumCancellationLatencyMs: 1_000,
  maximumPauseLatencyMs: 1_000,
  maximumResumeDurationMs: 900_000,
  restartProbeBudget: 1,
  maximumRestartProgressLatencyMs: 5_000,
  reportOnlyMaximumDurationMs: 1_200_000,
  maximumMeasuredJsHeapDeltaBytes: 384 * 1024 * 1024,
  memoryEvidenceScope: 'JavaScript heap delta only; excludes GPU and browser-process memory',
} as const
