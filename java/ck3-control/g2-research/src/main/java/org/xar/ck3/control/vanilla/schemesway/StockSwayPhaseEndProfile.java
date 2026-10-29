package org.xar.ck3.control.vanilla.schemesway;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Source;

/** Exact authored end/continue tree. This is provenance for planning, never a random roll or terminal classifier. */
public final class StockSwayPhaseEndProfile {
    public static final long SOURCE_BYTES = 424808;
    public static final String SOURCE_SHA256 = "57e30da751f6fd4c4513d6fec3e7aec008ffcf621ca2c79c3aa472197b4d3456";
    private StockSwayPhaseEndProfile() { }
    public enum Branch { THEOCRATIC_LESSEE_OPINION_AT_MOST_50, OPINION_BELOW_MINUS_25,
        OPINION_BELOW_0, OPINION_BELOW_35, OTHERWISE }
    public record EndReference(Branch branch, int percent, int firstLine, int lastLine) {
        public EndReference { Objects.requireNonNull(branch); }
    }
    public record Profile(G2Source source, List<EndReference> orderedAiBranches) {
        public Profile { Objects.requireNonNull(source); orderedAiBranches = List.copyOf(orderedAiBranches); }
        public String namedThreshold() { return "scheme_sway_opinion >= sway_max_value"; }
        public String belowThresholdReset() { return "reset_failed_scheme_effect"; }
        public String factionException() { return "target is owner's vassal AND faction member AND opinion of owner < 100"; }
        public boolean phaseSuccessCanContinueSameInstance() { return true; }
        public boolean namedGainOrTerminalClaimed() { return false; }
        public boolean evaluatesNativeCanContinue() { return false; }
        public boolean changesOrdinaryPolicy() { return false; }
    }
    public static Profile sourceBound(G2Source source) {
        Objects.requireNonNull(source);
        if (!source.exactBuild().equals("1.20.0.4") || source.sourceRef().bytes() != SOURCE_BYTES
                || !source.sourceRef().sha256().equals(SOURCE_SHA256)) {
            throw new IllegalArgumentException("exact .4 whole scheme effects source required");
        }
        return new Profile(source, List.of(
                new EndReference(Branch.THEOCRATIC_LESSEE_OPINION_AT_MOST_50, 10, 15594, 15610),
                new EndReference(Branch.OPINION_BELOW_MINUS_25, 10, 15611, 15626),
                new EndReference(Branch.OPINION_BELOW_0, 30, 15627, 15642),
                new EndReference(Branch.OPINION_BELOW_35, 50, 15643, 15658),
                new EndReference(Branch.OTHERWISE, 100, 15659, 15663)));
    }
}
