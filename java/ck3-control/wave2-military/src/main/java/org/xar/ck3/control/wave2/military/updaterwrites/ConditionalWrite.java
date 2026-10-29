package org.xar.ck3.control.wave2.military.updaterwrites;

/** Proposed source writes, never a native submission or observed effect. */
public sealed interface ConditionalWrite permits ConditionalWrite.Byte22Write, ConditionalWrite.Date188Write {
    record Byte22Write(boolean writeReady, Boolean wouldWrite, Long observedValue, Integer conditionalValue)
            implements ConditionalWrite {}
    record Date188Write(boolean writeReady, boolean writePredicateReady, Boolean wouldWrite,
                        boolean afterValueReady, Long observedValue, Long conditionalValue,
                        ValueOrigin valueOrigin) implements ConditionalWrite {}
    enum ValueOrigin { SOURCE_DERIVED_NEXT_FULL_CDATE64, OBSERVED_CURRENT_188_RETAINED }
}
