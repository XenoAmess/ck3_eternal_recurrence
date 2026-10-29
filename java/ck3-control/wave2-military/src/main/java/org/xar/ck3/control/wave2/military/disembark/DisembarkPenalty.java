package org.xar.ck3.control.wave2.military.disembark;

import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.math.BigInteger;

/** Current native getter observation only: no clamp, sentinel, active or expiry inference. */
public final class DisembarkPenalty {
    public static final String LEAF = "current_disembark_penalty_v1";
    public static final String SOURCE = "native_current_disembark_penalty_days_12003";
    public static final String PROJECTION_SOURCE = "source_bound_current_disembark_penalty_days_12003";
    public static final String NOT_PUBLISHED = "current_disembark_penalty_not_published";
    private static final String SHA_3 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    private static final String SHA_4 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

    private DisembarkPenalty() { }

    public sealed interface Observation permits Available, Unavailable { }

    /** All signed int32 values, including negative values, are genuine observations. */
    public record Available(int remainingDays) implements Observation { }

    public record Unavailable(String reason) implements Observation {
        public Unavailable {
            if (reason == null || reason.isEmpty()) { throw new IllegalArgumentException("nonempty unavailable reason required"); }
        }
    }

    /** The legacy producer preserves this extensible evidence object, including null/missing. */
    public record SourceProvenance(EvidenceJson.ObjectValue document) {
        public SourceProvenance {
            Objects.requireNonNull(document, "source provenance");
            for (String key : new String[]{"snapshot_id", "game_version", "executable_sha256"}) {
                EvidenceJson.Value value = document.member(key).orElse(EvidenceJson.NullValue.INSTANCE);
                if (value != EvidenceJson.NullValue.INSTANCE && !(value instanceof EvidenceJson.TextValue)) {
                    throw new IllegalArgumentException("declared source string/null required: " + key);
                }
            }
            // The original pure provenance boundary has no revision-width limit; retain exact integers rather than borrowing Map's limit.
            for (String key : new String[]{"revision", "native_revision", "date_raw"}) {
                EvidenceJson.Value value = document.member(key).orElse(EvidenceJson.NullValue.INSTANCE);
                if (value != EvidenceJson.NullValue.INSTANCE && !(value instanceof EvidenceJson.IntegerValue)) {
                    throw new IllegalArgumentException("declared source integer/null required: " + key);
                }
            }
            EvidenceJson.Value date = document.member("date_raw").orElse(EvidenceJson.NullValue.INSTANCE);
            if (date instanceof EvidenceJson.IntegerValue integer
                    && (integer.value().compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) < 0
                    || integer.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0)) {
                throw new IllegalArgumentException("declared source CDate raw must be signed int32");
            }
        }

        public void requireObservedBuild() {
            String version = stringMember("game_version");
            String sha = stringMember("executable_sha256").toUpperCase(Locale.ROOT);
            if (!(version.equals("1.20.0.3") && sha.equals(SHA_3))
                    && !(version.equals("1.20.0.4") && sha.equals(SHA_4))) {
                throw new IllegalArgumentException("current landing input requires its exact .3/.4 source");
            }
        }

        private String stringMember(String key) {
            EvidenceJson.Value value = document.member(key).orElse(EvidenceJson.NullValue.INSTANCE);
            if (value instanceof EvidenceJson.TextValue text) { return text.value(); }
            throw new IllegalArgumentException("exact native source string required: " + key);
        }
    }

    /** Empty observed is old-wire omission; Unavailable is a published native leaf. */
    public record Projection(Optional<Observation> observed, SourceProvenance sourceProvenance) {
        public Projection {
            Objects.requireNonNull(observed, "explicit observation presence");
            Objects.requireNonNull(sourceProvenance, "source provenance");
            if (observed.isPresent()) { sourceProvenance.requireObservedBuild(); }
        }
        public boolean currentDaysReady() { return observed.orElse(null) instanceof Available; }
        public Optional<Integer> remainingDays() {
            return observed.filter(Available.class::isInstance).map(Available.class::cast).map(Available::remainingDays);
        }
        public Optional<String> unavailableReason() {
            if (observed.isEmpty()) { return Optional.of(NOT_PUBLISHED); }
            return observed.filter(Unavailable.class::isInstance).map(Unavailable.class::cast).map(Unavailable::reason);
        }
    }

    public static Projection project(Optional<Observation> observed, SourceProvenance sourceProvenance) {
        return new Projection(observed, sourceProvenance);
    }
}
