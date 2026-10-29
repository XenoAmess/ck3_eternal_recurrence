package org.xar.ck3.control.wave2.governance.government;

import java.math.BigInteger;
import java.util.Objects;

/** Pure ordinary-campaign context. All native-source checks precede construction. */
public final class GovernmentContext {
    public static final String SCHEMA = "ordinary-campaign-government-context-v1";
    public static final String ORDINARY_LIFECYCLE = "ordinary_campaign_succession";
    private GovernmentContext() { }

    public enum Status {
        NOT_QUERIED("not_queried"), INACTIVE("inactive"), AVAILABLE("available"),
        NOT_PRESENT("not_present"), UNAVAILABLE("unavailable");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Status observation(String value) {
            return switch (value) {
                case "available" -> AVAILABLE;
                case "not_present" -> NOT_PRESENT;
                case "unavailable" -> UNAVAILABLE;
                default -> throw new IllegalArgumentException("government runtime adapter status is malformed");
            };
        }
    }

    public record GoalIdentity(String campaignId, BigInteger currentCharacterId) { }

    public record Snapshot(BigInteger nativeRevision, BigInteger dateRaw, BigInteger playerCharacterId,
            String lifecycle, GoalIdentity goalIdentity, boolean goalObject, String goalValidationError,
            String nativeBuildVersion, String nativeBuildSha256, String nativeBuildError) { }

    /** Canonical preserved wire is immutable text; it grants no native action capability. */
    public record Observation(Status status, boolean sameFrameReady, boolean coreAdapterReady,
            String unavailableReason, String governmentKey, String adapterFamily,
            String adapterStatus, String preservedWire) { }

    public record Request(Snapshot snapshot, boolean queryPermitted, Observation observation,
            String observationError, boolean observationPresent) { }

    public record Context(Status status, boolean queryPermitted, boolean identityObservationReady,
            boolean coreAdapterReady, boolean ordinaryGoalContextReady, String unavailableReason,
            String campaignId, BigInteger currentCharacterId, BigInteger snapshotRevision,
            BigInteger dateRaw, String governmentKey, String adapterFamily, String adapterStatus,
            String governmentRuntimeAdapterWire) {
        public Context {
            Objects.requireNonNull(status);
            if (ordinaryGoalContextReady && (!identityObservationReady || !coreAdapterReady)) {
                throw new IllegalArgumentException("ordinary goal readiness requires native identity and core readiness");
            }
            if (coreAdapterReady && !identityObservationReady) {
                throw new IllegalArgumentException("core readiness requires native identity readiness");
            }
        }
    }

    public static Context build(Request request) {
        Snapshot snapshot = request.snapshot();
        if (!ORDINARY_LIFECYCLE.equals(snapshot.lifecycle())) {
            return empty(request, Status.INACTIVE, "not_ordinary_campaign");
        }
        if (!request.queryPermitted()) {
            return empty(request, Status.NOT_QUERIED, "government_query_not_permitted");
        }
        if (!snapshot.goalObject()) {
            return empty(request, Status.NOT_QUERIED, "ordinary_campaign_goal_unavailable");
        }
        if (snapshot.goalValidationError() != null) {
            return empty(request, Status.UNAVAILABLE, snapshot.goalValidationError());
        }
        if (!request.observationPresent()) {
            return empty(request, Status.UNAVAILABLE, "government_observation_unavailable");
        }
        if (request.observationError() != null) {
            return empty(request, Status.UNAVAILABLE, request.observationError());
        }
        Observation observed = Objects.requireNonNull(request.observation());
        boolean identityReady = observed.status() == Status.AVAILABLE && observed.sameFrameReady();
        boolean coreReady = identityReady && observed.coreAdapterReady();
        boolean matches = snapshot.goalIdentity() != null && snapshot.playerCharacterId() != null
                && Objects.equals(snapshot.goalIdentity().currentCharacterId(), snapshot.playerCharacterId());
        String reason = observed.unavailableReason();
        if (identityReady && !matches) {
            reason = "ordinary_goal_current_ruler_not_matched";
        } else if (identityReady && !coreReady) {
            reason = observed.adapterStatus() == null ? "government_adapter_unavailable" : observed.adapterStatus();
        }
        GoalIdentity goal = snapshot.goalIdentity();
        return new Context(observed.status(), request.queryPermitted(), identityReady, coreReady,
                coreReady && matches, reason, goal == null ? null : goal.campaignId(),
                goal == null ? null : goal.currentCharacterId(), snapshot.nativeRevision(), snapshot.dateRaw(),
                observed.governmentKey(), observed.adapterFamily(), observed.adapterStatus(), observed.preservedWire());
    }

    private static Context empty(Request request, Status status, String reason) {
        Snapshot snapshot = request.snapshot();
        GoalIdentity goal = snapshot.goalIdentity();
        return new Context(status, request.queryPermitted(), false, false, false, reason,
                goal == null ? null : goal.campaignId(), goal == null ? null : goal.currentCharacterId(),
                snapshot.nativeRevision(), snapshot.dateRaw(), null, null, null, null);
    }
}
