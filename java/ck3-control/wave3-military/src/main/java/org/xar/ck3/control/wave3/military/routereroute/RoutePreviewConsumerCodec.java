package org.xar.ck3.control.wave3.military.routereroute;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonGenerator;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.*;

/** Runtime validation precedes the typed planner. Opaque preview extension fields survive the consumer. */
public final class RoutePreviewConsumerCodec {
    public static final int MAXIMUM_BYTES = 1_048_576;
    private RoutePreviewConsumerCodec() { }
    /** The same runtime validator is used when a planner continuation is serialized and read back. */
    public static Preview decodePreview(byte[] raw) {
        return preview(StrictJson.parse(raw, MAXIMUM_BYTES));
    }
    /** The lookup/planner envelope is 1 MiB; individual preview output retains EvidenceJson's original 64 KiB limit.
     * StrictJson.canonical is deliberately integer-only, so it cannot serialize opaque decimal preview extensions.
     */
    public static byte[] encodeEnvelope(JsonNode node) {
        StrictJson.require(node != null, "complete route envelope value required");
        try {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (JsonGenerator generator = new JsonFactory().createGenerator(output)) { writeEvidence(generator, evidence(node)); }
            byte[] bytes = output.toByteArray();
            StrictJson.require(bytes.length <= MAXIMUM_BYTES, "bounded route planner envelope required"); return bytes;
        } catch (IOException failure) { throw new IllegalArgumentException("cannot encode route planner envelope", failure); }
    }
    private static void writeEvidence(JsonGenerator generator, EvidenceJson.Value value) throws IOException {
        switch (value) {
            case EvidenceJson.ObjectValue object -> {
                generator.writeStartObject();
                for (EvidenceJson.Member member : object.members()) { generator.writeFieldName(member.name()); writeEvidence(generator, member.value()); }
                generator.writeEndObject();
            }
            case EvidenceJson.ArrayValue array -> { generator.writeStartArray(); for (EvidenceJson.Value item : array.values()) { writeEvidence(generator, item); } generator.writeEndArray(); }
            case EvidenceJson.TextValue text -> generator.writeString(text.value());
            case EvidenceJson.IntegerValue integer -> generator.writeNumber(integer.value());
            case EvidenceJson.DecimalValue decimal -> generator.writeNumber(decimal.token());
            case EvidenceJson.BooleanValue bool -> generator.writeBoolean(bool.value());
            case EvidenceJson.NullValue ignored -> generator.writeNull();
        }
    }
    public static Lookup decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw, MAXIMUM_BYTES), Set.of(
                "commands", "snapshot", "army_id", "origin_province_id", "target_province_id", "date_raw"));
        JsonNode commands = root.get("commands"); StrictJson.require(commands.isArray(), "history array required");
        List<HistoryEntry> entries = new ArrayList<>();
        for (JsonNode row : commands) { entries.add(history(row)); }
        Optional<Lease> expected = root.get("snapshot").isNull() ? Optional.empty() : Optional.of(snapshotLease(root.get("snapshot")));
        Optional<Integer> date = root.get("date_raw").isNull() ? Optional.empty()
                : Optional.of((int) StrictJson.integer(root.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE));
        return new Lookup(entries, new Query(army(root.get("army_id")), province(root.get("origin_province_id")),
                province(root.get("target_province_id")), date, expected));
    }
    public static byte[] project(byte[] raw) { return encode(RouteReroutePolicy.freshPreview(decode(raw))); }
    public static byte[] encode(Optional<Preview> preview) {
        if (preview.isEmpty()) { return "null".getBytes(java.nio.charset.StandardCharsets.UTF_8); }
        Preview value = preview.orElseThrow();
        List<EvidenceJson.Member> members = new ArrayList<>();
        for (EvidenceJson.Member member : value.originalDocument().members()) {
            if (!member.name().equals("route_province_ids")) { members.add(member); }
        }
        List<EvidenceJson.Value> route = new ArrayList<>(); value.routeProvinceIds().forEach(id -> route.add(EvidenceJson.integer(id)));
        members.add(EvidenceJson.member("route_province_ids", new EvidenceJson.ArrayValue(route)));
        byte[] encoded = EvidenceJson.encode(new EvidenceJson.ObjectValue(members));
        StrictJson.require(encoded.length <= MAXIMUM_BYTES, "bounded complete preview result required"); return encoded;
    }
    private static HistoryEntry history(JsonNode row) {
        StrictJson.require(row.isObject(), "history rows must be objects");
        String command = effectiveCommand(row); boolean successful = exactTrue(row.get("ok"));
        if ("restore-checkpoint".equals(command)) { return new Restore(successful); }
        int[] merged = parse(command, "merge-armies-", "-with-", false);
        if (merged != null && merged[0] != merged[1]) { return new Merge(successful, merged[0], merged[1]); }
        int[] requested = parse(command, "preview-move-army-", "-to-", true);
        if (requested == null) { return new Ignored(); }
        JsonNode result = effectiveResult(row);
        Optional<Lease> lease = result == null ? Optional.empty() : resultLease(result);
        JsonNode rawPreview = result == null ? null : result.get("route_preview");
        Optional<Preview> preview = Optional.empty();
        // A malformed historical result remains unusable; it cannot poison a newer or older valid receipt.
        if (rawPreview != null && rawPreview.isObject()) {
            try { preview = Optional.of(preview(rawPreview)); }
            catch (IllegalArgumentException rejected) { preview = Optional.empty(); }
        }
        return new ReturnedPreview(successful, requested[0], requested[1], lease, preview);
    }
    private static Preview preview(JsonNode node) {
        String status = StrictJson.text(node.get("status"));
        PreviewStatus typed = switch (status) { case "available" -> PreviewStatus.AVAILABLE; case "deferred" -> PreviewStatus.DEFERRED;
            default -> throw new IllegalArgumentException("available/deferred preview required"); };
        List<Integer> route = new ArrayList<>();
        if (typed == PreviewStatus.AVAILABLE) {
            JsonNode values = node.get("route_province_ids"); StrictJson.require(values != null && values.isArray(), "route array required");
            values.forEach(value -> route.add(province(value)));
        }
        JsonNode stage = node.get("native_rejection_stage");
        RejectionStage rejection = stage == null || stage.isNull() ? RejectionStage.NONE
                : "move_mode_unavailable".equals(stage.asText()) ? RejectionStage.MOVE_MODE_UNAVAILABLE : RejectionStage.OTHER;
        return new Preview(typed, army(node.get("army_id")), province(node.get("origin_province_id")),
                province(node.get("target_province_id")),
                (int) StrictJson.integer(node.get("previewed_date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE), route,
                rejection, EvidenceJson.object(evidence(node)));
    }
    private static Lease snapshotLease(JsonNode node) {
        StrictJson.require(node.isObject(), "snapshot object required");
        JsonNode diagnostics = node.get("diagnostics"); StrictJson.require(diagnostics != null && diagnostics.isObject(), "diagnostics object required");
        return new Lease(StrictJson.text(node.get("snapshot_id")), exactLong(node.get("revision")),
                exactLong(node.get("native_revision")), exactLong(diagnostics.get("connection_generation")),
                StrictJson.text(node.get("episode_run_id")));
    }
    private static Optional<Lease> resultLease(JsonNode node) {
        try { return Optional.of(new Lease(StrictJson.text(node.get("queried_snapshot_id")), exactLong(node.get("queried_revision")),
                exactLong(node.get("queried_native_revision")), exactLong(node.get("queried_connection_generation")),
                StrictJson.text(node.get("queried_episode_run_id")))); }
        catch (IllegalArgumentException rejected) { return Optional.empty(); }
    }
    private static long exactLong(JsonNode node) { return StrictJson.integer(node, 0, StrictJson.MAX_SAFE_INTEGER); }
    private static int army(JsonNode node) { return (int) StrictJson.integer(node, 0, Integer.MAX_VALUE); }
    private static int province(JsonNode node) { return (int) StrictJson.integer(node, 1, Integer.MAX_VALUE); }
    private static boolean exactTrue(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    private static String effectiveCommand(JsonNode row) {
        JsonNode command = row.get("command");
        if (command == null || !command.isTextual()) { return null; }
        if (!"auto-turn".equals(command.textValue())) { return command.textValue(); }
        JsonNode result = row.get("result"), auto = result != null && result.isObject() ? result.get("auto_turn") : null;
        JsonNode selected = auto != null && auto.isObject() ? auto.get("selected_step") : null;
        return selected != null && selected.isTextual() ? selected.textValue() : null;
    }
    private static JsonNode effectiveResult(JsonNode row) {
        JsonNode result = row.get("result"); if (result == null || !result.isObject()) { return null; }
        if (!"auto-turn".equals(row.path("command").asText())) { return result; }
        for (String key : List.of("assault_action", "route_preview", "war_action", "war_progress_before", "war_progress_after")) {
            JsonNode value = result.get(key); if (value != null && value.isObject()) { return result; }
        }
        JsonNode auto = result.get("auto_turn"), nested = auto != null && auto.isObject() ? auto.get("result") : null;
        return nested != null && nested.isObject() ? nested : result;
    }
    private static int[] parse(String command, String prefix, String separator, boolean targetIsProvince) {
        if (command == null || !command.startsWith(prefix)) { return null; }
        String tail = command.substring(prefix.length()); int index = tail.indexOf(separator);
        if (index < 0) { return null; }
        String left = tail.substring(0, index), right = tail.substring(index + separator.length());
        if (!left.matches("0|[1-9][0-9]*") || !right.matches(targetIsProvince ? "[1-9][0-9]*" : "0|[1-9][0-9]*")) { return null; }
        try { return new int[]{Integer.parseInt(left), Integer.parseInt(right)}; }
        catch (NumberFormatException rejected) { return null; }
    }
    private static EvidenceJson.Value evidence(JsonNode node) {
        if (node.isNull()) { return EvidenceJson.NullValue.INSTANCE; }
        if (node.isTextual()) { return EvidenceJson.text(node.textValue()); }
        if (node.isBoolean()) { return new EvidenceJson.BooleanValue(node.booleanValue()); }
        if (node.isIntegralNumber()) { return new EvidenceJson.IntegerValue(node.bigIntegerValue()); }
        if (node.isFloatingPointNumber()) {
            String token = node.decimalValue().toString();
            if (token.indexOf('.') < 0 && token.indexOf('e') < 0 && token.indexOf('E') < 0) { token += ".0"; }
            return new EvidenceJson.DecimalValue(token);
        }
        if (node.isArray()) { List<EvidenceJson.Value> values = new ArrayList<>(); node.forEach(value -> values.add(evidence(value))); return new EvidenceJson.ArrayValue(values); }
        StrictJson.require(node.isObject(), "JSON evidence value required"); List<EvidenceJson.Member> values = new ArrayList<>();
        node.properties().forEach(entry -> values.add(EvidenceJson.member(entry.getKey(), evidence(entry.getValue()))));
        return new EvidenceJson.ObjectValue(values);
    }
}
