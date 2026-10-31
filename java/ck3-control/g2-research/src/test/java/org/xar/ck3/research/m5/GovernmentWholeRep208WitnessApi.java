package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Objects;

/** Owned direction flag and whole admission are explicit, separate from normal result data. */
public final class GovernmentWholeRep208WitnessApi {
    private GovernmentWholeRep208WitnessApi() { }
    public enum ExpectedAdmission { NORMAL, DF_SET_UNSUPPORTED }
    public record Witness(String name,GovernmentWholeCrt189WitnessApi.Witness context,
            boolean ownedDirectionFlagSet,ExpectedAdmission expectedAdmission) {
        public Witness {
            Objects.requireNonNull(name);Objects.requireNonNull(context);Objects.requireNonNull(expectedAdmission);
        }
    }
    public interface Book { List<Witness> witnesses(); }
}
