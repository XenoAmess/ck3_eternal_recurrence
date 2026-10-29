package org.xar.ck3.control.wave2.planning.warcashprovenance;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;

import static org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapModels.*;

/** Existing financing diagnostic only: it neither queues a loan/cancel nor credits funding. */
public final class WarFinancingCapabilityGap {
    private static final BigInteger FIXED_BUFFER = BigInteger.valueOf(20_000_000);
    private static final BigInteger MAINTENANCE_MONTHS = BigInteger.valueOf(18);
    private WarFinancingCapabilityGap() { }

    public static Optional<Gap> observe(Input input) {
        List<PriorityWar> current = input.priorityWars().stream()
                .filter(war -> input.activeWarIds().contains(war.warId())).toList();
        if (current.isEmpty()) { return Optional.empty(); }
        List<BigInteger> crisis = current.stream().filter(PriorityWar::crisis).map(PriorityWar::warId).toList();
        Optional<BigInteger> normal = input.currentMaximumMaintenanceRaw()
                .map(rate -> FIXED_BUFFER.max(rate.multiply(MAINTENANCE_MONTHS)));
        boolean shortfall = input.treasuryRaw().filter(cash -> cash.compareTo(normal.orElse(FIXED_BUFFER)) < 0).isPresent();
        if (crisis.isEmpty() && !shortfall) { return Optional.empty(); }
        return Optional.of(new Gap(input.frame(), crisis, input.treasuryRaw(), normal,
                normal.isPresent() ? MaintenanceStatus.SAME_FRAME_OBSERVED : MaintenanceStatus.UNOBSERVED,
                input.constructionIntentPresent(), input.confirmCapabilityAdvertised()));
    }
}
