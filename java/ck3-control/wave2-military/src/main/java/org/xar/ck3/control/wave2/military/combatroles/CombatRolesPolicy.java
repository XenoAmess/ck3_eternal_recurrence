package org.xar.ck3.control.wave2.military.combatroles;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import static org.xar.ck3.control.contracts.StrictJson.require;
import org.xar.ck3.control.wave2.military.combatroles.CombatRoles.*;

/** Complete source .3 declared-readiness reducer and hypothetical phase selector; no game access. */
public final class CombatRolesPolicy {
    private CombatRolesPolicy() { }
    private record Active(boolean ready, Boolean active) { }

    private static void state(State state, boolean ready) {
        require(ready == (state.status() == Status.AVAILABLE)
                && ready != !state.unavailableReason().isEmpty(), "status/readiness/reason disagree");
    }
    private static boolean rosterReady(Roster roster) {
        if (roster.dataIdentity() == null || roster.capacity() == null || roster.count() == null
                || roster.count() < 0 || roster.references().size() != roster.count()) return false;
        for (int i = 0; i < roster.references().size(); i++) {
            Reference reference = roster.references().get(i);
            if (reference.nativeIndex() != i || reference.rawFullId() == null) return false;
        }
        return true;
    }
    private static void roster(Roster roster) {
        Integer count = roster.count();
        for (int i = 0; i < roster.references().size(); i++) {
            require(roster.references().get(i).nativeIndex() == i, "filtered/relabelled native reference order");
        }
        require(count == null ? roster.references().isEmpty()
                : roster.references().size() == Math.max(count, 0), "discarded demanded raw references");
        require(roster.referencesReady() == rosterReady(roster), "roster readiness differs");
        state(roster.state(), rosterReady(roster));
    }
    private static void rawReferences(RawReferences roster) {
        require(roster.observedCount() == roster.occurrences().size(), "observed count differs");
        int previous = -1;
        boolean complete = roster.count() != null && roster.count() >= 0
                && roster.occurrences().size() == roster.count();
        for (int i = 0; i < roster.occurrences().size(); i++) {
            RawOccurrence row = roster.occurrences().get(i);
            require(row.nativeIndex() >= 0 && row.nativeIndex() > previous
                    && (roster.count() == null || roster.count() < 0 || row.nativeIndex() < roster.count()),
                    "original native occurrence order differs");
            previous = row.nativeIndex();
            require(row.ready() == (row.rawFullId() != null), "raw occurrence readiness differs");
            state(row.state(), row.ready());
            complete &= row.nativeIndex() == i && row.rawFullId() != null;
        }
        require(roster.ready() == complete && roster.referencesReady() == complete,
                "original references readiness differs");
        state(roster.state(), roster.ready());
    }
    private static void resolution(Resolution value, Long requested, boolean generic) {
        state(value.state(), value.ready());
        boolean demanded = !generic || value.requestedFullId() != null
                || value.selection() != null || value.selectedObjectReady();
        require(!demanded || Objects.equals(value.requestedFullId(), requested), "resolver requested full DWORD differs");
        require(value.selection() == null || Objects.equals(value.usedFallback(),
                value.selection() == SelectionSource.NATIVE_FALLBACK), "fallback provenance differs");
        require(value.registryIndex() == null || requested != null && value.registryIndex() == (requested & 0xffffffL),
                "low24 index differs from full DWORD");
        require(!value.selectedObjectReady() || value.objectIdentity() != null && value.selection() != null,
                "selected operand has no physical/source association");
        if (value.selection() == SelectionSource.REGISTRY_FULL_ID && value.selectedObjectReady()) {
            require(Objects.equals(value.indexedFullId(), requested), "full generation differs");
            require(generic ? Objects.equals(value.selectedFullId(), requested)
                    : Objects.equals(value.objectIdentity(), value.indexedIdentity()), "selected full generation/object differs");
        }
        if (generic) {
            require(!Boolean.TRUE.equals(value.selectedFullIdReadReady()) || value.selectedFullId() != null,
                    "claimed selected full-ID read missing");
            require(!value.ready() || value.selectedObjectReady() && Boolean.TRUE.equals(value.selectedFullIdReadReady()),
                    "generic resolver metadata incomplete");
        } else {
            require(!Boolean.FALSE.equals(value.registryLoaded()) || requested == null && value.registryIndex() == null,
                    "nullstore branch relabelled undemanded reference");
            require(value.ready() == value.selectedObjectReady(), "selection readiness differs");
        }
    }
    private static boolean selectionReady(Resolution value, Long requested) {
        return value.selectedObjectReady() && value.objectIdentity() != null
                && (Boolean.FALSE.equals(value.registryLoaded()) || Boolean.TRUE.equals(value.registryLoaded()) && requested != null);
    }
    private static boolean undemanded(Resolution value) {
        return !value.ready() && !value.selectedObjectReady() && value.registryLoaded() == null
                && value.usedFallback() == null && value.requestedFullId() == null && value.registryCapacity() == null
                && value.registryIndex() == null && value.indexedFullId() == null && value.indexedIdentity() == null
                && value.selection() == null && value.objectIdentity() == null;
    }
    private static Active active(Occurrence row) {
        if (!selectionReady(row.combatResolution(), row.armyCombatId()) || row.combatMagic() == null) return new Active(false, null);
        if (row.combatMagic() != 0x436f6d62L) return new Active(true, false);
        return row.selectedCombatFullId() == null ? new Active(false, null)
                : new Active(true, row.selectedCombatFullId() != 0xffffffffL);
    }
    private static boolean managerReady(Manager value) {
        // A captured false vtable comparison is known; preserve it rather than silently relabelling it unknown.
        return value.gameStateIdentity() != null && value.domainIdentity() != null && value.managerIdentity() != null
                && value.secondaryVtableIdentity() != null && value.secondaryVtableMatched() != null && rosterReady(value.roster());
    }
    private static boolean ownerReady(Occurrence row) {
        return selectionReady(row.unitResolution(), row.armyUnitId())
                && selectionReady(row.characterResolution(), row.unitOwnerId()) && row.selectedCharacterId() != null;
    }
    private static boolean sideReady(Side side, Occurrence row) {
        return side.parentIdentity() != null && side.parentMatchesSelectedCombat() != null && row.actualArmyId() != null
                && rosterReady(side.armies()) && side.primary() != null && side.commander() != null
                && row.selectedCharacterId() != null && side.ownerMatchesPrimary() != null;
    }
    private static List<Integer> matches(Roster roster, Long target) {
        if (target == null) return List.of();
        return roster.references().stream().filter(row -> Objects.equals(row.rawFullId(), target)).map(Reference::nativeIndex).toList();
    }
    private static boolean phaseReady(Occurrence row) {
        return row.phase() != null && row.day() != null && row.forcedWinner() != null && row.finalized() != null && row.processing() != null;
    }
    private static boolean thresholdRequired(Occurrence row) { return Objects.equals(row.phase(), 0) && Objects.equals(row.forcedWinner(), -1); }
    private static boolean derive(Occurrence row, Manager manager) {
        Active active = active(row);
        if (!row.sameQueryArmySelectionMatched() || !active.ready()) return false;
        if (Boolean.FALSE.equals(active.active())) return true;
        return row.actualArmyId() != null && ownerReady(row) && managerReady(manager) && row.selectedCombatFullId() != null
                && sideReady(row.attackerSide(), row) && sideReady(row.defenderSide(), row) && phaseReady(row)
                && (!thresholdRequired(row) || row.maneuverThreshold() != null);
    }
    private static void side(Side side, Occurrence row) {
        roster(side.armies());
        Boolean comparison = row.selectedCharacterId() == null || side.primary() == null ? null
                : Objects.equals(row.selectedCharacterId(), side.primary());
        require(side.matchingArmyIndices().equals(matches(side.armies(), row.actualArmyId()))
                && side.matchingMembershipReady() == (row.actualArmyId() != null && rosterReady(side.armies()))
                && Objects.equals(side.ownerMatchesPrimary(), comparison), "side full-DWORD membership/owner association differs");
        Boolean parent = side.parentIdentity() == null ? null : Objects.equals(side.parentIdentity(), row.combatResolution().objectIdentity());
        require(Objects.equals(side.parentMatchesSelectedCombat(), parent), "side parent differs from physical selected Combat");
        require(side.sideInputsReady() == sideReady(side, row), "side readiness differs");
        state(side.state(), sideReady(side, row));
    }
    public static void validate(Inputs value) {
        Objects.requireNonNull(value);
        rawReferences(value.originalRoster());
        Manager manager = value.combatManager();
        roster(manager.roster());
        require(manager.managerInputsReady() == managerReady(manager), "manager readiness differs");
        state(manager.state(), managerReady(manager));
        require(value.occurrences().size() == value.originalRoster().occurrences().size(), "filtered original Army occurrences");
        for (int i = 0; i < value.occurrences().size(); i++) {
            Occurrence row = value.occurrences().get(i); RawOccurrence original = value.originalRoster().occurrences().get(i);
            require(row.nativeIndex() == original.nativeIndex() && Objects.equals(row.rawFullId(), original.rawFullId()),
                    "filtered/relabelled original Army occurrence");
            resolution(row.originalArmyResolution(), row.rawFullId(), true);
            resolution(row.combatResolution(), row.armyCombatId(), false);
            resolution(row.unitResolution(), row.armyUnitId(), false);
            resolution(row.characterResolution(), row.unitOwnerId(), false);
            Active active = active(row);
            require(row.activeCombatInputsReady() == active.ready() && Objects.equals(row.sourceActiveCombat(), active.active()),
                    "active Combat tag/full-ID association differs");
            require(row.combatMagic() == null || row.combatMagic() == 0x436f6d62L || row.selectedCombatFullId() == null,
                    "wrong Combat tag relabelled undemanded validity ID");
            require(row.currentCombatRolesPhaseInputsReady() == derive(row, manager), "role/phase readiness differs");
            state(row.state(), derive(row, manager));
            require(row.ownerInputsReady() == ownerReady(row), "owner selection readiness differs");
            side(row.attackerSide(), row); side(row.defenderSide(), row);
            boolean reached = active.ready() && Boolean.TRUE.equals(active.active());
            require(row.managerMatchIndices().equals(reached ? matches(manager.roster(), row.selectedCombatFullId()) : List.of())
                    && row.combatManagerMembershipReady() == (reached && managerReady(manager)), "manager full-DWORD occurrences differ");
            boolean threshold = reached && thresholdRequired(row);
            require(row.phaseInputsReady() == (reached && phaseReady(row)) && row.thresholdRequired() == threshold
                    && row.thresholdInputsReady() == (reached && (!threshold || row.maneuverThreshold() != null)),
                    "phase/threshold demand differs");
            require(threshold || row.maneuverThreshold() == null, "undemanded threshold present");
            require(reached || row.actualArmyId() == null && row.armyUnitId() == null && row.unitOwnerId() == null
                    && row.selectedCharacterId() == null && row.phase() == null && row.day() == null && row.forcedWinner() == null
                    && row.finalized() == null && row.processing() == null && row.maneuverThreshold() == null
                    && undemanded(row.unitResolution()) && undemanded(row.characterResolution()),
                    "inactive/unknown Combat relabelled undemanded owner/phase inputs");
        }
        RawReferences references = value.originalRoster();
        boolean covered = references.referencesReady() && references.count() != null && references.count() >= 0
                && value.occurrences().size() == references.count();
        boolean selected = covered && value.occurrences().stream().allMatch(Occurrence::sameQueryArmySelectionMatched);
        boolean ready = selected && value.occurrences().stream().allMatch(row -> derive(row, manager));
        require(value.rawRosterReferencesReady() == references.referencesReady() && value.originalArmySelectionsReady() == selected
                && value.currentCombatRolesPhaseInputsReady() == ready, "family readiness differs from original Army occurrences");
        state(value.state(), ready);
    }
    private static PhaseSelector selector(Occurrence row) {
        if (!row.phaseInputsReady() || !row.thresholdInputsReady()) return new PhaseSelector(false, null, null, null, null, null);
        int nextDay = row.day() + 1; // Defined Java int wrap is the source signed-DWORD wrap.
        int phase = row.phase(), day = nextDay; Worker worker = null; Decision decision;
        if (phase == 0 && row.forcedWinner() != -1) { phase = 1; day = 0; worker = Worker.MAIN; decision = Decision.FORCED_MAIN; }
        else if (phase == 0 && nextDay > row.maneuverThreshold()) { phase = 1; day = 0; decision = Decision.DURATION_MAIN_WITHOUT_WORKER; }
        else if (phase == 0) decision = Decision.MANEUVER_WAIT;
        else if (phase == 1) { worker = Worker.MAIN; decision = Decision.MAIN_WORKER; }
        else if (phase == 2) { worker = Worker.PURSUIT; decision = Decision.PURSUIT_WORKER; }
        else decision = Decision.OTHER_PHASE_WITHOUT_WORKER;
        return new PhaseSelector(true, decision, worker, nextDay, phase, day);
    }
    public static Projection project(Inputs value, Provenance provenance) {
        if (value == null) return new Projection(null, provenance, Status.UNAVAILABLE, false,
                "current_army_combat_roles_phase_inputs_unavailable", List.of());
        validate(value);
        List<ProjectedOccurrence> rows = new ArrayList<>();
        for (Occurrence row : value.occurrences()) {
            Membership membership = null;
            if (row.attackerSide().matchingMembershipReady() && row.defenderSide().matchingMembershipReady()) {
                boolean a = !row.attackerSide().matchingArmyIndices().isEmpty(), d = !row.defenderSide().matchingArmyIndices().isEmpty();
                membership = a && d ? Membership.BOTH : a ? Membership.ATTACKER : d ? Membership.DEFENDER : Membership.NEITHER;
            }
            PhaseLabel label = row.phase() == null ? null : switch (row.phase()) {
                case 0 -> PhaseLabel.MANEUVER; case 1 -> PhaseLabel.MAIN; case 2 -> PhaseLabel.PURSUIT;
                case 3 -> PhaseLabel.DONE; default -> PhaseLabel.UNRESOLVED;
            };
            rows.add(new ProjectedOccurrence(row, derive(row, value.combatManager()), membership, label, selector(row)));
        }
        boolean ready = value.currentCombatRolesPhaseInputsReady();
        return new Projection(value, provenance, value.state().status(), ready, ready ? null : value.state().unavailableReason(), rows);
    }
}
