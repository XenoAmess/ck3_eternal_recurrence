package org.xar.ck3.control.wave2.military.actualcontact;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Current-Province resolver mirror; the model cannot authenticate a native observation. */
public final class ActualContactModel {
    public static final String STEP_PREFIX = "query-actual-contact-scope-v1-";
    private ActualContactModel() { }

    public enum ScopeKind { PRE_CONTACT_PREDICTION, POST_CONTACT_OBSERVATION }
    public enum Transition { NONE, JOIN_EXISTING, CREATE_NEW, IN_COMBAT }
    public enum Side { ATTACKER, DEFENDER }

    public record Query(int subjectArmyId, int targetProvinceId) {
        public Query { require(subjectArmyId >= 0 && targetProvinceId > 0, "public CUnit and positive Province required"); }
        public String step() { return STEP_PREFIX + subjectArmyId + "-at-" + targetProvinceId; }
    }
    public record Binding(Query query, int dateRaw, BigInteger snapshotRevision) {
        public Binding { Objects.requireNonNull(query, "query"); revision(snapshotRevision); }
    }

    public record Scope(ScopeKind scopeKind, BigInteger snapshotRevision, int dateRaw, int subjectArmyId,
                        int subjectNativeCarmyId, int subjectOwnerCharacterId, int targetProvinceId,
                        List<Integer> provinceUnitArmyIds, List<Integer> provinceCombatIds, Transition transition,
                        Integer selectedCombatId, Integer selectedCombatArrayIndex, Side joinSide,
                        Integer defenderSeedCharacterId, boolean initiatorIsDefender, int adjacencyKindRaw,
                        List<Integer> loserExcludedNativeCarmyIds, List<Integer> opponentArmyIds,
                        List<Integer> attackerArmyIds, List<Integer> defenderArmyIds, boolean combatV3ParticipantScopeReady) {
        public Scope {
            Objects.requireNonNull(scopeKind, "scope kind"); Objects.requireNonNull(transition, "transition");
            revision(snapshotRevision); require(subjectArmyId >= 0, "public subject CUnit required");
            positive(subjectNativeCarmyId); positive(subjectOwnerCharacterId); positive(targetProvinceId);
            provinceUnitArmyIds = ids(provinceUnitArmyIds, true, true, false);
            provinceCombatIds = ids(provinceCombatIds, false, true, false);
            loserExcludedNativeCarmyIds = ids(loserExcludedNativeCarmyIds, false, false, false);
            opponentArmyIds = ids(opponentArmyIds, true, false, false);
            attackerArmyIds = ids(attackerArmyIds, true, false, true);
            defenderArmyIds = ids(defenderArmyIds, true, false, true);
            require(provinceUnitArmyIds.contains(subjectArmyId), "subject absent from current Province");
            require(attackerArmyIds.stream().noneMatch(defenderArmyIds::contains), "final contact sides overlap");
            if (selectedCombatId != null) { positive(selectedCombatId); }
            if (selectedCombatArrayIndex != null) { require(selectedCombatArrayIndex >= 0, "negative selected Combat index"); }
            if (defenderSeedCharacterId != null) { positive(defenderSeedCharacterId); }
            require(combatV3ParticipantScopeReady == (transition != Transition.NONE), "participant readiness disagrees");
            require((transition == Transition.IN_COMBAT) == (scopeKind == ScopeKind.POST_CONTACT_OBSERVATION),
                    "contact phase predicate disagrees");
            boolean selectedMatches = selectedCombatId != null && selectedCombatArrayIndex != null
                    && selectedCombatArrayIndex < provinceCombatIds.size()
                    && provinceCombatIds.get(selectedCombatArrayIndex).equals(selectedCombatId);
            if (transition == Transition.JOIN_EXISTING) {
                List<Integer> own = joinSide == Side.ATTACKER ? attackerArmyIds : defenderArmyIds;
                require(selectedMatches && joinSide != null && defenderSeedCharacterId == null
                        && !attackerArmyIds.isEmpty() && !defenderArmyIds.isEmpty() && opponentArmyIds.isEmpty()
                        && (joinSide == Side.ATTACKER) == attackerArmyIds.contains(subjectArmyId)
                        && (joinSide == Side.DEFENDER) == defenderArmyIds.contains(subjectArmyId)
                        && own.getLast() == subjectArmyId, "actual_contact_scope join projection disagrees");
            } else if (transition == Transition.CREATE_NEW) {
                require(selectedCombatId == null && selectedCombatArrayIndex == null && joinSide == null
                        && defenderSeedCharacterId != null && !opponentArmyIds.isEmpty()
                        && !opponentArmyIds.contains(subjectArmyId) && provinceUnitArmyIds.containsAll(opponentArmyIds),
                        "new contact scope disagrees");
                List<Integer> uniqueOpponents = List.copyOf(new LinkedHashSet<>(opponentArmyIds));
                require(attackerArmyIds.equals(initiatorIsDefender ? uniqueOpponents : List.of(subjectArmyId))
                        && defenderArmyIds.equals(initiatorIsDefender ? List.of(subjectArmyId) : uniqueOpponents),
                        "new contact final side insertion disagrees");
            } else if (transition == Transition.IN_COMBAT) {
                require(selectedMatches && joinSide == null && defenderSeedCharacterId == null && !initiatorIsDefender
                        && adjacencyKindRaw == 0 && loserExcludedNativeCarmyIds.isEmpty() && opponentArmyIds.isEmpty()
                        && !attackerArmyIds.isEmpty() && !defenderArmyIds.isEmpty()
                        && attackerArmyIds.contains(subjectArmyId) != defenderArmyIds.contains(subjectArmyId),
                        "in-combat observation disagrees");
            } else {
                require(selectedCombatId == null && selectedCombatArrayIndex == null && joinSide == null
                        && defenderSeedCharacterId == null && opponentArmyIds.isEmpty() && attackerArmyIds.isEmpty()
                        && defenderArmyIds.isEmpty() && !initiatorIsDefender && adjacencyKindRaw == 0,
                        "no-transition payload disagrees");
            }
        }
        public boolean matches(Binding expected) {
            return subjectArmyId == expected.query().subjectArmyId() && targetProvinceId == expected.query().targetProvinceId()
                    && dateRaw == expected.dateRaw() && snapshotRevision.equals(expected.snapshotRevision());
        }
    }

    public static Optional<Query> parseStep(String step) {
        if (step == null || !step.startsWith(STEP_PREFIX)) { return Optional.empty(); }
        String payload = step.substring(STEP_PREFIX.length()); int split = payload.indexOf("-at-");
        if (split < 0 || payload.indexOf("-at-", split + 4) >= 0) { return Optional.empty(); }
        try {
            int subject = decimal(payload.substring(0, split), true); int target = decimal(payload.substring(split + 4), false);
            return Optional.of(new Query(subject, target));
        } catch (IllegalArgumentException error) { return Optional.empty(); }
    }
    private static int decimal(String text, boolean allowZero) {
        require(!text.isEmpty() && (allowZero && text.equals("0") || text.charAt(0) != '0'), "canonical decimal required");
        for (int index = 0; index < text.length(); index++) { require(text.charAt(index) >= '0' && text.charAt(index) <= '9', "ASCII digits required"); }
        int result = Integer.parseInt(text); require(allowZero || result > 0, "positive Province required"); return result;
    }
    private static List<Integer> ids(List<Integer> values, boolean publicUnits, boolean increasing, boolean unique) {
        List<Integer> result = List.copyOf(values); Integer prior = null;
        for (Integer value : result) {
            require(publicUnits ? value >= 0 : value > 0, "identity outside native lane");
            if (increasing && prior != null) { require(prior < value, "native numeric order required"); }
            prior = value;
        }
        if (unique) { require(new HashSet<>(result).size() == result.size(), "duplicate final side identity"); }
        return result;
    }
    private static void revision(BigInteger value) {
        require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 revision required");
    }
    private static void positive(int value) { require(value > 0, "positive int32 native identity required"); }
    private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}
