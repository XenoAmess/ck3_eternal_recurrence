package org.xar.ck3.control.military.declarationpriority;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.OptionalInt;

/** Pure research ordering; no result of this policy grants permission to declare war. */
public final class DeclarationObjectivePriority {
    public static final String POLICY = "native-actor-owned-title-claim-research-first-v1";
    private static final BigInteger NO_STABLE_ID = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger NO_POWER = BigInteger.valueOf(Long.MAX_VALUE);

    private DeclarationObjectivePriority() { }

    public enum Priority {
        ACTOR_OWNED_NATIVE_TITLE_CLAIM(0), OTHER_OR_UNOBSERVED(1);
        private final int rank;
        Priority(int rank) { this.rank = rank; }
        public int rank() { return rank; }
    }

    /** The eight fields read by the original leaf and its sole ordering consumer. */
    public record Declaration(
            JsonField<String> declarationId,
            JsonField<BigInteger> targetCharacterId,
            JsonField<BigInteger> casusBelliIndex,
            JsonField<String> casusBelliKey,
            JsonField<BigInteger> configurationIndex,
            JsonField<BigInteger> claimantCharacterId,
            JsonField<List<BigInteger>> targetTitleIds,
            JsonField<String> source) {
        public Declaration {
            Objects.requireNonNull(declarationId, "declarationId");
            Objects.requireNonNull(targetCharacterId, "targetCharacterId");
            Objects.requireNonNull(casusBelliIndex, "casusBelliIndex");
            Objects.requireNonNull(casusBelliKey, "casusBelliKey");
            Objects.requireNonNull(configurationIndex, "configurationIndex");
            Objects.requireNonNull(claimantCharacterId, "claimantCharacterId");
            Objects.requireNonNull(targetTitleIds, "targetTitleIds");
            Objects.requireNonNull(source, "source");
            if (targetTitleIds.hasValue()) {
                targetTitleIds = JsonField.of(List.copyOf(targetTitleIds.value()));
            }
        }
    }

    /** Exact integer lanes, not probabilities, utility, admission, or victory predictions. */
    public record PowerAssessment(
            BigInteger targetCharacterId, BigInteger actorPowerBaseRaw,
            BigInteger actorNetworkContributionRaw, BigInteger targetNetworkContributionRaw,
            BigInteger targetPowerTotalRaw, BigInteger actualPowerRatioRaw, BigInteger distanceRaw) {
        public PowerAssessment {
            Objects.requireNonNull(targetCharacterId, "targetCharacterId");
            Objects.requireNonNull(actorPowerBaseRaw, "actorPowerBaseRaw");
            Objects.requireNonNull(actorNetworkContributionRaw, "actorNetworkContributionRaw");
            Objects.requireNonNull(targetNetworkContributionRaw, "targetNetworkContributionRaw");
            Objects.requireNonNull(targetPowerTotalRaw, "targetPowerTotalRaw");
            Objects.requireNonNull(actualPowerRatioRaw, "actualPowerRatioRaw");
            Objects.requireNonNull(distanceRaw, "distanceRaw");
        }
    }

    public record LeafInput(JsonField<BigInteger> actorCharacterId, JsonField<Declaration> declaration) {
        public LeafInput {
            requireEnvelopeField(actorCharacterId, "actorCharacterId");
            requireEnvelopeField(declaration, "declaration");
        }
    }

    public record SelectionInput(JsonField<BigInteger> actorCharacterId, List<Declaration> declarations,
                                 JsonField<List<PowerAssessment>> warEntryAssessments) {
        public SelectionInput {
            requireEnvelopeField(actorCharacterId, "actorCharacterId");
            declarations = List.copyOf(Objects.requireNonNull(declarations, "declarations"));
            Objects.requireNonNull(warEntryAssessments, "warEntryAssessments");
            if (warEntryAssessments.hasValue()) {
                warEntryAssessments = JsonField.of(List.copyOf(warEntryAssessments.value()));
                Map<BigInteger, PowerAssessment> unique = new HashMap<>();
                for (PowerAssessment row : warEntryAssessments.value()) {
                    if (unique.put(row.targetCharacterId(), row) != null) {
                        throw new IllegalArgumentException("duplicate target assessment");
                    }
                }
            }
        }
    }

    private static void requireEnvelopeField(JsonField<?> field, String name) {
        Objects.requireNonNull(field, name);
        if (field.presence() == JsonField.Presence.MISSING) {
            throw new IllegalArgumentException(name + " is required; unknown must be explicit null");
        }
    }

    public static Priority priority(LeafInput input) {
        Objects.requireNonNull(input, "input");
        if (!input.actorCharacterId().hasValue() || input.actorCharacterId().value().signum() <= 0
                || !input.declaration().hasValue()) {
            return Priority.OTHER_OR_UNOBSERVED;
        }
        Declaration row = input.declaration().value();
        if (!row.source().hasValue() || !row.source().value().equals("native")
                || !row.casusBelliKey().hasValue() || !row.casusBelliKey().value().equals("claim_cb")
                || !row.claimantCharacterId().hasValue()
                || !row.claimantCharacterId().value().equals(input.actorCharacterId().value())
                || !row.targetTitleIds().hasValue() || row.targetTitleIds().value().isEmpty()) {
            return Priority.OTHER_OR_UNOBSERVED;
        }
        for (BigInteger title : row.targetTitleIds().value()) {
            if (title.signum() <= 0) { return Priority.OTHER_OR_UNOBSERVED; }
        }
        return Priority.ACTOR_OWNED_NATIVE_TITLE_CLAIM;
    }

    /** Returns the original input index; exact ties retain the first original row. */
    public static OptionalInt preferredIndex(SelectionInput input) {
        Objects.requireNonNull(input, "input");
        Map<BigInteger, PowerAssessment> assessments = new HashMap<>();
        if (input.warEntryAssessments().hasValue()) {
            for (PowerAssessment row : input.warEntryAssessments().value()) {
                assessments.put(row.targetCharacterId(), row);
            }
        }
        int winner = -1;
        List<BigInteger> winnerKey = List.of();
        for (int index = 0; index < input.declarations().size(); index++) {
            Declaration row = input.declarations().get(index);
            List<BigInteger> key = preference(row, input.actorCharacterId(),
                    assessments.get(stableInteger(row.targetCharacterId())));
            if (winner < 0 || compare(key, winnerKey) < 0) {
                winner = index;
                winnerKey = key;
            }
        }
        return winner < 0 ? OptionalInt.empty() : OptionalInt.of(winner);
    }

    private static List<BigInteger> preference(Declaration row, JsonField<BigInteger> actor,
                                                PowerAssessment assessment) {
        List<BigInteger> key = new ArrayList<>(13);
        key.add(assessment == null ? BigInteger.ONE : BigInteger.ZERO);
        if (assessment == null) {
            for (int index = 0; index < 6; index++) { key.add(NO_POWER); }
        } else {
            key.add(assessment.targetPowerTotalRaw().subtract(assessment.actorPowerBaseRaw()).max(BigInteger.ZERO));
            key.add(assessment.actualPowerRatioRaw());
            key.add(assessment.actorNetworkContributionRaw().max(BigInteger.ZERO));
            key.add(assessment.targetNetworkContributionRaw().max(BigInteger.ZERO));
            key.add(assessment.targetPowerTotalRaw());
            key.add(assessment.distanceRaw());
        }
        key.add(BigInteger.valueOf(assessment == null
                ? priority(new LeafInput(actor, JsonField.of(row))).rank() : 1));
        String cb = row.casusBelliKey().hasValue() ? row.casusBelliKey().value().toLowerCase(Locale.ROOT) : "";
        int cbRank = cb.contains("holy_war") && cb.contains("county") ? 0
                : cb.contains("county") ? 1 : cb.contains("claim") ? 2 : 3;
        key.add(BigInteger.valueOf(cbRank));
        key.add(BigInteger.valueOf(row.targetTitleIds().hasValue() ? row.targetTitleIds().value().size() : 1_000_000));
        key.add(stableInteger(row.targetCharacterId()));
        key.add(stableInteger(row.casusBelliIndex()));
        key.add(stableInteger(row.configurationIndex()));
        return List.copyOf(key);
    }

    private static BigInteger stableInteger(JsonField<BigInteger> value) {
        return value.hasValue() ? value.value() : NO_STABLE_ID;
    }

    private static int compare(List<BigInteger> left, List<BigInteger> right) {
        for (int index = 0; index < left.size(); index++) {
            int result = left.get(index).compareTo(right.get(index));
            if (result != 0) { return result; }
        }
        return 0;
    }
}
