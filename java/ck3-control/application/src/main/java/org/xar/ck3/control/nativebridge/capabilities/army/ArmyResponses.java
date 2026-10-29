package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

public final class ArmyResponses {
    private ArmyResponses() { }
    public record Declarations(Frame frame, List<DeclarationContract.Choice> choices) { public Declarations { choices = List.copyOf(choices); } }
    public record DefaultRaise(Frame frame, PositiveId actor, String status, boolean legalityReady,
            Field<Boolean> nativeLegal, Field<PositiveId> province, String failure,
            Availability unraisedStatus, boolean unraisedReady, Field<Integer> unraisedSoldiers, String unraisedFailure) { }
    public record Truce(Frame frame, int owner, PositiveId toward, boolean hasTruce,
            boolean actualExpiryObservable, Field<Integer> expiryDateRaw, boolean sameFrameStable,
            boolean readiness, Field<String> unavailableReason) { }
    public enum SamplingStatus { ENABLED, DISABLED, BUSY, CLEAR_PENDING }
    public enum SamplingReadiness { OFF, INFLIGHT, AWAITING_SAMPLE, RETAINED_OBSERVATION }
    public record Gathering(boolean accepted, SamplingStatus status, boolean enabled, boolean busy, boolean clearCompleted,
            UInt64 epoch, UInt64 activeCaptures, UInt64 retained, UInt64 qualified, SamplingReadiness readiness) { }
    public record UiOwner(String requestId, UInt64 ticketSequence, UInt64 executorStartedSequence, UInt64 completedSequence,
            UInt64 pumpEpoch, long threadId, long dateRaw, UInt64 connectionGeneration) { }
    public record WarWindow(String schema, boolean available, String operation, String windowName, String status,
            Field<String> unavailableReason, PositiveId player, long dateRaw, UInt64 nativeRevision, UInt64 generation,
            UInt64 pumpEpoch, long threadId, boolean rootObserved, boolean present, boolean visible,
            boolean postObserved, boolean postPresent, boolean postVisible, boolean scopeUnchanged,
            boolean closureVerified, boolean ownerThreadVerified, boolean paused, UiOwner owner) { }
    public record WhitePeaceStatus(FullId war, String status, boolean pending, List<String> unsupportedFields) { public WhitePeaceStatus { unsupportedFields = List.copyOf(unsupportedFields); } }
    public record OccupationTarget(PositiveId title, PositiveId province, Field<PositiveId> holder,
            Field<PositiveId> controller, boolean occupiedByPlayerSide) { }
    public record OccupationTargets(Frame frame, FullId war, Availability status, boolean available, List<OccupationTarget> targets,
            List<String> unsupportedFields) { public OccupationTargets { targets = List.copyOf(targets); unsupportedFields = List.copyOf(unsupportedFields); } }
    public enum WarStateStatus { ACTIVE, POSTWAR_ARMIES, IDLE }
    public record WarState(WarStateStatus status, String snapshotId, BigInteger revision, BigInteger nativeRevision,
            BigInteger dateRaw, BigInteger player, List<NativeActiveWarsCodec.War> wars, List<NativeArmiesCodec.Army> playerArmies,
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj normalized) {
        public WarState { wars = List.copyOf(wars); playerArmies = List.copyOf(playerArmies); java.util.Objects.requireNonNull(normalized); }
    }
    public record Strength(PublicUnitId army, Field<PositiveId> nativeArmy, Availability status, String scopeRole,
            List<FullId> wars, Field<Integer> regimentCount, Field<Integer> currentSoldiers, Field<Integer> maximumSoldiers,
            Field<Long> aiBasePowerRaw, long aiBasePowerScale, Field<String> unavailableReason,
            List<String> notYetProjectedFields) { public Strength { wars = List.copyOf(wars); notYetProjectedFields = List.copyOf(notYetProjectedFields); } }
    public record Strengths(Frame frame, ArmyRequests.StrengthProfile profile, String phaseCoverage, List<Strength> armies,
            boolean completeSemanticProjection) { public Strengths { armies = List.copyOf(armies); } }
    public record CombatCompleteness(boolean inputObservationReady, boolean monteCarloReady, boolean plannerUsable,
            boolean activeAttackAllowed, List<String> missingDomains) { public CombatCompleteness { missingDomains = List.copyOf(missingDomains); } }
    public record CombatArmy(PublicUnitId army, Field<PositiveId> nativeArmy, String role, String status, List<String> unprojectedFields) { public CombatArmy { unprojectedFields = List.copyOf(unprojectedFields); } }
    public record CombatInputs(Frame frame, int version, PositiveId target, List<CombatArmy> armies,
            CombatCompleteness observedCompleteness, List<String> unprojectedFields) { public CombatInputs { armies = List.copyOf(armies); unprojectedFields = List.copyOf(unprojectedFields); } public boolean fullModelInputsReady() { return false; } }
    public record PhaseTrace(Frame frame, PositiveId combat, boolean evaluatorProbeReady,
            boolean productionTraceReady, boolean qualifiedWinProbabilityAvailable, List<String> unprojectedFields) { public PhaseTrace { unprojectedFields = List.copyOf(unprojectedFields); } }
    public record WarEntryAssessment(PositiveId target, String status, Field<Long> ownPowerRaw, Field<Long> targetPowerRaw,
            List<String> unprojectedFields) { public WarEntryAssessment { unprojectedFields = List.copyOf(unprojectedFields); } }
    public record WarEntry(Frame frame, List<WarEntryAssessment> assessments) { public WarEntry { assessments = List.copyOf(assessments); } }
}

