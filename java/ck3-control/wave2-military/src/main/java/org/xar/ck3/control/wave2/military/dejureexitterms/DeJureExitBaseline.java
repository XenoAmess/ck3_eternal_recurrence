package org.xar.ck3.control.wave2.military.dejureexitterms;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.util.HashSet;
import java.util.List;
import java.util.Optional;

/** Current native prestate only. No material effect, duration, recommendation or action can be constructed. */
public record DeJureExitBaseline(Frame expectedFrame, List<TitleHolder> titleHolderPrestate,
                                List<ResourceBalance> primaryResourceBalances, List<MonthlyIncome> primaryMonthlyGoldIncome,
                                Optional<TruceInputs> truceInputs, Optional<StorageCandidate> borderRaidStorageCandidate) {
    public static final String SCHEMA = "xar.ck3.defender-de-jure-exit-terms.v1";
    public static final String PREFIX = "query-defender-de-jure-exit-terms-v1-";
    public static final String CAPABILITY = "game.command.query-defender-de-jure-exit-terms-v1-N";
    public static final String TITLE_REASON = "runtime_target_scope_and_de_jure_change_semantics_unproven";
    public static final String RESOURCE_REASON = "conditional_effects_and_cb_prestige_factor_unread";
    public static final String TRUCE_REASON = "attacker_victory_truce_duration_unread";

    public DeJureExitBaseline {
        require(expectedFrame != null && truceInputs != null && borderRaidStorageCandidate != null, "typed complete baseline required");
        titleHolderPrestate = List.copyOf(titleHolderPrestate);
        require(titleHolderPrestate.size() == expectedFrame.targetTitleIds().size(), "complete ordered holder prestate required");
        for (int index = 0; index < titleHolderPrestate.size(); index++) {
            require(titleHolderPrestate.get(index).titleId() == expectedFrame.targetTitleIds().get(index), "title-holder prestate order differs");
        }
        primaryResourceBalances = List.copyOf(primaryResourceBalances);
        require(primaryResourceBalances.size() == 14 && new HashSet<>(primaryResourceBalances.stream()
                .map(row -> new ResourceIdentity(row.characterId(), row.resource())).toList()).size() == 14,
                "fourteen unique party/resource balances required");
        for (ResourceBalance row : primaryResourceBalances) {
            require(expectedFrame.isParty(row.characterId()), "resource character must be one of the observed parties");
        }
        primaryMonthlyGoldIncome = List.copyOf(primaryMonthlyGoldIncome);
        require(primaryMonthlyGoldIncome.size() == 2 && primaryMonthlyGoldIncome.stream().map(MonthlyIncome::characterId).distinct().count() == 2
                && primaryMonthlyGoldIncome.stream().allMatch(row -> expectedFrame.isParty(row.characterId())), "both party monthly incomes required");
        require(borderRaidStorageCandidate.isEmpty() || truceInputs.isPresent(), "storage candidate requires partial truce inputs");
    }
    public record Frame(long warId, long nativeRevision, long dateRaw, long defenderId, long attackerId, List<Long> targetTitleIds) {
        public Frame {
            positive(warId); positive(nativeRevision); positive(defenderId); positive(attackerId);
            require(defenderId != attackerId, "distinct native primary parties required");
            targetTitleIds = List.copyOf(targetTitleIds);
            require(!targetTitleIds.isEmpty() && new HashSet<>(targetTitleIds).size() == targetTitleIds.size(),
                    "nonempty unique target titles required");
            targetTitleIds.forEach(DeJureExitBaseline::positive);
        }
        public boolean isParty(long id) { return id == attackerId || id == defenderId; }
    }
    public record TitleHolder(long titleId, long holderCharacterId, Optional<Long> holderImmediateLiegeCharacterId) {
        public TitleHolder {
            positive(titleId); positive(holderCharacterId); require(holderImmediateLiegeCharacterId != null, "explicit nullable liege required");
            holderImmediateLiegeCharacterId.ifPresent(value -> { positive(value); require(value != holderCharacterId, "holder cannot be own immediate liege"); });
        }
    }
    public enum Resource {
        GOLD("gold"), PRESTIGE("prestige"), PRESTIGE_EXPERIENCE("prestige_experience"), PIETY("piety"),
        PIETY_EXPERIENCE("piety_experience"), LEGITIMACY("legitimacy"), STRESS("stress");
        private final String wire;
        Resource(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Resource fromWire(String value) {
            for (Resource candidate : values()) { if (candidate.wire.equals(value)) { return candidate; } }
            throw new org.xar.ck3.control.contracts.ContractViolationException("unknown native resource");
        }
    }
    private record ResourceIdentity(long characterId, Resource resource) { }
    public record ResourceBalance(long characterId, Resource resource, long raw) {
        public ResourceBalance { positive(characterId); require(resource != null, "typed native resource required"); }
    }
    public record MonthlyIncome(long characterId, long raw) { public MonthlyIncome { positive(characterId); } }
    public sealed interface Predicate permits ObservedPredicate, UnavailablePredicate { }
    public record ObservedPredicate(boolean value) implements Predicate { }
    public record UnavailablePredicate(String reason) implements Predicate {
        public UnavailablePredicate { org.xar.ck3.control.contracts.StrictJson.text(reason); }
    }
    public record TruceInputs(Predicate attackerFlexibleTrucesPerk, Predicate attackerGovernmentIsNomadic,
                              Predicate defenderGovernmentIsNomadic, Predicate nomadBoth,
                              UnavailablePredicate shortCondition, UnavailablePredicate longCondition,
                              UnavailablePredicate borderRaidPair) {
        public TruceInputs {
            require(attackerFlexibleTrucesPerk != null && attackerGovernmentIsNomadic != null && defenderGovernmentIsNomadic != null
                    && nomadBoth != null && shortCondition != null && longCondition != null && borderRaidPair != null,
                    "complete typed truce predicate set required");
            for (UnavailablePredicate condition : List.of(shortCondition, longCondition, borderRaidPair)) {
                require(condition.reason().equals("stock_condition_reader_unavailable"), "unadmitted stock predicates must stay unread");
            }
            if (attackerGovernmentIsNomadic instanceof ObservedPredicate attacker && defenderGovernmentIsNomadic instanceof ObservedPredicate defender) {
                require(nomadBoth.equals(new ObservedPredicate(attacker.value() && defender.value())), "nomad conjunction disagrees with both parties");
            } else {
                require(nomadBoth.equals(new UnavailablePredicate("party_government_flag_unavailable")), "nomad conjunction lacks a party observation");
            }
        }
    }
    public sealed interface StorageCandidate permits StructuralCandidate, UnavailableStorage { }
    public record StructuralCandidate(long storageCapacity, long activeWarCount, long matchingWarCount) implements StorageCandidate {
        public StructuralCandidate {
            require(storageCapacity > 0 && storageCapacity <= 1_000_000 && activeWarCount >= 1 && activeWarCount <= storageCapacity
                    && matchingWarCount >= 0 && matchingWarCount <= activeWarCount, "bounded consistent storage scan required");
        }
        public boolean candidate() { return matchingWarCount > 0; }
    }
    public record UnavailableStorage(String reason) implements StorageCandidate {
        public UnavailableStorage { org.xar.ck3.control.contracts.StrictJson.text(reason); }
    }
    static void positive(long value) { require(value > 0, "positive signed native int64 required"); }
}
