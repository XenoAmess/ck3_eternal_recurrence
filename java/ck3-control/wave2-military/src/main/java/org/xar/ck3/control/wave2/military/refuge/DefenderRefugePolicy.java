package org.xar.ck3.control.wave2.military.refuge;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Factual capital seeds and same-frame scope; Native retains route, contact and movement decisions. */
public final class DefenderRefugePolicy {
    public static final String INPUT_SCHEMA = "xar.defender-refuge-input.v1";
    public static final String OUTPUT_SCHEMA = "xar.defender-refuge-observation.v1";
    private static final BigInteger INT32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);

    private DefenderRefugePolicy() { }
    public enum Presence { MISSING, NULL, VALUE }
    public enum CurrentKind {
        DIRECTLY_HELD_CAPITAL("directly_held_capital"), DIRECT_VASSAL_CAPITAL("direct_vassal_capital");
        private final String wire;
        CurrentKind(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Readiness(Boolean directLandedVassalsReady, Boolean relatedCharacterContextsReady) { }
    public record Title(BigInteger titleId, BigInteger tierRaw) { }
    public record RelatedContext(String relationshipRole, BigInteger characterId,
            BigInteger immediateLiegeCharacterId, BigInteger topLiegeCharacterId,
            Title primaryTitle, BigInteger capitalProvinceId) { }
    public record HeldTitle(Title title, BigInteger capitalProvinceId) { }
    public record CampaignRoot(String status, BigInteger playerCharacterId, BigInteger topLiegeCharacterId,
            Readiness readiness, List<BigInteger> directLandedVassalCharacterIds,
            List<RelatedContext> relatedCharacterContexts, BigInteger snapshotRevision,
            BigInteger dateRaw, List<HeldTitle> heldTitlePartition) {
        public CampaignRoot {
            directLandedVassalCharacterIds = copyNullable(directLandedVassalCharacterIds);
            relatedCharacterContexts = copyNullable(relatedCharacterContexts);
            heldTitlePartition = copyNullable(heldTitlePartition);
        }
    }

    public record Enemy(BigInteger armyId, Boolean retreating) { }
    public record War(String playerSide, Boolean playerIsPrimaryWarLeader,
            List<BigInteger> warObjectiveProvinceIds, List<Enemy> enemyArmies) {
        public War { warObjectiveProvinceIds = copyNullable(warObjectiveProvinceIds); enemyArmies = copyNullable(enemyArmies); }
    }
    public record Army(BigInteger armyId, BigInteger currentProvinceId, BigInteger ownerCharacterId,
            Boolean controllable, String armyState, Boolean inCombat, Boolean retreating,
            List<BigInteger> routeProvinceIds, BigInteger moveTargetProvinceId) {
        public Army { routeProvinceIds = copyNullable(routeProvinceIds); }
    }
    public record Diagnostics(BigInteger bridgePid, BigInteger connectionGeneration) { }
    public record Snapshot(Boolean paused, Boolean mapReady, Presence activeEvent, Presence pendingCharacterInteraction,
            BigInteger actorCharacterId, BigInteger playedCharacterId, String snapshotId,
            BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw,
            Diagnostics diagnostics, List<War> activeWars, List<Army> playerArmies) {
        public Snapshot {
            Objects.requireNonNull(activeEvent); Objects.requireNonNull(pendingCharacterInteraction);
            activeWars = copyNullable(activeWars); playerArmies = copyNullable(playerArmies);
        }
        public BigInteger actor() { return actorCharacterId == null ? playedCharacterId : actorCharacterId; }
    }
    public record CacheBinding(String snapshotId, BigInteger revision, BigInteger nativeRevision,
            BigInteger dateRaw, BigInteger actorCharacterId, BigInteger bridgePid, BigInteger connectionGeneration) {
        public CacheBinding {
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(actorCharacterId); Objects.requireNonNull(bridgePid);
            Objects.requireNonNull(connectionGeneration);
        }
    }
    public record CachedQuery(CacheBinding cacheBinding, CampaignRoot campaignRootContext) { }
    public record Request(Snapshot snapshot, CampaignRoot root, CachedQuery cachedQuery) { }
    public record RefugeScope(int armyId, int currentProvinceId, int ownCapitalProvinceId, CurrentKind currentKind,
            List<Integer> candidateProvinceIds, List<Integer> hostileArmyIds) {
        public RefugeScope {
            Objects.requireNonNull(currentKind); candidateProvinceIds = List.copyOf(candidateProvinceIds);
            hostileArmyIds = List.copyOf(hostileArmyIds);
        }
    }
    public record Assessment(List<Integer> directVassalCapitalProvinceIds, RefugeScope lifecycleScope,
            RefugeScope sameFrameCachedScope) {
        public Assessment { directVassalCapitalProvinceIds = copyNullable(directVassalCapitalProvinceIds); }
    }

    /** null means incomplete/unavailable; an empty list means a complete observed empty capital set. */
    public static List<Integer> directVassalCapitalProvinceIds(CampaignRoot root) {
        if (root == null || !"available".equals(root.status()) || root.readiness() == null
                || !Boolean.TRUE.equals(root.readiness().directLandedVassalsReady())
                || !Boolean.TRUE.equals(root.readiness().relatedCharacterContextsReady())) { return null; }
        Integer actor = id(root.playerCharacterId(), false), topLiege = id(root.topLiegeCharacterId(), false);
        if (actor == null || topLiege == null || root.directLandedVassalCharacterIds() == null
                || root.relatedCharacterContexts() == null) { return null; }
        List<Integer> directIds = new ArrayList<>();
        for (BigInteger value : root.directLandedVassalCharacterIds()) {
            Integer parsed = id(value, false); if (parsed == null) { return null; } directIds.add(parsed);
        }
        if (new HashSet<>(directIds).size() != directIds.size()) { return null; }
        Map<Integer, Integer> found = new LinkedHashMap<>();
        for (RelatedContext row : root.relatedCharacterContexts()) {
            if (!"direct_landed_vassal".equals(row.relationshipRole())) { continue; }
            Integer characterId = id(row.characterId(), false);
            if (!directIds.contains(characterId) || found.containsKey(characterId)
                    || !Objects.equals(row.immediateLiegeCharacterId(), root.playerCharacterId())
                    || !Objects.equals(row.topLiegeCharacterId(), root.topLiegeCharacterId())) { return null; }
            Title title = row.primaryTitle();
            if (title == null || id(title.titleId(), false) == null || title.tierRaw() == null
                    || title.tierRaw().compareTo(BigInteger.ONE) < 0 || title.tierRaw().compareTo(BigInteger.valueOf(6)) > 0) { return null; }
            Integer province = id(row.capitalProvinceId(), false);
            if (row.capitalProvinceId() != null && province == null) { return null; }
            found.put(characterId, province);
        }
        if (!found.keySet().equals(new HashSet<>(directIds))) { return null; }
        List<Integer> provinces = new ArrayList<>();
        for (Integer province : found.values()) { if (province != null) { provinces.add(province); } }
        if (new HashSet<>(provinces).size() != provinces.size()) { return null; }
        provinces.sort(Integer::compareTo); return List.copyOf(provinces);
    }

    /** Caller supplies the existing same-frame verified campaign root; this function is no replacement verifier. */
    public static RefugeScope lifecycleScope(Snapshot snapshot, CampaignRoot root) {
        if (snapshot == null || root == null || !Boolean.TRUE.equals(snapshot.paused()) || !Boolean.TRUE.equals(snapshot.mapReady())
                || snapshot.activeEvent() == Presence.VALUE || snapshot.pendingCharacterInteraction() == Presence.VALUE
                || !"available".equals(root.status()) || !Objects.equals(root.snapshotRevision(), snapshot.nativeRevision())
                || !Objects.equals(root.dateRaw(), snapshot.dateRaw()) || !Objects.equals(root.playerCharacterId(), snapshot.actor())) { return null; }
        List<Integer> candidates = directVassalCapitalProvinceIds(root);
        if (candidates == null || candidates.isEmpty() || snapshot.activeWars() == null || snapshot.activeWars().size() != 1
                || snapshot.playerArmies() == null) { return null; }
        War war = snapshot.activeWars().getFirst();
        if (!"defender".equals(war.playerSide()) || !Boolean.TRUE.equals(war.playerIsPrimaryWarLeader())
                || war.warObjectiveProvinceIds() == null || !war.warObjectiveProvinceIds().isEmpty()) { return null; }
        List<Army> controlled = snapshot.playerArmies().stream().filter(row -> Boolean.TRUE.equals(row.controllable())).toList();
        if (controlled.size() != 1) { return null; }
        Army army = controlled.getFirst(); Integer armyId = id(army.armyId(), true), current = id(army.currentProvinceId(), false);
        List<BigInteger> directCounties = new ArrayList<>();
        if (root.heldTitlePartition() != null) {
            for (HeldTitle row : root.heldTitlePartition()) {
                if (row.title() != null && BigInteger.valueOf(2).equals(row.title().tierRaw())) { directCounties.add(row.capitalProvinceId()); }
            }
        }
        Integer ownCapital = directCounties.size() == 1 ? id(directCounties.getFirst(), false) : null;
        if (armyId == null || current == null || ownCapital == null || (!current.equals(ownCapital) && !candidates.contains(current))
                || !Objects.equals(army.ownerCharacterId(), snapshot.actor()) || !"regular".equals(army.armyState())
                || !Boolean.FALSE.equals(army.inCombat()) || !Boolean.FALSE.equals(army.retreating())
                || army.routeProvinceIds() == null || !army.routeProvinceIds().isEmpty() || army.moveTargetProvinceId() != null) { return null; }
        if (war.enemyArmies() == null) { return null; }
        List<Integer> hostileIds = new ArrayList<>();
        for (Enemy enemy : war.enemyArmies()) {
            if (Boolean.TRUE.equals(enemy.retreating())) { continue; }
            Integer hostileId = id(enemy.armyId(), true); if (hostileId == null) { return null; } hostileIds.add(hostileId);
        }
        Set<Integer> unique = new HashSet<>(hostileIds);
        if (hostileIds.isEmpty() || hostileIds.size() > 64 || unique.size() != hostileIds.size()) { return null; }
        hostileIds.sort(Integer::compareTo);
        List<Integer> remaining = new ArrayList<>();
        for (Integer province : candidates) { if (!province.equals(current)) { remaining.add(province); } }
        if (!current.equals(ownCapital)) { remaining.add(ownCapital); }
        return new RefugeScope(armyId, current, ownCapital,
                current.equals(ownCapital) ? CurrentKind.DIRECTLY_HELD_CAPITAL : CurrentKind.DIRECT_VASSAL_CAPITAL,
                remaining, hostileIds);
    }

    public static RefugeScope sameFrameScope(Snapshot snapshot, CachedQuery cachedQuery) {
        if (snapshot == null || cachedQuery == null || snapshot.diagnostics() == null || cachedQuery.cacheBinding() == null) { return null; }
        CacheBinding binding = cachedQuery.cacheBinding(); Diagnostics diagnostics = snapshot.diagnostics();
        if (!Objects.equals(binding.snapshotId(), snapshot.snapshotId()) || !Objects.equals(binding.revision(), snapshot.revision())
                || !Objects.equals(binding.nativeRevision(), snapshot.nativeRevision()) || !Objects.equals(binding.dateRaw(), snapshot.dateRaw())
                || !Objects.equals(binding.actorCharacterId(), snapshot.actor()) || !Objects.equals(binding.bridgePid(), diagnostics.bridgePid())
                || !Objects.equals(binding.connectionGeneration(), diagnostics.connectionGeneration())) { return null; }
        return lifecycleScope(snapshot, cachedQuery.campaignRootContext());
    }

    public static Assessment assess(Request request) {
        Objects.requireNonNull(request);
        return new Assessment(directVassalCapitalProvinceIds(request.root()), lifecycleScope(request.snapshot(), request.root()),
                sameFrameScope(request.snapshot(), request.cachedQuery()));
    }

    private static Integer id(BigInteger value, boolean unit) {
        return value != null && value.compareTo(unit ? BigInteger.ZERO : BigInteger.ONE) >= 0 && value.compareTo(INT32_MAX) <= 0
                ? value.intValueExact() : null;
    }
    private static <T> List<T> copyNullable(List<T> rows) { return rows == null ? null : List.copyOf(rows); }
}
