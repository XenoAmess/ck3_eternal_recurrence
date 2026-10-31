package org.xar.ck3.research.m4;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;

/** Literal data derives from held61B/public APIs; the owner had reviewed production without executing it for expected data. */
public final class Free61FullState201WitnessApi {
    private Free61FullState201WitnessApi() { }
    public record Witness(String name, Entry entry, Map<Long, Integer> memorySeed,
            List<CallStep> events, Map<Long, Integer> expectedFinalBytes, NormalReturn expected) {
        public Witness {
            Objects.requireNonNull(name); Objects.requireNonNull(entry); Objects.requireNonNull(expected);
            memorySeed = Map.copyOf(memorySeed); events = List.copyOf(events);
            expectedFinalBytes = Map.copyOf(expectedFinalBytes);
        }
    }
    public interface Book { List<Witness> witnesses(); }
}
