package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Values from actual battle readers. Availability and lifecycle absence never turn into an inferred win. */
public final class BattleResponses {
    private BattleResponses() { }
    public record SideFlags(boolean disallowRetreat, boolean allowEarlyRetreat, boolean skipPursuit) { }
    public record RetreatLegality(Availability status, Field<Boolean> nativeBoolean, int phaseRaw, Phase phase,
            Field<Long> baselineDateRaw, Field<Long> elapsedDays, Field<Integer> minimumDaysExclusive,
            Field<Boolean> landlessGateAllows, boolean legalNow, List<String> reasons, List<String> nativeReasonKeys, Field<Long> earliestDateRaw) {
        public RetreatLegality { reasons = List.copyOf(reasons); nativeReasonKeys = List.copyOf(nativeReasonKeys); }
    }
    public record Army(PublicUnitId publicId, PositiveId nativeArmy, PositiveId owner, FullId combatBacklink) { }
    public record AccoladeSource(String linkStatus, Field<Integer> accoladeIdRaw, String rowsStatus, String sourceGateStatus) { }
    public record Entry(String bucket, int bucketIndex, FullId regiment, PositiveId nativeArmy, PublicUnitId publicId,
            PositiveId owner, long startingRaw, long currentFightingRaw, long softCasualtiesRaw, boolean fightsMain,
            String hardStatus, Field<Long> hardRaw, Field<String> hardSource, Field<String> hardUnavailableReason,
            int effectiveMaxSize, long effectiveSiegeRaw, long effectiveDamageRaw, long effectiveToughnessRaw,
            long effectivePursuitRaw, long effectiveScreenRaw, long entryStrengthRaw,
            Field<UInt64> physicalIdentity, Field<Integer> knightCharacterIdRaw, Field<AccoladeSource> accoladeSource) { }
    public record HardLedger(int rowIndex, PositiveId participant, long hardCasualtiesRaw) { }
    public record CombatSide(Side side, PositiveId primaryParticipant, Field<PositiveId> commander, int currentRollPoints,
            List<Army> orderedArmies, List<Entry> levies, List<Entry> menAtArms, long storedCurrentRaw,
            long storedLevyCurrentRaw, boolean storedMatches, boolean storedLevyMatches, long derivedCurrentRaw,
            long derivedSoftRaw, long derivedMainHardRaw, long nonMainDifferenceRaw, List<HardLedger> hardLedger,
            long participantHardTotalRaw, long strengthRaw, long strengthScale, Field<Long> terminalLossBaselineRaw) {
        public CombatSide { orderedArmies = List.copyOf(orderedArmies); levies = List.copyOf(levies); menAtArms = List.copyOf(menAtArms); hardLedger = List.copyOf(hardLedger); }
    }
    public record Control(Frame frame, PublicUnitId subject, PositiveId subjectNative, FullId combat, PositiveId province,
            PublicUnitId selected, PositiveId selectedNative, PositiveId selectedOwner, PositiveId combatProvince,
            Side side, Scope scope, List<PublicUnitId> affected, List<PublicUnitId> unaffected, SideFlags sideFlags,
            RetreatLegality retreat, Phase phase, int phaseDay, Winner winner, Winner forcedWinner, boolean finalized,
            Field<FullId> resultId, int baseWidth, int finalWidth, int rollCadenceCounter,
            long baseAdvantageRaw, long resolvedAdvantageRaw, CombatSide attacker, CombatSide defender,
            List<String> unsupportedExtensions, Obj originalFrame) {
        public Control { affected = List.copyOf(affected); unaffected = List.copyOf(unaffected); unsupportedExtensions = List.copyOf(unsupportedExtensions); Objects.requireNonNull(originalFrame); }
        /** The core is useful for identity/retreat; simulation needs all exact-build operands. */
        public boolean fullSimulationInputsReady() { return false; }
    }
    public enum TransitionStatus { AVAILABLE, COMBAT_NOT_FOUND, STATE_CHANGED, UNAVAILABLE }
    public record Lifecycle(PositiveId province, Phase phase, int phaseDay, Winner winner, Winner forcedWinner,
            boolean finalized, Field<FullId> battleResult) { }
    public record CurrentSide(long currentRaw, long softRaw, long hardRaw, long nonMainDifferenceRaw, long participantHardRaw,
            List<HardLedger> participantHardLedger) { public CurrentSide { participantHardLedger = List.copyOf(participantHardLedger); } }
    public record CurrentObservation(Availability status, Field<String> unavailableReason, long scale,
            Field<Integer> baseWidth, Field<Integer> finalWidth, Field<Long> baseAdvantageRaw,
            Field<Long> resolvedAdvantageRaw, Field<CurrentSide> attacker, Field<CurrentSide> defender) { }
    public record Transition(Frame frame, FullId combat, TransitionStatus status, boolean ready, Field<Lifecycle> lifecycle,
            List<PublicUnitId> attackers, List<PublicUnitId> defenders, Field<CurrentObservation> current,
            List<String> unsupportedExtensions, Obj originalFrame) {
        public Transition { attackers = List.copyOf(attackers); defenders = List.copyOf(defenders); unsupportedExtensions = List.copyOf(unsupportedExtensions); Objects.requireNonNull(originalFrame); }
    }
    public record Signal(boolean askingForHelp, boolean assignedToHelp, boolean askingChanged,
            Field<Long> requestPowerBasisRaw, int crossCoordinatorRequestValidRaw, Field<Long> crossCoordinatorRequestPowerRaw,
            Field<Long> firstEdgeRemainingQ100000) { }
    public record Assignment(Field<PositiveId> target, String targetProvenance, String combatBindingStatus, Field<FullId> activeCombat) { }
    public record Route(PositiveId currentProvince, Field<PositiveId> moveTarget, List<PositiveId> provinces,
            String alignment, Field<List<Integer>> arrivals, Field<Integer> assignmentEta) {
        public Route { provinces = List.copyOf(provinces); Objects.requireNonNull(arrivals); if(arrivals instanceof Present<List<Integer>> present) arrivals = new Present<>(List.copyOf(present.value())); }
    }
    public record Subunit(List<PublicUnitId> units, boolean asking, boolean assigned, Field<PositiveId> target) { public Subunit { units = List.copyOf(units); } }
    public record NativeOrder(List<PositiveId> supportSearchProvinces, List<Subunit> parentSubunits) { public NativeOrder { supportSearchProvinces = List.copyOf(supportSearchProvinces); parentSubunits = List.copyOf(parentSubunits); } }
    public record Contact(String status, String temporalSemantics, List<FullId> compatibleCombats, Field<FullId> selectedIfNow, Field<ArmyReinforcementCodec.Arrival> arrivalAdmission) { public Contact { compatibleCombats = List.copyOf(compatibleCombats); Objects.requireNonNull(arrivalAdmission); } }
    public record ReinforcementState(Field<PositiveId> selectedNative, FullId coordinator, int unitStackIndex, int subunitIndex,
            Signal signal, Assignment assignment, Route route, NativeOrder nativeOrder, Contact contact) { }
    public record Reinforcement(Frame frame, PublicUnitId selected, Availability status, boolean ready,
            Field<String> unavailableReason, Field<ReinforcementState> state, Obj originalFrame) { public Reinforcement { Objects.requireNonNull(originalFrame); } }
    public record Journal(Field<UInt64> requestedAfter, UInt64 oldest, UInt64 latest, Field<UInt64> eventSequence, String eventStatus) { }
    public record WarScore(String status, Field<FullId> war, Field<Integer> rowIndex, Field<Long> valueRaw,
            Field<Boolean> winnerWarAttacker, Field<Boolean> side0WarAttacker, Field<Long> attackerRelativeDelta) { }
    public record Prior(FullId combat, String terminalKind, Field<Long> terminalDate, Field<Boolean> suppressResultEnvelopes,
            Field<Integer> phaseRaw, Field<Integer> phaseDay, Field<Integer> winnerRaw, Field<Boolean> finalizedBefore,
            Field<Integer> dailyGuardRaw, Field<PositiveId> province, Field<FullId> result, Field<Boolean> wipeRaw,
            Field<PositiveId> attackerPrimary, Field<PositiveId> defenderPrimary, Field<List<PublicUnitId>> attackers,
            Field<List<PublicUnitId>> defenders, WarScore warScore, List<String> unsupportedExtensions) {
        public Prior { Objects.requireNonNull(attackers); Objects.requireNonNull(defenders); unsupportedExtensions = List.copyOf(unsupportedExtensions); }
    }
    public record Removal(boolean combatResolves, Field<Boolean> provinceResolves, Field<Boolean> provinceContainsCombat,
            Field<Boolean> resultResolves, Field<Integer> resultRelevantPlayerCount) { }
    public record Subject(boolean exists, Field<PositiveId> currentProvince, Field<PositiveId> nativeArmy,
            Field<FullId> combatBacklink, Field<FullId> activeCombat, Field<Integer> movementState,
            Field<PositiveId> moveTarget, Field<List<PositiveId>> route, String aiMembershipStatus,
            Field<FullId> coordinator, Field<Integer> stackIndex, Field<Integer> subunitIndex, Field<Boolean> blockedByCombat) { }
    public record Successor(String state, List<FullId> matchingCombats, Field<FullId> selectedCombat, List<PublicUnitId> overlap) { public Successor { matchingCombats = List.copyOf(matchingCombats); overlap = List.copyOf(overlap); } }
    public record TerminalState(Prior prior, Removal removal, Subject subject, Successor successor) { }
    public record Terminal(Frame frame, Field<FullId> priorCombat, Field<PublicUnitId> subject,
            Availability status, boolean ready, Field<String> unavailableReason, Journal journal,
            Field<TerminalState> state, List<String> unsupportedExtensions, Obj originalFrame) { public Terminal { unsupportedExtensions = List.copyOf(unsupportedExtensions); Objects.requireNonNull(originalFrame); } }
    public record Knight(Frame frame, long observedDateRaw, PositiveId combat, PositiveId province,
            PublicUnitId subject, PositiveId nativeArmy, PositiveId character, PositiveId regiment,
            int prowess, long effectivenessRaw, long evaluatedDamageRaw, long evaluatedToughnessRaw,
            long storedEntryDamageRaw, long storedEntryToughnessRaw, long scale) { }
}
