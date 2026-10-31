package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Independent literal software data; no original Native execution or loaded-state observation. */
public final class GovernmentRoot178WitnessApi {
    private GovernmentRoot178WitnessApi() { }
    public record SeedByte(long addressBits,int byteBits) { }
    public record CallStep(OpaqueCall expected,Map<Long,Integer> expectedMemoryBefore,
            List<SeedByte> mutation,VolatileBits normalPost) {
        public CallStep {
            Objects.requireNonNull(expected);Objects.requireNonNull(normalPost);
            expectedMemoryBefore=Map.copyOf(expectedMemoryBefore);mutation=List.copyOf(mutation);
        }
    }
    public record AtomicStep(long addressBits,int addendBits,int oldBits,int storedBits) { }
    public record Witness(String name,GovernmentRoot178Api.Entry entry,List<SeedByte> memorySeed,
            List<CallStep> calls,List<Long> gsQword58,List<AtomicStep> atomics,
            Map<Long,Integer> expectedFinalBytes,GovernmentRoot178Api.NormalReturn expected) {
        public Witness {
            Objects.requireNonNull(name);Objects.requireNonNull(entry);Objects.requireNonNull(expected);
            memorySeed=List.copyOf(memorySeed);calls=List.copyOf(calls);gsQword58=List.copyOf(gsQword58);
            atomics=List.copyOf(atomics);expectedFinalBytes=Map.copyOf(expectedFinalBytes);
        }
    }
    public interface Book { List<Witness> witnesses(); }
}
