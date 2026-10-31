package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;

/** New 185-to-Tail protocol data for the existing formal M1 Dispatch194 body. */
public final class GovernmentCrtRegistry195WitnessApi {
    private GovernmentCrtRegistry195WitnessApi() { }
    public record Witness(String name,long imageBaseBits,GovernmentCrtBoundary185Api.Call request,
            Map<Long,Integer> memorySeed,List<GovernmentCrtBoundary185WitnessApi.Event> events,
            Map<Long,Integer> expectedFinalBytes,GovernmentPrimaryTail155Api.VolatileBits expectedVolatileBits) {
        public Witness {
            Objects.requireNonNull(name);Objects.requireNonNull(request);Objects.requireNonNull(expectedVolatileBits);
            memorySeed=Map.copyOf(memorySeed);events=List.copyOf(events);expectedFinalBytes=Map.copyOf(expectedFinalBytes);
        }
    }
    public interface Book { List<Witness> witnesses(); }
}
