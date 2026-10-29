package org.xar.ck3.control.wave2.planning.scoretarget;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/** Pure active consumer stage: listed proof, precise world fallback, then metric delta. */
public final class RebellionMetricAdapter {
    private RebellionMetricAdapter() { }

    public static RebellionMetricDelta project(SavedWarScan scan) {
        PlayerWarDefenceResult listed = PlayerWarDefence.project(scan.player());
        RebellionMetricDelta.WarScope scope = new RebellionMetricDelta.ListedScope(listed, scan.sourceRef());
        Optional<Boolean> own = listed instanceof PlayerWarDefenceResult.Known known
                ? Optional.of(known.ownDefence()) : Optional.empty();
        String method = "player_landed_war_list";
        boolean noUnknownFields = scan.unknownKeyFields().signum() == 0;
        if (listed instanceof PlayerWarDefenceResult.Unknown unknown
                && unknown.reason() == PlayerWarDefenceResult.Reason.MISSING_LIST
                && noUnknownFields && !scan.warContainers().isEmpty() && !scan.warLayoutUnknown()) {
            Optional<List<BigInteger>> defenders = allWorldDefenders(scan.player());
            if (defenders.isPresent()) {
                boolean defending = defenders.orElseThrow().stream().anyMatch(scan.player().actor()::equals);
                own = Optional.of(defending);
                scope = new RebellionMetricDelta.WorldScope(defending, scan.sourceRef());
                method = "independent_complete_world_war_roster";
            }
        }
        RebellionMetricDelta.Update update = new RebellionMetricDelta.Unchanged();
        if (noUnknownFields && own.isPresent()) {
            update = own.orElseThrow() ? new RebellionMetricDelta.UnknownControl(scan.sourceRef())
                    : new RebellionMetricDelta.ObservedNoRebellion(scan.sourceRef(),
                            method + ": player is no CB defender; anti-liege war excluded");
        }
        return new RebellionMetricDelta(scope, update);
    }

    private static Optional<List<BigInteger>> allWorldDefenders(PlayerWarInput input) {
        List<BigInteger> result = new ArrayList<>();
        for (PlayerWarInput.WarEntry entry : input.wars().values()) {
            if (!(entry instanceof PlayerWarInput.ObservedWar war) || war.conflictingDefender()
                    || !(war.defender() instanceof ScalarField.Text text)) { return Optional.empty(); }
            Optional<BigInteger> defender = war.defender().integer();
            if (defender.isEmpty()) { return Optional.empty(); }
            result.add(defender.orElseThrow());
        }
        return Optional.of(List.copyOf(result));
    }
}
