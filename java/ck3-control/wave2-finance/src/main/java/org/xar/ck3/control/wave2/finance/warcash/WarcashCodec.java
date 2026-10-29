package org.xar.ck3.control.wave2.finance.warcash;

import static org.xar.ck3.control.wave2.finance.warcash.WarcashModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Central raw-token boundary. SDK extensions are projected; domain classes never receive JSON. */
public final class WarcashCodec {
    public static final String REQUEST_SCHEMA = "g2.wave2-finance.warcash-request/v1";
    public static final int OUTPUT_MAX_BYTES = 65_536;
    private static final Set<String> FRAME_FIELDS = Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id");
    public enum Operation {
        OBSERVE_ACTIVE_WAR_CASH_RESOURCE_V1(Set.of("snapshot", "war_id", "inputs")),
        REQUIRE_COMPLETE_WAR_CASH_RESOURCE_V1(Set.of("receipt", "frame", "war_id")),
        OBSERVE_AGGREGATE_ACTIVE_WAR_CASH_RESOURCE_V1(Set.of("snapshot", "receipts")),
        REQUIRE_COMPLETE_AGGREGATE_WAR_CASH_RESOURCE_V1(Set.of("receipt", "frame", "war_ids"));
        private final Set<String> fields;
        Operation(Set<String> fields) { this.fields = fields; }
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
        static Operation parse(JsonNode value) {
            for (Operation operation : values()) { if (isText(value, operation.wire())) { return operation; } }
            throw new ContractViolationException("unknown war cash operation");
        }
    }
    /** Checked wire projection; opaque SDK extensions stay confined to this defensive boundary. */
    public record Request(Operation operation, ObjectNode arguments) {
        public Request {
            Objects.requireNonNull(operation, "operation");
            arguments = StrictJson.object(arguments, operation.fields).deepCopy();
        }
        @Override public ObjectNode arguments() { return arguments.deepCopy(); }
    }
    private WarcashCodec() { }
    public static Request parse(byte[] input) {
            ObjectNode request = StrictJson.object(StrictJson.parse(input), Set.of("schema", "operation", "arguments"));
            StrictJson.require(isText(request.get("schema"), REQUEST_SCHEMA), "war cash request schema differs");
            Operation operation = Operation.parse(request.get("operation"));
            return new Request(operation, StrictJson.object(request.get("arguments"), operation.fields));
    }
    public static JsonNode evaluate(Request request) {
            Objects.requireNonNull(request, "request");
            ObjectNode a = request.arguments;
            return switch (request.operation()) {
                case OBSERVE_ACTIVE_WAR_CASH_RESOURCE_V1 -> {
                    World world = world(a.get("snapshot")); BigInteger war = positiveInteger(a.get("war_id"));
                    yield single(WarcashPolicy.observe(world, inputs(a.get("inputs"), world.frame(), war)));
                }
                case REQUIRE_COMPLETE_WAR_CASH_RESOURCE_V1 -> verifySingle(a.get("receipt"), frame(a.get("frame"), false), positiveInteger(a.get("war_id"))).original();
                case OBSERVE_AGGREGATE_ACTIVE_WAR_CASH_RESOURCE_V1 -> aggregate(observeAggregate(world(a.get("snapshot")), a.get("receipts")));
                case REQUIRE_COMPLETE_AGGREGATE_WAR_CASH_RESOURCE_V1 -> aggregate(verifyCompleteAggregate(a.get("receipt"), frame(a.get("frame"), false), numberList(a.get("war_ids"), true)));
            };
    }
    public static byte[] evaluate(byte[] input) {
        try {
            return StrictJson.canonical(evaluate(parse(input)), OUTPUT_MAX_BYTES);
        } catch (ContractViolationException error) { throw error; }
        catch (IllegalArgumentException error) {
            if (error instanceof ProjectionDomainRejection && error.getCause() instanceof ContractViolationException original) { throw original; }
            throw new ContractViolationException("invalid war cash contract: " + error.getMessage(), error);
        }
    }
    public static ObjectNode single(SingleReceipt receipt) {
        ObjectNode result = StrictJson.object().put("schema", SINGLE_SCHEMA).put("status", receipt.complete() ? "complete" : "incomplete").put("read_only", true);
        result.set("source_frame", frame(receipt.frame())); result.put("war_id", receipt.warId()).put("gold_scale", GOLD_SCALE).put("observed_treasury_raw", receipt.treasuryRaw());
        put(result, "existing_shared_gold_commitment_raw", receipt.value(Amount.PENDING));
        put(result, "immediate_war_action_cost_raw", receipt.value(Amount.IMMEDIATE)); put(result, "war_future_gold_cost_raw", receipt.future());
        put(result, "minimum_gold_reserve_raw", receipt.value(Amount.POLICY)); put(result, "joint_gold_reserve_raw", receipt.jointReserve());
        put(result, "horizon_days", receipt.input().horizonDays());
        if (receipt.input().assumptions().isPresent()) { strings(result.putArray("future_bound_assumptions"), receipt.input().assumptions().orElseThrow()); }
        else { result.putNull("future_bound_assumptions"); }
        ObjectNode values = result.putObject("amount_values_raw"), sources = result.putObject("amount_sources"), observations = result.putObject("amount_observations");
        for (Amount amount : Amount.values()) {
            AmountFact fact = receipt.input().amounts().get(amount); put(values, amount.wire(), fact.raw());
            if (fact instanceof Measured measured) { sources.put(amount.wire(), measured.observation().source()); observations.set(amount.wire(), observation(measured.observation())); }
            else { sources.putNull(amount.wire()); observations.putNull(amount.wire()); }
        }
        if (receipt.input().claims().isPresent()) { result.set("resource_claims", claims(receipt.input().claims().orElseThrow())); }
        else { result.putNull("resource_claims"); }
        ObjectNode missing = result.putObject("missing"); receipt.missing().forEach(missing::put);
        return result.put("formal_action_ready", false);
    }
    public static ObjectNode aggregate(AggregateReceipt receipt) {
        ObjectNode result = StrictJson.object().put("schema", AGGREGATE_SCHEMA).put("status", receipt.complete() ? "complete" : "incomplete")
            .put("read_only", true).put("formal_action_ready", false);
        result.set("source_frame", frame(receipt.frame())); numbers(result.putArray("war_ids"), receipt.warIds());
        result.put("gold_scale", GOLD_SCALE).put("observed_treasury_raw", receipt.treasuryRaw());
        put(result, "existing_shared_gold_commitment_raw", receipt.values().get(Amount.PENDING));
        ObjectNode immediate = result.putObject("immediate_war_action_costs_raw");
        for (BigInteger id : receipt.warIds()) {
            Optional<SingleReceipt> row = receipt.receipts().stream().filter(item -> item.warId().equals(id)).findFirst();
            put(immediate, id.toString(), row.isPresent() ? row.orElseThrow().value(Amount.IMMEDIATE) : Optional.empty());
        }
        put(result, "war_future_gold_cost_raw", receipt.future()); put(result, "minimum_gold_reserve_raw", receipt.values().get(Amount.POLICY));
        put(result, "joint_gold_reserve_raw", receipt.jointReserve()); put(result, "horizon_days", receipt.horizonDays());
        ObjectNode assumptions = result.putObject("future_bound_assumptions_by_war");
        for (SingleReceipt row : receipt.receipts()) {
            if (row.input().assumptions().isPresent()) { strings(assumptions.putArray(row.warId().toString()), row.input().assumptions().orElseThrow()); }
            else { assumptions.putNull(row.warId().toString()); }
        }
        ObjectNode values = result.putObject("amount_values_raw"), resources = result.putObject("amount_resources");
        for (Amount amount : Amount.values()) {
            put(values, amount.wire(), receipt.values().get(amount)); ArrayNode array = resources.putArray(amount.wire());
            receipt.resources().get(amount).forEach(component -> array.add(component(component)));
        }
        if (receipt.occupied().isPresent()) { result.set("existing_resource_claims", union(receipt.occupied().orElseThrow())); }
        else { result.putNull("existing_resource_claims"); }
        ArrayNode rows = result.putArray("war_receipts"); receipt.receipts().forEach(row -> rows.add(single(row)));
        ObjectNode missing = result.putObject("missing"); receipt.missing().forEach(missing::put); return result;
    }
    private record VerifiedSingle(SingleReceipt receipt, ObjectNode original) { }
    public static Frame decodeObservedFrame(JsonNode value) { return frame(value, false); }
    public static SingleReceipt verifyCompleteSingle(JsonNode value, Frame expected, BigInteger war) {
        return verifySingle(value, expected, war).receipt();
    }
    private static VerifiedSingle verifySingle(JsonNode value, Frame expected, BigInteger war) {
        ObjectNode raw = record(value);
        require(isText(raw.get("schema"), SINGLE_SCHEMA) && isText(raw.get("status"), "complete") && actualTrue(raw.get("read_only"))
            && frame(raw.get("source_frame"), false).equals(expected) && positiveInteger(raw.get("war_id")).equals(war)
            && scale(raw.get("gold_scale")) && record(raw.get("missing")).isEmpty(), "complete same-frame active-war cash resource required");
        ObjectNode observations = record(raw.get("amount_observations")), sources = record(raw.get("amount_sources")), values = record(raw.get("amount_values_raw"));
        List<BigInteger> componentWars = new ArrayList<>(); componentWars.add(war);
        for (Amount amount : Amount.values()) {
            JsonNode observation = observations.get(amount.wire());
            if (observation != null && observation.has("resource_components")) {
                for (JsonNode component : array(observation.get("resource_components"))) {
                    for (BigInteger id : numberList(record(component).get("war_ids"), true)) { if (!componentWars.contains(id)) { componentWars.add(id); } }
                }
            }
        }
        EnumMap<Amount, AmountFact> facts = new EnumMap<>(Amount.class);
        for (Amount amount : Amount.values()) {
            Observation observed = parseObservation(observations.get(amount.wire()), expected, war, componentWars);
            require(observed.raw().equals(nonnegativeInteger(values.get(amount.wire())))
                && observed.source().equals(inputText(sources.get(amount.wire()))), "war cash amount lost same-frame provenance");
            facts.put(amount, new Measured(observed));
        }
        Optional<List<String>> assumptions = assumptions(raw.get("future_bound_assumptions"));
        require(assumptions.isPresent(), "bound assumptions required");
        Input input = new Input(expected, war, facts, Optional.of(positiveInteger(raw.get("horizon_days"))), assumptions, parseClaims(raw.get("resource_claims"), expected, war));
        SingleReceipt parsed = WarcashPolicy.observe(new World(expected, true, true, integer(raw.get("observed_treasury_raw")), componentWars), input);
        WarcashPolicy.requireComplete(parsed, expected, war);
        for (String key : List.of("existing_shared_gold_commitment_raw", "immediate_war_action_cost_raw", "war_future_gold_cost_raw", "minimum_gold_reserve_raw", "joint_gold_reserve_raw")) {
            require(nonnegativeInteger(raw.get(key)).equals(nonnegativeInteger(single(parsed).get(key))),
                key.equals("joint_gold_reserve_raw") ? "war cash joint reserve does not balance" : "war cash receipt differs from sourced amounts");
        }
        return new VerifiedSingle(parsed, raw.deepCopy());
    }
    private static AggregateReceipt observeAggregate(World world, JsonNode rawRows) {
        world.requireActiveUniverse(); List<SingleReceipt> receipts = new ArrayList<>();
        for (JsonNode rawValue : array(rawRows)) {
            ObjectNode raw = record(rawValue); BigInteger id = positiveInteger(raw.get("war_id"));
            require(isText(raw.get("schema"), SINGLE_SCHEMA) && actualTrue(raw.get("read_only")) && frame(raw.get("source_frame"), false).equals(world.frame())
                && integer(raw.get("observed_treasury_raw")).equals(world.treasuryRaw()), "aggregate receipt crossed frame or treasury");
            ObjectNode input = StrictJson.object(); input.set("source_frame", raw.get("source_frame")); input.set("war_id", raw.get("war_id"));
            ObjectNode observed = record(raw.get("amount_observations"));
            for (Amount amount : Amount.values()) { input.set(amount.wire(), nullable(observed.get(amount.wire()))); }
            for (String key : List.of("horizon_days", "future_bound_assumptions", "resource_claims")) { input.set(key, nullable(raw.get(key))); }
            SingleReceipt canonical = WarcashPolicy.observe(world, inputs(input, world.frame(), id)); ObjectNode rendered = single(canonical);
            var fields = rendered.fieldNames();
            while (fields.hasNext()) {
                String key = fields.next(); if (key.equals("resource_claims") && rendered.get(key).isNull()) { continue; }
                require(equal(nullable(raw.get(key)), rendered.get(key)), "aggregate receipt differs at " + key);
            }
            receipts.add(canonical);
        }
        return WarcashPolicy.aggregate(world, receipts);
    }
    public static AggregateReceipt verifyCompleteAggregate(JsonNode value, Frame expected, List<BigInteger> warIds) {
        ObjectNode raw = record(value);
        require(isText(raw.get("schema"), AGGREGATE_SCHEMA) && isText(raw.get("status"), "complete")
            && frame(raw.get("source_frame"), false).equals(expected) && numberList(raw.get("war_ids"), true).equals(warIds.stream().sorted().toList()), "complete same-frame aggregate required");
        World world = new World(expected, true, true, integer(raw.get("observed_treasury_raw")), warIds);
        AggregateReceipt canonical = observeAggregate(world, raw.get("war_receipts")); WarcashPolicy.requireComplete(canonical, expected, warIds);
        ObjectNode rendered = aggregate(canonical); require(equal(raw, rendered), "aggregate differs from sourced original receipts"); return canonical;
    }
    private static Input inputs(JsonNode value, Frame expected, BigInteger war) {
        ObjectNode raw = record(value);
        require(frame(raw.get("source_frame"), false).equals(expected) && positiveInteger(raw.get("war_id")).equals(war), "war cash inputs crossed full paused frame or WarID");
        EnumMap<Amount, AmountFact> amounts = new EnumMap<>(Amount.class);
        for (Amount amount : Amount.values()) {
            JsonNode row = raw.get(amount.wire());
            amounts.put(amount, row == null || row.isNull() ? new MissingAmount() : new Measured(parseObservation(row, expected, war, null)));
        }
        Optional<BigInteger> horizon = exact(raw.get("horizon_days")) && raw.get("horizon_days").bigIntegerValue().signum() > 0
            ? Optional.of(integer(raw.get("horizon_days"))) : Optional.empty();
        return new Input(expected, war, amounts, horizon, assumptions(raw.get("future_bound_assumptions")), parseClaims(raw.get("resource_claims"), expected, war));
    }
    private static Observation parseObservation(JsonNode value, Frame expected, BigInteger war, List<BigInteger> active) {
        require(value instanceof ObjectNode, "war cash amount needs same-frame sourced nonnegative Q100000 raw");
        ObjectNode row = record(value); require(scale(row.get("scale")), "observed Q100000 scale must be exact integer");
        Frame observedFrame = frame(row.get("source_frame"), false); BigInteger observedWar = positiveInteger(row.get("war_id"));
        require(observedFrame.equals(expected) && observedWar.equals(war),
            "amount lost same-frame provenance; same-frame sourced nonnegative Q100000 raw required");
        Optional<List<Component>> components = Optional.empty();
        if (row.has("resource_components")) {
            List<Component> parsed = new ArrayList<>();
            for (JsonNode raw : array(row.get("resource_components"))) {
                ObjectNode item = record(raw); require(scale(item.get("scale")), "component scale differs");
                Component component;
                try { component = new Component(new ResourceKey(inputText(item.get("resource_kind")), inputText(item.get("resource_id")), positiveInteger(item.get("owner_character_id"))),
                    nonnegativeInteger(item.get("raw")), inputText(item.get("source")), frame(item.get("source_frame"), false), numberList(item.get("war_ids"), true)); }
                catch (IllegalArgumentException error) { throw rejectedInput(error); }
                parsed.add(component);
            }
            parsed.sort(java.util.Comparator.comparing(Component::identity)); components = Optional.of(List.copyOf(parsed));
            if (active != null) { WarcashPolicy.validateComponents(parsed, nonnegativeInteger(row.get("raw")), expected, war, active); }
        }
        try { return new Observation(nonnegativeInteger(row.get("raw")), inputText(row.get("source")), observedFrame, observedWar, components); }
        catch (IllegalArgumentException error) { throw rejectedInput(error); }
    }
    private static Optional<Claims> parseClaims(JsonNode value, Frame expected, BigInteger war) {
        if (value == null || value.isNull()) { return Optional.empty(); }
        ObjectNode row = record(value); Frame claimFrame = frame(row.get("source_frame"), false); BigInteger claimWar = positiveInteger(row.get("war_id"));
        require(claimFrame.equals(expected) && claimWar.equals(war), "occupation crossed frame or war");
        try { return Optional.of(new Claims(inputText(row.get("source")), claimFrame, claimWar,
            numberList(row.get("army_ids"), false), numberList(row.get("ally_character_ids"), true), numberList(row.get("character_ids"), true), textList(row.get("commitment_keys")))); }
        catch (IllegalArgumentException error) { throw rejectedInput(error); }
    }
    private static Optional<List<String>> assumptions(JsonNode value) {
        if (value == null || !value.isArray() || value.isEmpty()) { return Optional.empty(); }
        for (JsonNode row : value) { if (!row.isTextual() || row.textValue().isEmpty()) { return Optional.empty(); } }
        return Optional.of(textList(value));
    }
    private static World world(JsonNode value) {
        ObjectNode snapshot = record(value); Frame frame = frame(snapshot, true);
        ObjectNode money = record(snapshot.get("played_character_gold")); require(scale(money.get("scale")), "same-frame treasury Q100000 required");
        List<BigInteger> wars = new ArrayList<>(); for (JsonNode row : array(snapshot.get("active_wars"))) { wars.add(positiveInteger(record(row).get("war_id"))); }
        return new World(frame, actualTrue(snapshot.get("paused")), actualTrue(snapshot.get("map_ready")), integer(money.get("raw")), wars);
    }
    private static Frame frame(JsonNode value, boolean snapshot) {
        ObjectNode row = snapshot ? record(value) : inputFrame(value);
        JsonNode actor = row.get("played_character_id"); if (actor == null || actor.isNull()) { actor = record(row.get("played_character")).get("character_id"); }
        return new Frame(positiveInteger(actor), positiveInteger(row.get("native_revision")), nonnegativeInteger(row.get("date_raw")), inputText(row.get("snapshot_id")),
            positiveInteger(row.get("revision")), inputText(row.get("episode_run_id")));
    }
    private static ObjectNode frame(Frame value) {
        return StrictJson.object().put("played_character_id", value.playedCharacterId()).put("native_revision", value.nativeRevision()).put("date_raw", value.dateRaw())
            .put("snapshot_id", value.snapshotId()).put("revision", value.revision()).put("episode_run_id", value.episodeRunId());
    }
    private static ObjectNode observation(Observation value) {
        ObjectNode row = StrictJson.object().put("raw", value.raw()).put("scale", GOLD_SCALE).put("source", value.source()).put("war_id", value.warId()); row.set("source_frame", frame(value.frame()));
        value.components().ifPresent(items -> { ArrayNode array = row.putArray("resource_components"); items.forEach(item -> array.add(component(item))); }); return row;
    }
    private static ObjectNode component(Component value) {
        ObjectNode row = StrictJson.object().put("resource_kind", value.identity().kind()).put("resource_id", value.identity().id()).put("owner_character_id", value.identity().ownerCharacterId())
            .put("raw", value.raw()).put("scale", GOLD_SCALE).put("source", value.source()); row.set("source_frame", frame(value.frame())); numbers(row.putArray("war_ids"), value.warIds()); return row;
    }
    private static ObjectNode claims(Claims value) {
        ObjectNode row = union(new ClaimUnion(value.armyIds(), value.allyCharacterIds(), value.characterIds(), value.commitmentKeys()));
        row.put("source", value.source()).put("war_id", value.warId()); row.set("source_frame", frame(value.frame())); return row;
    }
    private static ObjectNode union(ClaimUnion value) {
        ObjectNode row = StrictJson.object(); numbers(row.putArray("army_ids"), value.armyIds()); numbers(row.putArray("ally_character_ids"), value.allyCharacterIds());
        numbers(row.putArray("character_ids"), value.characterIds()); strings(row.putArray("commitment_keys"), value.commitmentKeys()); return row;
    }
    private static void put(ObjectNode row, String key, Optional<BigInteger> value) { if (value.isPresent()) { row.put(key, value.orElseThrow()); } else { row.putNull(key); } }
    private static void numbers(ArrayNode row, List<BigInteger> values) { values.forEach(row::add); }
    private static void strings(ArrayNode row, List<String> values) { values.forEach(row::add); }
    private static void require(boolean condition, String reason) { if (!condition) { throw rejectedInput(new ContractViolationException(reason)); } }
    private static ProjectionDomainRejection rejectedInput(IllegalArgumentException cause) {
        if (cause instanceof ProjectionDomainRejection refusal) { return refusal; }
        var refusal = new ProjectionDomainRejection(cause.getMessage());
        refusal.initCause(cause); return refusal;
    }
    private static String inputText(JsonNode value) {
        try { return StrictJson.text(value); }
        catch (ContractViolationException error) { throw rejectedInput(error); }
    }
    private static ObjectNode inputFrame(JsonNode value) {
        try { return StrictJson.object(value, FRAME_FIELDS); }
        catch (ContractViolationException error) { throw rejectedInput(error); }
    }
    private static ObjectNode record(JsonNode value) { require(value instanceof ObjectNode, "war cash JSON object required"); return (ObjectNode) value; }
    private static ArrayNode array(JsonNode value) { require(value instanceof ArrayNode, "war cash explicit array required"); return (ArrayNode) value; }
    private static BigInteger integer(JsonNode value) { require(exact(value), "exact integer required; no boolean/float/string"); return value.bigIntegerValue(); }
    private static BigInteger nonnegativeInteger(JsonNode value) { BigInteger result = integer(value); require(result.signum() >= 0, "nonnegative raw or identity required"); return result; }
    private static BigInteger positiveInteger(JsonNode value) { BigInteger result = integer(value); require(result.signum() > 0, "positive identity required"); return result; }
    private static boolean scale(JsonNode value) { return exact(value) && integer(value).equals(BigInteger.valueOf(GOLD_SCALE)); }
    private static boolean exact(JsonNode value) { return value != null && value.isIntegralNumber(); }
    private static boolean actualTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean isText(JsonNode value, String expected) { return value != null && value.isTextual() && value.textValue().equals(expected); }
    private static JsonNode nullable(JsonNode value) { return value == null ? NullNode.instance : value; }
    private static List<BigInteger> numberList(JsonNode value, boolean positive) {
        List<BigInteger> result = new ArrayList<>(); for (JsonNode row : array(value)) { result.add(positive ? positiveInteger(row) : nonnegativeInteger(row)); } return List.copyOf(result);
    }
    private static List<String> textList(JsonNode value) { List<String> result = new ArrayList<>(); for (JsonNode row : array(value)) { result.add(inputText(row)); } return List.copyOf(result); }
    private static boolean equal(JsonNode first, JsonNode second) { return java.util.Arrays.equals(StrictJson.canonical(first), StrictJson.canonical(second)); }
}
