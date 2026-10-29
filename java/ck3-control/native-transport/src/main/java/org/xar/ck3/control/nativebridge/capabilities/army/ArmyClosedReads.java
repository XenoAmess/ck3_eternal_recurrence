package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.Objects;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Complete values for three migrated read producers. No action or capture-control permission. */
public final class ArmyClosedReads {
    private ArmyClosedReads() { }
    public sealed interface Observation permits DefaultRaise, Truce, Gathering {
        PublicMethod method();
    }
    public record Build(String version, String executableSha256) {
        public Build {
            Objects.requireNonNull(version); Objects.requireNonNull(executableSha256);
            ArmyTypes.require(version.equals("1.20.0.4") && executableSha256.equalsIgnoreCase(ArmyResponseCodec.ACTUAL4_SHA)
                    || version.equals("1.20.0.3") && executableSha256.equalsIgnoreCase("94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
                    "unknown or mixed native executable/build");
        }
    }
    public enum RaiseStatus { AVAILABLE, PARTIAL, UNAVAILABLE, REQUIRES_PAUSED, INVALID_REQUEST }
    public enum ReserveStatus { AVAILABLE, UNAVAILABLE }
    public record QueryFrame(UInt64 sequence, UInt64 nativeRevision, int dateRaw) {
        public QueryFrame {
            Objects.requireNonNull(sequence); Objects.requireNonNull(nativeRevision);
            ArmyTypes.require(sequence.value().signum() > 0 && nativeRevision.value().signum() > 0, "positive native read sequence/revision required");
        }
    }
    public record DefaultRaise(QueryFrame frame, Build build, RaiseStatus status, int actor,
            boolean legalityReady, Field<Boolean> legal, Field<PositiveId> province, String failure,
            ReserveStatus reserveStatus, boolean reserveReady, Field<Integer> soldiers, String reserveFailure)
            implements Observation {
        public DefaultRaise {
            Objects.requireNonNull(frame); Objects.requireNonNull(build); Objects.requireNonNull(status);
            Objects.requireNonNull(legal); Objects.requireNonNull(province); Objects.requireNonNull(reserveStatus); Objects.requireNonNull(soldiers);
            ArmyTypes.require(actor >= 0 && failure != null && !failure.isEmpty() && reserveFailure != null && !reserveFailure.isEmpty(), "complete native raise result required");
            ArmyTypes.require(!(legal instanceof Missing<?>) && !(province instanceof Missing<?>) && !(soldiers instanceof Missing<?>), "native nullable raise fields cannot be absent");
            ArmyTypes.require(legalityReady == (legal instanceof Present<?>) && legalityReady == (status == RaiseStatus.AVAILABLE)
                    && (!legalityReady || province instanceof Present<?> && failure.equals("none")), "raise readiness differs from native legality");
            ArmyTypes.require(reserveReady == (reserveStatus == ReserveStatus.AVAILABLE) && reserveReady == (soldiers instanceof Present<?>)
                    && (reserveReady ? reserveFailure.equals("none") : !reserveFailure.equals("none")), "unraised reserve readiness differs from observation");
            if (soldiers instanceof Present<Integer> p) ArmyTypes.require(p.value() >= 0, "nonnegative reserve required");
        }
        @Override public PublicMethod method() { return PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1; }
    }
    public enum TruceStatus { AVAILABLE, NO_TRUCE }
    public record Truce(QueryFrame frame, Build build, int owner, PositiveId toward, TruceStatus status,
            boolean hasTruce, boolean expiryObservable, Field<Integer> expiryDateRaw, boolean stable,
            boolean readiness, Field<String> unavailableReason) implements Observation {
        public Truce {
            Objects.requireNonNull(frame); Objects.requireNonNull(build); Objects.requireNonNull(toward); Objects.requireNonNull(status);
            Objects.requireNonNull(expiryDateRaw); Objects.requireNonNull(unavailableReason);
            ArmyTypes.require(owner >= 0 && build.version().equals("1.20.0.4"), "truce requires actual4 and a complete current player");
            if (status == TruceStatus.AVAILABLE)
                ArmyTypes.require(hasTruce && expiryObservable && stable && readiness && expiryDateRaw instanceof Present<Integer> p
                        && p.value() > frame.dateRaw() && unavailableReason instanceof NullValue<?>, "available truce lacks persisted relation observation");
            else ArmyTypes.require(!hasTruce && !expiryObservable && stable && !readiness && expiryDateRaw instanceof NullValue<?>
                    && unavailableReason.equals(new Present<>("native_has_truce_false")), "no-truce must retain the successful negative observation");
        }
        @Override public PublicMethod method() { return PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1; }
    }
    /** A research capture-state observation, never a statement that a natural gathering stage completed. */
    public record Gathering(ArmyResponses.Gathering state) implements Observation {
        public Gathering { Objects.requireNonNull(state); }
        @Override public PublicMethod method() { return PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1; }
    }
}
