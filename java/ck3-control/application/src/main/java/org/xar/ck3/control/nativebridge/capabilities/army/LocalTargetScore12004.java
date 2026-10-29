package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Exact .4 local target-score stage. It grants no candidate, move, retreat or battle probability. */
public final class LocalTargetScore12004 {
    public static final String EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final int REJECTED_SCORE = -1_000_000;
    private static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private LocalTargetScore12004() { }

    public record Scope(String episode, String connectionGeneration, String nativeRevision,
                        String coordinatorIdentity, String updateSequence, int dateRaw, String exeSha256) {
        public Scope {
            Objects.requireNonNull(episode); if (episode.isBlank()) throw new IllegalArgumentException("episode required");
            decimal(connectionGeneration); decimal(nativeRevision); decimal(coordinatorIdentity); decimal(updateSequence);
            if (!EXE_SHA256.equals(exeSha256)) throw new IllegalArgumentException("exact .4 executable required");
        }
    }
    public enum LazyGate {
        RESOLVED_ZERO(0), RESOLVED_ONE(1), UNRESOLVED(2);
        private final int raw;
        LazyGate(int raw) { this.raw = raw; }
        public int raw() { return raw; }
        public static LazyGate fromRaw(int raw) {
            return switch (raw) { case 0 -> RESOLVED_ZERO; case 1 -> RESOLVED_ONE; case 2 -> UNRESOLVED;
                default -> throw new IllegalArgumentException("unknown native lazy gate"); };
        }
    }
    public record Constants(int supportOne, int supportTwo, int supportThree, int isSieging,
                            int wouldLiftSiege, int wouldStartCombat, int wouldStartSiege,
                            int closeRadius, int closeScore, int adjacentFriendlyScore) { }
    public record Relation(int firstRaw, int secondRaw) {
        public Relation { u8(firstRaw); u8(secondRaw); }
    }
    public record Facts(Scope scope, int flagsRaw, int relationRaw, int supportDepth, LazyGate localGate,
                        int kindRaw, int modeRaw, boolean sameOriginalTarget, int provinceX, int provinceY,
                        int goalX, int goalY, int radiusAdjustment, Constants constants, List<Relation> adjacent) {
        public Facts {
            Objects.requireNonNull(scope); u8(flagsRaw); u8(relationRaw); u8(kindRaw);
            Objects.requireNonNull(localGate); Objects.requireNonNull(constants); adjacent = List.copyOf(adjacent);
            if (adjacent.size() > 65_536) throw new IllegalArgumentException("adjacent scope exceeds native bound");
            if (sameOriginalTarget && !((flagsRaw & 0x10) != 0 && relationRaw <= 1))
                throw new IllegalArgumentException("same-target witness outside the original getter branch");
        }
    }
    public sealed interface Observation permits Available, Incomplete { Scope scope(); }
    public record Available(Facts facts) implements Observation {
        public Available { Objects.requireNonNull(facts); }
        @Override public Scope scope() { return facts.scope(); }
    }
    public record Incomplete(Scope scope, String reason) implements Observation {
        public Incomplete {
            Objects.requireNonNull(scope); Objects.requireNonNull(reason);
            if (!reason.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded diagnostic required");
        }
    }
    public sealed interface Result permits Scored, NotReady { }
    public record Scored(int delta, boolean rejected) implements Result {
        public Scored { if (rejected && delta != REJECTED_SCORE) throw new IllegalArgumentException("native sentinel differs"); }
        /** Actual 1A0582E caller: exact sentinel overwrites; all other deltas add with int32 wrap. */
        public int applyToPrior(int prior) { return delta == REJECTED_SCORE ? delta : prior + delta; }
    }
    public record NotReady(String reason) implements Result {
        public NotReady { Objects.requireNonNull(reason); }
    }

    /** No cached Facts are retained. A later query/update must supply its own observation. */
    public static Result consume(Scope current, Observation originalRead) {
        Objects.requireNonNull(current); Objects.requireNonNull(originalRead);
        if (!current.equals(originalRead.scope())) return new NotReady("coordinator_update_or_source_changed");
        if (originalRead instanceof Incomplete missing) return new NotReady(missing.reason());
        Facts f = ((Available) originalRead).facts();
        int flags = f.flagsRaw();
        if (((flags & 1) != 0 || (flags & 2) != 0 && f.kindRaw() == 1) && f.modeRaw() == 1)
            return new Scored(REJECTED_SCORE, true);
        // 19EF690 would mutate +10 when it is 2. This observer never calls it or invents its result.
        if (f.localGate() == LazyGate.UNRESOLVED) return new NotReady("native_local_gate_unresolved");
        boolean special = (flags & 0x10) != 0 && f.relationRaw() <= 1;
        boolean combat = f.localGate() != LazyGate.RESOLVED_ZERO && (flags & 0x20) != 0;
        boolean geometry = (flags & 0xc0) != 0 || f.sameOriginalTarget();
        int score = !geometry && !combat && !special && !(f.kindRaw() == 7 && (flags & 4) != 0) ? -1000 : 0;
        Constants c = f.constants();
        score += switch (f.supportDepth()) { case 1 -> c.supportOne(); case 2 -> c.supportTwo(); case 3 -> c.supportThree(); default -> 0; };
        if (f.sameOriginalTarget()) score += c.isSieging();
        else if ((flags & 0x80) != 0) score += c.wouldLiftSiege();
        else if (combat) score += c.wouldStartCombat();
        else if ((flags & 0x40) != 0) score += c.wouldStartSiege();
        if (geometry && f.kindRaw() != 0) {
            int dx = f.goalX() - f.provinceX(), dy = f.goalY() - f.provinceY();
            int radius = c.closeRadius() + f.radiusAdjustment();
            if (dx * dx + dy * dy < radius * radius) score += c.closeScore();
        }
        boolean adjacent = false;
        for (Relation r : f.adjacent()) {
            if (r.firstRaw() <= 1 || r.firstRaw() >= 8 && r.secondRaw() <= 1) adjacent = true;
        }
        if (adjacent) score += c.adjacentFriendlyScore();
        return new Scored(score, false);
    }

    public static Observation decode(byte[] wire) {
        ObjectNode n = closed(parse(wire), "schema_version", "scope", "status", "reason", "facts");
        if (i32(n.get("schema_version")) != 2) throw new IllegalArgumentException("local score schema version");
        Scope scope = scope(n.get("scope")); String status = text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts must be explicit null");
            return new Incomplete(scope, text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull()) throw new IllegalArgumentException("local score discriminant");
        ObjectNode f = closed(n.get("facts"), "flags_raw", "relation_raw", "support_depth", "local_gate_raw", "kind_raw", "mode_raw",
                "same_original_target", "province_x", "province_y", "goal_x", "goal_y", "radius_adjustment", "constants", "adjacent");
        ObjectNode c = closed(f.get("constants"), "support_one", "support_two", "support_three", "is_sieging", "would_lift_siege",
                "would_start_combat", "would_start_siege", "close_radius", "close_score", "adjacent_friendly_score");
        Constants constants = new Constants(i32(c.get("support_one")), i32(c.get("support_two")), i32(c.get("support_three")),
                i32(c.get("is_sieging")), i32(c.get("would_lift_siege")), i32(c.get("would_start_combat")), i32(c.get("would_start_siege")),
                i32(c.get("close_radius")), i32(c.get("close_score")), i32(c.get("adjacent_friendly_score")));
        List<Relation> adjacent = array(f.get("adjacent"), raw -> { ObjectNode r = closed(raw, "first_raw", "second_raw");
            return new Relation(i32(r.get("first_raw")), i32(r.get("second_raw"))); });
        return new Available(new Facts(scope, i32(f.get("flags_raw")), i32(f.get("relation_raw")), i32(f.get("support_depth")),
                LazyGate.fromRaw(i32(f.get("local_gate_raw"))), i32(f.get("kind_raw")), i32(f.get("mode_raw")), bool(f.get("same_original_target")),
                i32(f.get("province_x")), i32(f.get("province_y")), i32(f.get("goal_x")), i32(f.get("goal_y")), i32(f.get("radius_adjustment")), constants, adjacent));
    }
    public static byte[] encode(Observation value) {
        ObjectNode n = empty(); n.put("schema_version", 2); n.set("scope", encodeScope(value.scope()));
        if (value instanceof Incomplete missing) { n.put("status", "incomplete"); n.put("reason", missing.reason()); n.putNull("facts"); return bytes(n); }
        Facts v = ((Available) value).facts(); n.put("status", "available"); n.putNull("reason"); ObjectNode f = n.putObject("facts");
        f.put("flags_raw", v.flagsRaw()); f.put("relation_raw", v.relationRaw()); f.put("support_depth", v.supportDepth()); f.put("local_gate_raw", v.localGate().raw());
        f.put("kind_raw", v.kindRaw()); f.put("mode_raw", v.modeRaw()); f.put("same_original_target", v.sameOriginalTarget()); f.put("province_x", v.provinceX()); f.put("province_y", v.provinceY());
        f.put("goal_x", v.goalX()); f.put("goal_y", v.goalY()); f.put("radius_adjustment", v.radiusAdjustment()); Constants c = v.constants(); ObjectNode o = f.putObject("constants");
        o.put("support_one", c.supportOne()); o.put("support_two", c.supportTwo()); o.put("support_three", c.supportThree()); o.put("is_sieging", c.isSieging());
        o.put("would_lift_siege", c.wouldLiftSiege()); o.put("would_start_combat", c.wouldStartCombat()); o.put("would_start_siege", c.wouldStartSiege());
        o.put("close_radius", c.closeRadius()); o.put("close_score", c.closeScore()); o.put("adjacent_friendly_score", c.adjacentFriendlyScore());
        var rows = f.putArray("adjacent"); for (Relation r : v.adjacent()) { ObjectNode row = rows.addObject(); row.put("first_raw", r.firstRaw()); row.put("second_raw", r.secondRaw()); }
        return bytes(n);
    }
    static Scope scope(JsonNode raw) {
        ObjectNode n = closed(raw, "episode", "connection_generation", "native_revision", "coordinator_identity", "update_sequence", "date_raw", "exe_sha256");
        return new Scope(text(n.get("episode")), text(n.get("connection_generation")), text(n.get("native_revision")), text(n.get("coordinator_identity")), text(n.get("update_sequence")), i32(n.get("date_raw")), text(n.get("exe_sha256")));
    }
    static ObjectNode encodeScope(Scope s) {
        ObjectNode scope = empty(); scope.put("episode", s.episode()); scope.put("connection_generation", s.connectionGeneration()); scope.put("native_revision", s.nativeRevision());
        scope.put("coordinator_identity", s.coordinatorIdentity()); scope.put("update_sequence", s.updateSequence()); scope.put("date_raw", s.dateRaw()); scope.put("exe_sha256", s.exeSha256());
        return scope;
    }
    private static void decimal(String value) {
        Objects.requireNonNull(value);
        if (!value.matches("[1-9][0-9]{0,19}") || new BigInteger(value).compareTo(U64_MAX) > 0)
            throw new IllegalArgumentException("positive canonical uint64 decimal string required");
    }
    private static void u8(int value) { if (value < 0 || value > 255) throw new IllegalArgumentException("unsigned byte required"); }
}
