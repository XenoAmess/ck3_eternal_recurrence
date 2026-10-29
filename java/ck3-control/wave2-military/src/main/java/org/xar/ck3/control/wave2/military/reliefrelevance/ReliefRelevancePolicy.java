package org.xar.ck3.control.wave2.military.reliefrelevance;

import java.math.BigInteger;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Enemy;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Snapshot;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.War;

/** The actual strategy consumer of realm-siege scope, retaining the original factual fallback order. */
public final class ReliefRelevancePolicy {
    public static final String INPUT_SCHEMA = "xar.siege-relief-relevance-input.v1";
    public static final String OUTPUT_SCHEMA = "xar.siege-relief-relevance-observation.v1";
    private ReliefRelevancePolicy() { }

    public record WarObjectives(List<BigInteger> provinceIds) {
        public WarObjectives { provinceIds = provinceIds == null ? null : List.copyOf(provinceIds); }
    }
    /** Extra consumed facts are decoded from the same selected document nodes as the reusable realm graph. */
    public record Request(RealmSiegePolicy.Request realmFrame, List<BigInteger> candidateWarObjectiveProvinceIds,
            BigInteger candidateEnemySiegeProvinceHolderCharacterId, List<WarObjectives> activeWarObjectivesInStoredOrder) {
        public Request {
            Objects.requireNonNull(realmFrame);
            candidateWarObjectiveProvinceIds = candidateWarObjectiveProvinceIds == null ? null : List.copyOf(candidateWarObjectiveProvinceIds);
            activeWarObjectivesInStoredOrder = List.copyOf(activeWarObjectivesInStoredOrder);
            if ((realmFrame.candidateWar() == null && candidateWarObjectiveProvinceIds != null)
                    || (realmFrame.candidateEnemy() == null && candidateEnemySiegeProvinceHolderCharacterId != null)) {
                throw new IllegalArgumentException("extra consumed facts require their selected document node");
            }
            List<War> wars = realmFrame.snapshot().activeWars();
            if (activeWarObjectivesInStoredOrder.size() != (wars == null ? 0 : wars.size())) {
                throw new IllegalArgumentException("objective projection must match this exact active-war traversal");
            }
            if (realmFrame.candidateWarRef() != null && realmFrame.candidateWarRef().collection() == RealmSiegePolicy.WarCollection.ACTIVE_WARS
                    && !Objects.equals(candidateWarObjectiveProvinceIds, activeWarObjectivesInStoredOrder.get(realmFrame.candidateWarRef().index()).provinceIds())) {
                throw new IllegalArgumentException("candidate objective projection differs from its active-war node");
            }
        }
    }
    public record Assessment(boolean candidateSiegeReliefRelevant, List<BigInteger> objectiveProvinceIdsInStoredTraversal) {
        public Assessment { objectiveProvinceIdsInStoredTraversal = List.copyOf(objectiveProvinceIdsInStoredTraversal); }
    }

    /** Exact stable, first-occurrence traversal of native objective integers; no new positivity filter. */
    public static List<BigInteger> warObjectiveProvinceIds(List<WarObjectives> activeWars) {
        LinkedHashSet<BigInteger> seen = new LinkedHashSet<>();
        for (WarObjectives war : activeWars) { if (war.provinceIds() != null) { seen.addAll(war.provinceIds()); } }
        return List.copyOf(seen);
    }

    public static boolean isRelevant(Snapshot snapshot, War war, Enemy enemy,
            List<BigInteger> warObjectiveProvinceIds, BigInteger siegeProvinceHolderCharacterId) {
        if (snapshot == null || war == null || enemy == null) { return false; }
        if (Boolean.FALSE.equals(war.playerIsPrimaryWarLeader())) {
            return RealmSiegePolicy.qualifies(snapshot, war, enemy);
        }
        BigInteger province = enemy.currentProvinceId();
        if (province == null || province.signum() <= 0) { return false; }
        if (warObjectiveProvinceIds != null && warObjectiveProvinceIds.contains(province)) { return true; }
        if (Boolean.TRUE.equals(enemy.siegeProvinceInPlayerSubrealm())) { return true; }
        if (Boolean.FALSE.equals(enemy.siegeProvinceInPlayerSubrealm())) { return false; }
        BigInteger actor = snapshot.playedCharacter() == null ? null : snapshot.playedCharacter().characterId();
        return actor != null && actor.signum() > 0 && actor.equals(siegeProvinceHolderCharacterId);
    }

    public static Assessment assess(Request request) {
        Objects.requireNonNull(request);
        RealmSiegePolicy.Request frame = request.realmFrame();
        List<BigInteger> candidateObjectives = warObjectiveProvinceIds(List.of(new WarObjectives(request.candidateWarObjectiveProvinceIds())));
        return new Assessment(isRelevant(frame.snapshot(), frame.candidateWar(), frame.candidateEnemy(), candidateObjectives,
                request.candidateEnemySiegeProvinceHolderCharacterId()), warObjectiveProvinceIds(request.activeWarObjectivesInStoredOrder()));
    }
}
