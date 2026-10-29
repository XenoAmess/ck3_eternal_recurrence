package org.xar.ck3.control.wave3.governance.betrothalvalue;

import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Observed inputs and pure values only; these records carry no submission authority. */
public final class BetrothalValueModel {
    private BetrothalValueModel() { }
    public enum NativeStatus {
        AVAILABLE("available"), UNAVAILABLE("unavailable"), NOT_APPLICABLE("not_applicable");
        private final String wire;
        NativeStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ChoiceStatus { SELECTED, HELD }
    public enum Reason {
        CURRENT_PAIR_UNAVAILABLE("current_pair_unavailable"),
        NO_CURRENT_BILATERAL_BETROTHAL("no_current_bilateral_betrothal"),
        CURRENT_HEIR_ALREADY_MARRIED("current_heir_already_married"),
        CURRENT_PAIR_VALUE_UNKNOWN("current_pair_value_unknown"),
        ACTUAL_PAIR_NOT_READY("actual_pair_not_ready"),
        NATIVE_FINAL_CAN_SEND_NOT_TRUE("native_final_can_send_not_true"),
        NATIVE_RECIPIENT_NOT_POSITIVE("native_recipient_not_positive"),
        NATIVE_OUTCOME_NOT_MARRIAGE("native_outcome_not_marriage"),
        NONZERO_OR_UNKNOWN_SEND_COST_REQUIRES_JOINT_BUDGET("nonzero_or_unknown_send_cost_requires_joint_budget");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ExactBuild {
        CK3_11906("1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),
        CK3_12002("1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"),
        CK3_12003("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CK3_12004("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        private final String version;
        private final String sha256;
        ExactBuild(String version, String sha256) { this.version = version; this.sha256 = sha256; }
        public String version() { return version; }
        public String sha256() { return sha256; }
    }
    public record PlayedCharacter(BigInteger characterId, Boolean alive) { }
    /** Nullable members are unknown; the immutable original retains missing versus explicit null. */
    public record Snapshot(Boolean paused, Boolean mapReady, PlayedCharacter played,
                           BigInteger nativeRevision, BigInteger dateRaw, String episodeRunId,
                           ObjectValue original, Frame proposalFrame) {
        public Snapshot { Objects.requireNonNull(original); Objects.requireNonNull(proposalFrame); }
    }
    public record Relationship(String schema, String status, Boolean readOnly, Boolean advertised,
                               BigInteger nativeRevision, BigInteger heir, BigInteger partner,
                               BigInteger primarySpouse, Field<List<BigInteger>> spouses,
                               Boolean bilateralVerified, WireValue actionability,
                               String exactBuild, String executableSha256, Relation proposalProjection, ObjectValue original) {
        public Relationship {
            Objects.requireNonNull(spouses); Objects.requireNonNull(actionability); Objects.requireNonNull(proposalProjection);
            Objects.requireNonNull(original);
            if (spouses.presence() == Presence.VALUE) { spouses = Field.of(List.copyOf(spouses.value())); }
        }
    }
    public record EvaluationInput(Snapshot snapshot, Relationship relationship) {
        public EvaluationInput { Objects.requireNonNull(snapshot); Objects.requireNonNull(relationship); }
    }
    public record AdultReadback(boolean available, Boolean heirAdult, Boolean partnerAdult,
                                BigInteger heirMeasure, BigInteger partnerMeasure,
                                BigInteger heirThreshold, BigInteger partnerThreshold, Boolean ready) { }
    public record LegalityReadback(boolean sampled, Boolean completeCanSend) { }
    public record RecipientReadback(boolean ready, BigInteger acceptanceRaw, BigInteger answerStatusRaw) { }
    public record ChildHousePreview(NativeStatus status, String reason, BigInteger subject,
                                    BigInteger candidate, Boolean selected, Boolean effective,
                                    Boolean completeCanSend, BigInteger selectedParent,
                                    BigInteger houseId, BigInteger dynastyId, ObjectValue original) {
        public ChildHousePreview { Objects.requireNonNull(status); Objects.requireNonNull(reason); Objects.requireNonNull(original); }
    }
    public record ValidatedActionability(NativeStatus status, String unavailableReason,
                                         AdultReadback adult, LegalityReadback legality,
                                         RecipientReadback recipient, ChildHousePreview preview,
                                         Actionability projection, ObjectValue original) {
        public ValidatedActionability {
            Objects.requireNonNull(status); Objects.requireNonNull(adult); Objects.requireNonNull(legality);
            Objects.requireNonNull(recipient); Objects.requireNonNull(projection); Objects.requireNonNull(original);
        }
    }
    public record Choice(ChoiceStatus status, List<Reason> reasons, BigInteger heir, BigInteger partner,
                         ValidatedActionability value, WireValue descendants, WireValue descendantsSummary,
                         ResourceProposal resourceProposal) {
        public Choice {
            Objects.requireNonNull(status); reasons = List.copyOf(reasons); Objects.requireNonNull(value);
            Objects.requireNonNull(descendants); Objects.requireNonNull(descendantsSummary); Objects.requireNonNull(resourceProposal);
            if ((status == ChoiceStatus.SELECTED) != reasons.isEmpty()) { throw new IllegalArgumentException("choice/reason mismatch"); }
        }
    }
}
