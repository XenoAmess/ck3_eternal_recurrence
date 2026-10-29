package org.xar.ck3.control.wave2.military.combatroles;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Immutable current-observation operands. Readiness never authorizes a callback or a future battle. */
public final class CombatRoles {
    private CombatRoles() { }
    private static void unsigned32(Long value) {
        if (value != null && (value < 0 || value > 0xffffffffL)) throw new IllegalArgumentException("native unsigned32 outside domain");
    }
    private static void unsigned8(Integer value) {
        if (value != null && (value < 0 || value > 255)) throw new IllegalArgumentException("native unsigned8 outside domain");
    }
    private static void identity(String value) {
        if (value != null && value.isEmpty()) throw new IllegalArgumentException("empty native identity");
    }

    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum SelectionSource { REGISTRY_FULL_ID, NATIVE_FALLBACK }
    public enum Membership { ATTACKER, DEFENDER, BOTH, NEITHER }
    public enum PhaseLabel { MANEUVER, MAIN, PURSUIT, DONE, UNRESOLVED }
    public enum Decision { FORCED_MAIN, DURATION_MAIN_WITHOUT_WORKER, MANEUVER_WAIT,
        MAIN_WORKER, PURSUIT_WORKER, OTHER_PHASE_WITHOUT_WORKER }
    public enum Worker { MAIN, PURSUIT }

    public record State(Status status, String unavailableReason) {
        public State { Objects.requireNonNull(status); Objects.requireNonNull(unavailableReason); }
    }
    public record Reference(int nativeIndex, Long rawFullId) { public Reference { unsigned32(rawFullId); } }
    public record RawOccurrence(State state, boolean ready, int nativeIndex, Long rawFullId) {
        public RawOccurrence { Objects.requireNonNull(state); unsigned32(rawFullId); }
    }
    public record RawReferences(State state, boolean ready, boolean referencesReady, Integer count,
            String dataIdentity, Boolean dataPresent, List<RawOccurrence> occurrences, int observedCount) {
        public RawReferences { Objects.requireNonNull(state); identity(dataIdentity); occurrences = List.copyOf(occurrences); }
    }
    /** The generic original Army resolver has two additional metadata fields; source Selection does not. */
    public record Resolution(State state, boolean ready, Boolean registryLoaded, Boolean usedFallback,
            Long requestedFullId, Long registryCapacity, Long registryIndex, Long indexedFullId,
            String indexedIdentity, SelectionSource selection, String objectIdentity,
            boolean selectedObjectReady, Long selectedFullId, Boolean selectedFullIdReadReady) {
        public Resolution { Objects.requireNonNull(state); unsigned32(requestedFullId); unsigned32(registryCapacity);
            unsigned32(registryIndex); unsigned32(indexedFullId); unsigned32(selectedFullId);
            identity(indexedIdentity); identity(objectIdentity); }
    }
    public record Roster(State state, String dataIdentity, Long capacity, Integer count,
            List<Reference> references, boolean referencesReady) {
        public Roster { Objects.requireNonNull(state); identity(dataIdentity); unsigned32(capacity); references = List.copyOf(references); }
    }
    public record Manager(State state, String gameStateIdentity, String domainIdentity,
            String managerIdentity, String secondaryVtableIdentity, Boolean secondaryVtableMatched,
            Roster roster, boolean managerInputsReady) {
        public Manager { Objects.requireNonNull(state); Objects.requireNonNull(roster); identity(gameStateIdentity);
            identity(domainIdentity); identity(managerIdentity); identity(secondaryVtableIdentity); }
    }
    public record Side(State state, String parentIdentity, Boolean parentMatchesSelectedCombat,
            Roster armies, List<Integer> matchingArmyIndices, boolean matchingMembershipReady,
            Long primary, Long commander, Boolean ownerMatchesPrimary, boolean sideInputsReady) {
        public Side { Objects.requireNonNull(state); Objects.requireNonNull(armies);
            identity(parentIdentity); unsigned32(primary); unsigned32(commander); matchingArmyIndices = List.copyOf(matchingArmyIndices); }
    }
    public record Occurrence(State state, int nativeIndex, Long rawFullId,
            Resolution originalArmyResolution, boolean sameQueryArmySelectionMatched,
            Long actualArmyId, Long armyCombatId, Resolution combatResolution, Long combatMagic,
            Long selectedCombatFullId, Boolean sourceActiveCombat, boolean activeCombatInputsReady,
            List<Integer> managerMatchIndices, boolean combatManagerMembershipReady,
            Long armyUnitId, Long unitOwnerId, Resolution unitResolution, Resolution characterResolution,
            Long selectedCharacterId, boolean ownerInputsReady, Side attackerSide, Side defenderSide,
            Integer phase, Integer day, Integer forcedWinner, Integer finalized, Integer processing,
            boolean phaseInputsReady, boolean thresholdRequired, Integer maneuverThreshold,
            boolean thresholdInputsReady, boolean currentCombatRolesPhaseInputsReady) {
        public Occurrence {
            Objects.requireNonNull(state); Objects.requireNonNull(originalArmyResolution);
            Objects.requireNonNull(combatResolution); Objects.requireNonNull(unitResolution);
            Objects.requireNonNull(characterResolution); Objects.requireNonNull(attackerSide);
            Objects.requireNonNull(defenderSide); managerMatchIndices = List.copyOf(managerMatchIndices);
            unsigned32(rawFullId); unsigned32(actualArmyId); unsigned32(armyCombatId); unsigned32(combatMagic);
            unsigned32(selectedCombatFullId); unsigned32(armyUnitId); unsigned32(unitOwnerId); unsigned32(selectedCharacterId);
            unsigned8(finalized); unsigned8(processing);
        }
    }
    public record Inputs(State state, Boolean originalArmyManagerLoaded, String originalArmyManagerIdentity,
            RawReferences originalRoster, Manager combatManager, List<Occurrence> occurrences,
            boolean rawRosterReferencesReady, boolean originalArmySelectionsReady,
            boolean currentCombatRolesPhaseInputsReady) {
        public Inputs { Objects.requireNonNull(state); Objects.requireNonNull(originalRoster);
            Objects.requireNonNull(combatManager); identity(originalArmyManagerIdentity); occurrences = List.copyOf(occurrences); }
    }
    public record Provenance(String snapshotId, BigInteger revision, BigInteger nativeRevision,
            BigInteger dateRaw, String gameVersion, String executableSha256) { }
    public record PhaseSelector(boolean ready, Decision decision, Worker worker,
            Integer incrementedDay, Integer selectedPhase, Integer selectedDay) { }
    public record ProjectedOccurrence(Occurrence observed, boolean ready, Membership storedSideMembership,
            PhaseLabel phaseLabel, PhaseSelector hypotheticalPhaseSelector) { }
    public record Projection(Inputs observed, Provenance sourceProvenance, Status status,
            boolean ready, String unavailableReason, List<ProjectedOccurrence> occurrences) {
        public Projection { Objects.requireNonNull(status); occurrences = List.copyOf(occurrences); }
    }
    /** Preserve absent optional SDK member separately from present JSON null. */
    public sealed interface Member permits Missing, ExplicitNull, Present { }
    public record Missing() implements Member { }
    public record ExplicitNull() implements Member { }
    public record Present(Inputs value) implements Member { public Present { Objects.requireNonNull(value); } }
    public record ArmyMember(BigInteger armyId, Member member) {
        public ArmyMember { Objects.requireNonNull(armyId); Objects.requireNonNull(member); }
    }
}
