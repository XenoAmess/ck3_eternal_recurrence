package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Default-off one-day speed-two candidate over every published regular own/allied/enemy CUnit. */
public final class WarDailyWatch {
    public static final String POLICY = "war_daily_watch_v1";
    public static final String SCHEMA = "xar.ck3.java-war-daily-watch/v1";
    private static final Map<String,Integer> STATES = Map.of("regular",1,"moving",7,"retreating",6,"sieging",3);
    private WarDailyWatch() { }
    public enum Boundary { CONNECTION_CHANGED, ACTOR_OR_EPISODE_CHANGED, FRAME_UNKNOWN, TERMINAL,
        ACTIVE_EVENT, PENDING_INTERACTION, EXCLUSIVE_MODAL_OR_UNKNOWN, MAP_UNAVAILABLE }
    public record LocalPlayer(boolean present, Optional<BigInteger> id) {
        public LocalPlayer { Objects.requireNonNull(id); require(present || id.isEmpty(), "missing local player cannot carry an ID"); id.ifPresent(value -> require(value.signum() >= 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "local player ID domain differs")); }
    }
    public record Army(int publicCunitId, int ownerCharacterId, int provinceId, Optional<Integer> targetProvinceId, boolean retreating) {
        public Army { require(publicCunitId > 0 && ownerCharacterId > 0 && provinceId > 0, "watch candidate retains original positive regular roster scope"); Objects.requireNonNull(targetProvinceId); targetProvinceId.ifPresent(value -> require(value > 0, "positive target province required")); }
    }
    public record Roster(List<Integer> warIds, List<Army> armies) {
        public Roster { warIds = List.copyOf(warIds); armies = List.copyOf(armies); require(!warIds.isEmpty() && warIds.equals(warIds.stream().distinct().sorted().toList())
                && warIds.stream().allMatch(value -> value > 0) && !armies.isEmpty() && armies.size() <= 64
                && armies.stream().map(Army::publicCunitId).toList().equals(armies.stream().map(Army::publicCunitId).distinct().sorted().toList()), "complete untrimmed sorted war/watch roster required"); }
    }
    public record Context(ObservationIdentity starting, BigInteger connectionGeneration, LocalPlayer localPlayer, Roster roster) {
        public Context { Objects.requireNonNull(starting); Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(localPlayer); Objects.requireNonNull(roster);
            require(connectionGeneration.signum() > 0 && connectionGeneration.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "original watch connection domain required"); }
        public List<Integer> watchArmyIds() { return roster.armies().stream().map(Army::publicCunitId).toList(); }
        public boolean sameConnection(AdvanceObservationPort.Frame frame) {
            try { return frame.identity().machineId().equals(starting.machineId()) && frame.identity().game().equals(starting.game())
                    && connection(frame.semantic()).equals(Optional.of(new Connection(BigInteger.valueOf(starting.game().pid()), connectionGeneration))); }
            catch (IllegalArgumentException invalid) { return false; }
        }
        public boolean sameOwner(AdvanceObservationPort.Frame frame) {
            try { return sameConnection(frame) && frame.identity().frame().episodeRunId().equals(starting.frame().episodeRunId())
                    && frame.identity().frame().identity().player().equals(starting.frame().identity().player())
                    && local(frame.semantic()).equals(localPlayer) && owner(frame.semantic()); }
            catch (IllegalArgumentException invalid) { return false; }
        }
        public Optional<Boundary> boundary(AdvanceObservationPort.Frame frame) {
            if (!sameConnection(frame)) return Optional.of(Boundary.CONNECTION_CHANGED);
            if (!sameOwner(frame)) return Optional.of(Boundary.ACTOR_OR_EPISODE_CHANGED);
            if (frame.identity().frame().revision().compareTo(starting.frame().revision()) < 0
                    || frame.identity().frame().identity().nativeRevision().compareTo(starting.frame().identity().nativeRevision()) < 0
                    || frame.identity().frame().identity().dateRaw().compareTo(starting.frame().identity().dateRaw()) < 0) return Optional.of(Boundary.FRAME_UNKNOWN);
            return mandatory(frame.semantic());
        }
        public boolean readyToArm(AdvanceObservationPort.Frame frame) {
            return boundary(frame).isEmpty() && AdvancePolicy.truth(frame.semantic(), "paused")
                    && frame.identity().frame().identity().dateRaw().equals(starting.frame().identity().dateRaw())
                    && new IntegerValue(BigInteger.TWO).equals(frame.semantic().get("speed")) && WarDailyWatch.roster(frame.semantic()).equals(Optional.of(roster));
        }
    }
    private record Connection(BigInteger bridgePid, BigInteger generation) { }
    public static Optional<Context> select(AdvanceObservationPort.Frame frame, boolean enabled, boolean exactOneDay,
            String resultStep, Optional<String> proofKind, Set<String> capabilities, Set<OperationKey> steps, boolean assaultInProgress) {
        if (!enabled || !exactOneDay || !resultStep.equals("life-advance-one-day") || proofKind.isPresent() || assaultInProgress
                || !AdvancePolicy.truth(frame.semantic(), "paused") || mandatory(frame.semantic()).isPresent()
                || !ClockStatusRead.available(capabilities) || !capabilities.contains("game.state.pending-character-interaction")
                || !steps.containsAll(Set.of(new OperationKey("set-speed-2"), new OperationKey("pause-map"), new OperationKey("resume-map")))) return Optional.empty();
        try {
            Optional<Connection> connection = connection(frame.semantic()); Optional<Roster> roster = roster(frame.semantic());
            var identity = frame.identity();
            if (connection.isEmpty() || roster.isEmpty() || !owner(frame.semantic())
                    || !positive(frame.semantic().get("date_raw")) || !positive(frame.semantic().get("revision")) || !positive(frame.semantic().get("native_revision"))
                    || !identity.frame().snapshotId().equals("native:" + identity.frame().identity().nativeRevision())) return Optional.empty();
            return Optional.of(new Context(identity, connection.orElseThrow().generation(), local(frame.semantic()), roster.orElseThrow()));
        } catch (IllegalArgumentException | ArithmeticException invalid) { return Optional.empty(); }
    }
    private static Optional<Connection> connection(Obj snapshot) {
        if (!(snapshot.get("diagnostics") instanceof Obj diagnostic) || !AdvancePolicy.truth(diagnostic, "connected")
                || !(diagnostic.get("hello") instanceof Obj hello) || !AdvancePolicy.truth(hello, "ck3_build_match")) return Optional.empty();
        Value version = hello.members().containsKey("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version");
        Value sha = hello.members().containsKey("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256");
        if (!(version instanceof Text text) || !(sha instanceof Text digest) || !ExactCk3Build.CK3_12004.matches(text.value(), digest.value())
                || !positive(diagnostic.get("bridge_pid")) || !positive(diagnostic.get("connection_generation"))) return Optional.empty();
        return Optional.of(new Connection(integer(diagnostic.get("bridge_pid"), "bridge_pid"), integer(diagnostic.get("connection_generation"), "connection_generation")));
    }
    private static boolean owner(Obj snapshot) {
        return snapshot.get("played_character") instanceof Obj played && AdvancePolicy.truth(played, "alive")
                && positive(played.get("character_id")) && Objects.equals(snapshot.get("episode_character_id"), played.get("character_id"))
                && snapshot.get("episode_run_id") instanceof Text episode && !episode.value().isEmpty();
    }
    private static LocalPlayer local(Obj snapshot) {
        Value value = snapshot.get("local_player_id");
        return new LocalPlayer(snapshot.members().containsKey("local_player_id"), value == null || value == Nil.INSTANCE ? Optional.empty() : Optional.of(integer(value, "local_player_id")));
    }
    private static Optional<Boundary> mandatory(Obj snapshot) {
        if (!AdvancePolicy.falsehood(snapshot, "one_life_terminal") || snapshot.get("one_life_terminal_reason") != Nil.INSTANCE) return Optional.of(Boundary.TERMINAL);
        if (snapshot.get("active_event") != Nil.INSTANCE) return Optional.of(Boundary.ACTIVE_EVENT);
        if (snapshot.get("pending_character_interaction") != Nil.INSTANCE) return Optional.of(Boundary.PENDING_INTERACTION);
        if (!(snapshot.get("top_exclusive_modal_choice_hint") instanceof Obj hint) || !new Text("absent").equals(hint.get("status")) || !AdvancePolicy.truth(hint, "owner_verified")) return Optional.of(Boundary.EXCLUSIVE_MODAL_OR_UNKNOWN);
        return AdvancePolicy.truth(snapshot, "map_ready") ? Optional.empty() : Optional.of(Boundary.MAP_UNAVAILABLE);
    }
    private static Optional<Roster> roster(Obj snapshot) {
        try {
            List<Obj> players = objects(snapshot.get("player_armies")), wars = objects(snapshot.get("active_wars"));
            if (players.isEmpty() || wars.isEmpty() || !(snapshot.get("played_character") instanceof Obj played)) return Optional.empty();
            int actor = integer(played.get("character_id"), "character_id").intValueExact();
            Map<Integer,Army> all = new TreeMap<>(); Set<Integer> allied = new HashSet<>(), enemy = new HashSet<>(), warIds = new HashSet<>();
            add(players, true, actor, all, allied);
            for (Obj war : wars) {
                int id = positiveInt(war.get("war_id")); require(warIds.add(id), "duplicate WarID");
                add(objects(war.get("allied_armies")), false, actor, all, allied);
                add(objects(war.get("enemy_armies")), false, actor, all, enemy);
            }
            require(allied.stream().noneMatch(enemy::contains), "one CUnit appeared on both sides");
            return Optional.of(new Roster(warIds.stream().sorted().toList(), List.copyOf(all.values())));
        } catch (IllegalArgumentException | ArithmeticException invalid) { return Optional.empty(); }
    }
    private static void add(List<Obj> rows, boolean owned, int actor, Map<Integer,Army> all, Set<Integer> side) {
        Set<Integer> seen = new HashSet<>();
        for (Obj row : rows) {
            int id = positiveInt(row.get("army_id")), owner = positiveInt(row.get("owner_character_id")), province = positiveInt(row.get("current_province_id"));
            require(row.members().containsKey("move_target_province_id"), "move target must be explicit null or ID");
            Optional<Integer> target = row.get("move_target_province_id") == Nil.INSTANCE ? Optional.empty() : Optional.of(positiveInt(row.get("move_target_province_id")));
            boolean retreating = bool(row.get("retreating"), "retreating"), controlled = bool(row.get("controllable"), "controllable");
            String state = text(row.get("army_state"), "army_state");
            require(AdvancePolicy.falsehood(row, "in_combat") && STATES.containsKey(state) && state.equals("retreating") == retreating
                    && (!row.members().containsKey("army_state_code") || new IntegerValue(BigInteger.valueOf(STATES.get(state))).equals(row.get("army_state_code")))
                    && (!owned || controlled && owner == actor) && seen.add(id), "unknown/combat/duplicate or inconsistent watch army");
            Army fingerprint = new Army(id, owner, province, target, retreating); Army previous = all.putIfAbsent(id, fingerprint);
            require(previous == null || previous.equals(fingerprint), "same published CUnit changed its fingerprint"); side.add(id);
        }
    }
    private static List<Obj> objects(Value value) { return array(value, "complete roster").stream().map(row -> object(row, "army/war row")).toList(); }
    private static boolean positive(Value value) { return value instanceof IntegerValue number && number.value().signum() > 0 && number.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0; }
    private static int positiveInt(Value value) { require(positive(value), "watch candidate requires original positive int32 identity"); return integer(value, "id").intValueExact(); }
    public static Obj encode(Context context) {
        List<Value> armies = context.roster().armies().stream().map(army -> (Value) new Obj(Map.of("public_cunit_id", number(army.publicCunitId()),
                "owner_character_id", number(army.ownerCharacterId()), "province_id", number(army.provinceId()),
                "target_province_id", army.targetProvinceId().<Value>map(WarDailyWatch::number).orElse(Nil.INSTANCE), "retreating", new Bool(army.retreating())))).toList();
        return new Obj(Map.of("schema", new Text(SCHEMA), "starting", org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(ProposalLifecycleCodec.observation(context.starting()))),
                "connection_generation", new Text(context.connectionGeneration().toString()), "local_player_present", new Bool(context.localPlayer().present()),
                "local_player_id", context.localPlayer().id().<Value>map(IntegerValue::new).orElse(Nil.INSTANCE),
                "war_ids", new Arr(context.roster().warIds().stream().map(id -> (Value) number(id)).toList()), "armies", new Arr(armies)));
    }
    public static Context decode(Obj row) {
        require(row.members().keySet().equals(Set.of("schema","starting","connection_generation","local_player_present","local_player_id","war_ids","armies")) && new Text(SCHEMA).equals(row.get("schema")), "war daily watch context fields/version differ");
        List<Army> armies = new ArrayList<>();
        for (Value value : array(row.get("armies"), "armies")) {
            Obj army = object(value, "army"); require(army.members().keySet().equals(Set.of("public_cunit_id","owner_character_id","province_id","target_province_id","retreating")), "watch fingerprint fields differ");
            armies.add(new Army(positiveInt(army.get("public_cunit_id")),positiveInt(army.get("owner_character_id")),positiveInt(army.get("province_id")),
                    army.get("target_province_id") == Nil.INSTANCE ? Optional.empty() : Optional.of(positiveInt(army.get("target_province_id"))), bool(army.get("retreating"),"retreating")));
        }
        var generation = new CrossJsDecimalUInt64(text(row.get("connection_generation"), "connection_generation"));
        return new Context(ProposalLifecycleCodec.decodeObservation(toNode(row.get("starting"))), new BigInteger(generation.decimal()),
                new LocalPlayer(bool(row.get("local_player_present"),"local_player_present"), row.get("local_player_id") == Nil.INSTANCE ? Optional.empty() : Optional.of(integer(row.get("local_player_id"),"local_player_id"))),
                new Roster(array(row.get("war_ids"), "war_ids").stream().map(WarDailyWatch::positiveInt).toList(), armies));
    }
    private static IntegerValue number(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
}
