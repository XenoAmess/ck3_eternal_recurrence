package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Independent, source-derived data only. No subject implementation is consulted. */
public final class GovernmentCrtCallee186WitnessApi {
    private GovernmentCrtCallee186WitnessApi() {}

    public enum Subject { CALLEE, CALLER_3F24 }

    /** A single cursor observes complete bytes after the owned CALL push. */
    public record CallStep(Call expected, Map<Long, Integer> expectedMemoryBefore,
                           Map<Long, Integer> mutation, VolatileBits normalPost) {
        public CallStep {
            Objects.requireNonNull(expected);
            Objects.requireNonNull(normalPost);
            expectedMemoryBefore = Map.copyOf(expectedMemoryBefore);
            mutation = Map.copyOf(mutation);
        }
    }

    /** All byte values are unsigned 0..255; missing memory is unknown, never zero. */
    public record Witness(String name, Subject subject, Entry entry,
                          Map<Long, Integer> memorySeed, List<CallStep> events,
                          Map<Long, Integer> expectedFinalBytes, NormalReturn expected) {
        public Witness {
            Objects.requireNonNull(name);
            Objects.requireNonNull(subject);
            Objects.requireNonNull(entry);
            Objects.requireNonNull(expected);
            memorySeed = Map.copyOf(memorySeed);
            events = List.copyOf(events);
            expectedFinalBytes = Map.copyOf(expectedFinalBytes);
        }
    }

    public interface Book { List<Witness> witnesses(); }
}
