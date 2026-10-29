package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;

/** Narrow JSON/native boundary. Original packets remain in coordinator custody; no loose JSON enters domain types. */
public final class CoaCodec {
    private static final ObjectMapper JSON = new ObjectMapper();
    private CoaCodec() { }
    public static NativeRequest probeRequest(EncodedSource source, boolean apply) {
        ObjectNode fields = JSON.createObjectNode(); fields.put("source_base64", source.sourceBase64()); fields.put("apply", apply);
        return new NativeRequest(PROBE_STEP, "game.command." + PROBE_STEP, raw(fields));
    }
    public static NativeRequest exportRequest() { return primitive(EXPORT_STEP); }
    public static NativeRequest primitive(String step) {
        require(Set.of(EXPORT_STEP, "inspect-frontend-coat-of-arms-tree-v1", "inspect-frontend-coat-of-arms-pattern-grid-v1",
                "activate-frontend-coat-of-arms-designer-v1", "commit-frontend-dynasty-coat-of-arms-v1", "activate-frontend-coat-of-arms-custom-mode-v1").contains(step), "unregistered CoA primitive");
        return new NativeRequest(step, "game.command." + step, new RawJson("{}".getBytes(StandardCharsets.US_ASCII)));
    }
    public static ProbeResult nativeProbe(RawJson original, EncodedSource source, Binding binding, boolean apply) {
        ObjectNode envelope = object(parse(original)); nativeHeader(envelope, "coat_of_arms_probe");
        require(string(envelope, "step").equals(PROBE_STEP) && bool(envelope, "accepted"), "native probe identity invalid");
        require(integer(envelope, "snapshot_revision", BigInteger.ZERO, U64_MAX).equals(binding.nativeRevision()), "native probe revision drift");
        BigInteger sequence = integer(envelope, "query_sequence", BigInteger.ONE, U64_MAX);
        ObjectNode payload = object(envelope.get("coat_of_arms_probe")); exact(payload, "schema", "schema_version", "status", "date_raw", "source_bytes", "designer_observed", "clipboard_written", "clipboard_readback_matched", "detected", "apply_requested", "paste_invoked", "applied", "candidate_index", "preview_coat_of_arms_handle", "active_coat_of_arms_index", "reason", "provenance");
        require(string(payload, "schema").equals("xar.ck3.coat-of-arms-designer-probe.v1") && intValue(payload, "schema_version", 1, 1) == 1, "native probe schema invalid");
        require(integer(payload, "date_raw", BigInteger.valueOf(Long.MIN_VALUE), BigInteger.valueOf(Long.MAX_VALUE)).longValueExact() == binding.dateRaw(), "native probe date drift");
        require(intValue(payload, "source_bytes", 1, V2_MAX_BYTES) == source.sourceBytes(), "native probe source byte identity drift");
        ObjectNode provenance = object(payload.get("provenance")); exact(provenance, "backend_id");
        require(string(provenance, "backend_id").equals("ck3-1.19.0.6-native-coat-of-arms-designer-probe-v1"), "native probe provenance invalid");
        require(string(envelope, "status").equals(string(payload, "status")), "native probe status mirrors disagree");
        ProbeStatus status = switch (string(payload, "status")) { case "applied" -> ProbeStatus.APPLIED; case "detected" -> ProbeStatus.DETECTED;
            case "not_detected" -> ProbeStatus.NOT_DETECTED; case "apply_failed" -> ProbeStatus.APPLY_FAILED; case "unavailable" -> ProbeStatus.UNAVAILABLE; default -> throw new IllegalArgumentException("native probe status invalid"); };
        require(bool(payload, "apply_requested") == apply, "native probe apply request changed");
        return new ProbeResult(status, bool(payload, "detected"), bool(payload, "designer_observed"), bool(payload, "clipboard_written"),
                bool(payload, "clipboard_readback_matched"), apply, bool(payload, "paste_invoked"), bool(payload, "applied"),
                integer(payload, "candidate_index", BigInteger.ZERO, BigInteger.valueOf(0xffffffffL)).longValueExact(),
                integer(payload, "preview_coat_of_arms_handle", BigInteger.ZERO, BigInteger.valueOf(0xffffffffL)).longValueExact(),
                integer(payload, "active_coat_of_arms_index", BigInteger.ZERO, BigInteger.valueOf(0xffffffffL)).longValueExact(), nullableString(payload, "reason"), source, binding, sequence);
    }
    public static ExportResult nativeExport(RawJson original, Binding binding) {
        ObjectNode envelope = object(parse(original)); nativeHeader(envelope, "coat_of_arms_export");
        require(string(envelope, "step").equals(EXPORT_STEP) && bool(envelope, "accepted"), "native export identity invalid");
        require(integer(envelope, "snapshot_revision", BigInteger.ZERO, U64_MAX).equals(binding.nativeRevision()), "native export revision drift");
        BigInteger sequence = integer(envelope, "query_sequence", BigInteger.ZERO, U64_MAX);
        ObjectNode payload = object(envelope.get("coat_of_arms_export")); exact(payload, "schema", "schema_version", "status", "date_raw", "source_bytes", "designer_observed", "copy_invoked", "clipboard_read", "source", "reason", "provenance");
        require(string(payload, "schema").equals("xar.ck3.coat-of-arms-designer-export.v1") && intValue(payload, "schema_version", 1, 1) == 1, "native export schema invalid");
        require(integer(payload, "date_raw", BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)).longValueExact() == binding.dateRaw(), "native export date drift");
        ObjectNode provenance = object(payload.get("provenance")); exact(provenance, "backend_id");
        require(string(provenance, "backend_id").equals("ck3-1.19.0.6-native-coat-of-arms-designer-export-v1"), "native export provenance invalid");
        String status = string(payload, "status"); require(status.equals(string(envelope, "status")), "native export status mirrors disagree");
        require(status.equals("exported") || status.equals("unavailable"), "native export status invalid");
        Optional<String> source = nullableString(payload, "source"); Optional<String> digest = source.map(value -> sha256(ascii(value, V2_MAX_BYTES).getBytes(StandardCharsets.US_ASCII)));
        return new ExportResult(status.equals("exported") ? ExportStatus.EXPORTED : ExportStatus.UNAVAILABLE, bool(payload, "designer_observed"), bool(payload, "copy_invoked"), bool(payload, "clipboard_read"),
                source, digest, intValue(payload, "source_bytes", 0, V2_MAX_BYTES), nullableString(payload, "reason"), binding, sequence);
    }
    public static Tree tree(RawJson original, boolean grid) {
        ObjectNode envelope = object(parse(original)); String step = grid ? "inspect-frontend-coat-of-arms-pattern-grid-v1" : "inspect-frontend-coat-of-arms-tree-v1";
        return treeNode(envelope, step, grid ? "coat_of_arms_pattern_grid" : "coat_of_arms_page", grid);
    }
    /** Reused for the source-owned ruler-designer precondition census. */
    public static Tree rulerDesignerTree(RawJson original) { return treeNode(object(parse(original)), "inspect-frontend-gui-tree-v1", "ruler_designer", false); }
    private static Tree treeNode(ObjectNode envelope, String step, String root, boolean grid) {
        require(string(envelope, "step").equals(step) && bool(envelope, "accepted") && string(envelope, "scope_root_name").equals(root), "native CoA tree identity invalid");
        String status = string(envelope, "status"); boolean available = bool(envelope, "root_available");
        require((status.equals("available") || status.equals("unavailable")) && available == status.equals("available"), "native tree status invalid");
        int count = intValue(envelope, "widget_count", 0, 2048); JsonNode rows = envelope.get("widgets"); require(rows != null && rows.isArray() && rows.size() == count, "native tree widget count mismatch");
        List<Widget> widgets = new ArrayList<>();
        for (JsonNode row : rows) { ObjectNode widget = object(row); widgets.add(new Widget(string(widget, "runtime_name"), string(widget, "child_path"), intValue(widget, "depth", 0, 64), intValue(widget, "child_count", 0, 4096), integer(widget, "vtable_rva", BigInteger.ZERO, U64_MAX), bool(widget, "effective_visible"), bool(widget, "enabled"))); }
        Optional<Integer> directCount = Optional.empty();
        if (grid) {
            require(!widgets.isEmpty() && available, "pattern grid unavailable"); Widget first = widgets.get(0); int children = first.childCount();
            require(first.runtimeName().isEmpty() && first.childPath().isEmpty() && first.depth() == 0 && first.effectiveVisible() && first.enabled() && children > 0 && children < 2048, "pattern grid root invalid");
            Set<String> paths = new HashSet<>(); widgets.stream().filter(row -> row.depth() == 1).forEach(row -> paths.add(row.childPath()));
            require(paths.size() == children, "pattern direct child count mismatch"); for (int index = 0; index < children; index++) require(paths.contains(Integer.toString(index)), "pattern direct children incomplete"); directCount = Optional.of(children);
        }
        return new Tree(step, root, available, bool(envelope, "truncated"), widgets, directCount);
    }
    public record ActivationAck(String step, String backendId) { }
    public static ActivationAck activationAck(RawJson original, String expectedStep) {
        ObjectNode ack = object(parse(original)); require(string(ack, "step").equals(expectedStep) && bool(ack, "accepted") && string(ack, "status").equals("acknowledged_verification_pending"), "native activation ACK invalid");
        if (ack.has("backend_id")) require(string(ack, "backend_id").equals("native-headless"), "activation backend drift");
        return new ActivationAck(expectedStep, "native-headless");
    }
    private static void nativeHeader(ObjectNode row, String payload) {
        // backend_id is a projection injected by NativeDriver._execute_primitive_step, absent from the actual DLL result.
        if (row.has("backend_id")) { exact(row, "step", "accepted", "status", "query_sequence", "snapshot_revision", payload, "backend_id"); require(string(row, "backend_id").equals("native-headless"), "native backend projection drift"); }
        else exact(row, "step", "accepted", "status", "query_sequence", "snapshot_revision", payload);
    }
    public static FrontendBinding frontendBinding(RawJson capabilities) {
        List<FrontendBinding> candidates = new ArrayList<>(); visitFrontend(parse(capabilities), candidates); Set<FrontendBinding> unique = Set.copyOf(candidates);
        require(unique.size() == 1, "frontend CoA requires one exact native bridge"); return unique.iterator().next();
    }
    private static void visitFrontend(JsonNode node, List<FrontendBinding> candidates) {
        if (!node.isObject()) return; ObjectNode row = object(node);
        if (row.path("backend_id").asText().equals("native-headless") && row.path("mode").asText().equals("native-headless") && row.path("source").asText().equals("injected-dll-named-pipe")
                && row.path("visual_fallback").isBoolean() && !row.path("visual_fallback").booleanValue() && row.path("snapshot").isBoolean() && !row.path("snapshot").booleanValue()
                && contains(row.get("bridge_capabilities"), "game.command." + PROBE_STEP) && row.path("diagnostics").isObject()) {
            ObjectNode diagnostics = object(row.get("diagnostics")), hello = object(diagnostics.get("hello"));
            require(bool(diagnostics, "connected") && !bool(diagnostics, "semantic_state_available"), "frontend native bridge disconnected or semantic state available");
            long pid = integer(diagnostics, "bridge_pid", BigInteger.ONE, BigInteger.valueOf(0xffffffffL)).longValueExact();
            require(integer(hello, "pid", BigInteger.ONE, BigInteger.valueOf(0xffffffffL)).longValueExact() == pid, "frontend hello PID drift");
            require(string(hello, "game_adapter_id").equals(ADAPTER_ID) && string(hello, "game_adapter_status").equals("ready") && string(hello, "expected_ck3_version").equals(GAME_VERSION)
                    && string(hello, "expected_ck3_sha256").equalsIgnoreCase(EXE_SHA256) && bool(hello, "ck3_build_match") && contains(hello.get("capabilities"), "game.command." + PROBE_STEP), "frontend CoA exact build or capability drift");
            candidates.add(new FrontendBinding(integer(diagnostics, "connection_generation", BigInteger.ONE, U64_MAX), pid));
        }
        JsonNode backends = row.get("backends"); if (backends != null && backends.isArray()) for (JsonNode backend : backends) visitFrontend(backend, candidates);
    }
    private static boolean contains(JsonNode array, String expected) { if (array == null || !array.isArray()) return false; for (JsonNode value : array) if (value.isTextual() && value.textValue().equals(expected)) return true; return false; }
    public static Binding binding(RawJson input) {
        ObjectNode row = object(parse(input)); String mode = string(row, "mode");
        BigInteger generation = integer(row, "connection_generation", BigInteger.ONE, U64_MAX); long pid = integer(row, "bridge_pid", BigInteger.ONE, BigInteger.valueOf(0xffffffffL)).longValueExact();
        if (mode.equals("frontend")) { exact(row, "mode", "revision", "connection_generation", "bridge_pid"); require(integer(row, "revision", BigInteger.ZERO, BigInteger.ZERO).signum() == 0, "frontend revision must be zero"); return new FrontendBinding(generation, pid); }
        boolean gameplay = mode.equals("gameplay"); require(gameplay || mode.equals("frontend_snapshot"), "invalid binding mode");
        if (gameplay) exact(row, "mode", "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "connection_generation", "bridge_pid");
        else exact(row, "mode", "snapshot_id", "revision", "native_revision", "date_raw", "connection_generation", "bridge_pid");
        return new SnapshotBinding(gameplay ? SnapshotMode.GAMEPLAY : SnapshotMode.FRONTEND_SNAPSHOT, string(row, "snapshot_id"), integer(row, "revision", BigInteger.ONE, U64_MAX), integer(row, "native_revision", BigInteger.ONE, U64_MAX), integer(row, "date_raw", BigInteger.valueOf(Long.MIN_VALUE), BigInteger.valueOf(Long.MAX_VALUE)).longValueExact(), gameplay ? Optional.of(string(row, "episode_run_id")) : Optional.empty(), generation, pid);
    }
    static JsonNode parse(RawJson value) { try { return JSON.readTree(value.bytes()); } catch (IOException invalid) { throw new IllegalArgumentException("invalid native JSON", invalid); } }
    static RawJson raw(JsonNode value) { try { return new RawJson(JSON.writeValueAsBytes(value)); } catch (IOException invalid) { throw new IllegalArgumentException(invalid); } }
    static ObjectNode object(JsonNode node) { require(node != null && node.isObject(), "JSON object required"); return (ObjectNode) node; }
    static void exact(ObjectNode node, String... fields) { Set<String> found = new HashSet<>(); node.fieldNames().forEachRemaining(found::add); require(found.equals(Set.of(fields)), "JSON object fields differ from closed CoA contract"); }
    static String string(ObjectNode row, String field) { JsonNode value = row.get(field); require(value != null && value.isTextual(), "text field required: " + field); return value.textValue(); }
    static Optional<String> nullableString(ObjectNode row, String field) { JsonNode value = row.get(field); require(value != null && (value.isNull() || value.isTextual()), "required nullable string: " + field); return value.isNull() ? Optional.empty() : Optional.of(value.textValue()); }
    static boolean bool(ObjectNode row, String field) { JsonNode value = row.get(field); require(value != null && value.isBoolean(), "boolean field required: " + field); return value.booleanValue(); }
    static BigInteger integer(ObjectNode row, String field, BigInteger min, BigInteger max) { JsonNode value = row.get(field); require(value != null && value.isIntegralNumber(), "integer field required: " + field); BigInteger number = value.bigIntegerValue(); require(number.compareTo(min) >= 0 && number.compareTo(max) <= 0, "integer outside range: " + field); return number; }
    static int intValue(ObjectNode row, String field, int min, int max) { return integer(row, field, BigInteger.valueOf(min), BigInteger.valueOf(max)).intValueExact(); }
}
