package org.xar.ck3.control.wave2.military.supplyschedule;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;

/** Source-derived next-frame consumer boundary; outer native SDK rows remain extensible. */
public final class NativeNextDailySupplyScheduleCodec {
    private NativeNextDailySupplyScheduleCodec() { }
    public static NativeNextDailySupplySchedule fromSameQueryRow(JsonNode row) { return fromSameQueryRow(row, false); }
    public static NativeNextDailySupplySchedule fromSameQueryRowForHost(JsonNode row) { return fromSameQueryRow(row, true); }
    private static NativeNextDailySupplySchedule fromSameQueryRow(JsonNode row, boolean host) {
        input(host, () -> { StrictJson.require(row != null && row.isObject(), "same-query row object required"); return true; });
        Integer army = input(host, () -> signed32(row.get("army_id"))); Integer carmy = input(host, () -> signed32(row.get("native_carmy_id")));
        var frame = input(host, () -> SourceNextFrameCodec.decode(row.get("source_derived_next_daily_supply_frame_inputs_v1"), army, carmy));
        JsonNode family = row.get(FutureDailySupplyScheduleCodec.FAMILY_KEY);
        var schedule = family == null ? null : input(host, () -> FutureDailySupplyScheduleCodec.decode(family, army, carmy));
        return NativeNextDailySupplySchedule.project(schedule, frame);
    }
    public static JsonNode encode(NativeNextDailySupplySchedule value) {
        if (value == null) return NullNode.getInstance();
        ObjectNode node = (ObjectNode) FutureDailySupplyScheduleProjectionCodec.encode(value.scheduleProjection());
        if (value.nativeNextPairUsed()) {
            node.put("condition", "source_derived_next_date_and_day_with_observed_buckets_unchanged");
            node.put("calendar_derived", true); node.put("actual_future_date_stage_observed", false);
            node.set("source_next_pair", SourceNextFrameCodec.encode(value.sourceFrame()));
        }
        node.put("full_future_cdate64_reconstructed", value.fullFutureCdate64Reconstructed());
        node.put("source_derived_full_cdate64_ready", value.fullFutureCdate64Reconstructed());
        nullable(node, "source_derived_next_date_storage_raw64", value.nextDateStorageRaw64());
        nullable(node, "source_derived_next_calendar_day_u8", value.nextCalendarDayU8());
        nullable(node, "source_derived_next_calendar_month_u8", value.nextCalendarMonthU8());
        for (JsonNode frameNode : node.get("prospective_frames")) {
            ObjectNode frame = (ObjectNode) frameNode;
            if (value.nativeNextPairUsed()) { frame.put("origin", "source_derived_conditional_next_date_pair"); frame.put("actual_native_frame_observed", false); }
            nullable(frame, "date_storage_raw64", value.nextDateStorageRaw64()); nullable(frame, "calendar_day_u8", value.nextCalendarDayU8());
            nullable(frame, "calendar_month_u8", value.nextCalendarMonthU8());
            frame.put("source_derived_full_cdate64_ready", value.fullFutureCdate64Reconstructed());
        }
        return node;
    }

    private static <T> T input(boolean host, java.util.function.Supplier<T> validator) {
        try { return validator.get(); }
        catch (IllegalArgumentException rejected) {
            if (!host || rejected instanceof org.xar.ck3.control.contracts.projection.ProjectionDomainRejection) throw rejected;
            throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(rejected.getMessage());
        }
    }

    private static Integer signed32(JsonNode node) { return node == null || node.isNull() ? null : (int) StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static void nullable(ObjectNode node, String key, Number value) { if (value == null) node.putNull(key); else node.put(key, value.longValue()); }
}
