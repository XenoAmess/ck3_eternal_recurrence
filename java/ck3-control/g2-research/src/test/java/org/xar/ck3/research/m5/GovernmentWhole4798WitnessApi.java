package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;

/** Independent literal whole-caller inputs; no subject-derived oracle or Native FP assertion. */
public final class GovernmentWhole4798WitnessApi {
    private GovernmentWhole4798WitnessApi() { }
    public record OrdinaryStep(GovernmentPrimaryTail155Api.OpaqueCall expected,
            Map<Long,Integer> expectedMemoryBytes,List<SeedByte> mutation,
            GovernmentPrimaryTail155Api.VolatileBits normalPost,boolean unsupported) {
        public OrdinaryStep { Objects.requireNonNull(expected);expectedMemoryBytes=Map.copyOf(expectedMemoryBytes);
            mutation=List.copyOf(mutation);if(!unsupported)Objects.requireNonNull(normalPost); }
    }
    public enum Phase { INITIAL,LOOKUP,EARLIER,ROWS,COMPACTION,TAIL }
    /** Exactly visited owned budget event; fields retain the distinct original port semantics. */
    public record BudgetStep(Phase phase,long headerRva,long cursorOrCapacityBits,
            long endSlotOrFixedEndOrSignedLimitBits,boolean reject) { }
    public record InitialMxcsrStep(GovernmentInitialFrame162Api.Join expectedJoin,
            GovernmentWhole4798Api.MxcsrObservation observation) {
        public InitialMxcsrStep { Objects.requireNonNull(expectedJoin);Objects.requireNonNull(observation); }
    }
    public record FinalMxcsrStep(GovernmentMiddle166Api.Result expectedResult,
            GovernmentWhole4798Api.MxcsrObservation observation) {
        public FinalMxcsrStep { Objects.requireNonNull(expectedResult);Objects.requireNonNull(observation); }
    }
    public enum Failure { NONE,INITIAL_MXCSR_UNAVAILABLE,BUDGET,CPU_UNSUPPORTED,CALL_UNSUPPORTED,POST153_UNAVAILABLE }
    public record Witness(String name,GovernmentInitialFrame162Api.Entry entry,MemorySeed memorySeed,long gs58Bits,
            List<OrdinaryStep> initialCalls,List<OrdinaryStep> ordinaryCalls,
            List<GovernmentLookupLoop580WitnessApi.CallExpectation> lookupCalls,
            List<GovernmentLookupLoop580WitnessApi.CpuExpectation> cpuCalls,List<BudgetStep> budgets,
            InitialMxcsrStep afterInitial,FinalMxcsrStep afterFinal,
            List<GovernmentMiddle166WitnessApi.BoundaryStep> post153,
            Map<Long,Integer> expectedFinalBytes,GovernmentWhole4798Api.Result expectedResult,Failure failure) {
        public Witness { Objects.requireNonNull(name);Objects.requireNonNull(entry);Objects.requireNonNull(memorySeed);
            initialCalls=List.copyOf(initialCalls);ordinaryCalls=List.copyOf(ordinaryCalls);
            lookupCalls=List.copyOf(lookupCalls);cpuCalls=List.copyOf(cpuCalls);budgets=List.copyOf(budgets);
            post153=List.copyOf(post153);expectedFinalBytes=Map.copyOf(expectedFinalBytes);Objects.requireNonNull(failure);
            if((failure==Failure.NONE)!=(expectedResult!=null))throw new IllegalArgumentException("one normal or explicit owned rejection"); }
    }
    public interface Book { List<Witness> witnesses(); }
}
