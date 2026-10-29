package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;

/** Sole action body contract. Existing frame, source and postcondition codecs are reused without aliases. */
public final class ActionCodec {
    public static final String COMMAND_SCHEMA = "xar.java-action-command/v1";
    public static final String FRONTEND_COMMAND_SCHEMA = "xar.java-action-command/v2";
    public static final String LIFECYCLE_COMMAND_SCHEMA = "xar.java-action-command/v3";
    public static final String EXPLICIT_PROTOCOL_COMMAND_SCHEMA = "xar.java-action-command/v4";
    public static final String OPERATOR_COMMAND_SCHEMA = "xar.java-action-command/v5";
    private static final String PROTOCOL_ID_SCHEMA = "xar.java.original-protocol-request-id/v1";
    public static final int MAX_COMMAND_BYTES = 1024 * 1024;
    private ActionCodec() { }
    public static byte[] encodeCommand(ActionCommand command) {
        if (command.expectation() instanceof CommandExpectation.OperatorRebind) return encodeOriginCommand(command, OPERATOR_COMMAND_SCHEMA);
        if (command.origin() instanceof CommandOrigin.Frontend) return encodeOriginCommand(command, FRONTEND_COMMAND_SCHEMA);
        if (command.origin() instanceof CommandOrigin.LifecycleTerminal) return encodeOriginCommand(command, LIFECYCLE_COMMAND_SCHEMA);
        ObjectNode row = StrictJson.object(); row.put("schema", command.protocolIdentity() instanceof ExplicitOriginalProtocolId ? EXPLICIT_PROTOCOL_COMMAND_SCHEMA : COMMAND_SCHEMA); row.put("action_id", command.actionId());
        row.set("before", ProposalLifecycleCodec.observation(command.before())); row.set("source", ProposalLifecycleCodec.source(command.source()));
        row.put("session_id", command.sessionId()); row.put("operation", command.operation().value());
        row.set("expected", ProposalLifecycleCodec.expected(command.expected()));
        row.set("claims", claims(command.claims())); row.put("deadline", command.deadline().toString());
        if (command.protocolIdentity() instanceof ExplicitOriginalProtocolId explicit) row.set("protocol_identity", protocolIdentity(explicit));
        return encodeTypedCommand(row, command.arguments());
    }
    public static ActionCommand decodeCommand(byte[] raw) {
        JsonNode parsed = StrictJson.parse(raw, MAX_COMMAND_BYTES);
        StrictJson.require(parsed instanceof ObjectNode, "action command object required");
        OpportunityJson.Obj arguments = OpportunityJson.object(DriverJson.object(raw, MAX_COMMAND_BYTES).get("arguments"), "original action arguments");
        if (FRONTEND_COMMAND_SCHEMA.equals(text((ObjectNode) parsed, "schema"))) return decodeOriginCommand((ObjectNode) parsed, false, arguments);
        if (LIFECYCLE_COMMAND_SCHEMA.equals(text((ObjectNode) parsed, "schema"))) return decodeOriginCommand((ObjectNode) parsed, true, arguments);
        if (OPERATOR_COMMAND_SCHEMA.equals(text((ObjectNode) parsed, "schema"))) return decodeOperatorCommand((ObjectNode) parsed, arguments);
        boolean explicit = EXPLICIT_PROTOCOL_COMMAND_SCHEMA.equals(text((ObjectNode) parsed, "schema"));
        ObjectNode row = StrictJson.object(parsed, explicit
                ? Set.of("schema", "action_id", "before", "source", "session_id", "operation", "arguments", "expected", "claims", "deadline", "protocol_identity")
                : Set.of("schema", "action_id", "before", "source", "session_id", "operation", "arguments", "expected", "claims", "deadline"));
        StrictJson.require(explicit || COMMAND_SCHEMA.equals(text(row, "schema")), "exact action command schema required");
        ObjectNode expected = StrictJson.object(row.get("expected"), Set.of("version", "before", "source", "observer_schema", "values"));
        ExpectedPostcondition postcondition = new ExpectedPostcondition(Math.toIntExact(StrictJson.integer(expected.get("version"), 1, 1)),
                ProposalLifecycleCodec.decodeObservation(expected.get("before")), G2Wire.source(expected.get("source")), text(expected, "observer_schema"), ProposalLifecycleCodec.values(expected.get("values")));
        return new ActionCommand(text(row, "action_id"), new CommandOrigin.Gameplay(ProposalLifecycleCodec.decodeObservation(row.get("before"))), G2Wire.source(row.get("source")),
                text(row, "session_id"), new OperationKey(text(row, "operation")), arguments, new CommandExpectation.Gameplay(postcondition),
                claims(row.get("claims")), Instant.parse(text(row, "deadline")),
                explicit ? protocolIdentity(row.get("protocol_identity")) : ProtocolRequestIdentity.BodyDerived.INSTANCE);
    }
    private static ObjectNode protocolIdentity(ExplicitOriginalProtocolId actual) {
        ObjectNode row = StrictJson.object(); row.put("schema", PROTOCOL_ID_SCHEMA); row.put("kind", "EXPLICIT_ORIGINAL");
        row.put("contract", actual.contract().name()); row.put("request_id", actual.value()); row.set("producer_source", actual.producerSource().toJson());
        return row;
    }
    private static ExplicitOriginalProtocolId protocolIdentity(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "kind", "contract", "request_id", "producer_source"));
        StrictJson.require(PROTOCOL_ID_SCHEMA.equals(text(row, "schema")) && "EXPLICIT_ORIGINAL".equals(text(row, "kind")),
                "exact original protocol request identity schema and branch required");
        return new ExplicitOriginalProtocolId(ExplicitOriginalProtocolId.Contract.valueOf(text(row, "contract")),
                text(row, "request_id"), org.xar.ck3.control.contracts.ExactRef.fromJson(row.get("producer_source")));
    }
    private static byte[] encodeOriginCommand(ActionCommand command, String schema) {
        ObjectNode row = StrictJson.object(); row.put("schema", schema); row.put("action_id", command.actionId());
        row.set("origin", CommandOriginCodec.origin(command.origin())); row.set("source", ProposalLifecycleCodec.source(command.source()));
        row.put("session_id", command.sessionId()); row.put("operation", command.operation().value());
        row.set("expectation", CommandOriginCodec.expectation(command.expectation()));
        row.set("claims", claims(command.claims())); row.put("deadline", command.deadline().toString());
        return encodeTypedCommand(row, command.arguments());
    }
    private static ActionCommand decodeOperatorCommand(ObjectNode row, OpportunityJson.Obj arguments) {
        StrictJson.object(row, Set.of("schema", "action_id", "origin", "source", "session_id", "operation", "arguments", "expectation", "claims", "deadline"));
        var expectation = CommandOriginCodec.expectation(row.get("expectation"));
        StrictJson.require(expectation instanceof CommandExpectation.OperatorRebind, "operator command v5 requires its exact typed expectation");
        return new ActionCommand(text(row, "action_id"), CommandOriginCodec.origin(row.get("origin")), G2Wire.source(row.get("source")), text(row, "session_id"),
                new OperationKey(text(row, "operation")), arguments, expectation, claims(row.get("claims")), Instant.parse(text(row, "deadline")));
    }
    private static ActionCommand decodeOriginCommand(ObjectNode row, boolean lifecycle, OpportunityJson.Obj arguments) {
        StrictJson.object(row, Set.of("schema", "action_id", "origin", "source", "session_id", "operation", "arguments", "expectation", "claims", "deadline"));
        var origin = CommandOriginCodec.origin(row.get("origin"));
        StrictJson.require(lifecycle ? origin instanceof CommandOrigin.LifecycleTerminal : origin instanceof CommandOrigin.Frontend,
                "evolved action schema requires its exact origin phase");
        var expectation = CommandOriginCodec.expectation(row.get("expectation"));
        StrictJson.require(!(expectation instanceof CommandExpectation.OperatorRebind), "historical frontend/lifecycle schemas cannot carry an operator expectation");
        return new ActionCommand(text(row, "action_id"), origin, G2Wire.source(row.get("source")), text(row, "session_id"),
                new OperationKey(text(row, "operation")), arguments,
                expectation, claims(row.get("claims")), Instant.parse(text(row, "deadline")));
    }
    /** Preserve the owning header codecs; only the original typed argument subtree bypasses JsonNode number coercion. */
    private static byte[] encodeTypedCommand(ObjectNode header, OpportunityJson.Obj arguments) {
        OpportunityJson.Obj originalHeader = DriverJson.object(ProposalLifecycleCodec.encodePayload(header, MAX_COMMAND_BYTES), MAX_COMMAND_BYTES);
        byte[] raw = PublicDataJson.encodeTyped(originalHeader.with("arguments", arguments)).bytes();
        StrictJson.require(raw.length <= MAX_COMMAND_BYTES, "action command exceeds its original role budget");
        return raw;
    }
    public static String bodySha256(ActionCommand command) { return sha256(encodeCommand(command)); }
    public static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException unavailable) { throw new IllegalStateException(unavailable); }
    }
    public static ObjectNode claims(Claims claims) {
        ObjectNode row = StrictJson.object(); decimalIds(row.putArray("army_ids"), claims.armyIds());
        decimalIds(row.putArray("ally_character_ids"), claims.allyCharacterIds()); decimalCharacterIds(row.putArray("character_ids"), claims.characterIds());
        var keys = row.putArray("commitment_keys"); claims.commitmentKeys().stream().sorted().forEach(keys::add); return row;
    }
    public static Claims claims(JsonNode node) {
        ObjectNode row = StrictJson.object(node, Set.of("army_ids", "ally_character_ids", "character_ids", "commitment_keys"));
        Set<String> keys = new HashSet<>(); StrictJson.require(row.get("commitment_keys").isArray(), "commitment keys array required");
        row.get("commitment_keys").forEach(item -> StrictJson.require(keys.add(StrictJson.text(item)), "duplicate commitment key"));
        return new Claims(ids(row.get("army_ids")), ids(row.get("ally_character_ids")), signedCharacterIds(row.get("character_ids")), keys);
    }
    private static Set<BigInteger> ids(JsonNode node) {
        StrictJson.require(node != null && node.isArray(), "resource ID array required"); Set<BigInteger> ids = new HashSet<>();
        node.forEach(item -> StrictJson.require(ids.add(new BigInteger(new CrossJsDecimalUInt64(StrictJson.text(item)).decimal())), "duplicate resource ID")); return ids;
    }
    private static Set<BigInteger> signedCharacterIds(JsonNode node) {
        StrictJson.require(node != null && node.isArray(), "resource ID array required"); Set<BigInteger> ids = new HashSet<>();
        node.forEach(item -> {
            String text = StrictJson.text(item);
            StrictJson.require(text.length() <= 11, "bounded signed character ID required");
            BigInteger value;
            try { value = new BigInteger(text); } catch (NumberFormatException e) { throw new IllegalArgumentException("invalid signed character ID"); }
            NativeCharacterId.of(value);
            StrictJson.require(text.equals(value.toString()), "canonical signed character ID required");
            StrictJson.require(ids.add(value), "duplicate resource ID");
        });
        return ids;
    }
    private static void decimalIds(com.fasterxml.jackson.databind.node.ArrayNode array, Set<BigInteger> ids) {
        ids.stream().sorted().forEach(id -> array.add(new CrossJsDecimalUInt64(id.toString()).decimal()));
    }
    private static void decimalCharacterIds(com.fasterxml.jackson.databind.node.ArrayNode array, Set<BigInteger> ids) {
        ids.stream().sorted().forEach(id -> array.add(NativeCharacterId.of(id).asBigInteger().toString()));
    }
    static String text(ObjectNode row, String key) { return StrictJson.text(row.get(key)); }
    private static Set<String> fieldNames(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "arguments object required"); Set<String> fields = new HashSet<>(); node.fieldNames().forEachRemaining(fields::add); return fields;
    }
}
