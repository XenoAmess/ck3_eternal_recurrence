package org.xar.ck3.control.planning.optionalcadence;

import java.math.BigInteger;
import java.util.Collections;
import java.util.EnumMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/** Immutable domain values for the existing six-domain cadence wire contract. */
public final class CadenceModels {
    public static final String SCHEMA = "xar.optional-check-cadence.v1";
    public static final BigInteger RAW_PER_DAY = BigInteger.valueOf(24);
    public static final BigInteger COOLDOWN_RAW = BigInteger.valueOf(720);

    private CadenceModels() { }

    public enum Domain {
        RANSOM("ransom"), COUNCIL("council"), LIFESTYLE("lifestyle"),
        CONSTRUCTION("construction"), CROWN("crown"), FEAST("feast");

        private final String wire;
        Domain(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Domain fromWire(String value) {
            for (Domain domain : values()) {
                if (domain.wire.equals(value)) { return domain; }
            }
            throw new IllegalArgumentException("unknown optional check domain");
        }
    }

    public record Marker(BigInteger dateRaw, BigInteger nativeRevision) {
        public Marker {
            nonnegative(dateRaw, "date_raw");
            nonnegative(nativeRevision, "native_revision");
        }
    }

    /** This marker does not grant native freshness or source qualification. */
    public record Frame(String episodeRunId, Marker marker) {
        public Frame {
            nonempty(episodeRunId, "episode_run_id");
            Objects.requireNonNull(marker, "marker");
        }
        public Frame(String episodeRunId, BigInteger dateRaw, BigInteger nativeRevision) {
            this(episodeRunId, new Marker(dateRaw, nativeRevision));
        }
        public BigInteger dateRaw() { return marker.dateRaw(); }
        public BigInteger nativeRevision() { return marker.nativeRevision(); }
    }

    public record TechnicalDefer(Marker frame, String evidencePath) {
        public TechnicalDefer {
            Objects.requireNonNull(frame, "frame");
            nonempty(evidencePath, "evidence_path");
        }
    }

    public record Row(int consecutiveNoAction, Optional<BigInteger> nextDueDateRaw,
                      Optional<Marker> lastCheckFrame, Optional<Marker> lastActualActionFrame,
                      Optional<String> nativeCatalogue, Optional<TechnicalDefer> technicalDefer) {
        public Row {
            if (consecutiveNoAction < 0 || consecutiveNoAction > 2) {
                throw new IllegalArgumentException("consecutive_no_action must be 0..2");
            }
            Objects.requireNonNull(nextDueDateRaw, "nextDueDateRaw");
            Objects.requireNonNull(lastCheckFrame, "lastCheckFrame");
            Objects.requireNonNull(lastActualActionFrame, "lastActualActionFrame");
            Objects.requireNonNull(nativeCatalogue, "nativeCatalogue");
            Objects.requireNonNull(technicalDefer, "technicalDefer");
            nativeCatalogue.ifPresent(value -> nonempty(value, "native_catalogue"));
            if (technicalDefer.isPresent() && nextDueDateRaw.isEmpty()) {
                throw new IllegalArgumentException("technical_defer requires next_due_date_raw");
            }
            if (technicalDefer.isPresent()) {
                TechnicalDefer technical = technicalDefer.orElseThrow();
                if (!lastCheckFrame.filter(technical.frame()::equals).isPresent()
                        || nextDueDateRaw.orElseThrow().compareTo(technical.frame().dateRaw()) <= 0) {
                    throw new IllegalArgumentException("technical_defer must match its checked frame and future due date");
                }
            }
        }
        public static Row empty() {
            return new Row(0, Optional.empty(), Optional.empty(), Optional.empty(),
                    Optional.empty(), Optional.empty());
        }
    }

    public record State(String episodeRunId, Map<Domain, Row> domains) {
        public State {
            nonempty(episodeRunId, "episode_run_id");
            Objects.requireNonNull(domains, "domains");
            if (domains.size() != Domain.values().length) {
                throw new IllegalArgumentException("all six optional domains are required");
            }
            EnumMap<Domain, Row> copy = new EnumMap<>(Domain.class);
            for (Domain domain : Domain.values()) {
                copy.put(domain, Objects.requireNonNull(domains.get(domain), domain.wire()));
            }
            domains = Collections.unmodifiableMap(copy);
        }
        public Row row(Domain domain) { return domains.get(Objects.requireNonNull(domain, "domain")); }
        public State with(Domain domain, Row row) {
            EnumMap<Domain, Row> copy = new EnumMap<>(domains);
            copy.put(Objects.requireNonNull(domain, "domain"), Objects.requireNonNull(row, "row"));
            return new State(episodeRunId, copy);
        }
        public static State empty(String episodeRunId) {
            EnumMap<Domain, Row> rows = new EnumMap<>(Domain.class);
            for (Domain domain : Domain.values()) { rows.put(domain, Row.empty()); }
            return new State(episodeRunId, rows);
        }
    }

    public enum DeferStatus {
        COOLDOWN("cooldown_after_three_no_action_checks"),
        TECHNICAL_READ_UNAVAILABLE("technical_read_unavailable_deferred");
        private final String wire;
        DeferStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Deferred(DeferStatus status, int consecutiveNoAction, BigInteger nextDueDateRaw,
                           Optional<TechnicalDefer> technicalDefer, BigInteger remainingGameDays) {
        public Deferred {
            Objects.requireNonNull(status, "status");
            Objects.requireNonNull(nextDueDateRaw, "nextDueDateRaw");
            Objects.requireNonNull(technicalDefer, "technicalDefer");
            nonnegative(remainingGameDays, "remaining_game_days");
            if (consecutiveNoAction < 0 || consecutiveNoAction > 2
                    || (status == DeferStatus.TECHNICAL_READ_UNAVAILABLE) != technicalDefer.isPresent()
                    || (status == DeferStatus.COOLDOWN && consecutiveNoAction != 0)) {
                throw new IllegalArgumentException("inconsistent deferred branch");
            }
        }
    }

    /** Pending and unknown action states must retain their original receipt route. */
    public enum PendingState { ABSENT, PENDING, UNKNOWN }
    public enum ReadCompletion { COMPLETE_NO_ACTION, INCOMPLETE_OR_UNKNOWN }
    public enum CheckReason { DUE, FRAME_UNAVAILABLE, PENDING_RECEIPT, UNKNOWN_RECEIPT }
    public sealed interface ReviewGate permits CheckRequired, CheckDeferred { }
    public record CheckRequired(CheckReason reason) implements ReviewGate {
        public CheckRequired { Objects.requireNonNull(reason, "reason"); }
    }
    public record CheckDeferred(Deferred deferred) implements ReviewGate {
        public CheckDeferred { Objects.requireNonNull(deferred, "deferred"); }
    }
    public record Requalification(State state, boolean changed) {
        public Requalification { Objects.requireNonNull(state, "state"); }
    }

    static void nonempty(String value, String name) {
        if (value == null || value.isEmpty() || value.codePointCount(0, value.length()) > 32_768) {
            throw new IllegalArgumentException(name + " is required and bounded");
        }
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) {
                if (index + 1 == value.length() || !Character.isLowSurrogate(value.charAt(index + 1))) {
                    throw new IllegalArgumentException(name + " contains an unpaired surrogate");
                }
                index++;
            } else if (Character.isLowSurrogate(current)) {
                throw new IllegalArgumentException(name + " contains an unpaired surrogate");
            }
        }
    }
    static void nonnegative(BigInteger value, String name) {
        if (value == null || value.signum() < 0) {
            throw new IllegalArgumentException(name + " must be a nonnegative integer");
        }
    }
}
