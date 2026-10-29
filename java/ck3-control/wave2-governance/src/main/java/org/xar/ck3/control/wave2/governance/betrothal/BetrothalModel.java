package org.xar.ck3.control.wave2.governance.betrothal;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Immutable contracts for proposal construction; none of these objects grant action authority. */
public final class BetrothalModel {
    private BetrothalModel() { }

    public sealed interface WireValue permits NullValue, IntegerValue, DecimalValue, BooleanValue,
            TextValue, ArrayValue, ObjectValue { }
    public enum NullValue implements WireValue { INSTANCE }
    public record IntegerValue(BigInteger value) implements WireValue { public IntegerValue { Objects.requireNonNull(value); } }
    public record DecimalValue(BigDecimal value) implements WireValue {
        public DecimalValue {
            Objects.requireNonNull(value);
            value = value.stripTrailingZeros();
            // Integral decimal evidence must retain a floating token on the wire.
            // Negative scale already writes an exponent and must not be expanded.
            if (value.scale() == 0) { value = value.setScale(1); }
        }
    }
    public record BooleanValue(boolean value) implements WireValue { }
    public record TextValue(String value) implements WireValue { public TextValue { unicode(value); } }
    public record ArrayValue(List<WireValue> values) implements WireValue { public ArrayValue { values = List.copyOf(values); } }
    /** Explicit uninterpreted JSON evidence, never interpreted as readiness or provenance. */
    public record ObjectValue(Map<String, WireValue> values) implements WireValue {
        public ObjectValue { values = Map.copyOf(values); values.keySet().forEach(BetrothalModel::unicode); }
    }

    public enum Presence { MISSING, NULL, VALUE }
    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) { throw new IllegalArgumentException("field presence mismatch"); }
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nil() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
    }

    public record Frame(BigInteger playedCharacterId, BigInteger nativeRevision, BigInteger dateRaw,
                        String snapshotId, BigInteger revision, String episodeRunId) {
        public Frame {
            character(playedCharacterId); positive(playedCharacterId, "frame player"); positive(nativeRevision, "frame native revision");
            positive(revision, "frame revision"); Objects.requireNonNull(dateRaw);
            if (dateRaw.signum() < 0 || snapshotId == null || snapshotId.isEmpty()
                    || episodeRunId == null || episodeRunId.isEmpty()) { throw new IllegalArgumentException("M5 observed frame identity is incomplete"); }
        }
    }

    public record Roles(BigInteger actor, BigInteger heir, BigInteger partner,
                        BigInteger recipient, BigInteger intermediary) {
        public Roles { character(actor); character(heir); character(partner); character(recipient); character(intermediary); }
    }

    public enum CostTerm {
        GOLD("gold_raw"), PRESTIGE("prestige_raw"), PIETY("piety_raw"), RENOWN("renown_raw"),
        INFLUENCE("influence_raw"), HERD("herd_raw"), TREASURY("treasury_raw"),
        TREASURY_OR_GOLD("treasury_or_gold_raw"), MERIT("merit_raw"), BARTER_GOODS("barter_goods_raw");
        private final String wire;
        CostTerm(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record GenericCosts(Field<BigInteger> rawScale, Field<String> payerRole,
                               Field<String> applicationTiming, Map<CostTerm, Field<BigInteger>> amounts,
                               ObjectValue extensions) {
        public GenericCosts {
            Objects.requireNonNull(rawScale); Objects.requireNonNull(payerRole); Objects.requireNonNull(applicationTiming);
            java.util.EnumMap<CostTerm, Field<BigInteger>> normalized = new java.util.EnumMap<>(CostTerm.class);
            for (CostTerm term : CostTerm.values()) { normalized.put(term, amounts.getOrDefault(term, Field.missing())); }
            amounts = Map.copyOf(normalized); Objects.requireNonNull(extensions);
            if (extensions.values().containsKey("raw_scale") || extensions.values().containsKey("payer_role")
                    || extensions.values().containsKey("application_timing")) { throw new IllegalArgumentException("cost extension collides with contract"); }
            for (CostTerm term : CostTerm.values()) {
                if (extensions.values().containsKey(term.wire())) { throw new IllegalArgumentException("cost amount extension collision"); }
                Field<BigInteger> amount = amounts.get(term);
                if (amount != null && amount.value() != null && amount.value().bitLength() > 63) {
                    throw new IllegalArgumentException("native cost outside signed int64");
                }
            }
        }
    }

    public record Actionability(Roles roles, GenericCosts costs, Boolean readyToMarryBetrothed,
                                String predictedOutcomeIfAccepted, Boolean matrilinealOptionSelected,
                                WireValue nativeChildHousePreview, Boolean effectiveMatrilinealIfAccepted,
                                BigInteger recipientAiAcceptRaw, BigInteger recipientAnswerStatusRaw) {
        public Actionability {
            Objects.requireNonNull(roles); Objects.requireNonNull(nativeChildHousePreview);
            if (recipientAiAcceptRaw != null && recipientAiAcceptRaw.bitLength() > 63) { throw new IllegalArgumentException("native accept score outside signed int64"); }
        }
        public static Actionability empty() {
            return new Actionability(new Roles(null, null, null, null, null), null, null, null,
                    null, NullValue.INSTANCE, null, null, null);
        }
    }

    public record Relation(BigInteger nativeRevision, BigInteger heirCharacterId,
                           BigInteger betrothedCharacterId, Boolean bilateralVerified,
                           Actionability actionability, WireValue descendants, WireValue descendantsSummary) {
        public Relation { character(heirCharacterId); character(betrothedCharacterId); Objects.requireNonNull(actionability); Objects.requireNonNull(descendants); Objects.requireNonNull(descendantsSummary); }
    }

    public record BuildInput(Relation relation, Frame frame, boolean selected, List<String> reasons) {
        public BuildInput { Objects.requireNonNull(relation); Objects.requireNonNull(frame); reasons = List.copyOf(reasons); }
    }

    public record ExistingCommitment(String source, Boolean bilateralVerified, BigInteger heirCharacterId,
                                     BigInteger partnerCharacterId, String commitmentKey, String mode,
                                     Boolean newBetrothalCommitment, ObjectValue extensions) {
        public ExistingCommitment { Objects.requireNonNull(extensions); }
    }

    public record ResourceProposal(String schema, String mode, String typedStep, Frame sourceFrame,
                                   BigInteger sourceNativeRevision, Boolean selected, Boolean formalActionReady,
                                   List<String> reasons, Roles roles, List<BigInteger> characterClaims,
                                   GenericCosts immediateGenericCosts, ExistingCommitment existingCommitment,
                                   String benefit, String predictedOutcomeIfAccepted, Boolean matrilinealOptionSelected,
                                   WireValue nativeChildHousePreview, WireValue descendants, WireValue descendantsSummary,
                                   Boolean effectiveMatrilinealIfAccepted, BigInteger recipientAiAcceptRaw,
                                   BigInteger recipientAnswerStatusRaw, WireValue allianceEstablished,
                                   String futureAllianceObligation, List<String> unpriced,
                                   Boolean resourceReservationPerformed, ObjectValue extensions) {
        public ResourceProposal {
            Objects.requireNonNull(roles); reasons = reasons == null ? null : List.copyOf(reasons);
            characterClaims = characterClaims == null ? null : List.copyOf(characterClaims);
            unpriced = unpriced == null ? null : List.copyOf(unpriced);
            Objects.requireNonNull(nativeChildHousePreview); Objects.requireNonNull(descendants); Objects.requireNonNull(descendantsSummary);
            Objects.requireNonNull(allianceEstablished); Objects.requireNonNull(extensions);
            if (recipientAiAcceptRaw != null && recipientAiAcceptRaw.bitLength() > 63) { throw new IllegalArgumentException("native accept score outside signed int64"); }
        }
    }

    public record Plan(String selectedStep, ResourceProposal resourceProposal) { }
    public record AdaptInput(Frame frame, Plan plan) { public AdaptInput { Objects.requireNonNull(frame); Objects.requireNonNull(plan); } }
    public record Opportunity(Frame frame, String candidateId, BigInteger goldCostRaw,
                              List<BigInteger> characterIds, List<String> commitmentKeys,
                              ResourceProposal resourceProposal) {
        public Opportunity {
            Objects.requireNonNull(frame); Objects.requireNonNull(candidateId); Objects.requireNonNull(goldCostRaw);
            characterIds = List.copyOf(characterIds); commitmentKeys = List.copyOf(commitmentKeys); Objects.requireNonNull(resourceProposal);
        }
    }

    static void positive(BigInteger value, String name) {
        if (value == null || value.signum() <= 0) { throw new IllegalArgumentException(name + " must be positive integer"); }
    }
    private static void character(BigInteger value) {
        if (value != null && (value.signum() <= 0 || value.bitLength() > 31)) { throw new IllegalArgumentException("native CharacterID must be positive below 2**31 or null"); }
    }
    private static void unicode(String value) {
        Objects.requireNonNull(value);
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) {
                if (index + 1 >= value.length() || !Character.isLowSurrogate(value.charAt(index + 1))) {
                    throw new IllegalArgumentException("unpaired evidence Unicode surrogate");
                }
                index++;
            } else if (Character.isLowSurrogate(current)) { throw new IllegalArgumentException("unpaired evidence Unicode surrogate"); }
        }
    }
}
