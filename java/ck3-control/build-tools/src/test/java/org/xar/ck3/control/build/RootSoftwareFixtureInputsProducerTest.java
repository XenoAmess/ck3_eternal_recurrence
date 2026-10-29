package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class RootSoftwareFixtureInputsProducerTest {
    @TempDir Path root;
    private static final String PAYLOAD = "{ \"text\" : \"雪 } \\\" {\", \"nested\" : [ {\"n\":9007199254740993}, null ], \"decimal\" : 1.2300 }";

    @Test void actualGoldenReaderToExistingHostRequestPreservesExactTokenAndAllOriginalRoles() throws Exception {
        FileRef golden = goldenPlanFixture(root.resolve("golden"));
        var plan = FreshSdkFixtureStage.readProducerGoldenPlan(golden);
        var produced = RootSoftwareFixtureInputsProducer.produce(golden, root.resolve("published"));
        var request = readRequest(produced.requestRef());
        assertEquals(8, request.originalRequestRefs().size());
        assertEquals(21, request.originalFixtureRefs().size());
        assertTrue(request.originalFixtureRefs().containsAll(FreshSdkFixtureStage.producerGoldenInputs(plan)));
        assertTrue(request.originalFixtureRefs().containsAll(List.of(golden, plan.originalInstallMapRef())));
        assertEquals(plan.vectors().getFirst().request(), request.probeRequestRef());
        assertEquals(produced.probePayloadRef(), request.probePayloadRef());
        assertArrayEquals(PAYLOAD.getBytes(StandardCharsets.UTF_8), Files.readAllBytes(Path.of(produced.probePayloadRef().path())));
        produced.requestRef().verify(); produced.probePayloadRef().verify();
    }

    @Test void actualHostSourcePlanToExistingRequestUsesEightExplicitMainTargets() throws Exception {
        FileRef plan = hostFixturePlanFixture(root.resolve("host"));
        var produced = RootSoftwareFixtureInputsProducer.produceFromHostFixturePlan(plan, root.resolve("published"));
        var request = readRequest(produced.requestRef());
        assertEquals(8, request.originalRequestRefs().size());
        assertEquals(17, request.originalFixtureRefs().size());
        assertTrue(request.originalFixtureRefs().contains(plan));
        assertTrue(request.originalFixtureRefs().containsAll(request.originalRequestRefs()));
        for (int index = 0; index < 8; index++)
            assertEquals("M" + index + ".request.json", Path.of(request.originalRequestRefs().get(index).path()).getFileName().toString());
        assertArrayEquals(PAYLOAD.getBytes(StandardCharsets.UTF_8), Files.readAllBytes(Path.of(produced.probePayloadRef().path())));
        try (var files = Files.list(root.resolve("published"))) { assertEquals(2, files.count()); }
    }

    @Test void originalRequestRefMutationFailsBeforeAnyOutputExists() throws Exception {
        FileRef golden = goldenPlanFixture(root.resolve("golden"));
        var plan = FreshSdkFixtureStage.readProducerGoldenPlan(golden);
        Files.writeString(Path.of(plan.vectors().getLast().request().path()), "changed original");
        assertThrows(IOException.class, () -> RootSoftwareFixtureInputsProducer.produce(golden, root.resolve("published")));
        assertFalse(Files.exists(root.resolve("published")));
    }

    @Test void crossedMissingAndDuplicateHostTargetsFailThroughActualProducer() throws Exception {
        for (String kind : List.of("crossed", "missing", "duplicate")) {
            Path group = root.resolve(kind); FileRef original = hostFixturePlanFixture(group);
            ObjectNode plan = (ObjectNode) ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(original.path())));
            var rows = (com.fasterxml.jackson.databind.node.ArrayNode) plan.get("ready_rows");
            if (kind.equals("crossed")) ((ObjectNode) rows.get(0)).put("milestone", "M7");
            else if (kind.equals("missing")) rows.remove(0);
            else rows.add(rows.get(0).deepCopy());
            Files.write(Path.of(original.path()), ControlBuild.strictMapper().writeValueAsBytes(plan));
            FileRef changed = FileRef.measure(Path.of(original.path())); Path output = group.resolve("published");
            assertThrows(IOException.class, () -> RootSoftwareFixtureInputsProducer.produceFromHostFixturePlan(changed, output));
            assertFalse(Files.exists(output));
        }
    }

    @Test void wrongMachineAndUnknownSourcePlanFieldsAreNotAccepted() throws Exception {
        for (String kind : List.of("machine", "unknown")) {
            Path group = root.resolve(kind); FileRef original = hostFixturePlanFixture(group);
            ObjectNode plan = (ObjectNode) ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(original.path())));
            if (kind.equals("machine")) plan.put("machine_id", "another-machine");
            else plan.put("unknown_source_field", true);
            Files.write(Path.of(original.path()), ControlBuild.strictMapper().writeValueAsBytes(plan));
            FileRef changed = FileRef.measure(Path.of(original.path()));
            assertThrows(IOException.class, () -> RootSoftwareFixtureInputsProducer.produceFromHostFixturePlan(changed, group.resolve("published")));
            assertFalse(Files.exists(group.resolve("published")));
        }
    }

    @Test void missingNullBooleanArrayAndDuplicatePayloadsRefuseWithoutReserializingThem() throws Exception {
        List<String> bodies = List.of("{}", "{\"milestone\":\"G2-M0\",\"payload\":null}",
                "{\"milestone\":\"G2-M0\",\"payload\":true}", "{\"milestone\":\"G2-M0\",\"payload\":[]}",
                "{\"milestone\":\"G2-M0\",\"payload\":{},\"payload\":{}}",
                "{\"milestone\":\"G2-M0\",\"payload\":{\"x\":1,\"x\":2}}",
                "{\"milestone\":false,\"payload\":{}}", "{\"milestone\":\"G2-M0\",\"payload\":{}} {} ");
        for (int index = 0; index < bodies.size(); index++) {
            Path path = root.resolve("bad-" + index + ".json"); Files.writeString(path, bodies.get(index));
            FileRef ref = FileRef.measure(path);
            assertThrows(IOException.class, () -> RootSoftwareFixtureInputsProducer.payload(ref, "G2-M0"));
        }
    }

    @Test void wrongMilestoneAndExistingOutputCannotBeUsedForAnotherProduction() throws Exception {
        Path raw = root.resolve("crossed.json"); Files.writeString(raw, request("G2-M1"));
        assertThrows(IOException.class, () -> RootSoftwareFixtureInputsProducer.payload(FileRef.measure(raw), "G2-M0"));
        FileRef plan = hostFixturePlanFixture(root.resolve("host"));
        Path output = root.resolve("published"); Files.createDirectory(output); Files.writeString(output.resolve("keep"), "original");
        assertThrows(IOException.class, () -> RootSoftwareFixtureInputsProducer.produceFromHostFixturePlan(plan, output));
        assertEquals("original", Files.readString(output.resolve("keep")));
        assertFalse(Files.exists(output.resolve("software-fixture-inputs.json")));
    }

    @Test void byteOffsetsPreserveEscapesWhitespaceUtf8WideIntegersAndDecimalLexemes() throws Exception {
        Path raw = root.resolve("request.json"); Files.writeString(raw, request("G2-M0"));
        assertArrayEquals(PAYLOAD.getBytes(StandardCharsets.UTF_8), RootSoftwareFixtureInputsProducer.payload(FileRef.measure(raw), "G2-M0"));
    }

    @Test void checkoutOriginalsReachPersistedHostRequestWithExactPayloadAndOrderedRoles() throws Exception {
        Path checkout = checkoutFixture(root.resolve("checkout"));
        var produced = RootSoftwareFixtureInputsProducer.produceFromCheckout(checkout, root.resolve("published"));
        var request = readRequest(produced.requestRef());
        assertEquals(8, request.originalFixtureRefs().size());
        assertEquals(request.originalFixtureRefs(), request.originalRequestRefs());
        assertEquals(request.originalRequestRefs().getFirst(), request.probeRequestRef());
        for (int index = 0; index < 8; index++)
            assertEquals(FileRef.measure(checkout.resolve("g2-research/src/test/resources/g2-http/M"
                    + index + ".request.json")), request.originalRequestRefs().get(index));
        assertArrayEquals(PAYLOAD.getBytes(StandardCharsets.UTF_8),
                Files.readAllBytes(Path.of(produced.probePayloadRef().path())));
        try (var files = Files.list(root.resolve("published"))) { assertEquals(2, files.count()); }
    }

    @Test void checkoutMissingCrossedOrMalformedFinalOriginalFailsBeforePublication() throws Exception {
        for (String kind : List.of("missing", "crossed", "malformed")) {
            Path checkout = checkoutFixture(root.resolve(kind));
            Path last = checkout.resolve("g2-research/src/test/resources/g2-http/M7.request.json");
            if (kind.equals("missing")) Files.delete(last);
            else if (kind.equals("crossed")) Files.writeString(last, request("G2-M6"));
            else Files.writeString(last, "{\"milestone\":\"G2-M7\",\"payload\":true}");
            Path output = root.resolve(kind + "-published");
            assertThrows(IOException.class, () -> RootSoftwareFixtureInputsProducer.produceFromCheckout(checkout, output));
            assertFalse(Files.exists(output));
        }
    }

    /** Explicit test-only request files; the production method never imports this helper. */
    static Path checkoutFixture(Path directory) throws IOException {
        Path inputs = Files.createDirectories(directory.resolve("g2-research/src/test/resources/g2-http"));
        for (int index = 0; index < 8; index++)
            Files.writeString(inputs.resolve("M" + index + ".request.json"), request("G2-M" + index));
        return directory;
    }

    private static RootSoftwareFixtureHandoff.Request readRequest(FileRef ref) throws IOException {
        ref.verify(); return ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(ref.path())), RootSoftwareFixtureHandoff.Request.class);
    }

    private static String request(String milestone) {
        return "{\"schema\":\"xar.g2-research-request/v1\",\"milestone\":\"" + milestone + "\",\"payload\":" + PAYLOAD + "}";
    }

    /** Shared software-only pins for the real CLI test; these are never published as actual SDK/host inputs. */
    static FileRef hostFixturePlanFixture(Path directory) throws IOException {
        Files.createDirectories(directory); var mapper = ControlBuild.strictMapper(); var plan = mapper.createObjectNode();
        plan.put("schema", "xar.g2-host-actual-fixture-plan/v1"); plan.put("machine_id", WindowsJobProcess.currentMachineId());
        plan.put("observed_at_utc", Instant.now().toString()); plan.put("status", "SYNTHETIC_SOFTWARE_PRODUCER_TEST_ONLY");
        plan.putNull("supersedes"); plan.putArray("pending"); plan.putNull("host_map"); plan.putArray("upstream_artifact_indexes");
        plan.put("fixture_target_note", "software test inputs"); plan.put("server_context_note", "no running host");
        plan.putNull("actual"); plan.put("new_game_days", 0); var rows = plan.putArray("ready_rows");
        for (int index = 0; index < 8; index++) for (String suffix : List.of("request", "result")) {
            Path path = directory.resolve("M" + index + "." + suffix + ".json");
            Files.writeString(path, suffix.equals("request") ? request("G2-M" + index) : "{\"software_result\":true}");
            var row = rows.addObject(); row.put("milestone", "M" + index);
            row.set("source_ref", mapper.valueToTree(FileRef.measure(path)));
            row.put("target_relative", "g2-research/src/test/resources/g2-http/" + path.getFileName());
            row.put("qualification", "SYNTHETIC_SOURCE_SHAPE_NOT_EXECUTION");
        }
        Path path = directory.resolve("host-plan.json"); Files.write(path, mapper.writeValueAsBytes(plan)); return FileRef.measure(path);
    }

    /** Uses the existing strict nineteen-role contract with explicit test-only fixture provenance. */
    static FileRef goldenPlanFixture(Path directory) throws IOException {
        Files.createDirectories(directory); var mapper = ControlBuild.strictMapper(); var refs = new ArrayList<FileRef>();
        var roles = new ArrayList<>(List.of("context_input", "context_result", "evaluate_request"));
        for (int index = 0; index < 3; index++) {
            Path path = directory.resolve(roles.get(index) + ".json"); Files.writeString(path, "{\"software_test\":true}"); refs.add(FileRef.measure(path));
        }
        var vectors = new ArrayList<FreshSdkFixtureStage.ProducerGoldenVector>();
        for (var milestone : FreshSdkFixtureStage.GoldenMilestone.values()) {
            Path input = directory.resolve(milestone.name() + ".request.json"), result = directory.resolve(milestone.name() + ".result.json");
            Files.writeString(input, request("G2-" + milestone.name())); Files.writeString(result, "{\"software_test\":true}");
            FileRef request = FileRef.measure(input), response = FileRef.measure(result);
            refs.add(request); refs.add(response); roles.add("G2-" + milestone.name() + ".request"); roles.add("G2-" + milestone.name() + ".result");
            vectors.add(new FreshSdkFixtureStage.ProducerGoldenVector(milestone, request, response));
        }
        Path client = directory.resolve("client-test-input.txt"), tests = directory.resolve("test-module-input.txt");
        Files.writeString(client, "software-only client digest"); Files.writeString(tests, "software-only test digest");
        FileRef clientRef = FileRef.measure(client), testRef = FileRef.measure(tests);
        var origin = mapper.createObjectNode(); origin.put("schema", "xar.existing-python-producer-golden-install-map/v1");
        origin.put("machine_id", WindowsJobProcess.currentMachineId()); origin.put("observed_at_utc", Instant.now().toString());
        origin.put("status", "EXACT_EXISTING_SETUP_HANDOFF_NO_NEW_RUNNER"); origin.set("existing_setup_spec_ref", mapper.valueToTree(clientRef));
        origin.put("setup_source_field", "SYNTHETIC_TEST_ONLY"); origin.set("test_module_ref", mapper.valueToTree(testRef));
        origin.put("logical_module", "tools.g2_saved_campaign.test_java_projection_client_v1");
        origin.put("framework", "test fixture only"); origin.put("golden_install", "test fixture only");
        origin.put("actual_config_seam", "not an actual SDK run"); origin.put("authority", "SOFTWARE_TEST_ONLY_NO_ADMISSION");
        var counts = origin.putObject("classes"); counts.put("ProjectionClientContractTests", 49);
        counts.put("ProjectionClientG2ProducerGoldenTests", 4); counts.put("ProjectionClientActualJavaTests", 2);
        var rows = origin.putArray("roles");
        for (int index = 0; index < refs.size(); index++) { var row = rows.addObject(); row.put("role", roles.get(index)); row.set("ref", mapper.valueToTree(refs.get(index))); }
        Path install = directory.resolve("test-install-map.json"); Files.write(install, mapper.writeValueAsBytes(origin));
        var plan = new FreshSdkFixtureStage.ProducerGoldenPlan("xar.sdk-producer-golden-plan/v1", WindowsJobProcess.currentMachineId(), FileRef.measure(install),
                new SdkSourceAssembly.Digest(clientRef.bytes(), clientRef.sha256()), new SdkSourceAssembly.Digest(testRef.bytes(), testRef.sha256()),
                refs.get(0), refs.get(1), refs.get(2), vectors);
        Path output = directory.resolve("test-golden-plan.json"); Files.write(output, mapper.writeValueAsBytes(plan)); return FileRef.measure(output);
    }
}
