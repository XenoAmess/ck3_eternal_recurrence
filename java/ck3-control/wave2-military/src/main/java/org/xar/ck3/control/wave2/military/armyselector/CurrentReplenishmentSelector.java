package org.xar.ck3.control.wave2.military.armyselector;

import static org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.*;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;

/** Select by observed strength first; conditional current refill only breaks stationary ties. */
public final class CurrentReplenishmentSelector {
    private CurrentReplenishmentSelector() {}
    public static Selection select(Input input) {
        List<Long> wars = input.activeWarIds().stream().filter(id -> id > 0).distinct().sorted().toList();
        if (input.armies().isEmpty()) return new Selection(null, SelectionStatus.NOT_APPLICABLE, wars, false, List.of());
        int strongest = input.armies().stream().mapToInt(CurrentReplenishmentSelector::soldiers).max().orElseThrow();
        List<Army> tied = input.armies().stream().filter(army -> soldiers(army) == strongest).sorted(Comparator.comparingInt(Army::armyId)).toList();
        Army selected = tied.getFirst();
        if (wars.isEmpty() || strongest < 0 || tied.size() < 2 || tied.stream().anyMatch(army -> !stationary(army))
                || tied.stream().map(Army::currentProvinceId).distinct().count() != tied.size()) {
            return new Selection(selected, SelectionStatus.NOT_APPLICABLE, wars, false, List.of());
        }
        Snapshot snapshot = input.snapshot();
        if (!Boolean.TRUE.equals(snapshot.paused())) return unavailable(selected, wars, false, List.of());
        if (snapshot.strengthsStatus().presence() != Presence.VALUE) return unavailable(selected, wars, true, List.of());
        if (!"available".equals(snapshot.strengthsStatus().value()) || snapshot.snapshotId() == null
                || !snapshot.snapshotId().equals(snapshot.queriedSnapshotId())
                || !Objects.equals(snapshot.revision(), snapshot.queriedRevision())
                || snapshot.strengths().presence() != Presence.VALUE) return unavailable(selected, wars, false, List.of());
        List<Candidate> candidates = new ArrayList<>();
        boolean complete = true;
        for (Army army : tied) {
            List<StrengthRow> matches = snapshot.strengths().value().stream().filter(row -> row.armyId() == army.armyId()).toList();
            Candidate receipt = new Candidate(army.armyId(), strongest, null, null, null, Slot.missing());
            if (matches.size() == 1) {
                StrengthRow row = matches.getFirst();
                if (row.status() == Coverage.AVAILABLE && "player".equals(row.scopeRole())
                        && Objects.equals(row.currentSoldiers(), strongest) && row.warIds() != null
                        && row.warIds().stream().anyMatch(wars::contains) && row.ordered() != null) {
                    Projection projection = OrderedRefill.project(row);
                    if (projection.orderedCoreReady() && projection.currentMaximumReady() && projection.conditionalCurrent() != null) {
                        long delta = (long) projection.conditionalCurrent() - strongest;
                        receipt = new Candidate(army.armyId(), strongest, projection.conditionalCurrent(), delta, Math.max(0, delta), Slot.missing());
                    } else receipt = new Candidate(army.armyId(), strongest, null, null, null, Slot.of(projection.missingInputs()));
                }
            }
            candidates.add(receipt); complete &= receipt.available();
        }
        if (!complete) return unavailable(selected, wars, false, candidates);
        Candidate chosen = candidates.stream().min(Comparator.comparing(Candidate::positiveOpportunity).thenComparingInt(Candidate::armyId)).orElseThrow();
        Army chosenArmy = tied.stream().filter(army -> army.armyId() == chosen.armyId()).findFirst().orElseThrow();
        return new Selection(chosenArmy, SelectionStatus.AVAILABLE, wars, false, candidates);
    }
    private static int soldiers(Army army) { return army.soldiers() == null ? -1 : army.soldiers(); }
    private static boolean stationary(Army army) {
        return "regular".equals(army.armyState()) && army.moveTargetProvinceId() == null
                && List.of().equals(army.routeProvinceIds()) && army.currentProvinceId() != null && army.currentProvinceId() > 0;
    }
    private static Selection unavailable(Army army, List<Long> wars, boolean query, List<Candidate> candidates) {
        return new Selection(army, SelectionStatus.CURRENT_INPUTS_UNAVAILABLE, wars, query, candidates);
    }
}
