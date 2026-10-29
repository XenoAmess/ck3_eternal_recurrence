package org.xar.ck3.control.wave3.governance.lifecycle;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

final class SuccessionLifecycleContractTest {
    @TestFactory
    Stream<DynamicTest> originalProducerAndActualBindingConsumers() throws IOException {
        JsonNode golden = golden(); assertEquals(8, golden.get("cases").size()); assertTrue(golden.get("source_refs_unchanged").booleanValue());
        JsonNode original = golden.get("original_unittest");
        assertTrue(original.get("whole_modules").booleanValue()); assertEquals(4, original.get("modules").size());
        assertTrue(original.get("tests").intValue() >= 24);
        assertEquals(original.get("tests").intValue(), original.get("discovered_tests").intValue());
        assertEquals(original.get("tests").intValue(), original.get("discovered_test_ids").size());
        for (String counter : List.of("failures", "errors", "skipped")) { assertEquals(0, original.get(counter).intValue()); }
        assertTrue(golden.get("machine_id").isTextual()); assertTrue(golden.get("actual_checkpoint_consumer_rejected_mixed_anchors").booleanValue());
        return StreamSupport.stream(golden.get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            byte[] result = SuccessionLifecycleConsumerPort.apply(raw(row.get("request")));
            assertEquals(row.get("expected"), SuccessionLifecycleCodec.parse(result));
            SuccessionLifecycleBinding binding = SuccessionLifecycleCodec.decode(result);
            assertEquals(row.get("expected"), SuccessionLifecycleCodec.parse(SuccessionLifecycleCodec.normalize(result)));
            JsonNode consumers = row.get("actual_consumers");
            assertTrue(consumers.get("checkpoint_environment_binding").get("accepted").booleanValue());
            assertEquals(binding, SuccessionLifecycleConsumers.equalAnchors(binding, binding, binding));
            assertConsumer(consumers.get("ordinary_seed_binding"), binding, true);
            assertConsumer(consumers.get("rogue_checkpoint_binding"), binding, false);
        }));
    }
    @TestFactory
    Stream<DynamicTest> originalStrictLifecycleFailures() throws IOException {
        JsonNode source = golden(); assertEquals(16, source.get("rejections").size());
        return StreamSupport.stream(source.get("rejections").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () ->
                assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleCodec.normalize(row.get("raw_binding_json").textValue().getBytes(StandardCharsets.UTF_8)))));
    }
    @TestFactory
    Stream<DynamicTest> originalThreeAnchorConsumersRetainEverySourceAndEnvironmentGuard() throws IOException {
        JsonNode source = golden(); assertEquals(20, source.get("anchor_consumer_cases").size());
        return StreamSupport.stream(source.get("anchor_consumer_cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            JsonNode consumers = row.get("actual_consumers"), anchors = row.get("anchors"); assertEquals(3, anchors.size());
            assertAnchorConsumer(consumers.get("checkpoint_environment_binding"), anchors, "checkpoint");
            assertAnchorConsumer(consumers.get("ordinary_seed_anchors"), anchors, "ordinary");
            assertAnchorConsumer(consumers.get("rogue_checkpoint_anchors"), anchors, "rogue");
        }));
    }
    @Test
    void actualBindingAndAnchorReaderSourcesRemainPinned() throws Exception {
        Path root = repositoryRoot();
        for (JsonNode ref : golden().get("source_refs")) {
            Path path = root.resolve(ref.get("path").textValue()).normalize(); assertTrue(path.startsWith(root));
            byte[] bytes = Files.readAllBytes(path); assertEquals(ref.get("bytes").longValue(), bytes.length, path.toString());
            assertEquals(ref.get("sha256").textValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), path.toString());
        }
    }
    @Test
    void ordinaryAbsenceIsADistinctBoundProfileAndNotTheFrozenOffSeedProfile() {
        SuccessionLifecycleBinding value = new SuccessionLifecycleBinding(SuccessionLifecycleBinding.Profile.ORDINARY_VERIFIED_MOD_ABSENCE, "absent_by_verified_xar_mod_not_loaded", "a".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumers.ordinarySeed(value));
        assertThrows(IllegalArgumentException.class, () -> new SuccessionLifecycleBinding(SuccessionLifecycleBinding.Profile.ORDINARY_VERIFIED_MOD_ABSENCE, "caller-green", "a".repeat(64)));
        assertThrows(IllegalArgumentException.class, () -> new SuccessionLifecycleBinding(SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF, "prepared-environment-manifest", null));
        assertFalse(value.equals(SuccessionLifecycleBinding.unknown()));
    }
    @Test
    void coldAnchorEqualityPreservesSourceAndEnvironmentAndRejectsMissing() {
        SuccessionLifecycleBinding first = new SuccessionLifecycleBinding(SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF, "prepared-environment-manifest", "a".repeat(64));
        SuccessionLifecycleBinding environmentDrift = new SuccessionLifecycleBinding(first.profile(), first.source(), "b".repeat(64));
        SuccessionLifecycleBinding sourceDrift = new SuccessionLifecycleBinding(first.profile(), "other-original-source", first.environmentSha256());
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumers.equalAnchors(first, environmentDrift, first));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumers.equalAnchors(first, first, sourceDrift));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumers.equalAnchors(first, null, first));
    }
    @Test
    void unknownNeverBecomesRogueAndLegacyIsExplicit() {
        assertEquals(SuccessionLifecycleBinding.Profile.UNKNOWN, SuccessionLifecycleBinding.unknown().profile());
        assertEquals(SuccessionLifecycleBinding.Profile.ROGUE_ONE_LIFE, SuccessionLifecycleBinding.legacyRogue().profile());
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumers.rogueCheckpoint(SuccessionLifecycleBinding.unknown()));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleCodec.normalize("null".getBytes(StandardCharsets.UTF_8)));
    }
    @Test
    void wrapperTypesDuplicateKeysTrailingContentUtf8AndSizeAreStrict() {
        String value = "{\"schema\":\"" + SuccessionLifecycleConsumerPort.SCHEMA + "\",\"operation\":\"legacy\"}";
        assertEquals(SuccessionLifecycleBinding.legacyRogue(), SuccessionLifecycleCodec.decode(SuccessionLifecycleConsumerPort.apply(value.getBytes(StandardCharsets.UTF_8))));
        for (String raw : List.of(value + "{}", value.substring(0, value.length() - 1) + ",\"operation\":\"unknown\"}", value.replace("\"legacy\"", "true"), value.substring(0, value.length() - 1) + ",\"restore_allowed\":true}")) {
            assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumerPort.apply(raw.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumerPort.apply(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumerPort.apply(new byte[SuccessionLifecycleCodec.MAX_BYTES + 1]));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumerPort.apply("{\"x\":\"\\ud800\"}".getBytes(StandardCharsets.UTF_8)));
    }
    @Test
    void exactSixFieldsRejectNullMissingAndWrongPrimitiveTokens() {
        ObjectNode binding = (ObjectNode) SuccessionLifecycleCodec.parse(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue()));
        for (String field : List.of("schema", "lifecycle", "xar_enabled", "pact_contract", "source", "environment_sha256")) {
            ObjectNode missing = binding.deepCopy(); missing.remove(field); assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleCodec.normalize(raw(missing)));
        }
        for (String token : List.of("true", "1", "1.0", "[]", "{}")) {
            String wrong = new String(raw(binding), StandardCharsets.UTF_8).replace("\"source\":\"legacy-driver-default\"", "\"source\":" + token);
            assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleCodec.normalize(wrong.getBytes(StandardCharsets.UTF_8)));
        }
    }
    @Test
    void actualVanillaProducerRoundTripsWithoutFrozenOrRogueAdmission() {
        ObjectNode produced = org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla().toJson();
        SuccessionLifecycleBinding value = SuccessionLifecycleCodec.decode(raw(produced));
        assertEquals(SuccessionLifecycleBinding.Profile.ORDINARY_VANILLA_CONFIGURATION, value.profile());
        assertTrue(value.profile().ordinary());
        assertEquals("ordinary_vanilla_configuration", value.source());
        assertEquals(null, value.environmentSha256());
        assertEquals(produced, SuccessionLifecycleCodec.parse(SuccessionLifecycleCodec.normalize(raw(produced))));
        ObjectNode request = new ObjectMapper().createObjectNode().put("schema", SuccessionLifecycleConsumerPort.SCHEMA).put("operation", "normalize");
        request.set("binding", produced);
        assertEquals(produced, SuccessionLifecycleCodec.parse(SuccessionLifecycleConsumerPort.apply(raw(request))));
        assertEquals(value, SuccessionLifecycleConsumerPort.consume(new SuccessionLifecycleConsumerPort.AnchorRequest(
                SuccessionLifecycleConsumerPort.Consumer.CHECKPOINT, value, value, value)));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumerPort.consume(
                new SuccessionLifecycleConsumerPort.BindingRequest(SuccessionLifecycleConsumerPort.Consumer.ORDINARY, value)));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumerPort.consume(
                new SuccessionLifecycleConsumerPort.BindingRequest(SuccessionLifecycleConsumerPort.Consumer.ROGUE, value)));
        SuccessionLifecycleBinding frozen = new SuccessionLifecycleBinding(
                SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF, "prepared-environment-manifest", "a".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleConsumers.equalAnchors(value, frozen, value));
    }
    @Test
    void vanillaConfigurationCannotClaimFrozenEnvironmentOrVerifiedAbsence() {
        ObjectNode produced = org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla().toJson();
        for (ObjectNode crossed : List.of(
                produced.deepCopy().put("source", "caller-green"),
                produced.deepCopy().put("source", "absent_by_verified_xar_mod_not_loaded"),
                produced.deepCopy().put("environment_sha256", "a".repeat(64)),
                produced.deepCopy().put("pact_contract", "absent_by_verified_xar_mod_not_loaded"),
                produced.deepCopy().put("pact_contract", "absent_by_fresh_campaign_xar_off_contract"),
                produced.deepCopy().put("xar_enabled", "xar_off"),
                produced.deepCopy().put("xar_enabled", true),
                produced.deepCopy().put("lifecycle", "rogue_one_life"))) {
            assertThrows(IllegalArgumentException.class, () -> SuccessionLifecycleCodec.normalize(raw(crossed)), crossed.toString());
        }
        assertThrows(IllegalArgumentException.class, () -> new SuccessionLifecycleBinding(
                SuccessionLifecycleBinding.Profile.ORDINARY_VANILLA_CONFIGURATION, "caller-green", null));
        assertThrows(IllegalArgumentException.class, () -> new SuccessionLifecycleBinding(
                SuccessionLifecycleBinding.Profile.ORDINARY_VANILLA_CONFIGURATION, "ordinary_vanilla_configuration", "a".repeat(64)));
        assertThrows(IllegalArgumentException.class, () -> new SuccessionLifecycleBinding(
                SuccessionLifecycleBinding.Profile.ORDINARY_VERIFIED_MOD_ABSENCE, "absent_by_verified_xar_mod_not_loaded", null));
    }
    private static void assertConsumer(JsonNode expected, SuccessionLifecycleBinding binding, boolean ordinary) {
        if (expected.get("accepted").booleanValue()) {
            SuccessionLifecycleBinding result = ordinary ? SuccessionLifecycleConsumers.ordinarySeed(binding) : SuccessionLifecycleConsumers.rogueCheckpoint(binding);
            assertEquals(expected.get("binding"), SuccessionLifecycleCodec.parse(SuccessionLifecycleCodec.encode(result)));
        } else { assertThrows(IllegalArgumentException.class, () -> { if (ordinary) { SuccessionLifecycleConsumers.ordinarySeed(binding); } else { SuccessionLifecycleConsumers.rogueCheckpoint(binding); } }); }
    }
    private static void assertAnchorConsumer(JsonNode expected, JsonNode anchors, String consumer) {
        try {
            SuccessionLifecycleBinding[] values = new SuccessionLifecycleBinding[3];
            for (int index = 0; index < values.length; index++) {
                SuccessionLifecycleBinding value = SuccessionLifecycleCodec.decode(raw(anchors.get(index)));
                values[index] = switch (consumer) {
                    case "ordinary" -> SuccessionLifecycleConsumers.ordinarySeed(value);
                    case "rogue" -> SuccessionLifecycleConsumers.rogueCheckpoint(value);
                    case "checkpoint" -> value;
                    default -> throw new IllegalArgumentException("unknown test consumer");
                };
            }
            SuccessionLifecycleBinding value = SuccessionLifecycleConsumers.equalAnchors(values[0], values[1], values[2]);
            assertTrue(expected.get("accepted").booleanValue()); assertEquals(expected.get("binding"), SuccessionLifecycleCodec.parse(SuccessionLifecycleCodec.encode(value)));
        } catch (IllegalArgumentException rejected) { assertFalse(expected.get("accepted").booleanValue()); }
    }
    private static Path repositoryRoot() {
        String configured = System.getenv("XAR_REPO_ROOT");
        if (configured == null || configured.isBlank()) { configured = System.getProperty("xar.repo"); }
        Path root = configured == null || configured.isBlank() ? Path.of("..").toAbsolutePath().normalize() : Path.of(configured).toAbsolutePath().normalize();
        if (configured == null || configured.isBlank()) { while (root != null && !Files.isRegularFile(root.resolve("AGENTS.md"))) { root = root.getParent(); } }
        assertNotNull(root, "actual original producer repository required");
        assertTrue(Files.isRegularFile(root.resolve("AGENTS.md")), "configured original source checkout required"); return root;
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = SuccessionLifecycleContractTest.class.getResourceAsStream("/lifecycle/original-producer-golden.json")) {
            assertNotNull(input, "submitted actual original-producer golden required; no Python fallback or skipped default test");
            byte[] bytes = input.readNBytes(60_001); assertTrue(bytes.length <= 60_000, "separate bounded fixture collection, not a runtime lifecycle envelope");
            return new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build()).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).readTree(bytes);
        }
    }
    private static byte[] raw(JsonNode value) { return SuccessionLifecycleCodec.encodeNode(value); }
}
