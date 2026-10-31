package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;

/** New 185-port bridge data for formally reused M1 Notify181 and Wait179. */
public final class GovernmentCrtNative192WitnessApi {
    private GovernmentCrtNative192WitnessApi() { }
    public enum Kind { NOTIFY_TAIL, WAIT_CALL }
    public record Witness(String name,Kind kind,GovernmentCrtBoundary185Api.Entry entry,
            Map<Long,Integer> memorySeed,List<GovernmentCrtBoundary185WitnessApi.Event> events,
            Map<Long,Integer> expectedFinalBytes,GovernmentCrtBoundary185Api.NormalReturn expected) {
        public Witness {
            Objects.requireNonNull(name);Objects.requireNonNull(kind);Objects.requireNonNull(entry);Objects.requireNonNull(expected);
            memorySeed=Map.copyOf(memorySeed);events=List.copyOf(events);expectedFinalBytes=Map.copyOf(expectedFinalBytes);
        }
    }
    public interface Book { List<Witness> witnesses(); }
}
