package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Independent literal software data; no Native or loaded-state observation. */
public final class GovernmentNormalizeFull174WitnessApi {
    private GovernmentNormalizeFull174WitnessApi() { }
    public record SeedByte(long addressBits, int byteBits) { }
    /** The callback verifies full preCALL bits and selected memory BEFORE applying its explicit mutation/poststate. */
    public record CallStep(OpaqueCall expected, Map<Long,Integer> expectedMemoryBefore,
            List<SeedByte> mutation, VolatileBits normalPost) {
        public CallStep {
            Objects.requireNonNull(expected); Objects.requireNonNull(normalPost);
            expectedMemoryBefore=Map.copyOf(expectedMemoryBefore); mutation=List.copyOf(mutation);
        }
    }
    public record AtomicStep(long addressBits, int addendBits, int oldBits, int storedBits) { }
    /** Final bytes overlay the complete initial seed image, preserving untouched bytes. */
    public record Witness(String name, GovernmentNormalizeFull174Api.Entry entry,
            List<SeedByte> memorySeed, List<CallStep> calls, List<Long> gsQword58,
            List<AtomicStep> atomics, Map<Long,Integer> expectedFinalBytes,
            GovernmentNormalizeFull174Api.NormalReturn expected) {
        public Witness {
            Objects.requireNonNull(name); Objects.requireNonNull(entry); Objects.requireNonNull(expected);
            memorySeed=List.copyOf(memorySeed); calls=List.copyOf(calls); gsQword58=List.copyOf(gsQword58);
            atomics=List.copyOf(atomics); expectedFinalBytes=Map.copyOf(expectedFinalBytes);
        }
    }
    public interface Book { List<Witness> witnesses(); }
}
