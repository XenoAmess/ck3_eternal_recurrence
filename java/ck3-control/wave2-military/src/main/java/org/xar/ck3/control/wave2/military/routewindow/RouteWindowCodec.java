package org.xar.ck3.control.wave2.military.routewindow;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Available;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Conflict;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Horizon;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.OpposingEdge;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Projection;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Route;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.SameProvince;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Unavailable;

/** Validates a declared projection from the caller-bound normalized H1 receipt. */
public final class RouteWindowCodec {
    private RouteWindowCodec() { }

    private record Input(JsonNode horizon, int days) { }
    private static Input decodeInput(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("horizon", "horizon_days"));
        return new Input(input.get("horizon"), (int) StrictJson.integer(input.get("horizon_days"), 1, 3));
    }
    /** No route projection, result construction or serialization executes here. */
    public static void validateRequest(byte[] raw) { decodeInput(raw); }

    public static byte[] project(byte[] raw) {
        Input input = decodeInput(raw);
        return encode(decodeAndProject(input.horizon(), input.days()));
    }

    private static Projection decodeAndProject(JsonNode horizon, int days) {
        if (!object(horizon) || !text(horizon.get("status"), "available")) {
            return new Unavailable(days, null, null, List.of("available_route_contact_horizon"));
        }
        JsonNode rawStart = horizon.get("date_raw");
        if (!int32(rawStart) || rawStart.longValue() + (long) days * RouteWindowPolicy.RAW_UNITS_PER_DAY > Integer.MAX_VALUE) {
            return new Unavailable(days, null, null, List.of("date_raw"));
        }
        int start = rawStart.intValue(); int end = Math.toIntExact((long) start + (long) days * RouteWindowPolicy.RAW_UNITS_PER_DAY);
        List<String> missing = new ArrayList<>(); JsonNode subject = horizon.get("subject_route");
        JsonNode hostiles = horizon.get("hostile_routes"); JsonNode ids = horizon.get("hostile_army_ids");
        if (!object(subject)) { missing.add("subject_route"); }
        List<JsonNode> hostileRows = new ArrayList<>();
        if (hostiles == null || !hostiles.isArray() || ids == null || !ids.isArray()) { missing.add("hostile_routes"); }
        else {
            hostiles.forEach(hostileRows::add);
            boolean complete = !ids.isEmpty() && hostiles.size() == ids.size();
            for (int index = 0; complete && index < hostiles.size(); index++) {
                JsonNode row = hostiles.get(index); JsonNode id = ids.get(index);
                complete = object(row) && publicId(id) && publicId(row.get("army_id")) && row.get("army_id").equals(id);
            }
            if (!complete) { missing.add("complete_hostile_routes"); }
        }
        List<Route> parsed = new ArrayList<>();
        for (int index = -1; index < hostileRows.size(); index++) {
            String name = index < 0 ? "subject_route" : "hostile_routes[" + index + "]";
            JsonNode row = index < 0 ? subject : hostileRows.get(index);
            if (!object(row)) { if (!missing.contains(name)) { missing.add(name); } continue; }
            if (!timeline(row, start) || !publicId(row.get("army_id"))) { missing.add(name + ".complete_timeline"); continue; }
            parsed.add(new Route(row.get("army_id").intValue(), row.get("current_province_id").intValue(),
                    integers(row.get("route_province_ids")), integers(row.get("arrival_date_raws"))));
        }
        if (!missing.isEmpty()) { return new Unavailable(days, start, end, missing); }
        return RouteWindowPolicy.project(new Horizon(start, days, parsed.getFirst(), parsed.subList(1, parsed.size())));
    }

    public static byte[] encode(Projection projection) {
        ObjectNode output = StrictJson.object(); output.put("context_basis", "frozen_current_routes");
        output.put("horizon_days", projection.horizonDays()); nullable(output, "window_start_date_raw", projection.windowStartDateRaw());
        nullable(output, "window_end_date_raw", projection.windowEndDateRaw());
        var conflicts = output.putArray("conflicts"); var missing = output.putArray("missing");
        if (projection instanceof Available available) {
            output.put("status", "available"); output.put("contact_free", available.contactFree());
            nullable(output, "first_contact_date_raw", available.firstContactDateRaw());
            output.put("contact_free_whole_days", available.contactFreeWholeDays());
            for (Conflict conflict : available.conflicts()) {
                ObjectNode row = conflicts.addObject(); row.put("hostile_army_id", conflict.hostileArmyId());
                row.put("overlap_start_date_raw", conflict.overlapStartDateRaw()); row.put("overlap_end_date_raw", conflict.overlapEndDateRaw());
                if (conflict instanceof SameProvince province) {
                    row.put("kind", "same_province"); row.put("province_id", province.provinceId());
                } else if (conflict instanceof OpposingEdge edge) {
                    row.put("kind", "opposing_edge"); row.put("subject_from_province_id", edge.subjectFromProvinceId());
                    row.put("subject_to_province_id", edge.subjectToProvinceId()); row.put("hostile_from_province_id", edge.hostileFromProvinceId());
                    row.put("hostile_to_province_id", edge.hostileToProvinceId());
                }
            }
        } else if (projection instanceof Unavailable unavailable) {
            output.put("status", "unavailable"); output.putNull("contact_free"); output.putNull("first_contact_date_raw");
            output.put("contact_free_whole_days", 0); unavailable.missing().forEach(missing::add);
        }
        return StrictJson.canonical(output);
    }

    private static boolean timeline(JsonNode row, int start) {
        JsonNode provinces = row.get("route_province_ids"); JsonNode arrivals = row.get("arrival_date_raws");
        if (!boolTrue(row.get("timeline_observable")) || !int32(row.get("current_province_id"))
                || row.get("current_province_id").intValue() <= 0 || provinces == null || !provinces.isArray()
                || arrivals == null || !arrivals.isArray() || provinces.size() != arrivals.size()) { return false; }
        for (JsonNode province : provinces) { if (!int32(province) || province.intValue() <= 0) { return false; } }
        Integer previous = null;
        for (JsonNode arrival : arrivals) {
            if (!int32(arrival) || arrival.intValue() < start || previous != null && previous > arrival.intValue()) { return false; }
            previous = arrival.intValue();
        }
        return true;
    }
    private static boolean int32(JsonNode value) { return value != null && value.isIntegralNumber() && value.canConvertToInt(); }
    private static boolean publicId(JsonNode value) { return int32(value) && value.intValue() >= 0; }
    private static boolean object(JsonNode value) { return value != null && value.isObject(); }
    private static boolean text(JsonNode value, String expected) { return value != null && value.isTextual() && value.textValue().equals(expected); }
    private static boolean boolTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static List<Integer> integers(JsonNode values) { List<Integer> result = new ArrayList<>(); values.forEach(value -> result.add(value.intValue())); return result; }
    private static void nullable(ObjectNode output, String field, Integer value) { if (value == null) { output.putNull(field); } else { output.put(field, value); } }
}
