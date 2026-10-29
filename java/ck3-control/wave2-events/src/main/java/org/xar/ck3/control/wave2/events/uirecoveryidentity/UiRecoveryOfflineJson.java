package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryEvidenceLookup.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;

/** Strict typed byte boundary for the two existing UI-analysis/lookup operations. */
public final class UiRecoveryOfflineJson {
    public static final String ANALYSIS_SCHEMA = "xar.ui-recovery-analysis-input/v1";
    public static final String LOOKUP_SCHEMA = "xar.ui-recovery-known-lookup-input/v1";
    public static final int ANALYSIS_MAX_BYTES = FILE_LIMIT;
    public static final int LOOKUP_MAX_BYTES = WIRE_LIMIT;
    private UiRecoveryOfflineJson() { }
    public record AnalysisRequest(EvidenceDocument before, EvidenceDocument after, String backendSha256, EvidenceDocument laterProgress) { }
    public sealed interface LookupRequest permits Lookup, Backend { }
    public record Lookup(EvidenceDocument window, String backendSha256) implements LookupRequest { }
    public record Backend(EvidenceDocument snapshot) implements LookupRequest { }

    public static AnalysisRequest decodeAnalysis(byte[] raw) {
        ObjectNode row = object(parse(raw, ANALYSIS_MAX_BYTES)); exact(row, Set.of("schema", "before", "after", "backend_sha256", "later_progress"));
        require(ANALYSIS_SCHEMA.equals(text(row.get("schema"))), "UI analysis schema required");
        return new AnalysisRequest(document(row.get("before"), FILE_LIMIT), document(row.get("after"), FILE_LIMIT),
                optionalBackend(row.get("backend_sha256")), document(row.get("later_progress"), FILE_LIMIT));
    }
    public static LookupRequest decodeLookup(byte[] raw) {
        ObjectNode row = object(parse(raw, LOOKUP_MAX_BYTES)); require(LOOKUP_SCHEMA.equals(text(row.get("schema"))), "UI lookup schema required");
        if ("lookup".equals(text(row.get("operation")))) {
            exact(row, Set.of("schema", "operation", "window", "backend_sha256"));
            return new Lookup(document(row.get("window"), WIRE_LIMIT), optionalBackend(row.get("backend_sha256")));
        }
        require("backend".equals(text(row.get("operation"))), "closed UI lookup operation required");
        exact(row, Set.of("schema", "operation", "snapshot")); return new Backend(document(row.get("snapshot"), WIRE_LIMIT));
    }
    public static EvidenceDocument analyze(AnalysisRequest input, EventSourceReadContext configured) {
        Objects.requireNonNull(input); return new UiRecoveryEvidenceLookup(configured).analyze(value(input.before()), value(input.after()), input.backendSha256(), value(input.laterProgress()));
    }
    public static EvidenceDocument lookup(LookupRequest input, EventSourceReadContext configured) {
        UiRecoveryEvidenceLookup lookup = new UiRecoveryEvidenceLookup(configured);
        if (input instanceof Backend backend) {
            String sha = lookup.boundBackend(value(backend.snapshot()));
            return document(sha == null ? NullNode.instance : JsonNodeFactory.instance.textNode(sha), WIRE_LIMIT);
        }
        Lookup query = (Lookup) input;
        if (query.backendSha256() == null) return document(NullNode.instance, WIRE_LIMIT);
        return lookup.lookup(value(query.window()), null, query.backendSha256()).orElseGet(() -> document(NullNode.instance, WIRE_LIMIT));
    }
    public static byte[] encode(EvidenceDocument document) { byte[] raw = document.json().getBytes(StandardCharsets.UTF_8); parse(raw, FILE_LIMIT); return raw; }
    private static JsonNode value(EvidenceDocument document) { return parse(document.json().getBytes(StandardCharsets.UTF_8), FILE_LIMIT); }
    private static String optionalBackend(JsonNode node) { require(node != null && (node.isNull() || node.isTextual()), "UI expected backend is nullable text"); return node.isNull() ? null : node.textValue(); }
    private static void exact(ObjectNode node, Set<String> expected) { java.util.Set<String> actual = new java.util.HashSet<>(); node.fieldNames().forEachRemaining(actual::add); require(actual.equals(expected), "exact UI recovery request fields required"); }
}
