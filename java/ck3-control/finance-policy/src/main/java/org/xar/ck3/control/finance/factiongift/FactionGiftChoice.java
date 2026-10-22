package org.xar.ck3.control.finance.factiongift;

import java.math.BigInteger;
import java.util.Objects;

/** A proposed choice only. This type neither authorizes nor submits a gift. */
public sealed interface FactionGiftChoice permits FactionGiftChoice.Selected, FactionGiftChoice.Declined {
    Status status();

    Reason reason();

    enum Status {
        SELECTED("selected"), UNAVAILABLE("unavailable"),
        NO_LEGAL_CANDIDATE("no_legal_candidate"), BUDGET_REJECT("budget_reject");

        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    enum Reason {
        SELECTED("one_budgeted_native_legal_faction_member", Status.SELECTED),
        ENUMERATION_OR_RESERVE_UNPROVEN("enumeration_or_reserve_unproven", Status.UNAVAILABLE),
        COMPLETE_NATIVE_EMPTY("complete_native_empty", Status.NO_LEGAL_CANDIDATE),
        MALFORMED_NATIVE_OBSERVATION("malformed_native_observation", Status.UNAVAILABLE),
        NATIVE_OBSERVATION_INCOMPLETE("native_observation_incomplete", Status.UNAVAILABLE),
        NATIVE_IDENTITY_OR_METRIC_UNAVAILABLE("native_identity_or_metric_unavailable", Status.UNAVAILABLE),
        CANDIDATE_FRAME_DRIFT("candidate_frame_drift", Status.UNAVAILABLE),
        FACTION_MEMBERSHIP_UNAVAILABLE("faction_membership_unavailable", Status.UNAVAILABLE),
        FACTION_OR_RECIPIENT_STATE_UNAVAILABLE("faction_or_recipient_state_unavailable", Status.UNAVAILABLE),
        GIFT_PREVIEW_UNAVAILABLE("gift_preview_unavailable", Status.UNAVAILABLE),
        GIFT_LEGALITY_UNAVAILABLE("gift_legality_unavailable", Status.UNAVAILABLE),
        GIFT_DEFINITION_UNAVAILABLE("gift_definition_unavailable", Status.UNAVAILABLE),
        GIFT_VALUE_UNAVAILABLE("gift_value_unavailable", Status.UNAVAILABLE),
        GOLD_RESERVE_NOT_SATISFIED("gold_reserve_not_satisfied", Status.BUDGET_REJECT),
        COMPLETE_NATIVE_NO_LEGAL_MEMBER("complete_native_no_legal_member", Status.NO_LEGAL_CANDIDATE);

        private final String wire;
        private final Status status;
        Reason(String wire, Status status) { this.wire = wire; this.status = status; }
        public String wire() { return wire; }
        public Status status() { return status; }
    }

    enum MembershipRole {
        LEADER("leader"), CHARACTER_MEMBER("character_member");
        private final String wire;
        MembershipRole(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    record Selected(BigInteger sourceFactionId, BigInteger recipientCharacterId,
                    MembershipRole membershipRole, BigInteger snapshotRevision,
                    BigInteger nativeSnapshotRevision, BigInteger dateRaw,
                    BigInteger playerCharacterId, BigInteger definitionStableHash,
                    BigInteger goldCostRaw, BigInteger opinionDelta) implements FactionGiftChoice {
        public Selected {
            positive(sourceFactionId, "sourceFactionId");
            positive(recipientCharacterId, "recipientCharacterId");
            Objects.requireNonNull(membershipRole, "membershipRole");
            positive(snapshotRevision, "snapshotRevision");
            positive(nativeSnapshotRevision, "nativeSnapshotRevision");
            Objects.requireNonNull(dateRaw, "dateRaw");
            positive(playerCharacterId, "playerCharacterId");
            positive(definitionStableHash, "definitionStableHash");
            positive(goldCostRaw, "goldCostRaw");
            positive(opinionDelta, "opinionDelta");
        }
        @Override public Status status() { return Status.SELECTED; }
        @Override public Reason reason() { return Reason.SELECTED; }
    }

    record Declined(Reason reason) implements FactionGiftChoice {
        public Declined {
            Objects.requireNonNull(reason, "reason");
            if (reason == Reason.SELECTED) {
                throw new IllegalArgumentException("selected requires a complete Selected value");
            }
        }
        @Override public Status status() { return reason.status(); }
    }

    private static void positive(BigInteger value, String field) {
        if (Objects.requireNonNull(value, field).signum() <= 0) {
            throw new IllegalArgumentException(field + " must be positive");
        }
    }
}
