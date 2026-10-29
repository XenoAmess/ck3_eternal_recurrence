package org.xar.ck3.control.wave3.planning.warpriorityfocus;

import java.math.BigInteger;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.warbudget.BudgetPoliticalStakesCodec;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;

/** Original cash-protection predicates and ordering, projected to the construction consumer's focus. */
public final class WarCashFocusProjection {
    private WarCashFocusProjection() { }

    public record FocusedWar(BigInteger warId, Optional<BigInteger> observedPlayerRaisedSoldiers,
                             Optional<BigInteger> observedEnemyRaisedSoldiers) {
        public FocusedWar {
            Objects.requireNonNull(warId, "warId");
            Objects.requireNonNull(observedPlayerRaisedSoldiers, "observedPlayerRaisedSoldiers");
            Objects.requireNonNull(observedEnemyRaisedSoldiers, "observedEnemyRaisedSoldiers");
            observedPlayerRaisedSoldiers.ifPresent(WarCashFocusProjection::nonnegative);
            observedEnemyRaisedSoldiers.ifPresent(WarCashFocusProjection::nonnegative);
        }
    }

    public static Optional<FocusedWar> observe(WarCashFocusProjectionCodec.Request request) {
        Objects.requireNonNull(request, "request");
        List<WarCashFocusProjectionCodec.ObservedWar> protectedWars = request.wars().stream()
                .filter(war -> protects(request, war)).sorted(Comparator
                        .comparing((WarCashFocusProjectionCodec.ObservedWar war) -> !war.primaryTitleTargeted())
                        .thenComparing(war -> !war.directHeldTargeted())
                        .thenComparing(war -> !war.defensiveTargetsExposed())
                        .thenComparing(war -> war.score().orElse(BigInteger.ZERO))
                        .thenComparing(WarCashFocusProjectionCodec.ObservedWar::warId)).toList();
        if (protectedWars.isEmpty()) { return Optional.empty(); }
        // The original consumer first selects the sorted ID, then the first original row with that ID.
        BigInteger identity = protectedWars.getFirst().warId();
        return request.wars().stream().filter(war -> war.warId().equals(identity)).findFirst()
                .map(war -> new FocusedWar(war.warId(), request.ownCount(), war.enemyCount()));
    }

    private static boolean protects(WarCashFocusProjectionCodec.Request request,
                                    WarCashFocusProjectionCodec.ObservedWar war) {
        boolean primary = war.primary();
        boolean losing = war.score().filter(score -> score.signum() < 0).isPresent();
        boolean deficit = request.ownCount().isPresent() && war.enemyCount().isPresent()
                && request.ownCount().orElseThrow().compareTo(war.enemyCount().orElseThrow()) < 0;
        boolean political = BudgetPoliticalStakesCodec.qualified(
                BudgetPoliticalStakesCodec.observe(request.politicalContext(), war.ordinal()));
        boolean nonleadingSiege = RealmSiegePolicy.warQualifies(request.realmSnapshot(), war.realmWar());
        return primary && losing && political
                || primary && losing && war.defensiveTargetsExposed()
                || primary && war.defender() && deficit && request.completeOwnRows() && war.completeEnemyRows()
                || primary && losing && deficit
                || primary && losing && request.primaryCount() > 1 && request.aggregateDeficit()
                || primary && war.hostileSiege()
                || nonleadingSiege
                || primary && request.allOwnRetreating()
                || primary && war.defender() && war.hostileObjectiveOccupation()
                || primary && war.score().filter(score -> score.compareTo(BigInteger.valueOf(-100)) <= 0).isPresent();
    }

    private static void nonnegative(BigInteger value) {
        if (value.signum() < 0) { throw new IllegalArgumentException("observed count cannot be negative"); }
    }
}
