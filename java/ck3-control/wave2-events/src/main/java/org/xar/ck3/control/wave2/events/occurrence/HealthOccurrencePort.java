package org.xar.ck3.control.wave2.events.occurrence;

import java.math.BigInteger;
import java.util.Map;
import java.util.Objects;

/** The actual health.1015 occurrence gate, not a complete event recommendation. */
public final class HealthOccurrencePort {
    private HealthOccurrencePort() { }
    public record ReviewedSources(String healthEventsSha256, String healthEffectsSha256) { }
    public record Assessment(EventOccurrence.Result occurrence, Map<String, Boolean> checks) {
        public Assessment {
            Objects.requireNonNull(occurrence, "occurrence");
            checks = Map.copyOf(checks);
        }
        public boolean occurrenceBoundReady() { return checks.values().stream().allMatch(Boolean::booleanValue); }
        public boolean actionAuthorized() { return false; }
    }
    public static Assessment assess(EventOccurrence.Result occurrence, BigInteger playedCharacterId,
                                    BigInteger maximumOccurrences, ReviewedSources actualRegistrySources) {
        Objects.requireNonNull(occurrence, "occurrence");
        Objects.requireNonNull(playedCharacterId, "playedCharacterId");
        boolean source = actualRegistrySources != null
            && "74073E049A416C744B36A2A996FA467610705E38D53C836B050F1AC6F66E1212".equals(actualRegistrySources.healthEventsSha256())
            && "ABEFA738C913C660A52FA747BCC92FCA2F57D77A0F47D903BEDC2882F3D5A9DB".equals(actualRegistrySources.healthEffectsSha256());
        boolean history = occurrence.status() == EventOccurrence.Status.AVAILABLE
            && "health.1015".equals(occurrence.eventDefinitionKey()) && playedCharacterId.equals(occurrence.playedCharacterId());
        boolean within = maximumOccurrences != null && maximumOccurrences.signum() > 0 && history
            && BigInteger.valueOf(occurrence.count().longValue()).compareTo(maximumOccurrences) < 0;
        return new Assessment(occurrence, Map.of("health1015_exact_source", source,
            "occurrence_history_ready", history, "max_occurrences", within));
    }
}
