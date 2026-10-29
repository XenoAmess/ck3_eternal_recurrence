package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition.Operation;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionModel;

/** Public DATA projection of the original lifecycle result; never changes its persistent proof. */
public final class LifecyclePublicResultCodec {
    private record Role(List<String> path, boolean required) {
        private Role { path = List.copyOf(path); }
    }
    private static final Role REVISION = new Role(List.of("revision"), true);
    private static final List<Role> RECONCILIATION_ROLES = List.of(
            new Role(List.of("predecessor_binding", "revision"), true),
            new Role(List.of("predecessor_binding", "native_revision"), true),
            new Role(List.of("successor_binding", "revision"), true),
            new Role(List.of("successor_binding", "native_revision"), true));
    private static final List<Role> CONTINUED_ROLES = java.util.stream.Stream.concat(
            java.util.stream.Stream.of(REVISION), RECONCILIATION_ROLES.stream().map(role ->
                    new Role(java.util.stream.Stream.concat(java.util.stream.Stream.of("succession_reconciliation"),
                            role.path().stream()).toList(), role.required()))).toList();

    private LifecyclePublicResultCodec() { }

    /** Same optional revision DATA role as terminal inspection; this never asserts a DEATH transition. */
    public static RawJson encodeSettlementInspection(RawJson originalInspection) {
        return encode(Kind.DEATH, originalInspection);
    }

    /** Restore only the inspection revision role, preserving missing/null and all ordinary numeric fields. */
    public static RawJson decodeSettlementInspection(RawJson publicInspection) {
        return decode(Kind.DEATH, publicInspection);
    }

    public static Optional<Kind> kindOfOperation(String operation) {
        Objects.requireNonNull(operation);
        if (operation.equals(Operation.DEATH_TERMINAL.key().value())) return Optional.of(Kind.DEATH);
        if (operation.equals(Operation.CONTINUE_SUCCESSOR.key().value())) return Optional.of(Kind.CONTINUE_SUCCESSOR);
        if (operation.equals(Operation.START_NEXT_EPISODE.key().value())) return Optional.of(Kind.NEXT_EPISODE);
        return Optional.empty();
    }

    /** Recognizes only the sole M3 available DTO; other unavailable/null DATA is not rewritten. */
    public static boolean isAvailableReconciliation(RawJson original) {
        ObjectNode value = object(original);
        return value.path("schema").isTextual() && SuccessionModel.RECONCILIATION_SCHEMA.equals(value.get("schema").textValue())
                && value.path("status").isTextual() && "available".equals(value.get("status").textValue());
    }

    public static RawJson encodeReconciliation(RawJson original) {
        GoalCodec.decodeReconciliation(original.bytes());
        ObjectNode value = object(original);
        for (Role role : RECONCILIATION_ROLES) transform(value, role, true);
        PublicSnapshotCodec.publicNumbers(value, ""); RawJson encoded = PublicDataJson.encodePreservingDecimals(value,original);
        StrictJson.require(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES).equals(DriverJson.object(decodeReconciliation(encoded).bytes(),RawJson.MAXIMUM_BYTES)),
                "M3 public serialization changed its original JSON type domain");
        return encoded;
    }

    public static RawJson decodeReconciliation(RawJson publicResult) {
        ObjectNode value = object(publicResult); PublicSnapshotCodec.publicNumbers(value, "");
        for (Role role : RECONCILIATION_ROLES) transform(value, role, false);
        RawJson original = PublicDataJson.encodePreservingDecimals(value,publicResult); GoalCodec.decodeReconciliation(original.bytes()); return original;
    }

    public static RawJson encode(Kind kind, RawJson originalResult) {
        Objects.requireNonNull(kind); Objects.requireNonNull(originalResult);
        ObjectNode original = object(originalResult);
        validateOriginal(kind, original);
        ObjectNode publicResult = original.deepCopy();
        for (Role role : roles(kind)) transform(publicResult, role, true);
        PublicSnapshotCodec.publicNumbers(publicResult, "");
        RawJson encoded = PublicDataJson.encodePreservingDecimals(publicResult,originalResult);
        StrictJson.require(DriverJson.object(originalResult.bytes(),RawJson.MAXIMUM_BYTES).equals(DriverJson.object(decode(kind,encoded).bytes(),RawJson.MAXIMUM_BYTES)),
                "lifecycle public serialization changed the original JSON type domain");
        return encoded;
    }

    /** Restores only the five source-owned revision roles; other strings remain strings. */
    public static RawJson decode(Kind kind, RawJson publicResult) {
        Objects.requireNonNull(kind); Objects.requireNonNull(publicResult);
        ObjectNode original = object(publicResult);
        PublicSnapshotCodec.publicNumbers(original, "");
        for (Role role : roles(kind)) transform(original, role, false);
        validateOriginal(kind, original);
        return PublicDataJson.encodePreservingDecimals(original,publicResult);
    }

    private static List<Role> roles(Kind kind) {
        return switch (kind) {
            // Death preserves missing/null from the actual native terminal frame.
            case DEATH -> List.of(new Role(REVISION.path(), false));
            case CONTINUE_SUCCESSOR -> CONTINUED_ROLES;
            case NEXT_EPISODE, ACTOR_SWITCH -> List.of();
        };
    }

    private static void validateOriginal(Kind kind, ObjectNode original) {
        if (kind != Kind.CONTINUE_SUCCESSOR) return;
        JsonNode reconciliation = original.get("succession_reconciliation");
        StrictJson.require(reconciliation instanceof ObjectNode, "original successor requires its actual M3 reconciliation");
        GoalCodec.decodeReconciliation(PublicDataJson.encode(reconciliation).bytes());
        StrictJson.require(original.get("revision") != null
                && original.get("revision").equals(reconciliation.path("successor_binding").get("revision")),
                "actual successor result revision differs from its original M3 binding");
    }

    private static void transform(ObjectNode result, Role role, boolean encode) {
        ObjectNode parent = result;
        for (int index = 0; index < role.path().size() - 1; index++) {
            JsonNode child = parent.get(role.path().get(index));
            StrictJson.require(child instanceof ObjectNode, "original lifecycle revision parent object required");
            parent = (ObjectNode) child;
        }
        String field = role.path().getLast(); JsonNode value = parent.get(field);
        if (value == null || value.isNull()) {
            StrictJson.require(!role.required(), "original lifecycle revision role missing or null");
            return;
        }
        if (encode) {
            StrictJson.require(value.isIntegralNumber() && value.bigIntegerValue().signum() >= 0,
                    "original lifecycle revision must be an exact nonnegative integer");
            parent.put(field, value.bigIntegerValue().toString());
        } else {
            StrictJson.require(value.isTextual() && value.textValue().length() <= 4300
                    && value.textValue().matches("0|[1-9][0-9]*"),
                    "public lifecycle revision requires a canonical decimal string");
            parent.put(field, new BigInteger(value.textValue()));
        }
    }
    private static ObjectNode object(RawJson value) {
        JsonNode parsed = PublicDataJson.object(value);
        StrictJson.require(parsed instanceof ObjectNode, "original lifecycle result object required");
        return (ObjectNode) parsed;
    }
}
