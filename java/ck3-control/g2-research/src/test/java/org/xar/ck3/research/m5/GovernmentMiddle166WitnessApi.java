package org.xar.ck3.research.m5;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
/** Frozen independent new-input protocol. Every missing byte fails; no native availability. */
public final class GovernmentMiddle166WitnessApi {
    private GovernmentMiddle166WitnessApi() { }
    public record BoundaryStep(GovernmentPrimarySuffix155Api.Entry expectedEntry,
            GovernmentCaller153Api.Outcome expectedOutcome,long expectedPostPrefixR14Bits,
            GovernmentPrimarySuffix155Api.VolatileObservation observation) {
        public BoundaryStep {Objects.requireNonNull(expectedEntry);Objects.requireNonNull(expectedOutcome);Objects.requireNonNull(observation);}
    }
    /** A null expectedResult means an explicit unsupported path, not a normal result. */
    public record Witness(String name,GovernmentCompaction160Api.Entry entry,MemorySeed memorySeed,
            long gs58Bits,List<CallStep> calls,List<BoundaryStep> boundaries,
            long compactionIterationLimit,long tailIterationLimit,
            Map<Long,Integer> expectedFinalBytes,GovernmentMiddle166Api.Result expectedResult,
            String expectedFailureSubstring) {
        public Witness {Objects.requireNonNull(name);Objects.requireNonNull(entry);Objects.requireNonNull(memorySeed);
            calls=List.copyOf(calls);boundaries=List.copyOf(boundaries);expectedFinalBytes=Map.copyOf(expectedFinalBytes);
            if((expectedResult==null)==(expectedFailureSubstring==null))throw new IllegalArgumentException("one normal or unsupported oracle required");}
    }
    public interface WitnessBook {List<Witness> witnesses();}
}
