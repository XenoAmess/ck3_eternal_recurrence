package org.xar.ck3.control.wave2.governance.betrothal;

import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;

/** JSON is checked here before constructing the immutable projection. */
public final class BetrothalCodec {
    public static final String BUILD_SCHEMA = "xar.ck3.betrothal-build-request.v1";
    public static final String ADAPT_SCHEMA = "xar.ck3.betrothal-adapt-request.v1";
    public static final int MAX_BYTES = 262_144;
    private static final Set<String> FRAME_FIELDS = Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id");
    private static final Set<String> COST_FIELDS = costFields();
    private static final Set<String> COMMITMENT_FIELDS = Set.of("source", "bilateral_verified", "heir_character_id", "partner_character_id", "commitment_key", "mode", "new_betrothal_commitment");
    private static final Set<String> RESOURCE_FIELDS = Set.of("schema", "mode", "typed_step", "source_frame", "source_native_revision", "selected", "formal_action_ready", "reasons",
            "actor_character_id", "heir_character_id", "partner_character_id", "recipient_character_id", "intermediary_character_id", "character_claims", "immediate_generic_costs", "existing_commitment",
            "benefit", "predicted_outcome_if_accepted", "matrilineal_option_selected", "native_child_house_preview", "current_first_heir_descendants_v1", "current_first_heir_descendants_summary_v1",
            "effective_matrilineal_if_accepted", "recipient_ai_accept_raw", "recipient_answer_status_raw", "alliance_established", "future_alliance_obligation", "unpriced", "resource_reservation_performed");
    private static final ObjectMapper MAPPER = JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS, DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private BetrothalCodec() { }

    public static BuildInput decodeBuild(byte[] raw) {
        ObjectNode root = StrictJson.object(parse(raw), Set.of("schema", "relation", "snapshot", "selected", "reasons"));
        require(BUILD_SCHEMA.equals(text(root.get("schema"))), "betrothal build request schema");
        return new BuildInput(relation(object(root.get("relation"))), snapshotFrame(object(root.get("snapshot"))),
                requiredBoolean(root.get("selected")), strings(root.get("reasons")));
    }

    public static AdaptInput decodeAdapt(byte[] raw) {
        ObjectNode root = StrictJson.object(parse(raw), Set.of("schema", "frame", "plan"));
        require(ADAPT_SCHEMA.equals(text(root.get("schema"))), "betrothal adapt request schema");
        ObjectNode plan = object(root.get("plan"));
        JsonNode choice = plan.get("current_betrothal_choice");
        JsonNode resource = choice != null && choice.isObject() ? choice.get("resource_proposal") : null;
        return new AdaptInput(frame(object(root.get("frame"))), new Plan(nullableText(plan.get("selected_step")),
                resource == null || resource.isNull() ? null : resource(object(resource))));
    }

    public static ResourceProposal decodeResource(byte[] raw) { return resource(object(parse(raw))); }
    public static byte[] encodeResource(ResourceProposal resource) { return encode(resourceNode(resource)); }
    public static byte[] encodeOpportunity(Opportunity opportunity) { return encode(opportunityNode(opportunity)); }
    public static JsonNode readJson(byte[] raw) { return parse(raw); }
    /** Immutable JSON evidence seam reused by adjacent governance projections, never an authority token. */
    public static WireValue decodeEvidence(byte[] raw) { return wire(parse(raw)); }
    public static byte[] encodeEvidence(WireValue value) { return encode(wireNode(value)); }
    /** Copy an already parsed adapter tree without reserializing decimal tokens into integer tokens. */
    public static WireValue projectEvidence(JsonNode node) {
        try {
            require(node != null && MAPPER.writeValueAsBytes(node).length <= MAX_BYTES, "bounded parsed evidence required");
            return wire(node);
        } catch (IOException error) { throw new IllegalArgumentException("invalid parsed JSON evidence", error); }
    }

    public static ObjectNode resourceNode(ResourceProposal resource) {
        ObjectNode node = StrictJson.object();
        put(node, "schema", resource.schema()); put(node, "mode", resource.mode()); put(node, "typed_step", resource.typedStep());
        node.set("source_frame", resource.sourceFrame() == null ? MAPPER.getNodeFactory().nullNode() : frameNode(resource.sourceFrame()));
        put(node, "source_native_revision", resource.sourceNativeRevision()); put(node, "selected", resource.selected()); put(node, "formal_action_ready", resource.formalActionReady());
        putStrings(node, "reasons", resource.reasons()); rolesNode(node, resource.roles()); putIntegers(node, "character_claims", resource.characterClaims());
        node.set("immediate_generic_costs", resource.immediateGenericCosts() == null ? MAPPER.getNodeFactory().nullNode() : costsNode(resource.immediateGenericCosts()));
        node.set("existing_commitment", resource.existingCommitment() == null ? MAPPER.getNodeFactory().nullNode() : commitmentNode(resource.existingCommitment()));
        put(node, "benefit", resource.benefit()); put(node, "predicted_outcome_if_accepted", resource.predictedOutcomeIfAccepted()); put(node, "matrilineal_option_selected", resource.matrilinealOptionSelected());
        node.set("native_child_house_preview", wireNode(resource.nativeChildHousePreview()));
        node.set("current_first_heir_descendants_v1", wireNode(resource.descendants())); node.set("current_first_heir_descendants_summary_v1", wireNode(resource.descendantsSummary()));
        put(node, "effective_matrilineal_if_accepted", resource.effectiveMatrilinealIfAccepted()); put(node, "recipient_ai_accept_raw", resource.recipientAiAcceptRaw());
        put(node, "recipient_answer_status_raw", resource.recipientAnswerStatusRaw()); node.set("alliance_established", wireNode(resource.allianceEstablished()));
        put(node, "future_alliance_obligation", resource.futureAllianceObligation()); putStrings(node, "unpriced", resource.unpriced());
        put(node, "resource_reservation_performed", resource.resourceReservationPerformed()); extensions(node, resource.extensions()); return node;
    }

    public static ObjectNode opportunityNode(Opportunity opportunity) {
        ObjectNode node = StrictJson.object();
        node.put("schema", "xar.ck3.m5-observed-opportunity.v1"); node.set("frame", frameNode(opportunity.frame()));
        node.put("candidate_id", opportunity.candidateId()); node.put("domain", "marriage"); node.put("source_policy", "current-first-heir-betrothal-formal-v1"); node.put("domain_policy_ready", true);
        node.put("gold_cost_raw", opportunity.goldCostRaw()); node.put("minimum_gold_reserve_raw", 0); node.putNull("projected_supply_margin_raw"); node.put("war_slot_claim", 0); node.putNull("war_operation");
        node.putArray("army_ids"); node.putArray("ally_character_ids"); putIntegers(node, "character_ids", opportunity.characterIds()); putStrings(node, "commitment_keys", opportunity.commitmentKeys());
        ObjectNode evidence = node.putObject("evidence"); evidence.put("mode", BetrothalProposals.MODE); evidence.set("resource_proposal", resourceNode(opportunity.resourceProposal()));
        evidence.put("existing_betrothal_commitment_reused", true); evidence.putNull("alliance_established"); return node;
    }

    public static ObjectNode frameNode(Frame frame) {
        ObjectNode node = StrictJson.object(); node.put("played_character_id", frame.playedCharacterId()); node.put("native_revision", frame.nativeRevision());
        node.put("date_raw", frame.dateRaw()); node.put("snapshot_id", frame.snapshotId()); node.put("revision", frame.revision()); node.put("episode_run_id", frame.episodeRunId()); return node;
    }

    private static Relation relation(ObjectNode node) {
        JsonNode action = node.get("betrothal_actionability");
        return new Relation(nullableInteger(node.get("native_revision")), nullableInteger(node.get("heir_character_id")), nullableInteger(node.get("betrothed_character_id")),
                nullableBoolean(node.get("bilateral_verified")), action == null || action.isNull() ? Actionability.empty() : actionability(object(action)),
                wire(node.get("current_first_heir_descendants_v1")), wire(node.get("current_first_heir_descendants_summary_v1")));
    }

    private static Actionability actionability(ObjectNode node) {
        JsonNode costs = node.get("generic_costs");
        return new Actionability(roles(node), costs == null || costs.isNull() ? null : costs(object(costs)), nullableBoolean(node.get("ready_to_marry_betrothed")),
                nullableText(node.get("predicted_outcome_if_accepted")), nullableBoolean(node.get("matrilineal_option_selected")), wire(node.get("native_child_house_preview")),
                nullableBoolean(node.get("effective_matrilineal_if_accepted")), nullableInteger(node.get("recipient_ai_accept_raw")), nullableInteger(node.get("recipient_answer_status_raw")));
    }

    private static ResourceProposal resource(ObjectNode node) {
        JsonNode source = node.get("source_frame"), costs = node.get("immediate_generic_costs"), commitment = node.get("existing_commitment");
        return new ResourceProposal(nullableText(node.get("schema")), nullableText(node.get("mode")), nullableText(node.get("typed_step")), source == null || source.isNull() ? null : frame(object(source)),
                nullableInteger(node.get("source_native_revision")), nullableBoolean(node.get("selected")), nullableBoolean(node.get("formal_action_ready")), nullableStrings(node.get("reasons")), roles(node), nullableIntegers(node.get("character_claims")),
                costs == null || costs.isNull() ? null : costs(object(costs)), commitment == null || commitment.isNull() ? null : commitment(object(commitment)),
                nullableText(node.get("benefit")), nullableText(node.get("predicted_outcome_if_accepted")), nullableBoolean(node.get("matrilineal_option_selected")),
                wire(node.get("native_child_house_preview")), wire(node.get("current_first_heir_descendants_v1")), wire(node.get("current_first_heir_descendants_summary_v1")),
                nullableBoolean(node.get("effective_matrilineal_if_accepted")), nullableInteger(node.get("recipient_ai_accept_raw")), nullableInteger(node.get("recipient_answer_status_raw")),
                wire(node.get("alliance_established")), nullableText(node.get("future_alliance_obligation")), nullableStrings(node.get("unpriced")), nullableBoolean(node.get("resource_reservation_performed")), extensionValues(node, RESOURCE_FIELDS));
    }

    private static ExistingCommitment commitment(ObjectNode node) {
        return new ExistingCommitment(nullableText(node.get("source")), nullableBoolean(node.get("bilateral_verified")), nullableInteger(node.get("heir_character_id")), nullableInteger(node.get("partner_character_id")),
                nullableText(node.get("commitment_key")), nullableText(node.get("mode")), nullableBoolean(node.get("new_betrothal_commitment")), extensionValues(node, COMMITMENT_FIELDS));
    }

    private static GenericCosts costs(ObjectNode node) {
        EnumMap<CostTerm, Field<BigInteger>> amounts = new EnumMap<>(CostTerm.class);
        for (CostTerm term : CostTerm.values()) { amounts.put(term, field(node, term.wire(), BetrothalCodec::integer)); }
        return new GenericCosts(field(node, "raw_scale", BetrothalCodec::integer), field(node, "payer_role", BetrothalCodec::text),
                field(node, "application_timing", BetrothalCodec::text), amounts, extensionValues(node, COST_FIELDS));
    }

    private static Frame snapshotFrame(ObjectNode node) {
        JsonNode player = node.get("played_character_id");
        if (player == null || player.isNull()) {
            JsonNode played = node.get("played_character"); player = played != null && played.isObject() ? played.get("character_id") : null;
        }
        return new Frame(integer(player), integer(node.get("native_revision")), integer(node.get("date_raw")), text(node.get("snapshot_id")), integer(node.get("revision")), text(node.get("episode_run_id")));
    }

    private static Frame frame(ObjectNode node) { StrictJson.object(node, FRAME_FIELDS); return snapshotFrame(node); }
    private static Roles roles(ObjectNode node) { return new Roles(nullableInteger(node.get("actor_character_id")), nullableInteger(node.get("heir_character_id")), nullableInteger(node.get("partner_character_id")), nullableInteger(node.get("recipient_character_id")), nullableInteger(node.get("intermediary_character_id"))); }
    private static void rolesNode(ObjectNode node, Roles roles) { put(node, "actor_character_id", roles.actor()); put(node, "heir_character_id", roles.heir()); put(node, "partner_character_id", roles.partner()); put(node, "recipient_character_id", roles.recipient()); put(node, "intermediary_character_id", roles.intermediary()); }

    private static ObjectNode costsNode(GenericCosts costs) {
        ObjectNode node = StrictJson.object(); write(node, "raw_scale", costs.rawScale(), BigIntegerNode::valueOf);
        write(node, "payer_role", costs.payerRole(), MAPPER.getNodeFactory()::textNode); write(node, "application_timing", costs.applicationTiming(), MAPPER.getNodeFactory()::textNode);
        costs.amounts().forEach((term, value) -> write(node, term.wire(), value, BigIntegerNode::valueOf)); extensions(node, costs.extensions()); return node;
    }

    private static ObjectNode commitmentNode(ExistingCommitment commitment) {
        ObjectNode node = StrictJson.object(); put(node, "source", commitment.source()); put(node, "bilateral_verified", commitment.bilateralVerified());
        put(node, "heir_character_id", commitment.heirCharacterId()); put(node, "partner_character_id", commitment.partnerCharacterId()); put(node, "commitment_key", commitment.commitmentKey());
        put(node, "mode", commitment.mode()); put(node, "new_betrothal_commitment", commitment.newBetrothalCommitment()); extensions(node, commitment.extensions()); return node;
    }

    private static ObjectValue extensionValues(ObjectNode node, Set<String> known) {
        Map<String, WireValue> result = new HashMap<>();
        node.properties().forEach(entry -> { if (!known.contains(entry.getKey())) { result.put(entry.getKey(), wire(entry.getValue())); } }); return new ObjectValue(result);
    }
    private static void extensions(ObjectNode node, ObjectValue extension) { extension.values().forEach((key, value) -> { require(!node.has(key), "extension collides with contract"); node.set(key, wireNode(value)); }); }

    private static WireValue wire(JsonNode node) {
        if (node == null || node.isNull()) { return NullValue.INSTANCE; }
        if (node.isIntegralNumber()) { return new IntegerValue(node.bigIntegerValue()); }
        if (node.isFloatingPointNumber()) { return new DecimalValue(node.decimalValue()); }
        if (node.isBoolean()) { return new BooleanValue(node.booleanValue()); }
        if (node.isTextual()) { return new TextValue(text(node)); }
        if (node.isArray()) { List<WireValue> result = new ArrayList<>(); node.forEach(value -> result.add(wire(value))); return new ArrayValue(result); }
        ObjectNode object = object(node); Map<String, WireValue> result = new HashMap<>(); object.properties().forEach(entry -> {
            if (!entry.getKey().isEmpty()) { StrictJson.text(entry.getKey()); }
            result.put(entry.getKey(), wire(entry.getValue()));
        }); return new ObjectValue(result);
    }

    private static JsonNode wireNode(WireValue value) {
        return switch (value) {
            case NullValue ignored -> MAPPER.getNodeFactory().nullNode();
            case IntegerValue integer -> BigIntegerNode.valueOf(integer.value());
            case DecimalValue decimal -> DecimalNode.valueOf(decimal.value().scale() == 0 ? decimal.value().setScale(1) : decimal.value());
            case BooleanValue bool -> MAPPER.getNodeFactory().booleanNode(bool.value());
            case TextValue text -> MAPPER.getNodeFactory().textNode(text.value());
            case ArrayValue array -> { ArrayNode result = MAPPER.createArrayNode(); array.values().forEach(item -> result.add(wireNode(item))); yield result; }
            case ObjectValue object -> { ObjectNode result = StrictJson.object(); new TreeSet<>(object.values().keySet()).forEach(key -> result.set(key, wireNode(object.values().get(key)))); yield result; }
        };
    }

    private static JsonNode parse(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded betrothal input required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode result = MAPPER.readTree(text); require(result != null, "JSON value required"); return result;
        } catch (IOException error) { throw new IllegalArgumentException("invalid betrothal JSON/UTF-8/duplicate fields", error); }
    }
    private static byte[] encode(JsonNode node) {
        try { byte[] result = MAPPER.writeValueAsBytes(wireNode(wire(node))); require(result.length <= MAX_BYTES, "betrothal output exceeds byte budget"); return result; }
        catch (IOException error) { throw new IllegalArgumentException("cannot serialize betrothal proposal", error); }
    }
    private static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "object required"); return (ObjectNode) node; }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "exact integer required; no bool/float/string"); return node.bigIntegerValue(); }
    private static BigInteger nullableInteger(JsonNode node) { return node == null || node.isNull() ? null : integer(node); }
    private static String text(JsonNode node) { require(node != null && node.isTextual(), "string required"); String value = node.textValue(); if (!value.isEmpty()) { StrictJson.text(value); } return value; }
    private static String nullableText(JsonNode node) { return node == null || node.isNull() ? null : text(node); }
    private static boolean requiredBoolean(JsonNode node) { require(node != null && node.isBoolean(), "boolean required"); return node.booleanValue(); }
    private static Boolean nullableBoolean(JsonNode node) { return node == null || node.isNull() ? null : requiredBoolean(node); }
    private static List<String> strings(JsonNode node) { require(node != null && node.isArray(), "string array required"); List<String> result = new ArrayList<>(); node.forEach(value -> result.add(text(value))); return List.copyOf(result); }
    private static List<String> nullableStrings(JsonNode node) { return node == null || node.isNull() ? null : strings(node); }
    private static List<BigInteger> nullableIntegers(JsonNode node) { if (node == null || node.isNull()) { return null; } require(node.isArray(), "integer array required"); List<BigInteger> result = new ArrayList<>(); node.forEach(value -> result.add(integer(value))); return List.copyOf(result); }
    private static <T> Field<T> field(ObjectNode node, String key, Function<JsonNode, T> reader) { JsonNode value = node.get(key); return value == null ? Field.missing() : value.isNull() ? Field.nil() : Field.of(reader.apply(value)); }
    private static <T> void write(ObjectNode node, String key, Field<T> field, Function<T, JsonNode> writer) { if (field.presence() == Presence.NULL) { node.putNull(key); } else if (field.presence() == Presence.VALUE) { node.set(key, writer.apply(field.value())); } }
    private static void put(ObjectNode node, String key, String value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void put(ObjectNode node, String key, BigInteger value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void put(ObjectNode node, String key, Boolean value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void putStrings(ObjectNode node, String key, List<String> values) { if (values == null) { node.putNull(key); } else { ArrayNode array = node.putArray(key); values.forEach(array::add); } }
    private static void putIntegers(ObjectNode node, String key, List<BigInteger> values) { if (values == null) { node.putNull(key); } else { ArrayNode array = node.putArray(key); values.forEach(array::add); } }
    private static Set<String> costFields() { Set<String> result = new TreeSet<>(Set.of("raw_scale", "payer_role", "application_timing")); for (CostTerm term : CostTerm.values()) { result.add(term.wire()); } return Set.copyOf(result); }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}

