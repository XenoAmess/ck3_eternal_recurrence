package org.xar.ck3.control.wave3.planning.peacetimescope;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Frame;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Actor;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.CollectionState;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Flag;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Gold;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Presence;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Readback;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.Scene;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope.StableObservation;

/** Strict declared-field projection from two semantic observations, not from supplied qualification labels. */
public final class PeacetimeScopeCodec {
    public static final String SCHEMA = "xar.java.m5-peacetime-scope.v1";
    public static final int MAXIMUM_WRAPPER_BYTES = 131072;
    private PeacetimeScopeCodec() { }
    public record Request(Scene before, BigInteger expectedRevision, Readback readback) {
        public Request { Objects.requireNonNull(before); Objects.requireNonNull(expectedRevision); Objects.requireNonNull(readback); }
    }
    public static Request decode(byte[] raw) {
        Obj root = object(OpportunityJson.parse(raw), "request");
        exact(root, Set.of("schema", "before", "expected_revision", "reader"));
        require(text(root.get("schema"), "schema").equals(SCHEMA), "unsupported peacetime scope schema");
        BigInteger expectedRevision = integer(root.get("expected_revision"), "expected_revision");
        Scene before = project(object(root.get("before"), "before"));
        // Validate initial observations before interpreting any subsequent reader payload.
        PeacetimeScope.requirePeacefulFrame(before, expectedRevision);
        Obj reader = object(root.get("reader"), "reader"); String kind = text(reader.get("kind"), "reader.kind");
        Readback readback;
        if (kind.equals("unavailable")) {
            exact(reader, Set.of("kind")); readback = PeacetimeScope.ReaderUnavailable.INSTANCE;
        } else {
            require(kind.equals("returned"), "reader kind must be unavailable or returned"); exact(reader, Set.of("kind", "snapshot"));
            readback = reader.get("snapshot") instanceof Obj current
                    ? new PeacetimeScope.Observed(project(current)) : PeacetimeScope.MalformedSnapshot.INSTANCE;
        }
        return new Request(before, expectedRevision, readback);
    }
    public static StableObservation verify(byte[] raw) {
        Request request = decode(raw); return PeacetimeScope.verify(request.before, request.expectedRevision, request.readback);
    }
    public static byte[] encode(StableObservation observation) {
        Objects.requireNonNull(observation);
        Map<String, Value> fields = new LinkedHashMap<>();
        fields.put("frame", encodeFrame(observation.frame())); fields.put("observed_gold_raw", new IntegerValue(observation.observedGoldRaw()));
        return OpportunityJson.encode(new Obj(fields));
    }
    public static byte[] verifyAndEncode(byte[] raw) { return encode(verify(raw)); }

    /** Public adapter projection; no eligibility or successful-reader flag is consumed. */
    public static Scene project(Obj snapshot) {
        Value player = snapshot.get("played_character_id");
        Value playedValue = snapshot.get("played_character");
        Obj played = playedValue instanceof Obj obj ? obj : null;
        if (player == null || player == Nil.INSTANCE) { player = played == null ? null : played.get("character_id"); }
        Frame frame = new Frame(integer(player, "played_character_id"), integer(snapshot.get("native_revision"), "native_revision"),
                integer(snapshot.get("date_raw"), "date_raw"), text(snapshot.get("snapshot_id"), "snapshot_id"),
                integer(snapshot.get("revision"), "revision"), text(snapshot.get("episode_run_id"), "episode_run_id"));
        Actor actor = played == null ? null : new Actor(integer(played.get("character_id"), "played_character.character_id"), flag(played, "alive"));
        Value rawGold = snapshot.get("played_character_gold"); Gold gold = null;
        if (rawGold != null && rawGold != Nil.INSTANCE) {
            Obj wallet = object(rawGold, "played_character_gold");
            gold = new Gold(integer(wallet.get("raw"), "gold.raw"), integer(wallet.get("scale"), "gold.scale"));
        }
        return new Scene(frame, flag(snapshot, "paused"), flag(snapshot, "map_ready"), actor,
                presence(snapshot, "active_event"), presence(snapshot, "pending_character_interaction"), presence(snapshot, "one_life_terminal_reason"),
                collection(snapshot, "active_wars"), collection(snapshot, "player_armies"), gold);
    }
    private static Obj encodeFrame(Frame frame) {
        Map<String, Value> fields = new LinkedHashMap<>(); fields.put("played_character_id", new IntegerValue(frame.player()));
        fields.put("native_revision", new IntegerValue(frame.nativeRevision())); fields.put("date_raw", new IntegerValue(frame.dateRaw()));
        fields.put("snapshot_id", new Text(frame.snapshotId())); fields.put("revision", new IntegerValue(frame.revision()));
        fields.put("episode_run_id", new Text(frame.episodeRunId())); return new Obj(fields);
    }
    private static Flag flag(Obj row, String key) {
        Value value = row.get(key); if (value == null) { return Flag.MISSING; } if (value == Nil.INSTANCE) { return Flag.NULL; }
        require(value instanceof Bool, key + " must be a boolean token"); return ((Bool) value).value() ? Flag.TRUE : Flag.FALSE;
    }
    private static Presence presence(Obj row, String key) {
        Value value = row.get(key); return value == null ? Presence.MISSING : value == Nil.INSTANCE ? Presence.NULL : Presence.PRESENT;
    }
    private static CollectionState collection(Obj row, String key) {
        Value value = row.get(key); if (value == null) { return CollectionState.MISSING; } if (value == Nil.INSTANCE) { return CollectionState.NULL; }
        require(value instanceof Arr, key + " must be a JSON array"); return ((Arr) value).items().isEmpty() ? CollectionState.EMPTY : CollectionState.NONEMPTY;
    }
    private static Obj object(Value value, String name) { return OpportunityJson.object(value, name); }
    private static BigInteger integer(Value value, String name) { return OpportunityJson.integer(value, name); }
    private static String text(Value value, String name) { return OpportunityJson.text(value, name); }
    private static void exact(Obj row, Set<String> keys) { require(row.members().keySet().equals(keys), "missing or extra wrapper fields"); }
    private static void require(boolean condition, String message) { OpportunityJson.require(condition, message); }
}
