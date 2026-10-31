package org.xar.ck3.research.m5;

/** Raw owned-memory boundary for two exactly compared complete RFs. No Game object type. */
public final class GovernmentResult168Api {
    private GovernmentResult168Api() { }
    /** Only the two held code instances; distinct fallback slots remain distinct. */
    public enum Instance {
        RESULT_16F40A0(0x16F40A0L, 0x5D213E8L),
        RESULT_ABF7E0(0xABF7E0L, 0x5D1E2A8L);
        private final long entryRva;
        private final long fallbackSlotRva;
        Instance(long entryRva, long fallbackSlotRva) {
            this.entryRva=entryRva; this.fallbackSlotRva=fallbackSlotRva;
        }
        public long entryRva() { return entryRva; }
        public long fallbackSlotRva() { return fallbackSlotRva; }
    }
    @FunctionalInterface public interface WorkBudget {
        /**
         * Before each actual reachable loop-header entry: entry+0x80 rollback XADD,
         * entry+0x90 lock poll, or entry+0xD8 bucket key comparison.
         * addressBits is respectively the lock address or current bucket address.
         * May throw UnsupportedOperationException; all prior writes remain and no
         * normal return, rollback, automatic unlock or invented poststate follows.
         */
        void beforeStep(long instructionRva, long addressBits);
    }
}
