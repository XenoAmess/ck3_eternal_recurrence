package org.xar.ck3.control.wave3.planning.participatingwar;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/** Detached facts from all published participant wars; owns no query or action port. */
public final class ParticipatingWarThreats {
    private ParticipatingWarThreats() { }
    public enum Leadership { PRIMARY, NON_PRIMARY, MISSING, EXPLICIT_NULL }
    public enum Presence { OBSERVED, MISSING, EXPLICIT_NULL, INVALID }
    public enum Reason {
        CURRENT_FRAME_IDENTITY_UNAVAILABLE, CURRENT_PAUSED_LIVING_PLAYER_REQUIRED,
        PUBLISHED_ACTIVE_WAR_ARRAY_UNAVAILABLE, DISTINCT_NATIVE_PARTICIPATING_WAR_IDENTITY_UNAVAILABLE,
        PUBLISHED_ENEMY_ARMY_ARRAY_UNAVAILABLE, PUBLISHED_ENEMY_ARMY_IDENTITY_UNAVAILABLE,
        STRENGTH_CACHE_CONTRACT_UNAVAILABLE, PUBLISHED_SNAPSHOT_BOUNDARY_UNAVAILABLE
    }
    public enum NonParticipantLiegeScope { UNASSESSED_NONPARTICIPANT_LIEGE_WARS }
    public sealed interface Soldiers permits Present, Missing, ExplicitNull, Invalid { }
    public record Present(BigInteger value) implements Soldiers {
        public Present { require(value != null && value.signum() >= 0, "nonnegative soldier integer required"); }
    }
    public record Missing() implements Soldiers { }
    public record ExplicitNull() implements Soldiers { }
    public record Invalid() implements Soldiers { }
    public record Army(int armyId, Soldiers soldiers) {
        public Army { require(armyId >= 0, "public ArmyID must retain slot zero"); Objects.requireNonNull(soldiers); }
    }
    public record War(int warId, Leadership leadership, List<Army> enemies) {
        public War { require(warId > 0, "positive scope WarID required; raw zero remains unassessed"); Objects.requireNonNull(leadership); enemies = List.copyOf(enemies); }
    }
    public record CacheRow(int armyId, String role, boolean available, Soldiers soldiers) {
        public CacheRow { require(armyId >= 0, "public ArmyID required"); Objects.requireNonNull(role); Objects.requireNonNull(soldiers); }
    }
    public record Snapshot(Frame frame, List<War> wars, boolean currentStrengthCache, List<CacheRow> strengths) {
        public Snapshot { Objects.requireNonNull(frame); wars = List.copyOf(wars); strengths = List.copyOf(strengths); }
    }
    public record Membership(int armyId, List<Integer> warIds) {
        public Membership { require(armyId >= 0, "public ArmyID required"); warIds = List.copyOf(warIds);
            require(!warIds.isEmpty() && new HashSet<>(warIds).size() == warIds.size() && warIds.stream().allMatch(id -> id > 0), "distinct positive membership WarIDs required"); }
    }
    public sealed interface Strength permits Known, Unknown, Conflict { }
    public record Known(BigInteger soldiers) implements Strength {
        public Known { require(soldiers != null && soldiers.signum() >= 0, "nonnegative soldiers required"); }
    }
    public record Unknown(Presence firstUnavailablePresence) implements Strength {
        public Unknown { require(firstUnavailablePresence != null && firstUnavailablePresence != Presence.OBSERVED, "unknown source presence required"); }
    }
    public record Conflict(int armyId) implements Strength {
        public Conflict { require(armyId >= 0, "conflicting public ArmyID required"); }
    }
    public sealed interface Observation permits Observed, Unavailable {
        default NonParticipantLiegeScope nonParticipantLiegeScope() { return NonParticipantLiegeScope.UNASSESSED_NONPARTICIPANT_LIEGE_WARS; }
        default boolean actionAuthorized() { return false; }
    }
    public record Observed(Frame frame, List<Integer> participatingWarIds, List<Integer> primaryWarIds,
                           List<Integer> nonPrimaryWarIds, List<Integer> leadershipUnknownWarIds,
                           List<Membership> enemyArmyMemberships, Strength strength) implements Observation {
        public Observed {
            Objects.requireNonNull(frame); participatingWarIds = List.copyOf(participatingWarIds);
            primaryWarIds = List.copyOf(primaryWarIds); nonPrimaryWarIds = List.copyOf(nonPrimaryWarIds);
            leadershipUnknownWarIds = List.copyOf(leadershipUnknownWarIds); enemyArmyMemberships = List.copyOf(enemyArmyMemberships); Objects.requireNonNull(strength);
            Set<Integer> all = new HashSet<>(participatingWarIds), groups = new HashSet<>();
            require(all.size() == participatingWarIds.size() && all.stream().allMatch(id -> id > 0), "distinct positive participating wars required");
            for (List<Integer> group : List.of(primaryWarIds, nonPrimaryWarIds, leadershipUnknownWarIds)) {
                for (int id : group) require(all.contains(id) && groups.add(id), "war leadership groups must partition scope");
            }
            require(groups.equals(all), "war leadership groups must cover scope"); Set<Integer> armies = new HashSet<>();
            for (Membership row : enemyArmyMemberships) require(armies.add(row.armyId()) && all.containsAll(row.warIds()), "distinct armies and scoped memberships required");
            if (strength instanceof Conflict conflict) require(armies.contains(conflict.armyId()), "conflict must name an observed enemy");
        }
        public List<Integer> uniqueEnemyArmyIds() { return enemyArmyMemberships.stream().map(Membership::armyId).toList(); }
        public boolean leadershipScopeComplete() { return leadershipUnknownWarIds.isEmpty(); }
    }
    public record Unavailable(Optional<Frame> sourceFrame, Reason reason, Presence sourcePresence) implements Observation {
        public Unavailable { Objects.requireNonNull(sourceFrame); Objects.requireNonNull(reason); Objects.requireNonNull(sourcePresence); }
    }


    /** Consequences remain unassessed even when every observed raised soldier is counted. */
    public enum NonPrimaryRiskStatus {
        UNASSESSED, NO_OBSERVED_NON_PRIMARY_OR_UNRESOLVED_LEADERSHIP_WARS
    }
    public sealed interface NonPrimaryRisk permits ObservedNonPrimaryRisk, UnavailableNonPrimaryRisk {
        default NonParticipantLiegeScope nonParticipantLiegeScope() {
            return NonParticipantLiegeScope.UNASSESSED_NONPARTICIPANT_LIEGE_WARS;
        }
        default boolean politicalAndTerritorialConsequencesAssessed() { return false; }
        default boolean unraisedReservesBounded() { return false; }
        default boolean actionAuthorized() { return false; }
    }
    public record ObservedNonPrimaryRisk(Frame frame, List<Integer> nonPrimaryWarIds,
                                         List<Integer> leadershipUnknownWarIds) implements NonPrimaryRisk {
        public ObservedNonPrimaryRisk {
            Objects.requireNonNull(frame);
            nonPrimaryWarIds = List.copyOf(nonPrimaryWarIds);
            leadershipUnknownWarIds = List.copyOf(leadershipUnknownWarIds);
            Set<Integer> wars = new HashSet<>();
            for (List<Integer> group : List.of(nonPrimaryWarIds, leadershipUnknownWarIds))
                for (int id : group) require(id > 0 && wars.add(id), "distinct positive risk WarIDs required");
        }
        public NonPrimaryRiskStatus status() {
            return nonPrimaryWarIds.isEmpty() && leadershipUnknownWarIds.isEmpty()
                    ? NonPrimaryRiskStatus.NO_OBSERVED_NON_PRIMARY_OR_UNRESOLVED_LEADERSHIP_WARS
                    : NonPrimaryRiskStatus.UNASSESSED;
        }
    }
    public record UnavailableNonPrimaryRisk(Optional<Frame> sourceFrame, Reason reason,
                                             Presence sourcePresence) implements NonPrimaryRisk {
        public UnavailableNonPrimaryRisk {
            Objects.requireNonNull(sourceFrame); Objects.requireNonNull(reason); Objects.requireNonNull(sourcePresence);
        }
    }

    /** The observed enemy count supplies no CB effects or non-leading political consequences. */
    public static NonPrimaryRisk nonPrimaryRisk(Observation observation) {
        Objects.requireNonNull(observation);
        return switch (observation) {
            case Observed value -> new ObservedNonPrimaryRisk(value.frame(), value.nonPrimaryWarIds(),
                    value.leadershipUnknownWarIds());
            case Unavailable value -> new UnavailableNonPrimaryRisk(value.sourceFrame(), value.reason(),
                    value.sourcePresence());
        };
    }

    /** Reproduces the original current-cache/fallback count while preserving every enemy membership. */
    public static Observed observe(Snapshot snapshot) {
        List<Integer> ids = new ArrayList<>(), primary = new ArrayList<>(), nonPrimary = new ArrayList<>(), unknown = new ArrayList<>();
        LinkedHashMap<Integer, List<Integer>> memberships = new LinkedHashMap<>(); List<Army> enemies = new ArrayList<>();
        for (War war : snapshot.wars()) {
            require(!ids.contains(war.warId()), "duplicate WarID"); ids.add(war.warId());
            switch (war.leadership()) {
                case PRIMARY -> primary.add(war.warId());
                case NON_PRIMARY -> nonPrimary.add(war.warId());
                case MISSING, EXPLICIT_NULL -> unknown.add(war.warId());
            }
            for (Army army : war.enemies()) {
                List<Integer> wars = memberships.computeIfAbsent(army.armyId(), ignored -> new ArrayList<>());
                if (!wars.contains(war.warId())) wars.add(war.warId()); enemies.add(army);
            }
        }
        List<Membership> rows = memberships.entrySet().stream().map(row -> new Membership(row.getKey(), row.getValue())).toList();
        return new Observed(snapshot.frame(), ids, primary, nonPrimary, unknown, rows, count(enemies, snapshot));
    }
    private static Strength count(List<Army> armies, Snapshot snapshot) {
        LinkedHashMap<Integer, BigInteger> counts = new LinkedHashMap<>();
        for (Army army : armies) {
            Soldiers amount = army.soldiers();
            if (snapshot.currentStrengthCache()) {
                List<CacheRow> matching = snapshot.strengths().stream().filter(row -> row.armyId() == army.armyId() && row.role().equals("active_war_enemy")).toList();
                if (matching.size() == 1 && matching.getFirst().available()) amount = matching.getFirst().soldiers();
            }
            if (!(amount instanceof Present present)) return new Unknown(amount instanceof Missing ? Presence.MISSING : amount instanceof ExplicitNull ? Presence.EXPLICIT_NULL : Presence.INVALID);
            BigInteger previous = counts.putIfAbsent(army.armyId(), present.value());
            if (previous != null && !previous.equals(present.value())) return new Conflict(army.armyId());
        }
        return new Known(counts.values().stream().reduce(BigInteger.ZERO, BigInteger::add));
    }
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}
