package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Objects;

/** Independent whole189 data: original typed whole protocol plus ordered CRT ports. */
public final class GovernmentWholeCrt189WitnessApi {
    private GovernmentWholeCrt189WitnessApi() { }
    public record Witness(GovernmentWholeConcrete173WitnessApi.Witness legacy,
            List<GovernmentCrtBoundary185WitnessApi.Event> crtEvents) {
        public Witness { Objects.requireNonNull(legacy);crtEvents=List.copyOf(crtEvents); }
    }
    public interface Book { List<Witness> witnesses(); }
}
