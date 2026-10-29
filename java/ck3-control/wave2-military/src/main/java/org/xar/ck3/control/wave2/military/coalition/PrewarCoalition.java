package org.xar.ck3.control.wave2.military.coalition;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Same-frame current inventory evidence. This domain never submits a declaration. */
public final class PrewarCoalition {
    public static final String INVENTORY_SCOPE = "same_frame_owned_current_inventory_v1";
    public static final String FINAL_ROLES_SOURCE = "finalized_selected_cb_context";
    public static final String MOBILIZATION_SOURCE = "actual4_raise_command_final_validator_and_owned_current_rosters";
    public static final String COMPONENT_COMBINATION = "maximum_proven_component";
    public static final String ASSUMPTION = "policy_margin_not_calibrated_probability";
    public static final String DEFAULT_POLICY_ID = "prewar-current-inventory-force-risk-3-to-2-v1";
    public static final Policy DEFAULT_POLICY = new Policy(DEFAULT_POLICY_ID, 3, 2);

    private PrewarCoalition() { }

    public enum ObservationStatus {
        PARTIAL("partial"), AVAILABLE("available");
        private final String wire;
        ObservationStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum RiskStatus {
        UNKNOWN("unknown"), QUALIFIED("qualified"), RISK_REJECTED("risk_rejected");
        private final String wire;
        RiskStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum RiskReason {
        EVIDENCE_UNAVAILABLE("required_current_inventory_evidence_unavailable"),
        MARGIN_PASSED("complete_current_inventory_force_margin_passed"),
        ZERO_ACTOR_FLOOR("actor_current_inventory_floor_is_zero"),
        MARGIN_INSUFFICIENT("complete_current_inventory_force_margin_insufficient");
        private final String wire;
        RiskReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum MissingDomain {
        TWO_ROUND("same_frame_two_round_observation"), FINAL_ROLES("final_cb_roles"),
        PARTICIPANTS("potential_enemy_participants"), CURRENT_ALLIES("potential_enemy_current_allies"),
        HOLY_JOINERS("potential_enemy_holy_joiners"), ADDITIONAL_SUPPORTERS("potential_enemy_additional_supporters"),
        SELECTED_CB_INITIAL("selected_cb_initial_participants"), ACTOR_LOWER("actor_current_inventory_lower"),
        ENEMY_UPPER("enemy_current_inventory_upper"), ENEMY_OVERFLOW("enemy_upper_aggregate_overflow"),
        MOBILIZATION("native_mobilization_qualification");
        private final String wire;
        MissingDomain(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static MissingDomain fromWire(String wire) {
            for (MissingDomain value : values()) if (value.wire.equals(wire)) return value;
            throw new ProjectionDomainRejection("unknown prewar missing domain: " + wire);
        }
    }

    public enum ParticipantSource {
        PRIMARY_DEFENDER("primary_defender"), CURRENT_ALLY("current_ally"), HOLY_WAR_JOINER("holy_war_joiner"),
        CONTRACT_SUBJECT("contract_subject"), CONTRACT_SUZERAIN("contract_suzerain"),
        CONFEDERATION_MEMBER("confederation_member"), SAME_HOUSE("same_house"), IMMEDIATE_LIEGE("immediate_liege"),
        TOP_LIEGE("top_liege"), DIARCH("diarch"), RELIGIOUS_AUTHORITY("religious_authority"),
        RELIGIOUS_FOLLOWER("religious_follower"), FORCED_INITIAL_PARTICIPANT("forced_initial_participant");
        private final String wire;
        ParticipantSource(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static ParticipantSource fromWire(String wire) {
            for (ParticipantSource value : values()) if (value.wire.equals(wire)) return value;
            throw new ProjectionDomainRejection("unknown prewar participant source: " + wire);
        }
    }

    public record SelectedDeclaration(int targetCharacterId, int casusBelliIndex, String casusBelliKey,
                                      int configurationIndex, int claimantCharacterId, List<Integer> targetTitleIds) {
        public SelectedDeclaration {
            Objects.requireNonNull(casusBelliKey);
            targetTitleIds = List.copyOf(targetTitleIds);
        }
    }

    public record TwoRoundObservation(boolean completeDtoEqual, boolean frameBindingEqual, String unavailableReason) {
        public boolean ready() { return completeDtoEqual && frameBindingEqual; }
    }

    public record FinalCbRoles(boolean available, String unavailableReason, Integer primaryAttackerCharacterId,
                               Integer primaryDefenderCharacterId, Boolean nativeFallback, Boolean finalCanSend) { }

    public record Participant(int characterId, List<ParticipantSource> sources) {
        public Participant { sources = List.copyOf(sources); }
    }

    public record PotentialEnemyParticipants(boolean available, String unavailableReason, boolean collectionComplete,
                                             List<Participant> participants, boolean currentAlliesComplete,
                                             boolean holyJoinersComplete, boolean additionalSupportersComplete,
                                             boolean selectedCbInitialComplete) {
        public PotentialEnemyParticipants { participants = List.copyOf(participants); }
    }

    public record OwnerForce(int ownerCharacterId, Long actorLowerSoldiers, boolean actorLowerReady,
                             Long inventoryUpperSoldiers, boolean inventoryUpperReady, List<String> unavailableReasons) {
        public OwnerForce { unavailableReasons = List.copyOf(unavailableReasons); }
    }

    public record Mobilization(boolean available, String unavailableReason, Boolean nativeRaiseLegal,
                               Integer defaultRaiseProvinceId, Long unraisedLowerSoldiers, boolean unraisedLowerReady,
                               Long raisedCommandableLowerSoldiers, boolean raisedLowerReady,
                               Long executableLowerSoldiers, boolean executableLowerReady,
                               Long physicalInventoryLowerSoldiers, Integer nativeUnraisedStockSoldiers,
                               boolean nativeUnraisedStockReady) { }

    public record Observation(ObservationStatus status, String gameVersion, String executableSha256,
                              BigInteger captureEpoch, BigInteger nativeRevision, BigInteger publicRevision,
                              int dateRaw, int actorCharacterId, String declarationId,
                              SelectedDeclaration selectedDeclaration, Integer effectiveTargetCharacterId,
                              BigInteger ticket, BigInteger querySequence, TwoRoundObservation twoRoundObservation,
                              FinalCbRoles finalCbRoles, PotentialEnemyParticipants potentialEnemyParticipants,
                              List<OwnerForce> ownerForces, Long actorLowerSoldiers, Long enemyUpperSoldiers,
                              boolean enemyForceCoverageComplete, boolean completeInitialParticipantsReady,
                              List<MissingDomain> missingRequiredDomains, Mobilization nativeMobilizationQualification) {
        public Observation {
            Objects.requireNonNull(status); Objects.requireNonNull(selectedDeclaration);
            Objects.requireNonNull(twoRoundObservation); Objects.requireNonNull(finalCbRoles);
            Objects.requireNonNull(potentialEnemyParticipants); Objects.requireNonNull(nativeMobilizationQualification);
            ownerForces = List.copyOf(ownerForces);
            missingRequiredDomains = List.copyOf(missingRequiredDomains);
        }
    }

    public record Policy(String policyId, long minimumActorToEnemyRatioNumerator,
                         long minimumActorToEnemyRatioDenominator) {
        public Policy {
            if (policyId == null || policyId.isEmpty() || !policyId.equals(stripPython(policyId))
                    || minimumActorToEnemyRatioNumerator < 1 || minimumActorToEnemyRatioDenominator < 1) {
                throw new ProjectionDomainRejection("nonempty policy ID and positive int64 margin required");
            }
            if (policyId.equals(DEFAULT_POLICY_ID)
                    && (minimumActorToEnemyRatioNumerator != 3 || minimumActorToEnemyRatioDenominator != 2)) {
                throw new ProjectionDomainRejection("changed prewar margin requires a distinct policy ID");
            }
        }
    }

    public record RiskResult(RiskStatus status, boolean forceRiskQualified, RiskReason reason, Policy policy,
                             Long actorLowerSoldiers, Long enemyUpperSoldiers, List<MissingDomain> missingRequiredDomains) {
        public RiskResult { missingRequiredDomains = List.copyOf(missingRequiredDomains); }
    }

    static String stripPython(String value) {
        int first = 0;
        int last = value.length();
        while (first < last && pythonWhitespace(value.codePointAt(first))) first += Character.charCount(value.codePointAt(first));
        while (last > first && pythonWhitespace(value.codePointBefore(last))) last -= Character.charCount(value.codePointBefore(last));
        return value.substring(first, last);
    }

    private static boolean pythonWhitespace(int codePoint) {
        return Character.isWhitespace(codePoint) || codePoint == 0x85 || codePoint == 0xa0
                || codePoint == 0x2007 || codePoint == 0x202f;
    }

    /** Called only after the strict adapter has revalidated the full observation and independent bindings. */
    static RiskResult assessValidated(Observation observation, Policy policy) {
        Long lower = observation.actorLowerSoldiers();
        Long upper = observation.enemyUpperSoldiers();
        List<MissingDomain> missing = observation.missingRequiredDomains();
        if (!missing.isEmpty()) return new RiskResult(RiskStatus.UNKNOWN, false,
                RiskReason.EVIDENCE_UNAVAILABLE, policy, lower, upper, missing);
        Objects.requireNonNull(lower); Objects.requireNonNull(upper);
        boolean qualified = lower > 0 && BigInteger.valueOf(lower)
                .multiply(BigInteger.valueOf(policy.minimumActorToEnemyRatioDenominator()))
                .compareTo(BigInteger.valueOf(upper)
                        .multiply(BigInteger.valueOf(policy.minimumActorToEnemyRatioNumerator()))) >= 0;
        return new RiskResult(qualified ? RiskStatus.QUALIFIED : RiskStatus.RISK_REJECTED, qualified,
                qualified ? RiskReason.MARGIN_PASSED : lower == 0 ? RiskReason.ZERO_ACTOR_FLOOR
                        : RiskReason.MARGIN_INSUFFICIENT, policy, lower, upper, missing);
    }
}
