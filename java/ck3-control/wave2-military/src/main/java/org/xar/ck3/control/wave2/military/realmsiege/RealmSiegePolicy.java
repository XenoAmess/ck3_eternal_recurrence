package org.xar.ck3.control.wave2.military.realmsiege;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Recognition of one current native realm siege. This class cannot move, spend, or submit. */
public final class RealmSiegePolicy {
    public static final String INPUT_SCHEMA = "xar.realm-siege-request.v1";
    public static final String OUTPUT_SCHEMA = "xar.realm-siege-observation.v1";

    private RealmSiegePolicy() { }

    public enum Presence { MISSING, NULL, VALUE }
    public enum WarCollection { ACTIVE_WARS, DETACHED_WARS }
    public enum EnemyCollection { CANDIDATE_WAR_ENEMIES, DETACHED_ENEMIES }

    public record IntegerField(Presence presence, BigInteger value) {
        public IntegerField {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) {
                throw new IllegalArgumentException("integer field presence/value disagree");
            }
        }
    }

    public record PlayedCharacter(String source, BigInteger characterId, Boolean alive) { }
    public record Diagnostics(Boolean connected, BigInteger bridgePid, BigInteger connectionGeneration) { }

    public record Enemy(String source, BigInteger armyId, BigInteger ownerCharacterId, Boolean controllable,
            String armyState, BigInteger armyStateCode, Boolean inCombat, Boolean retreating,
            BigInteger currentProvinceId, Boolean siegeProvinceInPlayerSubrealm,
            IntegerField moveTargetProvinceId, List<BigInteger> routeProvinceIds, String routeReadStatus) {
        public Enemy {
            Objects.requireNonNull(moveTargetProvinceId);
            routeProvinceIds = copyNullable(routeProvinceIds);
        }
    }

    public record War(String source, BigInteger warId, String playerSide, Boolean playerIsPrimaryWarLeader,
            BigInteger playerRelativeWarScore, List<Enemy> enemyArmies) {
        public War { enemyArmies = copyNullable(enemyArmies); }
    }

    public record Snapshot(String source, BigInteger nativeRevision, String snapshotId, BigInteger revision,
            BigInteger dateRaw, String episodeRunId, Boolean paused, Boolean mapReady,
            Presence activeEvent, Presence pendingCharacterInteraction, PlayedCharacter playedCharacter,
            Diagnostics diagnostics, List<War> activeWars) {
        public Snapshot {
            Objects.requireNonNull(activeEvent); Objects.requireNonNull(pendingCharacterInteraction);
            activeWars = copyNullable(activeWars);
        }
    }

    public record WarReference(WarCollection collection, int index) {
        public WarReference { Objects.requireNonNull(collection); nonnegativeIndex(index); }
    }
    public record EnemyReference(EnemyCollection collection, int index) {
        public EnemyReference { Objects.requireNonNull(collection); nonnegativeIndex(index); }
    }

    /** References resolve only into this immutable document; no membership booleans are accepted. */
    public record Request(Snapshot snapshot, List<War> detachedWars, List<Enemy> detachedEnemies,
            WarReference candidateWarRef, EnemyReference candidateEnemyRef) {
        public Request {
            Objects.requireNonNull(snapshot);
            detachedWars = List.copyOf(detachedWars); detachedEnemies = List.copyOf(detachedEnemies);
            if (candidateWarRef != null) { resolveWar(snapshot, detachedWars, candidateWarRef); }
            if (candidateEnemyRef != null) {
                resolveEnemy(candidateWarRef == null ? null : resolveWar(snapshot, detachedWars, candidateWarRef),
                        detachedEnemies, candidateEnemyRef);
            }
        }
        public War candidateWar() { return candidateWarRef == null ? null : resolveWar(snapshot, detachedWars, candidateWarRef); }
        public Enemy candidateEnemy() {
            return candidateEnemyRef == null ? null : resolveEnemy(candidateWar(), detachedEnemies, candidateEnemyRef);
        }
    }

    public record WarScope(BigInteger warId, boolean scopeObserved, List<Boolean> enemyScopesInStoredOrder) {
        public WarScope { enemyScopesInStoredOrder = List.copyOf(enemyScopesInStoredOrder); }
    }
    public record Assessment(boolean candidateEnemyScopeObserved, boolean candidateWarScopeObserved,
            List<WarScope> currentWarScopesInStoredOrder) {
        public Assessment { currentWarScopesInStoredOrder = List.copyOf(currentWarScopesInStoredOrder); }
    }

    /** Java reference identity intentionally implements Python `row is war` / `row is enemy`. */
    public static boolean qualifies(Snapshot snapshot, War war, Enemy enemy) {
        if (snapshot == null || war == null || enemy == null || !frameObserved(snapshot)) { return false; }
        BigInteger actor = snapshot.playedCharacter().characterId();
        return containsIdentity(snapshot.activeWars(), war) && containsIdentity(war.enemyArmies(), enemy)
                && "native".equals(war.source()) && positive(war.warId())
                && "defender".equals(war.playerSide()) && Boolean.FALSE.equals(war.playerIsPrimaryWarLeader())
                && war.playerRelativeWarScore() != null
                && war.playerRelativeWarScore().compareTo(BigInteger.valueOf(-100)) > 0
                && war.playerRelativeWarScore().compareTo(BigInteger.valueOf(100)) < 0
                && "native".equals(enemy.source()) && publicCunit(enemy.armyId())
                && positive(enemy.ownerCharacterId()) && !enemy.ownerCharacterId().equals(actor)
                && Boolean.FALSE.equals(enemy.controllable()) && "sieging".equals(enemy.armyState())
                && BigInteger.valueOf(3).equals(enemy.armyStateCode())
                && Boolean.FALSE.equals(enemy.inCombat()) && Boolean.FALSE.equals(enemy.retreating())
                && positive(enemy.currentProvinceId()) && Boolean.TRUE.equals(enemy.siegeProvinceInPlayerSubrealm())
                && enemy.moveTargetProvinceId().presence() == Presence.NULL
                && enemy.routeProvinceIds() != null && enemy.routeProvinceIds().isEmpty()
                && "complete_empty".equals(enemy.routeReadStatus());
    }

    public static boolean warQualifies(Snapshot snapshot, War war) {
        if (war == null || war.enemyArmies() == null) { return false; }
        return war.enemyArmies().stream().anyMatch(enemy -> qualifies(snapshot, war, enemy));
    }

    /** All current consumers can reuse the same document-owned instances and stored row order. */
    public static Assessment assess(Request request) {
        Objects.requireNonNull(request);
        Snapshot snapshot = request.snapshot();
        List<WarScope> scopes = new ArrayList<>();
        if (snapshot.activeWars() != null) {
            for (War war : snapshot.activeWars()) {
                List<Boolean> enemies = new ArrayList<>();
                if (war.enemyArmies() != null) {
                    for (Enemy enemy : war.enemyArmies()) { enemies.add(qualifies(snapshot, war, enemy)); }
                }
                scopes.add(new WarScope(war.warId(), warQualifies(snapshot, war), enemies));
            }
        }
        return new Assessment(qualifies(snapshot, request.candidateWar(), request.candidateEnemy()),
                warQualifies(snapshot, request.candidateWar()), scopes);
    }

    private static boolean frameObserved(Snapshot snapshot) {
        PlayedCharacter played = snapshot.playedCharacter(); Diagnostics diagnostics = snapshot.diagnostics();
        return played != null && diagnostics != null && "injected-dll-named-pipe".equals(snapshot.source())
                && positive(snapshot.nativeRevision()) && ("native:" + snapshot.nativeRevision()).equals(snapshot.snapshotId())
                && nonnegative(snapshot.revision()) && snapshot.dateRaw() != null
                && snapshot.episodeRunId() != null && !snapshot.episodeRunId().isEmpty()
                && Boolean.TRUE.equals(snapshot.paused()) && Boolean.TRUE.equals(snapshot.mapReady())
                && snapshot.activeEvent() != Presence.VALUE && snapshot.pendingCharacterInteraction() != Presence.VALUE
                && "native".equals(played.source()) && positive(played.characterId()) && Boolean.TRUE.equals(played.alive())
                && Boolean.TRUE.equals(diagnostics.connected()) && positive(diagnostics.bridgePid())
                && nonnegative(diagnostics.connectionGeneration());
    }

    private static War resolveWar(Snapshot snapshot, List<War> detached, WarReference reference) {
        List<War> rows = reference.collection() == WarCollection.ACTIVE_WARS ? snapshot.activeWars() : detached;
        return at(rows, reference.index());
    }
    private static Enemy resolveEnemy(War candidateWar, List<Enemy> detached, EnemyReference reference) {
        List<Enemy> rows = reference.collection() == EnemyCollection.CANDIDATE_WAR_ENEMIES
                ? candidateWar == null ? null : candidateWar.enemyArmies() : detached;
        return at(rows, reference.index());
    }
    private static <T> T at(List<T> rows, int index) {
        if (rows == null || index >= rows.size()) { throw new IllegalArgumentException("local member reference is outside document"); }
        return rows.get(index);
    }
    private static <T> boolean containsIdentity(List<T> rows, T candidate) {
        return rows != null && rows.stream().anyMatch(row -> row == candidate);
    }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    private static boolean publicCunit(BigInteger value) {
        return value != null && value.signum() >= 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0;
    }
    private static boolean nonnegative(BigInteger value) { return value != null && value.signum() >= 0; }
    private static void nonnegativeIndex(int index) {
        if (index < 0) { throw new IllegalArgumentException("nonnegative local reference index required"); }
    }
    private static <T> List<T> copyNullable(List<T> rows) { return rows == null ? null : List.copyOf(rows); }
}
