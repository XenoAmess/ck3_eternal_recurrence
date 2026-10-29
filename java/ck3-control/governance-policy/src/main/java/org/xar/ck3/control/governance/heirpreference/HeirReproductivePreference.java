package org.xar.ck3.control.governance.heirpreference;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Orders existing positive choices; it grants neither eligibility nor a forecast. */
public final class HeirReproductivePreference {
    public static final String BASIS = "native_reproductive_branch_preference_v1";

    private HeirReproductivePreference() { }

    /** Historical leaf IDs are exact positive Python integers, never doubles. */
    public record CandidateId(BigInteger value) {
        public CandidateId {
            Objects.requireNonNull(value, "candidate ID");
            if (value.signum() <= 0) {
                throw new IllegalArgumentException("candidate ID must be positive");
            }
        }
    }

    public enum ObservedComparison { UNAVAILABLE, PASS, FAIL }

    public enum PreferenceClass {
        OBSERVED_PASS(0, "observed_pass"),
        PARTIAL_OR_ABSENT(1, "partial_or_absent"),
        OBSERVED_FAIL(2, "observed_fail");

        private final int order;
        private final String wireStatus;

        PreferenceClass(int order, String wireStatus) {
            this.order = order;
            this.wireStatus = wireStatus;
        }

        public int order() { return order; }
        public String wireStatus() { return wireStatus; }
    }

    public record ComparisonRow(CandidateId candidateId, ObservedComparison floor,
                                ObservedComparison age) {
        public ComparisonRow {
            Objects.requireNonNull(candidateId, "candidate ID");
            Objects.requireNonNull(floor, "observed floor");
            Objects.requireNonNull(age, "observed age");
        }
    }

    /** Original ordinal keeps distinct opaque choices, including a repeated ID. */
    public record PreferredChoice(int originalOrdinal, CandidateId candidateId,
                                  PreferenceClass preferenceClass, boolean ageConsidered) {
        public PreferredChoice {
            if (originalOrdinal < 0) {
                throw new IllegalArgumentException("negative original ordinal");
            }
            Objects.requireNonNull(candidateId, "candidate ID");
            Objects.requireNonNull(preferenceClass, "preference class");
        }
    }

    public static List<PreferredChoice> prioritize(List<CandidateId> choices,
                                                   List<ComparisonRow> rows) {
        List<CandidateId> orderedInput = List.copyOf(choices);
        Map<CandidateId, ComparisonRow> byId = new HashMap<>();
        for (ComparisonRow row : List.copyOf(rows)) {
            // Match the old producer's comprehension: the final row wins.
            byId.put(row.candidateId(), row);
        }
        List<PreferredChoice> result = new ArrayList<>(orderedInput.size());
        for (int ordinal = 0; ordinal < orderedInput.size(); ordinal++) {
            CandidateId candidate = orderedInput.get(ordinal);
            ComparisonRow row = byId.get(candidate);
            ObservedComparison floor = row == null ? ObservedComparison.UNAVAILABLE : row.floor();
            ObservedComparison age = row == null ? ObservedComparison.UNAVAILABLE : row.age();
            boolean ageConsidered = floor == ObservedComparison.PASS;
            PreferenceClass preference = PreferenceClass.PARTIAL_OR_ABSENT;
            if (floor == ObservedComparison.FAIL) {
                preference = PreferenceClass.OBSERVED_FAIL;
            } else if (ageConsidered && age != ObservedComparison.UNAVAILABLE) {
                preference = age == ObservedComparison.PASS
                        ? PreferenceClass.OBSERVED_PASS : PreferenceClass.OBSERVED_FAIL;
            }
            result.add(new PreferredChoice(ordinal, candidate, preference, ageConsidered));
        }
        // List.sort is stable; every original positive choice remains available.
        result.sort(Comparator.comparingInt(choice -> choice.preferenceClass().order()));
        return List.copyOf(result);
    }
}
