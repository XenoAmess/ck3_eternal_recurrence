package org.xar.ck3.control.contracts.offline;

import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import static org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.*;

/** The independent metadata role is 2 MiB. Original source/document and map limits stay unchanged. */
public final class OfflineEventAnalysisWire {
    private static final ObjectMapper MAPPER = new ObjectMapper(com.fasterxml.jackson.core.JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private OfflineEventAnalysisWire() { }
    public static final class InvalidRequest extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        private final boolean oversized;
        public InvalidRequest(boolean oversized, String message) { super(message); this.oversized = oversized; }
        public boolean oversized() { return oversized; }
    }
    public static CaptureRequest decodeCapture(byte[] raw) {
        try {
            ObjectNode root = request(raw, CAPTURE_REQUEST_SCHEMA, Set.of("schema", "batch_id", "launch_ref"));
            return new CaptureRequest(text(root, "batch_id"), ExactRef.fromJson(root.get("launch_ref")));
        } catch (InvalidRequest failure) { throw failure; }
        catch (IllegalArgumentException failure) { throw invalid(failure); }
    }
    public static ReviewRequest decodeReview(byte[] raw) {
        try {
            ObjectNode root = request(raw, REVIEW_REQUEST_SCHEMA, Set.of("schema", "batch_id", "source_refs"));
            return new ReviewRequest(text(root, "batch_id"), refs(root.get("source_refs"), 4609));
        } catch (InvalidRequest failure) { throw failure; }
        catch (IllegalArgumentException failure) { throw invalid(failure); }
    }
    public static BatchRequest decodeBatch(byte[] raw) {
        try {
            ObjectNode root = request(raw, BATCH_REQUEST_SCHEMA, Set.of("schema", "batch_id", "manifest_ref", "captured_refs"));
            return new BatchRequest(text(root, "batch_id"), ExactRef.fromJson(root.get("manifest_ref")), refs(root.get("captured_refs"), 512));
        } catch (InvalidRequest failure) { throw failure; }
        catch (IllegalArgumentException failure) { throw invalid(failure); }
    }
    public static byte[] encode(BatchRequest request) {
        var root = StrictJson.object(); root.put("schema", BATCH_REQUEST_SCHEMA); root.put("batch_id", request.batchId());
        root.set("manifest_ref", request.manifestRef().toJson());
        var refs = root.putArray("captured_refs"); request.capturedRefs().forEach(ref -> refs.add(ref.toJson()));
        byte[] raw = encodeMetadata(root);
        if (!request.equals(decodeBatch(raw))) throw new IllegalStateException("offline batch request round trip differs");
        return raw;
    }
    public static byte[] encode(CaptureResult result) {
        var root = StrictJson.object(); root.put("schema", CAPTURE_RESULT_SCHEMA); root.put("batch_id", result.batchId());
        var refs = root.putArray("source_refs"); result.sourceRefs().forEach(ref -> refs.add(ref.toJson())); return encodeMetadata(root);
    }
    public static byte[] encode(ReviewResult result) {
        var root = StrictJson.object(); root.put("schema", REVIEW_RESULT_SCHEMA); root.put("batch_id", result.batchId());
        var rows = root.putArray("reviews");
        for (Review review : result.reviews()) {
            var row = rows.addObject(); row.put("incident_id", review.incidentId()); row.put("status", review.status().wire()); row.set("review", review.review().toJson());
        }
        root.set("publication", publication(result.publication()));
        var refs = root.putArray("source_refs"); result.sourceRefs().forEach(ref -> refs.add(ref.toJson())); return encodeMetadata(root);
    }
    public static byte[] encode(OfflineEventAnalysisContract.Error error) {
        var root = StrictJson.object(); root.put("schema", ERROR_SCHEMA);
        if (error.batchId().isPresent()) root.put("batch_id", error.batchId().orElseThrow()); else root.putNull("batch_id");
        root.put("code", error.code().wire()); root.put("message", error.message()); return encodeMetadata(root);
    }
    /** Domain report JSON remains original raw bytes, including decimal token category and Unicode. */
    public static byte[] validateBatchResult(byte[] raw, String expectedBatchId) {
        byte[] retained = ProjectionJson.object(raw, MAX_METADATA_BYTES).bytes();
        var root = object(retained, Set.of("schema", "batch_id", "machine_id", "observed_at_utc", "idempotent", "report_ref",
                "report", "outputs", "grants_manifest", "Game_MCP_OBS_calls", "timeline_writer_calls"));
        if (!BATCH_RESULT_SCHEMA.equals(text(root, "schema")) || !batchId(expectedBatchId).equals(text(root, "batch_id"))
                || !root.get("idempotent").isBoolean() || !root.get("report").isObject()) throw new IllegalArgumentException("exact offline batch result required");
        StrictJson.utc(text(root, "observed_at_utc"));
        if (!text(root, "machine_id").matches("[a-z0-9][a-z0-9-]{0,63}")) throw new IllegalArgumentException("offline result machine required");
        absolute(ExactRef.fromJson(root.get("report_ref"))); refs(root.get("outputs"), 4096); publication(root.get("grants_manifest"));
        StrictJson.integer(root.get("Game_MCP_OBS_calls"), 0, 0); StrictJson.integer(root.get("timeline_writer_calls"), 0, 0);
        JsonNode schema = root.path("report").get("schema");
        if (schema != null) StrictJson.require(schema.isTextual() && (schema.textValue().equals(OfflineBatchBinding.REPORT_V1)
                || schema.textValue().equals(OfflineBatchBinding.REPORT_V2) || schema.textValue().equals(OfflineBatchBinding.REPORT_V3)), "Unsupported source-review report version");
        if (schema != null && (schema.textValue().equals(OfflineBatchBinding.REPORT_V2) || schema.textValue().equals(OfflineBatchBinding.REPORT_V3))) {
            validateObservedReport(root.get("report"), text(root, "machine_id"));
        }
        return retained;
    }
    private static void validateObservedReport(JsonNode value, String machine) {
        var report = StrictJson.object(value, Set.of("schema", "machine_id", "observed_at_utc", "manifest", "session_id",
                "scan_observation", "scan_source", "index_ref", "entries", "already_known", "unresolved", "Game_MCP_OBS_calls", "material_effects_verified"));
        var binding = new OfflineBatchBinding.ObservedScan(text(report, "session_id"), OfflineBatchBinding.observationForReport(report),
                OfflineBatchBinding.source(report.get("scan_source")), ExactRef.fromJson(report.get("index_ref")));
        StrictJson.require(machine.equals(text(report, "machine_id")) && machine.equals(binding.observation().machineId()), "Report and actual result machines differ");
        StrictJson.utc(text(report, "observed_at_utc"));
        OfflineBatchBinding.requireReport(report, binding, ExactRef.fromJson(report.get("manifest")));
        StrictJson.integer(report.get("Game_MCP_OBS_calls"), 0, 0);
        StrictJson.require(report.get("material_effects_verified").isBoolean() && !report.get("material_effects_verified").booleanValue(), "Source research grants no material effect");
        for (String field : List.of("entries", "already_known", "unresolved")) {
            JsonNode rows = report.get(field);
            StrictJson.require(rows.isArray() && rows.size() <= 256, "Finite source-review rows required");
            java.util.Set<String> ids = new java.util.HashSet<>();
            for (JsonNode row : rows) {
                StrictJson.require(row.isObject() && row.path("incident_id").isTextual(), "Actual incident identity required");
                String id = row.path("incident_id").textValue();
                StrictJson.require(id.matches("[0-9a-f]{32}") && ids.add(id), "Distinct original incident identities required");
            }
        }
    }
    public static ObjectNode parseMetadataObject(byte[] raw) { return object(raw, null); }
    private static ObjectNode request(byte[] raw, String schema, Set<String> fields) {
        if (raw != null && raw.length > MAX_METADATA_BYTES) throw new InvalidRequest(true, "offline metadata exceeds 2097152 bytes");
        ObjectNode root = object(raw, fields);
        if (!schema.equals(text(root, "schema"))) throw new IllegalArgumentException("exact offline request schema required");
        return root;
    }
    private static ObjectNode object(byte[] raw, Set<String> fields) {
        byte[] retained = ProjectionJson.object(raw, MAX_METADATA_BYTES).bytes();
        try {
            JsonNode value = MAPPER.readTree(retained);
            if (!(value instanceof ObjectNode object)) throw new IllegalArgumentException("offline metadata object required");
            return fields == null ? object : StrictJson.object(object, fields);
        } catch (IOException failure) { throw new IllegalArgumentException("invalid offline metadata JSON", failure); }
    }
    private static List<ExactRef> refs(JsonNode value, int maximum) {
        if (value == null || !value.isArray() || value.size() > maximum) throw new IllegalArgumentException("bounded exact source reference array required");
        List<ExactRef> refs = new ArrayList<>(); value.forEach(row -> refs.add(ExactRef.fromJson(row)));
        return references(refs, maximum);
    }
    private static ObjectNode publication(Publication publication) {
        var row = publication.reference().toJson(); row.put("grants", publication.grants()); row.put("added", publication.added()); return row;
    }
    private static Publication publication(JsonNode value) {
        var row = StrictJson.object(value, Set.of("path", "bytes", "sha256", "grants", "added"));
        return new Publication(new ExactRef(text(row, "path"), StrictJson.integer(row.get("bytes"), 0, StrictJson.MAX_SAFE_INTEGER), text(row, "sha256")),
                Math.toIntExact(StrictJson.integer(row.get("grants"), 0, Integer.MAX_VALUE)),
                Math.toIntExact(StrictJson.integer(row.get("added"), 0, Integer.MAX_VALUE)));
    }
    private static byte[] encodeMetadata(ObjectNode object) {
        try { return ProjectionJson.object(MAPPER.writeValueAsBytes(object), MAX_METADATA_BYTES).bytes(); }
        catch (IOException | RuntimeException failure) { throw new IllegalStateException("invalid offline metadata output", failure); }
    }
    private static String text(ObjectNode object, String field) { return StrictJson.text(object.get(field)); }
    private static InvalidRequest invalid(IllegalArgumentException failure) {
        return new InvalidRequest(false, "invalid exact offline request");
    }
}
