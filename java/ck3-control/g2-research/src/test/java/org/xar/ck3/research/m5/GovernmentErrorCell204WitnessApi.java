package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;

/** Independent owned-Java fullstate and normal-call protocol data. */
public final class GovernmentErrorCell204WitnessApi {
    private GovernmentErrorCell204WitnessApi() { }
    public enum Dispatch { DIRECT, BOUND_CALL }
    public record Witness(String name, Dispatch dispatch, Entry entry, long callerSiteRva,
            Map<Long,Integer> memorySeed, List<Event> events,
            Map<Long,Integer> expectedFinalBytes, NormalReturn expectedReturn) {
        public Witness {
            memorySeed=Map.copyOf(memorySeed);
            events=List.copyOf(events);
            expectedFinalBytes=Map.copyOf(expectedFinalBytes);
        }
    }
    public interface Book { List<Witness> witnesses(); }
}
