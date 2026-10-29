package org.xar.ck3.control.wave3.runtime.timelineowner;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit source-only receipts; parsing a golden never reopens a historical source view. */
final class TimelineOwnerSourceView {
    static final String REFERENCE_SCHEMA = "xar.sdk-reference-actual/v1";
    static final String REFERENCE_STATUS = "REFERENCE_INPUTS_ASSEMBLED_NOT_IMPORTED";
    private static final int MAX_ACTUAL = 2_097_152;
    private static final Set<String> COMMON = Set.of("schema", "scope", "selected_view",
            "interpreter_prefixes", "external_dependency_qualification", "initial_repo_sources",
            "after_imports_repo_sources", "after_suite_repo_sources", "recorded_repo_sources",
            "source_pre_post_equal", "unrecorded_repo_sources");

    sealed interface Proof permits LegacyProof, ReferenceProof, OracleReferenceProof { FileRef actualRef(); }
    record LegacyProof(FileRef actualRef) implements Proof { }
    record ReferenceProof(FileRef actualRef) implements Proof { }
    record OracleReferenceProof(FileRef actualRef) implements Proof { }

    private TimelineOwnerSourceView() { }

    /** The SDK reader owns complete source, machine, frozen input, route and purpose guards. */
    static Proof readLive(FileRef reference, Path expectedRoot) throws IOException {
        StrictJson.require(reference.bytes() > 0 && reference.bytes() <= MAX_ACTUAL, "bounded actual receipt required");
        reference.verify();
        JsonNode envelope;
        try (InputStream input = Files.newInputStream(Path.of(reference.path()))) {
            byte[] raw = input.readNBytes(MAX_ACTUAL + 1);
            StrictJson.require(raw.length == reference.bytes(), "actual receipt length changed");
            envelope = ControlBuild.strictMapper().readTree(raw);
        }
        String schema = StrictJson.text(envelope.get("schema"));
        Proof result;
        Path root;
        if (REFERENCE_SCHEMA.equals(schema)) {
            SdkSourceAssembly.ReferenceActual actual = SdkSourceAssembly.readReferenceActual(reference);
            root = Path.of(actual.graphRoot()).toRealPath();
            if (actual.purpose() == SdkSourceAssembly.ReferencePurpose.REFERENCE_ORACLE_ONLY) {
                FileRef reviewRef = actual.reviewRef(); reviewRef.verify();
                StrictJson.require(reviewRef.bytes() > 0 && reviewRef.bytes() <= MAX_ACTUAL, "Bounded reference review required");
                SdkSourceAssembly.ReferenceReview review;
                try (InputStream input = Files.newInputStream(Path.of(reviewRef.path()))) {
                    byte[] raw = input.readNBytes(MAX_ACTUAL + 1);
                    StrictJson.require(raw.length == reviewRef.bytes(), "Reference review length changed");
                    review = ControlBuild.strictMapper().readValue(raw, SdkSourceAssembly.ReferenceReview.class);
                }
                var parent = review.parentSourceReview();
                StrictJson.require(parent.completeSdkInputInventory().originalFiles() == 1468
                        && parent.sourceClosure().stream().filter(row -> row.role() == SdkSourceAssembly.SourceRole.SDK_SOURCE)
                        .allMatch(row -> row.origin() == SdkSourceAssembly.InputOrigin.FROZEN_SDK_SOURCE && row.overlays().isEmpty())
                        && review.request().selections().stream().noneMatch(row ->
                            row.relativePath().equals(parent.request().sdkRelativeRoot() + "/xar_autoplayer/bridge/native_driver.py")),
                        "Oracle timeline capture retains the unchanged complete frozen SDK and native driver");
                reviewRef.verify();
            }
            result = switch (actual.purpose()) {
                case LEGACY_REFERENCE_ONLY -> new ReferenceProof(reference);
                case REFERENCE_ORACLE_ONLY -> new OracleReferenceProof(reference);
            };
        } else {
            StrictJson.require(SdkSourceAssembly.ASSEMBLY_SCHEMA.equals(schema), "explicit source receipt schema required");
            SdkSourceAssembly.Actual actual = SdkSourceAssembly.readActual(reference);
            root = Path.of(actual.graphRoot()).toRealPath();
            result = new LegacyProof(reference);
        }
        StrictJson.require(root.equals(expectedRoot.toRealPath()), "selected physical root differs");
        reference.verify();
        return result;
    }

    static Proof readProvenance(JsonNode golden) {
        JsonNode provenance = golden.get("source_provenance");
        String schema = StrictJson.text(provenance == null ? null : provenance.get("schema"));
        Set<String> fields = new HashSet<>(COMMON);
        Proof result;
        if ("xar.ck3.measured-repo-import-closure/v1".equals(schema)) {
            fields.add("assembly_actual_ref");
            StrictJson.object(provenance, fields);
            equal(provenance, "selected_view", "legacy");
            result = new LegacyProof(fileRef(provenance.get("assembly_actual_ref"), "ACTUAL.json"));
        } else {
            boolean oracle = "xar.ck3.measured-repo-import-closure/v3".equals(schema);
            StrictJson.require(oracle || "xar.ck3.measured-repo-import-closure/v2".equals(schema), "explicit provenance version required");
            fields.addAll(Set.of("reference_actual_ref", "reference_actual_schema", "reference_purpose",
                    "reference_status", "reference_actual_imports_observed", "reference_runtime_qualified", "reference_prepared"));
            StrictJson.object(provenance, fields);
            equal(provenance, "selected_view", oracle ? "oracle_reference" : "legacy_reference");
            equal(provenance, "reference_actual_schema", REFERENCE_SCHEMA);
            equal(provenance, "reference_purpose", (oracle ? SdkSourceAssembly.ReferencePurpose.REFERENCE_ORACLE_ONLY
                    : SdkSourceAssembly.ReferencePurpose.LEGACY_REFERENCE_ONLY).name());
            equal(provenance, "reference_status", REFERENCE_STATUS);
            for (String key : Set.of("reference_actual_imports_observed", "reference_runtime_qualified", "reference_prepared")) {
                JsonNode value = provenance.get(key);
                StrictJson.require(value != null && value.isBoolean() && !value.booleanValue(), "reference grants no import, runtime or Prepared qualification");
            }
            FileRef reference = fileRef(provenance.get("reference_actual_ref"), "REFERENCE-ACTUAL.json");
            result = oracle ? new OracleReferenceProof(reference) : new ReferenceProof(reference);
        }
        equal(provenance, "scope", "repo-python-excluding-interpreter-prefixes/v1");
        equal(provenance, "external_dependency_qualification", "not_granted_by_repo_source_observer");
        StrictJson.integer(provenance.get("initial_repo_sources"), 0, 0);
        long recorded = StrictJson.integer(provenance.get("recorded_repo_sources"), 1, 4096);
        for (String field : Set.of("after_imports_repo_sources", "after_suite_repo_sources")) {
            StrictJson.integer(provenance.get(field), 1, recorded);
        }
        StrictJson.trueValue(provenance.get("source_pre_post_equal"));
        JsonNode missing = provenance.get("unrecorded_repo_sources");
        StrictJson.require(missing != null && missing.isArray() && missing.isEmpty(), "complete observed source inventory required");
        JsonNode prefixes = provenance.get("interpreter_prefixes");
        StrictJson.require(prefixes != null && prefixes.isArray() && !prefixes.isEmpty(), "explicit interpreter prefixes required");
        for (JsonNode prefix : prefixes) { StrictJson.text(prefix); }
        return result;
    }

    static void requireSameProof(Proof expected, Proof observed) {
        StrictJson.require(expected.equals(observed), "capture changed the selected source provenance");
    }

    private static FileRef fileRef(JsonNode node, String filename) {
        StrictJson.object(node, Set.of("path", "bytes", "sha256"));
        String path = StrictJson.text(node.get("path"));
        StrictJson.require(Path.of(path).getFileName().toString().equals(filename), "explicit actual receipt filename required");
        return new FileRef(path, StrictJson.integer(node.get("bytes"), 1, MAX_ACTUAL), StrictJson.text(node.get("sha256")));
    }

    private static void equal(JsonNode node, String field, String expected) {
        StrictJson.require(expected.equals(StrictJson.text(node.get(field))), "source provenance " + field + " differs");
    }
}
