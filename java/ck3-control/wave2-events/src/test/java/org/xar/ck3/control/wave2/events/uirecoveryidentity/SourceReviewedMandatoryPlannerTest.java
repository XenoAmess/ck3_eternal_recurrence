package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

final class SourceReviewedMandatoryPlannerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    @TempDir Path temporary;

    private static ObjectNode golden() throws IOException {
        try (InputStream resource = SourceReviewedMandatoryPlannerTest.class.getResourceAsStream("/uirecoveryidentity/observed-ui-recovery-producer-golden-v1.json.gz")) {
            if (resource == null) throw new IOException("mandatory actual observed-UI worker/lookup/planner fixture missing; NOT RUN");
            byte[] packed = resource.readNBytes(65_537); assertTrue(packed.length <= 65_536);
            try (InputStream stream = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                byte[] raw = stream.readNBytes(1_048_577); assertTrue(raw.length <= 1_048_576); RetainedJson.parse(raw);
                ObjectNode result = (ObjectNode) JSON.readTree(raw);
                assertEquals("xar.observed-ui-recovery-producer-golden/v1", result.path("schema").textValue());
                assertEquals(2, result.path("cases").size()); return result;
            }
        }
    }

    @TestFactory Stream<DynamicTest> actualOriginalKnowledgeAcrossGameInstances() throws IOException {
        ObjectNode root = golden(); List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode row : root.path("cases")) {
            tests.add(DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
                Path base = temporary.resolve(row.path("name").textValue()); Files.createDirectories(base);
                Map<String, Path> relocated = new HashMap<>(); List<ProjectionEvidenceGrant> grants = new ArrayList<>();
                for (JsonNode file : row.path("files")) {
                    Path relative = Path.of(file.path("relative").textValue());
                    assertFalse(relative.isAbsolute()); assertFalse(relative.startsWith("..")); assertEquals(relative, relative.normalize());
                    Path destination = base.resolve(relative); assertTrue(destination.startsWith(base));
                    byte[] raw = Base64.getDecoder().decode(root.path("blobs").path(file.path("sha256").textValue()).textValue());
                    assertEquals(file.path("bytes").longValue(), raw.length);
                    assertEquals(file.path("sha256").textValue(), sha(raw));
                    Files.createDirectories(destination.getParent()); Files.write(destination, raw, StandardOpenOption.CREATE_NEW);
                    relocated.put(file.path("path").textValue(), destination);
                    if (file.path("role").textValue().startsWith("UI_RECOVERY_")) {
                        grants.add(new ProjectionEvidenceGrant(destination, raw.length, sha(raw), file.path("origin_machine_id").textValue(),
                                ProjectionEvidenceRole.valueOf(file.path("role").textValue())));
                    }
                }
                Path reviewPath = relocated.get(row.path("review_path").textValue()); assertNotNull(reviewPath);
                ObjectNode review = (ObjectNode) JSON.readTree(Files.readAllBytes(reviewPath));
                for (String field : List.of("before_path", "after_path", "later_source_path")) {
                    Path path = relocated.get(review.path(field).textValue()); assertNotNull(path); review.put(field, path.toString());
                }
                // Only declared paths change. All original evidence raw bytes and their SHA stay exact.
                Files.write(reviewPath, JSON.writeValueAsBytes(review));
                ObjectNode expected = ((ObjectNode) row.path("expected")).deepCopy();
                ((ObjectNode) expected.path("known_ui_recovery_source")).put("review_path", reviewPath.toString());
                ((ObjectNode) expected.path("unknown_mandatory_choice_v1").path("known_ui_recovery_source")).put("review_path", reviewPath.toString());
                Path state = base.resolve(row.path("state_relative").textValue()); Path stock = base.resolve("stock");
                Files.createDirectories(state); Files.createDirectories(stock);
                String machine = root.path("machine_id").textValue();
                EventSourceReadContext context = new EventSourceReadContext(machine, state, stock, grants);
                SourceReviewedMandatoryPlanner.Input input = SourceReviewedMandatoryPlanner.decode(JSON.writeValueAsBytes(row.path("request")));
                byte[] actual = SourceReviewedMandatoryPlanner.encode(new SourceReviewedMandatoryPlanner(context).plan(input));
                assertEquals(RetainedJson.parse(JSON.writeValueAsBytes(expected)), RetainedJson.parse(actual));
                assertEquals("fresh-instance-token", JSON.readTree(actual).path("unknown_mandatory_choice_v1").path("selection").path("action_token").textValue());

                List<ProjectionEvidenceGrant> missing = grants.stream().filter(grant -> grant.role() != ProjectionEvidenceRole.UI_RECOVERY_BEFORE).toList();
                EventSourceReadContext noBefore = new EventSourceReadContext(machine, state, stock, missing);
                assertThrows(TrustedEventSourceContext.UnavailableException.class, () -> new SourceReviewedMandatoryPlanner(noBefore).plan(input));
                Path oldBefore = grants.stream().filter(grant -> grant.role() == ProjectionEvidenceRole.UI_RECOVERY_BEFORE).findFirst().orElseThrow().path();
                Files.writeString(oldBefore, " ", StandardOpenOption.APPEND);
                assertThrows(TrustedEventSourceContext.UnavailableException.class, () -> new SourceReviewedMandatoryPlanner(context).plan(input));
            }));
        }
        return tests.stream();
    }

    private static String sha(byte[] raw) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
}
