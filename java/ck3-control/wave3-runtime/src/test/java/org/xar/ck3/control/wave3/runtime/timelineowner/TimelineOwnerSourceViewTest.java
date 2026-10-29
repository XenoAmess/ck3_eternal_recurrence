package org.xar.ck3.control.wave3.runtime.timelineowner;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Synthetic metadata exercises parsing only; it grants no live source or producer qualification. */
final class TimelineOwnerSourceViewTest {
    @Test
    void explicitReferenceMetadataSurvivesCanonicalJsonRoundTrip() {
        ObjectNode golden = fixture(true);
        TimelineOwnerSourceView.Proof proof = TimelineOwnerSourceView.readProvenance(golden);
        assertInstanceOf(TimelineOwnerSourceView.ReferenceProof.class, proof);
        assertEquals(proof, TimelineOwnerSourceView.readProvenance(StrictJson.parse(StrictJson.canonical(golden))));
    }

    @Test
    void oracleReferenceHasItsOwnExplicitVersionAndProof() {
        ObjectNode golden = oracleFixture();
        TimelineOwnerSourceView.Proof proof = TimelineOwnerSourceView.readProvenance(golden);
        assertInstanceOf(TimelineOwnerSourceView.OracleReferenceProof.class, proof);
        assertEquals(proof, TimelineOwnerSourceView.readProvenance(StrictJson.parse(StrictJson.canonical(golden))));
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.requireSameProof(
                proof, TimelineOwnerSourceView.readProvenance(fixture(true))));
    }

    @Test
    void oracleVersionCannotBorrowLegacyPurposeOrView() {
        ObjectNode wrongPurpose = oracleFixture(); provenance(wrongPurpose).put("reference_purpose", "LEGACY_REFERENCE_ONLY");
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(wrongPurpose));
        ObjectNode wrongView = oracleFixture(); provenance(wrongView).put("selected_view", "legacy_reference");
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(wrongView));
    }

    @Test
    void existingLegacyMetadataRetainsItsOwnBranch() {
        ObjectNode golden = fixture(false);
        TimelineOwnerSourceView.Proof proof = TimelineOwnerSourceView.readProvenance(golden);
        assertInstanceOf(TimelineOwnerSourceView.LegacyProof.class, proof);
        assertEquals(proof, TimelineOwnerSourceView.readProvenance(StrictJson.parse(StrictJson.canonical(golden))));
    }

    @Test
    void oracleOnlyPurposeCannotBecomeTimelineLegacyReference() {
        rejects("reference_purpose", "REFERENCE_ORACLE_ONLY");
    }

    @Test
    void receiptAndProvenanceSchemasCannotBeRelabelled() {
        rejects("reference_actual_schema", "xar.sdk-source-assembly-actual/v1");
        rejects("schema", "xar.ck3.measured-repo-import-closure/v4");
        rejects("selected_view", "legacy");
    }

    @Test
    void referenceStatusCannotClaimOrdinaryAssembly() {
        rejects("reference_status", "SOURCE_ASSEMBLED_NOT_IMPORTED");
    }

    @Test
    void referenceCannotGrantImportsRuntimeOrPrepared() {
        for (String field : List.of("reference_actual_imports_observed", "reference_runtime_qualified", "reference_prepared")) {
            ObjectNode golden = fixture(true); provenance(golden).put(field, true);
            assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
            provenance(golden).put(field, 0);
            assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
        }
    }

    @Test
    void branchesRejectTheOtherReceiptFieldAndUnknownFields() {
        for (boolean reference : List.of(true, false)) {
            ObjectNode golden = fixture(reference);
            provenance(golden).set(reference ? "assembly_actual_ref" : "reference_actual_ref", receipt(golden, reference).deepCopy());
            assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
        }
    }

    @Test
    void requiredFieldsRejectBothMissingAndNull() {
        for (String field : List.of("reference_purpose", "reference_actual_ref", "reference_actual_schema", "initial_repo_sources", "interpreter_prefixes", "source_pre_post_equal", "recorded_repo_sources")) {
            ObjectNode golden = fixture(true); provenance(golden).remove(field);
            assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
            provenance(golden).putNull(field);
            assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
        }
    }

    @Test
    void receiptSizeRejectsEqualBooleanFloatAndStringRepresentations() {
        for (String value : List.of("true", "1.0", "\"1\"")) {
            ObjectNode golden = fixture(true);
            receipt(golden, true).set("bytes", StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
        }
    }

    @Test
    void receiptSizeIsPositiveAndBoundedAndFieldsAreExact() {
        for (long value : List.of(0L, -1L, 2_097_153L)) {
            ObjectNode golden = fixture(true); receipt(golden, true).put("bytes", value);
            assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
        }
        ObjectNode golden = fixture(true); receipt(golden, true).put("extra", 1);
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
    }

    @Test
    void receiptRequiresItsExplicitFilenameAbsolutePathAndHash() {
        ObjectNode golden = fixture(true);
        receipt(golden, true).put("path", Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().resolve("ACTUAL.json").toString());
        ObjectNode wrongFilename = golden;
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(wrongFilename));
        golden = fixture(true); receipt(golden, true).put("path", "REFERENCE-ACTUAL.json");
        ObjectNode relative = golden;
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(relative));
        golden = fixture(true); receipt(golden, true).put("sha256", "A".repeat(64));
        ObjectNode wrongHash = golden;
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(wrongHash));
    }

    @Test
    void duplicateJsonAndChangedSourceProofAreRejected() {
        String raw = new String(StrictJson.canonical(fixture(true)), StandardCharsets.UTF_8);
        String duplicate = raw.replace("\"reference_purpose\":", "\"reference_purpose\":\"LEGACY_REFERENCE_ONLY\",\"reference_purpose\":");
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(duplicate.getBytes(StandardCharsets.UTF_8)));
        TimelineOwnerSourceView.Proof reference = TimelineOwnerSourceView.readProvenance(fixture(true));
        TimelineOwnerSourceView.Proof legacy = TimelineOwnerSourceView.readProvenance(fixture(false));
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.requireSameProof(reference, legacy));
        ObjectNode changed = fixture(true); receipt(changed, true).put("sha256", "b".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.requireSameProof(reference, TimelineOwnerSourceView.readProvenance(changed)));
    }

    private static void rejects(String field, String value) {
        ObjectNode golden = fixture(true); provenance(golden).put(field, value);
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerSourceView.readProvenance(golden));
    }

    private static ObjectNode provenance(ObjectNode golden) {
        return (ObjectNode) golden.get("source_provenance");
    }

    private static ObjectNode receipt(ObjectNode golden, boolean reference) {
        return (ObjectNode) provenance(golden).get(reference ? "reference_actual_ref" : "assembly_actual_ref");
    }

    private static ObjectNode oracleFixture() {
        ObjectNode golden = fixture(true); ObjectNode p = provenance(golden);
        p.put("schema", "xar.ck3.measured-repo-import-closure/v3");
        p.put("selected_view", "oracle_reference"); p.put("reference_purpose", "REFERENCE_ORACLE_ONLY");
        return golden;
    }

    private static ObjectNode fixture(boolean reference) {
        ObjectNode golden = StrictJson.object(); ObjectNode p = golden.putObject("source_provenance");
        p.put("schema", "xar.ck3.measured-repo-import-closure/" + (reference ? "v2" : "v1"));
        p.put("selected_view", reference ? "legacy_reference" : "legacy");
        p.put("scope", "repo-python-excluding-interpreter-prefixes/v1");
        p.put("external_dependency_qualification", "not_granted_by_repo_source_observer");
        p.putArray("interpreter_prefixes").add("/synthetic-interpreter");
        p.put("initial_repo_sources", 0); p.put("after_imports_repo_sources", 1);
        p.put("after_suite_repo_sources", 1); p.put("recorded_repo_sources", 1);
        p.put("source_pre_post_equal", true); p.putArray("unrecorded_repo_sources");
        ObjectNode ref = p.putObject(reference ? "reference_actual_ref" : "assembly_actual_ref");
        ref.put("path", Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().resolve(".assembly")
                .resolve(reference ? "REFERENCE-ACTUAL.json" : "ACTUAL.json").toString());
        ref.put("bytes", 1); ref.put("sha256", "a".repeat(64));
        if (reference) {
            p.put("reference_actual_schema", TimelineOwnerSourceView.REFERENCE_SCHEMA);
            p.put("reference_purpose", "LEGACY_REFERENCE_ONLY");
            p.put("reference_status", TimelineOwnerSourceView.REFERENCE_STATUS);
            p.put("reference_actual_imports_observed", false);
            p.put("reference_runtime_qualified", false); p.put("reference_prepared", false);
        }
        return golden;
    }
}
