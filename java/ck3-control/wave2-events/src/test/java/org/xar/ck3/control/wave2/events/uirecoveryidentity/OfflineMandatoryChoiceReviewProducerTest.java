package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryEvidenceLookup.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

final class OfflineMandatoryChoiceReviewProducerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    @TempDir Path temporary;
    private static ObjectNode golden() throws IOException {
        try (InputStream resource = OfflineMandatoryChoiceReviewProducerTest.class.getResourceAsStream("/uirecoveryidentity/observed-ui-recovery-producer-golden-v1.json.gz")) {
            if (resource == null) throw new IOException("mandatory actual original worker/lookup/planner corpus missing; NOT RUN");
            byte[] packed = resource.readNBytes(65_537); assertTrue(packed.length <= 65_536);
            try (InputStream input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                byte[] raw = input.readNBytes(1_048_577); assertTrue(raw.length <= 1_048_576); RetainedJson.parse(raw);
                ObjectNode root = (ObjectNode) JSON.readTree(raw);
                assertEquals("xar.observed-ui-recovery-producer-golden/v1", root.path("schema").textValue());
                assertEquals(2, root.path("cases").size()); return root;
            }
        }
    }

    @TestFactory Stream<DynamicTest> originalWorkerToJavaProducerToSharedLookupAndLivePlanner() throws IOException {
        ObjectNode root = golden(); List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode row : root.path("cases")) tests.add(DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
            Path base = temporary.resolve(row.path("name").textValue()); Files.createDirectories(base);
            Map<String, Path> relocated = new HashMap<>(); Map<String, byte[]> originals = new HashMap<>();
            List<ProjectionEvidenceGrant> grants = new ArrayList<>();
            for (JsonNode file : row.path("files")) {
                String original = file.path("path").textValue(); Path relative = Path.of(file.path("relative").textValue());
                assertFalse(relative.isAbsolute()); assertFalse(relative.startsWith("..")); assertEquals(relative, relative.normalize());
                Path target = base.resolve(relative); assertTrue(target.startsWith(base));
                byte[] bytes = Base64.getDecoder().decode(root.path("blobs").path(file.path("sha256").textValue()).textValue());
                assertEquals(file.path("bytes").longValue(), bytes.length); assertEquals(file.path("sha256").textValue(), sha(bytes));
                originals.put(original, bytes); relocated.put(original, target);
                String role = file.path("role").textValue();
                if (role.startsWith("UI_RECOVERY_")) {
                    Files.createDirectories(target.getParent()); Files.write(target, bytes, StandardOpenOption.CREATE_NEW);
                    grants.add(new ProjectionEvidenceGrant(target, bytes.length, sha(bytes), file.path("origin_machine_id").textValue(), ProjectionEvidenceRole.valueOf(role)));
                }
            }
            // Both real worker publications must be captured. A manually supplied known file cannot substitute.
            assertNotEquals(row.path("review_path").textValue(), row.path("worker_review_path").textValue());
            assertTrue(row.path("review_path").textValue().contains("known-ui-recovery"));
            byte[] originalReview = originals.get(row.path("review_path").textValue()); assertNotNull(originalReview);
            assertNotNull(originals.get(row.path("worker_review_path").textValue()));
            ObjectNode expectedReview = (ObjectNode) JSON.readTree(originalReview);
            for (String field : List.of("before_path", "after_path", "later_source_path")) {
                Path actual = relocated.get(expectedReview.path(field).textValue()); assertNotNull(actual); expectedReview.put(field, actual.toString());
            }
            Path beforePath = Path.of(expectedReview.path("before_path").textValue());
            Path historical = beforePath.getParent().getParent().getParent().getParent();
            Path state = base.resolve(row.path("state_relative").textValue()); Path stock = base.resolve("stock");
            Files.createDirectories(state); Files.createDirectories(stock);
            String machine = root.path("machine_id").textValue();
            EventSourceReadContext context = new EventSourceReadContext(machine, state, stock, grants);
            ObjectNode before = (ObjectNode) JSON.readTree(Files.readAllBytes(beforePath));
            assertTrue(new UiRecoveryEvidenceLookup(new EventSourceReadContext(machine, state, stock)).lookup(before.get("native_window"), null, null).isEmpty(), "first modal must not require a nonexistent knowledge grant");
            Path output = state.resolve("evidence/unknown-mandatory-choice-reviews");
            var configuration = new OfflineMandatoryChoiceReviewProducer.Configuration(context, output, state.resolve("offline-evidence-grants.json"), historical);
            var result = OfflineMandatoryChoiceReviewProducer.reviewOnce(configuration); assertEquals(1, result.reviews().size());
            var summary = result.reviews().getFirst(); assertEquals("known_ui_recovery_observed", summary.status());
            byte[] actualRaw = Files.readAllBytes(summary.review());
            assertEquals(summary.bytes(), actualRaw.length); assertEquals(summary.sha256(), sha(actualRaw));
            assertEquals(RetainedJson.parse(JSON.writeValueAsBytes(expectedReview)), RetainedJson.parse(actualRaw));
            Path known = output.resolve("known-ui-recovery").resolve(expectedReview.path("source_key").textValue()).resolve("incident-1.json");
            assertArrayEquals(actualRaw, Files.readAllBytes(known));
            ObjectNode expectedPlan = ((ObjectNode) row.path("expected")).deepCopy();
            ((ObjectNode) expectedPlan.path("known_ui_recovery_source")).put("review_path", known.toString());
            ((ObjectNode) expectedPlan.path("unknown_mandatory_choice_v1").path("known_ui_recovery_source")).put("review_path", known.toString());
            byte[] actualPlan = SourceReviewedMandatoryPlanner.encode(new SourceReviewedMandatoryPlanner(context).plan(SourceReviewedMandatoryPlanner.decode(JSON.writeValueAsBytes(row.path("request")))));
            assertEquals(RetainedJson.parse(JSON.writeValueAsBytes(expectedPlan)), RetainedJson.parse(actualPlan));
            assertEquals("fresh-instance-token", JSON.readTree(actualPlan).path("unknown_mandatory_choice_v1").path("selection").path("action_token").textValue());

            Path laterPath = Path.of(expectedReview.path("later_source_path").textValue());
            ObjectNode newer = ((ObjectNode) JSON.readTree(Files.readAllBytes(laterPath))).deepCopy(); newer.put("ended_at_utc", "2026-10-15T09:00:02+00:00");
            ObjectNode frame = (ObjectNode) newer.path("result").path("structured_content"); frame.put("date_raw", frame.path("date_raw").longValue() + 1); frame.put("native_revision", frame.path("native_revision").longValue() + 1);
            Files.write(laterPath.resolveSibling("0003-1-result.json"), JSON.writeValueAsBytes(newer), StandardOpenOption.CREATE_NEW);
            var repeated = OfflineMandatoryChoiceReviewProducer.reviewOnce(configuration);
            assertEquals(summary, repeated.reviews().getFirst()); assertEquals(0, repeated.grants().added());
            assertArrayEquals(actualRaw, Files.readAllBytes(known));
            Files.writeString(laterPath, " ", StandardOpenOption.APPEND);
            assertThrows(RuntimeException.class, () -> OfflineMandatoryChoiceReviewProducer.reviewOnce(configuration));
            assertArrayEquals(actualRaw, Files.readAllBytes(known), "drift cannot overwrite established immutable knowledge");
        }));
        return tests.stream();
    }

    @Test void typedCodecRejectsUnknownFieldsAndRootPaths() {
        assertThrows(IllegalArgumentException.class, () -> UiRecoveryOfflineJson.decodeAnalysis("{\"schema\":\"xar.ui-recovery-analysis-input/v1\",\"before\":{},\"after\":{},\"backend_sha256\":null,\"later_progress\":null,\"known\":true}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> UiRecoveryOfflineJson.decodeLookup("{\"schema\":\"xar.ui-recovery-known-lookup-input/v1\",\"operation\":\"lookup\",\"window\":{},\"backend_sha256\":null,\"review_root\":\"injected\"}".getBytes(StandardCharsets.UTF_8)));
    }
}
