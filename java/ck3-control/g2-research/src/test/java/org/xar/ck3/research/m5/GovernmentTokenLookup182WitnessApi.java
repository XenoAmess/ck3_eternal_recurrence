package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Independent literal software data; no Native or loaded-state observation. */
public final class GovernmentTokenLookup182WitnessApi {
    private GovernmentTokenLookup182WitnessApi() { }

    public record SeedByte(long addressBits, int byteBits) { }

    public sealed interface Event permits AtomicStep, LoopStep, PauseStep, GsStep, CallStep { }

    public record AtomicStep(long addressBits, int addendBits, int oldBits, int storedBits) implements Event { }

    public record LoopStep(long headerRva, long lockAddressBits) implements Event { }

    public record PauseStep(long pauseRva, List<SeedByte> mutation) implements Event {
        public PauseStep { mutation = List.copyOf(mutation); }
    }

    public record GsStep(long returnedBits) implements Event { }

    public record CallStep(OpaqueCall expected, Map<Long, Integer> expectedMemoryBefore, List<SeedByte> mutation, VolatileBits normalPost) implements Event {
        public CallStep {
            Objects.requireNonNull(expected);
            Objects.requireNonNull(normalPost);
            expectedMemoryBefore = Map.copyOf(expectedMemoryBefore);
            mutation = List.copyOf(mutation);
        }
    }

    public record Witness(String name, GovernmentTokenLookup182Api.Entry entry, List<SeedByte> memorySeed, List<Event> events, Map<Long, Integer> expectedFinalBytes, GovernmentTokenLookup182Api.NormalReturn expected) {
        public Witness {
            Objects.requireNonNull(name);
            Objects.requireNonNull(entry);
            Objects.requireNonNull(expected);
            memorySeed = List.copyOf(memorySeed);
            events = List.copyOf(events);
            expectedFinalBytes = Map.copyOf(expectedFinalBytes);
        }
    }

    public interface Book { List<Witness> witnesses(); }
}
