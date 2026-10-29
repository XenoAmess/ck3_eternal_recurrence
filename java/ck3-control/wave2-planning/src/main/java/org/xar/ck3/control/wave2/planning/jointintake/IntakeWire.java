package org.xar.ck3.control.wave2.planning.jointintake;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/** Concentrated strict projection of extensible legacy snapshot/source containers. */
final class IntakeWire {
    private IntakeWire() { }
    static final Set<String> FRAME_FIELDS = Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id");
    static Frame frame(Obj row, boolean exact) {
        if (exact) require(row.members().keySet().equals(FRAME_FIELDS), "exact observed frame required");
        Value actor = row.get("played_character_id");
        if (!exact && (actor == null || actor == Nil.INSTANCE) && row.get("played_character") instanceof Obj played)
            actor = played.get("character_id");
        return new Frame(positive(actor, "played character"), positive(row.get("native_revision"), "native revision"),
                nonnegative(row.get("date_raw"), "date"), text(row.get("snapshot_id"), "snapshot"),
                positive(row.get("revision"), "revision"), text(row.get("episode_run_id"), "episode"));
    }
    static Obj frameNode(Frame frame) {
        return new Obj(Map.of("played_character_id", number(frame.playedCharacterId()), "native_revision", number(frame.nativeRevision()),
                "date_raw", number(frame.dateRaw()), "snapshot_id", new Text(frame.snapshotId()), "revision", number(frame.revision()),
                "episode_run_id", new Text(frame.episodeRunId())));
    }
    static void sourceFrame(Value value, Frame expected, String actorKey) {
        Obj source = object(value, "source frame"); Obj canonical = frameNode(expected);
        for (String key : List.of("native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id"))
            require(java.util.Objects.equals(source.get(key), canonical.get(key)), "source crossed observed frame: " + key);
        require(number(expected.playedCharacterId()).equals(source.get(actorKey)), "source actor crossed frame");
    }
    static BigInteger positive(Value value, String name) {
        BigInteger result = integer(value, name); require(result.signum() > 0, name + " must be positive"); return result;
    }
    static IntegerValue number(BigInteger value) { return new IntegerValue(value); }
    static Value presentOrNull(Obj object, String key) { Value value = object.get(key); return value == null ? Nil.INSTANCE : value; }
    static boolean missingOrNull(Value value) { return value == null || value == Nil.INSTANCE; }
    static void equalsValue(Value actual, Value expected, String name) { require(java.util.Objects.equals(actual, expected), name); }
    record Field(String name, Value value) { }
    static Field f(String name, Value value) { return new Field(name, value); }
    static Obj obj(Field... fields) {
        Map<String, Value> result = new LinkedHashMap<>();
        for (Field field : fields) { OpportunityJson.require(!result.containsKey(field.name()), "duplicate emitted field"); result.put(field.name(), field.value()); }
        return new Obj(result);
    }
    static Arr strings(List<String> values) { return new Arr(values.stream().<Value>map(Text::new).toList()); }
    static Arr integers(List<BigInteger> values) { return new Arr(values.stream().<Value>map(IntegerValue::new).toList()); }
    static List<BigInteger> ids(Value value, String name, boolean zeroAllowed) {
        List<BigInteger> result = new ArrayList<>();
        for (Value item : array(value, name)) result.add(zeroAllowed ? nonnegative(item, name) : positive(item, name));
        require(new java.util.HashSet<>(result).size() == result.size(), "duplicate " + name); result.sort(BigInteger::compareTo); return List.copyOf(result);
    }
    static Obj proposal(Frame frame, String id, String domain, String policy, BigInteger cost, BigInteger reserve,
                        Value supply, int slots, List<BigInteger> armies, List<BigInteger> allies,
                        List<BigInteger> characters, List<String> keys, Obj evidence, Value operation) {
        Obj raw = obj(f("schema", new Text("xar.ck3.m5-observed-opportunity.v1")), f("frame", frameNode(frame)),
                f("candidate_id", new Text(id)), f("domain", new Text(domain)), f("source_policy", new Text(policy)),
                f("domain_policy_ready", new Bool(true)), f("gold_cost_raw", number(cost)), f("minimum_gold_reserve_raw", number(reserve)),
                f("projected_supply_margin_raw", supply), f("war_slot_claim", number(BigInteger.valueOf(slots))), f("war_operation", operation),
                f("army_ids", integers(armies)), f("ally_character_ids", integers(allies)), f("character_ids", integers(characters)),
                f("commitment_keys", strings(keys)), f("evidence", evidence));
        return OpportunityJson.object(OpportunityJson.parse(ObservedOpportunitySelector.normalizeProposal(OpportunityJson.encode(
                obj(f("frame", frameNode(frame)), f("proposal", raw))))), "normalized proposal");
    }

    // Local input aliases deliberately leave shared parser/encoder and internal result invariants unmarked.
    private static void require(boolean condition, String reason) { IntakeWire.domain(condition, reason); }
    private static Obj object(Value value, String name) { return IntakeWire.inputObject(value, name); }
    private static List<Value> array(Value value, String name) { return IntakeWire.inputArray(value, name); }
    private static String text(Value value, String name) { return IntakeWire.inputText(value, name); }
    private static BigInteger integer(Value value, String name) { return IntakeWire.inputInteger(value, name); }
    private static BigInteger nonnegative(Value value, String name) { return IntakeWire.inputNonnegative(value, name); }
    private static boolean bool(Value value, String name) { return IntakeWire.inputBool(value, name); }

    /** Exact caller-input predicates only; parser, encoder, comparator and internal builders retain ordinary failures. */
    static void domain(boolean condition, String reason) { if (!condition) throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(reason); }
    static Obj inputObject(Value value, String name) { domain(value instanceof Obj, name + " must be an object"); return OpportunityJson.object(value, name); }
    static List<Value> inputArray(Value value, String name) { domain(value instanceof Arr, name + " must be an array"); return OpportunityJson.array(value, name); }
    static String inputText(Value value, String name) { domain(value instanceof Text && !((Text) value).value().isEmpty(), name + " must be nonempty text"); return OpportunityJson.text(value, name); }
    static BigInteger inputInteger(Value value, String name) { domain(value instanceof IntegerValue, name + " must be an integer token"); return OpportunityJson.integer(value, name); }
    static BigInteger inputNonnegative(Value value, String name) { BigInteger result = inputInteger(value, name); domain(result.signum() >= 0, name + " must be nonnegative"); return result; }
    static boolean inputBool(Value value, String name) { domain(value instanceof Bool, name + " must be a boolean"); return OpportunityJson.bool(value, name); }
}
