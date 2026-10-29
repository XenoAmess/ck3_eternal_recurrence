package org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.PublicUnsigned64.Minimum;
import org.xar.ck3.control.contracts.PublicUnsigned64.NumericInput;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry.DriverRegistryContract.*;

/** Public-only uint64 decimal strings; the actual native result and archive remain numeric and unchanged. */
public final class DriverRegistryCodec {
    private static final int MAXIMUM_BYTES = 1 << 20;
    private DriverRegistryCodec() { }
    public static CachedRequest cached(PublicBindings.Arguments arguments) {
        if (!(arguments instanceof PublicBindings.Value value)) throw new IllegalArgumentException("cached succession requires explicit named arguments");
        ObjectNode fields = StrictJson.object(StrictJson.parse(value.original().bytes(), MAXIMUM_BYTES), Set.of("expected_revision"));
        return new CachedRequest(PublicUnsigned64.parse(fields.get("expected_revision"), Minimum.ONE, NumericInput.SAFE_INTEGER_OR_DECIMAL));
    }
    public static RawJson encode(CachedResponse response) {
        ObjectNode fields = object(CachedSuccession12004.encodePublic(response.original()));
        public64(fields, "queried_revision", Minimum.ONE); public64(fields, "queried_native_revision", Minimum.ONE);
        public64(fields, "connection_generation", Minimum.ONE);
        ObjectNode nativeResult = objectField(fields, "native_result"); public64(nativeResult, "snapshot_revision", Minimum.ONE);
        ObjectNode payload = objectField(nativeResult, "actor_cached_succession"); public64(payload, "capture_epoch", Minimum.ONE);
        nullable64(payload, "native_data_pointer", Minimum.ZERO); nullable64(payload, "land_state_pointer", Minimum.ONE);
        return new RawJson(StrictJson.canonical(fields, MAXIMUM_BYTES));
    }
    /** Serialized public consumer reverses only the seven named uint64 wire fields before the existing strict decoder. */
    public static CachedResponse decode(RawJson publicResult) {
        ObjectNode fields = object(publicResult);
        native64(fields, "queried_revision", Minimum.ONE); native64(fields, "queried_native_revision", Minimum.ONE);
        native64(fields, "connection_generation", Minimum.ONE);
        ObjectNode nativeResult = objectField(fields, "native_result"); native64(nativeResult, "snapshot_revision", Minimum.ONE);
        ObjectNode payload = objectField(nativeResult, "actor_cached_succession"); native64(payload, "capture_epoch", Minimum.ONE);
        nullableNative64(payload, "native_data_pointer", Minimum.ZERO); nullableNative64(payload, "land_state_pointer", Minimum.ONE);
        var binding = new CachedSuccession12004.Binding(StrictJson.text(fields.get("queried_snapshot_id")),
                fields.get("queried_revision").bigIntegerValue(), fields.get("queried_native_revision").bigIntegerValue(),
                (int) StrictJson.integer(fields.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                StrictJson.integer(fields.get("game_pid"), 1, 0xffff_ffffL), fields.get("connection_generation").bigIntegerValue(),
                StrictJson.integer(fields.get("player_character_id"), Integer.MIN_VALUE, 0xffff_fffeL));
        var result = new CachedResponse(CachedSuccession12004.decodePublic(new RawJson(StrictJson.canonical(fields, MAXIMUM_BYTES)), binding));
        StrictJson.require(object(publicResult).equals(object(encode(result))), "public cached succession wire differs from its sole normalized serializer");
        return result;
    }
    private static ObjectNode object(RawJson raw) {
        JsonNode fields = StrictJson.parse(raw.bytes(), MAXIMUM_BYTES);
        StrictJson.require(fields instanceof ObjectNode, "public cached succession object required"); return (ObjectNode) fields;
    }
    private static ObjectNode objectField(ObjectNode parent, String key) {
        JsonNode value = parent.get(key); StrictJson.require(value instanceof ObjectNode, "public cached succession missing object " + key); return (ObjectNode) value;
    }
    private static void public64(ObjectNode fields, String key, Minimum minimum) {
        JsonNode value = fields.get(key); StrictJson.require(value != null && value.isIntegralNumber(), "actual original numeric uint64 required: " + key);
        fields.put(key, PublicUnsigned64.canonical(value.bigIntegerValue(), minimum));
    }
    private static void nullable64(ObjectNode fields, String key, Minimum minimum) {
        StrictJson.require(fields.has(key), "original nullable uint64 field missing: " + key);
        if (!fields.get(key).isNull()) public64(fields, key, minimum);
    }
    private static void native64(ObjectNode fields, String key, Minimum minimum) {
        BigInteger value = PublicUnsigned64.parse(fields.get(key), minimum, NumericInput.DECIMAL_ONLY); fields.put(key, value);
    }
    private static void nullableNative64(ObjectNode fields, String key, Minimum minimum) {
        StrictJson.require(fields.has(key), "public nullable uint64 field missing: " + key);
        if (!fields.get(key).isNull()) native64(fields, key, minimum);
    }
}
