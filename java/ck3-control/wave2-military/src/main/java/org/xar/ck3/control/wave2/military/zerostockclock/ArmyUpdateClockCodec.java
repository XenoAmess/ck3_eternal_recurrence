package org.xar.ck3.control.wave2.military.zerostockclock;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Single closed family boundary for the complete observed Army update clock. */
public final class ArmyUpdateClockCodec {
    private static final Set<String> FIELDS = Set.of("status", "ready", "unavailable_reason", "current_date_raw",
            "native_day_index", "selected_bucket_phase", "observed_army_bucket_phase", "last_supply_update_date_raw",
            "grace_anchor_date_raw", "loaded_grace_days", "last_supply_update_date_storage_raw64", "grace_anchor_date_storage_raw64");
    private ArmyUpdateClockCodec() { }
    public static ArmyUpdateClock decode(byte[] raw) { return decode(StrictJson.parse(raw)); }
    public static ArmyUpdateClock decode(JsonNode node) {
        if (node == null || node.isNull()) return null;
        ObjectNode value = StrictJson.object(node, FIELDS);
        ArmyUpdateClock.Status status = switch (StrictJson.text(value.get("status"))) {
            case "available" -> ArmyUpdateClock.Status.AVAILABLE;
            case "not_registered" -> ArmyUpdateClock.Status.NOT_REGISTERED;
            case "unavailable" -> ArmyUpdateClock.Status.UNAVAILABLE;
            default -> throw new ContractViolationException("unknown army clock status");
        };
        StrictJson.require(value.get("ready").isBoolean(), "army clock ready must be bool");
        JsonNode reason = value.get("unavailable_reason");
        return new ArmyUpdateClock(status, value.get("ready").booleanValue(), reason.isNull() ? null : StrictJson.text(reason),
                i32(value, "current_date_raw"), i32(value, "native_day_index"), i32(value, "selected_bucket_phase"),
                i32(value, "observed_army_bucket_phase"), i32(value, "last_supply_update_date_raw"),
                i32(value, "grace_anchor_date_raw"), i32(value, "loaded_grace_days"),
                i64(value, "last_supply_update_date_storage_raw64"), i64(value, "grace_anchor_date_storage_raw64"));
    }
    public static JsonNode encode(ArmyUpdateClock value) {
        if (value == null) return com.fasterxml.jackson.databind.node.NullNode.getInstance();
        ObjectNode out = StrictJson.object(); out.put("status", value.status().name().toLowerCase(Locale.ROOT));
        out.put("ready", value.ready()); out.put("unavailable_reason", value.unavailableReason());
        out.put("current_date_raw", value.currentDateRaw()); out.put("native_day_index", value.nativeDayIndex());
        out.put("selected_bucket_phase", value.selectedBucketPhase()); out.put("observed_army_bucket_phase", value.observedArmyBucketPhase());
        out.put("last_supply_update_date_raw", value.lastSupplyUpdateDateRaw()); out.put("grace_anchor_date_raw", value.graceAnchorDateRaw());
        out.put("loaded_grace_days", value.loadedGraceDays()); out.put("last_supply_update_date_storage_raw64", value.lastSupplyUpdateDateStorageRaw64());
        out.put("grace_anchor_date_storage_raw64", value.graceAnchorDateStorageRaw64()); return out;
    }
    static Long i64(JsonNode node, String field) {
        JsonNode value = node.get(field); return value == null || value.isNull() ? null : StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE);
    }
    static Integer i32(JsonNode node, String field) {
        JsonNode value = node.get(field); return value == null || value.isNull() ? null : (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE);
    }
}
