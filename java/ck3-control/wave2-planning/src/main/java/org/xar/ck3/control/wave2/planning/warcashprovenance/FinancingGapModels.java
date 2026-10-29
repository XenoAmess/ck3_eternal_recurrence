package org.xar.ck3.control.wave2.planning.warcashprovenance;

import org.xar.ck3.control.contracts.StrictJson;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Values projected from current inputs, without action or cash-source eligibility. */
public final class FinancingGapModels {
    private FinancingGapModels() { }

    /** Distinct from map SavedFrame: the original observed snapshot ID is opaque. */
    public record ObservedFrame(BigInteger playedCharacterId, BigInteger nativeRevision,
                                BigInteger dateRaw, String snapshotId, BigInteger revision,
                                String episodeRunId) {
        public ObservedFrame {
            positive(playedCharacterId, "played_character_id");
            positive(nativeRevision, "native_revision");
            nonnegative(dateRaw, "date_raw");
            positive(revision, "revision");
            StrictJson.text(snapshotId);
            StrictJson.text(episodeRunId);
        }
    }

    public record PriorityWar(BigInteger warId, boolean primaryPlayerWar,
                              Optional<BigInteger> playerRelativeWarScore,
                              boolean raisedForceDeficit, boolean objectiveOccupationObserved,
                              boolean hostileSubrealmSiegeObserved, boolean allOwnArmiesRetreating) {
        public PriorityWar {
            Objects.requireNonNull(warId, "warId");
            Objects.requireNonNull(playerRelativeWarScore, "playerRelativeWarScore");
        }
        public boolean crisis() {
            return primaryPlayerWar && playerRelativeWarScore.filter(score -> score.compareTo(BigInteger.valueOf(-25)) <= 0).isPresent()
                    && (raisedForceDeficit || objectiveOccupationObserved || hostileSubrealmSiegeObserved || allOwnArmiesRetreating);
        }
    }

    /** The codec derives maintenance from the actual root identity, never a supplied GREEN flag. */
    public record Input(ObservedFrame frame, Set<BigInteger> activeWarIds, List<PriorityWar> priorityWars,
                        Optional<BigInteger> treasuryRaw, Optional<BigInteger> currentMaximumMaintenanceRaw,
                        boolean constructionIntentPresent, Optional<Boolean> confirmCapabilityAdvertised) {
        public Input {
            Objects.requireNonNull(frame, "frame");
            activeWarIds = Set.copyOf(activeWarIds);
            priorityWars = List.copyOf(priorityWars);
            Objects.requireNonNull(treasuryRaw, "treasuryRaw");
            Objects.requireNonNull(currentMaximumMaintenanceRaw, "currentMaximumMaintenanceRaw");
            currentMaximumMaintenanceRaw.ifPresent(value -> nonnegative(value, "maintenance raw"));
            Objects.requireNonNull(confirmCapabilityAdvertised, "confirmCapabilityAdvertised");
        }
    }

    public enum MaintenanceStatus {
        SAME_FRAME_OBSERVED("same_frame_observed"), UNOBSERVED("unobserved");
        private final String wire;
        MaintenanceStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Gap(ObservedFrame sourceFrame, List<BigInteger> crisisWarIds,
                      Optional<BigInteger> observedTreasuryRaw, Optional<BigInteger> ordinaryMilitaryBufferRaw,
                      MaintenanceStatus maximumMilitaryMaintenanceStatus, boolean constructionIntentPresent,
                      Optional<Boolean> confirmCapabilityAdvertised) {
        public Gap {
            Objects.requireNonNull(sourceFrame, "sourceFrame");
            crisisWarIds = List.copyOf(crisisWarIds);
            Objects.requireNonNull(observedTreasuryRaw, "observedTreasuryRaw");
            Objects.requireNonNull(ordinaryMilitaryBufferRaw, "ordinaryMilitaryBufferRaw");
            ordinaryMilitaryBufferRaw.ifPresent(value -> nonnegative(value, "ordinary military buffer"));
            Objects.requireNonNull(maximumMilitaryMaintenanceStatus, "maximumMilitaryMaintenanceStatus");
            Objects.requireNonNull(confirmCapabilityAdvertised, "confirmCapabilityAdvertised");
            if (ordinaryMilitaryBufferRaw.isPresent() != (maximumMilitaryMaintenanceStatus == MaintenanceStatus.SAME_FRAME_OBSERVED)) {
                throw new IllegalArgumentException("maintenance observation branch differs");
            }
        }
    }

    private static void positive(BigInteger value, String name) {
        if (value == null || value.signum() <= 0) { throw new IllegalArgumentException(name + " must be positive"); }
    }
    private static void nonnegative(BigInteger value, String name) {
        if (value == null || value.signum() < 0) { throw new IllegalArgumentException(name + " must be nonnegative"); }
    }
}
