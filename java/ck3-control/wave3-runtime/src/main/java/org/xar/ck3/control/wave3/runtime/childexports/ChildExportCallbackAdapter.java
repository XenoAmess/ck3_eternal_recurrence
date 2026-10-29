package org.xar.ck3.control.wave3.runtime.childexports;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Base64;
import java.util.ArrayList;
import java.util.List;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.Packet;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.ProcessReadbacks;

/**
 * Payload adapter registered in the existing single host; no transport/process ownership.
 * A retained local role and actual original reader values remain caller responsibilities.
 */
public final class ChildExportCallbackAdapter {
    public static final String INPUT_SCHEMA = "xar.java.child-export-callback-input/v1";
    public static final String RESULT_SCHEMA = "xar.java.child-export-callback-result/v1";

    public enum Operation { CANONICALIZE_WIRE, PRODUCE_WIRE, VALIDATE_READBACKS }

    public sealed interface Request permits CanonicalizeWire, ProduceWire, ValidateReadbacks { }

    /** Base64 carries original bytes through the default host JSON without integer or UTF-8 rewriting. */
    public record CanonicalizeWire(ChildRole retainedRole, String wireBase64) implements Request {
        public CanonicalizeWire {
            StrictJson.require(retainedRole != null, "original retained edge role required");
            // These are untrusted private input bytes, so fail at the typed decode
            // boundary. Project/encoder exceptions remain host04 internal failures.
            ChildExportCodec.decode(retainedRole, decodeBase64(wireBase64));
        }
    }

    /** Post-reader JSON value projection; it cannot create or transfer a retained handle. */
    public record ValidateReadbacks(ChildRole retainedRole, String keysJsonBase64) implements Request {
        public ValidateReadbacks {
            StrictJson.require(retainedRole != null, "original retained edge role required");
            JsonNode projection = StrictJson.parse(decodeBase64(keysJsonBase64),
                    ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES,
                    StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300);
            ChildExportCodec.parseReadbacks(retainedRole, projection);
        }
    }

    /** Actual retained HANDLE locations cross the host JSON as exact decimal text, never floating numbers. */
    public record ProduceWire(ChildRole retainedRole, List<String> locationDecimals) implements Request {
        public ProduceWire {
            StrictJson.require(retainedRole != null && locationDecimals != null, "complete actual export inputs required");
            StrictJson.require(locationDecimals.size() == retainedRole.exportedRoles().size(), "actual child export count differs");
            // The original roles export at most two locations. Two canonical
            // 4300-digit values plus the fixed role/frame bytes fit below 16 KiB;
            // the callback regression encodes that actual maximal legal input.
            StrictJson.require(retainedRole.exportedRoles().size() <= 2, "private export input budget requires at most two locations");
            for (String decimal : locationDecimals) {
                StrictJson.require(decimal != null && decimal.matches("[1-9][0-9]*"), "canonical positive remote location decimal text required");
                StrictJson.require(decimal.length() <= ChildExportCodec.PRIVATE_INTEGER_MAX_DECIMAL_DIGITS,
                        "original private JSON input integer digit profile exceeded");
            }
            locationDecimals = List.copyOf(locationDecimals);
        }
    }

    public sealed interface Result permits CanonicalWire, CheckedReadbacks { }

    public record CanonicalWire(Operation operation, Packet packet, String wireBase64) implements Result {
        public CanonicalWire {
            StrictJson.require(operation == Operation.CANONICALIZE_WIRE || operation == Operation.PRODUCE_WIRE,
                    "exact wire-producing callback operation required");
            StrictJson.require(packet != null, "decoded original packet required");
            decodeBase64(wireBase64);
        }
    }

    public record CheckedReadbacks(ProcessReadbacks readbacks) implements Result {
        public CheckedReadbacks { StrictJson.require(readbacks != null, "complete original process observations required"); }
    }

    private ChildExportCallbackAdapter() { }

    public static Request decodeRequest(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "child callback payload object required");
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(value.get("schema"))), "exact child callback input schema required");
        String operation = StrictJson.text(value.get("operation"));
        return switch (operation) {
            case "CANONICALIZE_WIRE" -> {
                ObjectNode row = StrictJson.object(value, Set.of("schema", "operation", "retained_role", "wire_base64"));
                yield new CanonicalizeWire(ChildRole.parse(StrictJson.text(row.get("retained_role"))),
                        StrictJson.text(row.get("wire_base64")));
            }
            case "VALIDATE_READBACKS" -> {
                ObjectNode row = StrictJson.object(value, Set.of("schema", "operation", "retained_role", "keys_json_base64"));
                yield new ValidateReadbacks(ChildRole.parse(StrictJson.text(row.get("retained_role"))),
                        StrictJson.text(row.get("keys_json_base64")));
            }
            case "PRODUCE_WIRE" -> {
                ObjectNode row = StrictJson.object(value, Set.of("schema", "operation", "retained_role", "location_decimals"));
                ChildRole role = ChildRole.parse(StrictJson.text(row.get("retained_role")));
                JsonNode values = row.get("location_decimals");
                StrictJson.require(values != null && values.isArray() && values.size() == role.exportedRoles().size(),
                        "exact actual child export input count required");
                List<String> decimals = new ArrayList<>();
                for (JsonNode decimal : values) { decimals.add(StrictJson.text(decimal)); }
                yield new ProduceWire(role, decimals);
            }
            default -> throw new ContractViolationException("unsupported exact child callback operation");
        };
    }

    public static Result evaluate(Request request) {
        StrictJson.require(request != null, "typed child callback request required");
        return switch (request) {
            case CanonicalizeWire wire -> {
                Packet packet = ChildExportCodec.decode(wire.retainedRole(), decodeBase64(wire.wireBase64()));
                yield new CanonicalWire(Operation.CANONICALIZE_WIRE, packet,
                        Base64.getEncoder().encodeToString(ChildExportCodec.encode(packet)));
            }
            case ProduceWire producer -> {
                List<ChildExportValues.Export> exports = new ArrayList<>();
                List<ChildRole> roles = producer.retainedRole().exportedRoles();
                for (int index = 0; index < roles.size(); index++) {
                    exports.add(new ChildExportValues.Export(roles.get(index),
                            new ChildExportValues.RemoteLocation(new BigInteger(producer.locationDecimals().get(index)))));
                }
                Packet packet = new Packet(producer.retainedRole(), exports);
                yield new CanonicalWire(Operation.PRODUCE_WIRE, packet,
                        Base64.getEncoder().encodeToString(ChildExportCodec.encode(packet)));
            }
            case ValidateReadbacks keys -> {
                JsonNode projection = StrictJson.parse(decodeBase64(keys.keysJsonBase64()),
                        ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES,
                        StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300);
                yield new CheckedReadbacks(ChildExportCodec.parseReadbacks(keys.retainedRole(), projection));
            }
        };
    }

    /** Registration port for the existing typed host dispatch; it does not read stdin or launch anything. */
    public static ObjectNode handle(JsonNode payload) {
        return encodeResult(evaluate(decodeRequest(payload)));
    }

    public static ObjectNode encodeResult(Result result) {
        StrictJson.require(result != null, "typed child callback result required");
        ObjectNode reply = StrictJson.object();
        reply.put("schema", RESULT_SCHEMA);
        switch (result) {
            case CanonicalWire wire -> {
                reply.put("operation", wire.operation().name());
                reply.put("retained_role", wire.packet().exportingRole().wire());
                reply.put("wire_base64", wire.wireBase64());
                reply.put("export_count", wire.packet().exports().size());
            }
            case CheckedReadbacks keys -> {
                reply.put("operation", Operation.VALIDATE_READBACKS.name());
                reply.put("retained_role", keys.readbacks().directRole().wire());
                reply.put("process_count", keys.readbacks().processes().size());
            }
        }
        return reply;
    }

    private static byte[] decodeBase64(String encoded) {
        StrictJson.text(encoded);
        StrictJson.require(encoded.length() <= ((ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES + 2) / 3) * 4,
                "bounded private callback base64 required");
        byte[] raw;
        try {
            raw = Base64.getDecoder().decode(encoded);
        } catch (IllegalArgumentException error) {
            throw new ContractViolationException("invalid canonical callback base64", error);
        }
        StrictJson.require(raw.length > 0 && raw.length <= ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES,
                "bounded nonempty original private callback bytes required");
        StrictJson.require(Base64.getEncoder().encodeToString(raw).equals(encoded), "canonical base64 required");
        return raw;
    }
}

