package org.xar.ck3.control.wave2.prisoners.releasepreview;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.SupportedBuild;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

final class ReleasePreview12003Test {
    private static final FrameBinding FRAME = new FrameBinding(BigInteger.valueOf(1014), 53286360, 29829, 61540);
    private static final List<String> CASES = List.of("gate_true", "gate_false", "old11",
            "selected_change_prison", "puppet_role_mismatch");

    @Test
    void separateProcessConsumerArgumentsFailBeforeOutputCreation(@TempDir Path temporary) {
        Path output = temporary.resolve("must-remain-absent");
        IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                () -> ReleasePreviewCompatibilityCapture.main(new String[] {
                    "source-test-machine", output.toString(), "unused-native", "unused-python", "unused-source"
                }));
        assertTrue(failure.getMessage().contains("separate-process registered consumer mode is unavailable"));
        assertFalse(Files.exists(output));
    }

    @Test
    void wholeProjectionManifestDoesNotGrantConsumerQualification(@TempDir Path temporary) throws IOException {
        Path output = temporary.resolve("projection-only");
        ReleasePreviewCompatibilityCapture.main(new String[] {"source-test-machine", output.toString()});
        JsonNode capture = StrictJson.parse(Files.readAllBytes(output.resolve("CAPTURE.json")), 131_072);
        assertEquals("xar.java.releasepreview.compatibility-capture.v2", capture.path("schema").textValue());
        assertEquals(10, capture.path("vectors").size());
        assertEquals("NOT_RUN_NO_NATIVE_PRODUCER_DIRECTORY_SUPPLIED",
                capture.path("kinship_capture_status").textValue());
        assertEquals("NOT_RUN_REQUIRES_ADMITTED_SAME_PYTHON_PROCESS",
                capture.path("registered_consumer_status").textValue());
        assertTrue(capture.path("registered_consumer_qualification_granted").isBoolean());
        assertFalse(capture.path("registered_consumer_qualification_granted").booleanValue());
        assertFalse(capture.has("registered_consumers"));
    }

    @Test
    void realNativeProducersAndLegacyNormalizedLeavesRoundTrip() throws IOException {
        for (SupportedBuild build : SupportedBuild.values()) {
            for (String name : CASES) {
                byte[] raw = resource(directory(build) + "/" + name + ".json");
                JsonNode root = StrictJson.parse(raw, ReleaseCollectionProjection12003.MAX_BYTES);
                JsonNode leaf = selectedLeaf(root);
                ReleasePreview12003 preview = ReleasePreviewCodec12003.fromNode(leaf, FRAME);
                assertEquals(leaf, ReleasePreviewCodec12003.toNode(preview), build + "/" + name);
                assertEquals(preview, ReleasePreviewCodec12003.decode(ReleasePreviewCodec12003.encode(preview), FRAME));
                ReleaseCollectionProjection12003.Observation collection =
                        ReleaseCollectionProjection12003.decode(raw, build, FRAME);
                assertEquals(preview, collection.rows().get(2).preview());
                assertEquals(4, collection.rows().size());
                assertEquals(2, collection.selectedOrdinal());
                assertEquals(hash(raw), collection.originalSha256());
                if (name.startsWith("gate_")) {
                    ReleasePreview12003.Available available = assertInstanceOf(ReleasePreview12003.Available.class, preview);
                    assertEquals("gate_true".equals(name), available.canSend());
                    assertEquals(10, available.costs().entries().size());
                } else { assertInstanceOf(ReleasePreview12003.Unavailable.class, preview); }
            }
        }
    }

    @Test
    void pinnedOriginalBytesAreMandatoryAndMachineBound() throws IOException {
        JsonNode manifest = StrictJson.parse(resource("source-pins.json"), 131_072);
        assertEquals("xar.java.releasepreview.source-pins.v1", manifest.path("schema").textValue());
        assertTrue(manifest.path("machine_id").isTextual());
        assertFalse(manifest.path("machine_id").textValue().isBlank());
        StrictJson.utc(StrictJson.text(manifest.get("observed_at_utc")));
        JsonNode vectors = manifest.get("vectors");
        assertTrue(vectors != null && vectors.isArray() && vectors.size() >= 10,
                "original producer goldens must be supplied by the shared execution owner");
        for (JsonNode vector : vectors) {
            String path = StrictJson.text(vector.get("resource"));
            assertEquals(StrictJson.text(vector.get("sha256")), hash(resource(path)), path);
        }
        JsonNode sources = manifest.get("sources");
        assertTrue(sources != null && sources.isArray() && sources.size() >= 7);
        for (JsonNode source : sources) {
            assertTrue(StrictJson.text(source.get("sha256")).matches("[0-9a-f]{64}"));
            StrictJson.text(source.get("path"));
        }
    }

    @Test
    void observedFalseGateIsAnAvailableInputRatherThanAReleaseResult() throws IOException {
        ReleasePreview12003.Available preview = assertInstanceOf(ReleasePreview12003.Available.class,
                ReleasePreviewCodec12003.fromNode(selectedLeaf(nativeRoot("gate_false")), FRAME));
        assertFalse(preview.canSend());
        ObjectNode wire = ReleasePreviewCodec12003.toNode(preview);
        assertTrue(wire.path("acceptance").path("would_accept_now").booleanValue());
        assertFalse(wire.has("material_result"));
        assertFalse(wire.has("released"));
        assertThrows(UnsupportedOperationException.class, () -> preview.costs().entries().clear());
    }

    @Test
    void currentUnsignedFrameAndSignedCostsRetainTheirWholeNativeWidths() throws IOException {
        ObjectNode leaf = available();
        BigInteger maximum = StrictJson.UINT64_MAX;
        FrameBinding wide = new FrameBinding(maximum, Integer.MIN_VALUE, 0xffff_ffffL, 0xffff_fffeL);
        leaf.put("snapshot_id", wide.snapshotId());
        leaf.put("native_revision", maximum);
        leaf.put("public_revision", maximum);
        leaf.put("proof_epoch", maximum);
        leaf.put("date_raw", wide.dateRaw());
        leaf.set("roles", ReleasePreviewValues12003.writeRoles(wide.roles()));
        leaf.put("puppet_or_actor_character_id", wide.playerCharacterId());
        ((ObjectNode) leaf.get("definition")).put("deterministic_key_hash", 0xffff_ffffL);
        ((ObjectNode) leaf.get("definition")).put("runtime_ordinal", Integer.MAX_VALUE);
        ArrayNode costs = (ArrayNode) leaf.get("costs").get("entries");
        ((ObjectNode) costs.get(0)).put("raw", Long.MIN_VALUE);
        ((ObjectNode) costs.get(1)).put("raw", Long.MAX_VALUE);
        byte[] encoded = StrictJson.canonical(leaf);
        ReleasePreview12003 decoded = ReleasePreviewCodec12003.decode(encoded, wide);
        assertArrayEquals(encoded, ReleasePreviewCodec12003.encode(decoded));
        leaf.put("proof_epoch", maximum.add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(leaf, wide));
        assertThrows(IllegalArgumentException.class,
                () -> new FrameBinding(BigInteger.ZERO, 0, 1, 2));
        assertThrows(IllegalArgumentException.class,
                () -> new FrameBinding(BigInteger.ONE, 0, 1, 1));
    }

    @Test
    void strictRawTokensRejectBoolFloatStringsDuplicatesAndTrailingContent() throws IOException {
        String raw = new String(StrictJson.canonical(available()), StandardCharsets.UTF_8);
        for (String replacement : List.of("true", "1014.0", "1.014e3", "\"1014\"", "null")) {
            byte[] malformed = raw.replace("\"native_revision\":1014", "\"native_revision\":" + replacement)
                    .getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.decode(malformed, FRAME), replacement);
        }
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.decode(
                raw.replace("\"can_send\":true", "\"can_send\":true,\"can_send\":false")
                        .getBytes(StandardCharsets.UTF_8), FRAME));
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.decode(
                (raw + "{}").getBytes(StandardCharsets.UTF_8), FRAME));
        assertThrows(IllegalArgumentException.class,
                () -> ReleasePreviewCodec12003.decode(new byte[] {(byte) 0xff}, FRAME));
    }

    @Test
    void malformedAvailableInputsNeverBecomeUnavailabilityOrAnObservedRefusal() throws IOException {
        for (String field : List.of("proof_epoch", "roles", "acceptance", "readiness", "costs", "option_keys")) {
            ObjectNode missing = available();
            missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(missing, FRAME), field);
        }
        ObjectNode extra = available();
        extra.put("future_release_effect", true);
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(extra, FRAME));
        ObjectNode stale = available();
        stale.put("snapshot_id", "native:1013");
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(stale, FRAME));
        ObjectNode prisoner = available();
        ((ObjectNode) prisoner.get("roles")).put("recipient_character_id", 61541);
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(prisoner, FRAME));
        ObjectNode acceptance = available();
        ((ObjectNode) acceptance.get("acceptance")).put("would_accept_now", false);
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(acceptance, FRAME));
        ObjectNode readiness = available();
        ((ObjectNode) readiness.get("readiness")).put("same_frame_ready", false);
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(readiness, FRAME));
    }

    @Test
    void optionAndResourceOrderScaleAndSelectedMaskAreExact() throws IOException {
        ObjectNode selected = available();
        selected.put("selected_option_mask_bits", 1);
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(selected, FRAME));
        ObjectNode options = available();
        ((ArrayNode) options.get("option_keys")).set(0, options.get("option_keys").get(1));
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(options, FRAME));
        ObjectNode cost = available();
        ((ObjectNode) cost.get("costs").get("entries").get(0)).put("resource_key", "piety");
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(cost, FRAME));
        ObjectNode scale = available();
        ((ObjectNode) scale.get("costs")).put("raw_scale", 10000);
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(scale, FRAME));
    }

    @Test
    void unknownNativeUnavailableReasonsRemainVerbatimAndHaveOnlyLegacySixFields() throws IOException {
        ObjectNode unavailable = (ObjectNode) selectedLeaf(nativeRoot("old11")).deepCopy();
        unavailable.put("unavailable_reason", "hostage_or_unknown_family_rule_未知\nretained");
        ReleasePreview12003 value = ReleasePreviewCodec12003.fromNode(unavailable, FRAME);
        assertEquals(unavailable, ReleasePreviewCodec12003.toNode(value));
        assertEquals(6, ReleasePreviewCodec12003.toNode(value).size());
        unavailable.put("can_send", false);
        assertThrows(IllegalArgumentException.class, () -> ReleasePreviewCodec12003.fromNode(unavailable, FRAME));
    }

    @Test
    void actualCollectionProjectionPreservesFamilyNullsAndRejectsCustodyOrEpochDrift() throws IOException {
        ObjectNode root = nativeRoot("gate_true");
        ReleaseCollectionProjection12003.Observation before = ReleaseCollectionProjection12003.decode(
                StrictJson.canonical(root), SupportedBuild.CK3_12004, FRAME);
        assertInstanceOf(ReleaseCollectionProjection12003.MeasuredLineage.class, before.rows().get(2).lineage());
        assertEquals(new ReleaseCollectionProjection12003.MeasuredTitleTier(null), before.rows().get(2).primaryTitleTier());
        assertEquals(new NativeKinship12003.Missing(), before.rows().get(2).nativeKinship());
        root.put("sdk_future_container", "preserved in original SHA only");
        ReleaseCollectionProjection12003.Observation extended = ReleaseCollectionProjection12003.decode(
                StrictJson.canonical(root), SupportedBuild.CK3_12004, FRAME);
        assertEquals(before.rows(), extended.rows());
        assertNotEquals(before.originalSha256(), extended.originalSha256());
        ObjectNode badCustody = nativeRoot("gate_true");
        ((ObjectNode) badCustody.get("player_prisoner_collection").get("prisoners").get(2))
                .put("jailer_character_id", 999);
        assertThrows(IllegalArgumentException.class, () -> ReleaseCollectionProjection12003.decode(
                StrictJson.canonical(badCustody), SupportedBuild.CK3_12004, FRAME));
        ObjectNode badEpoch = nativeRoot("gate_true");
        badEpoch.put("observation_revision", 1926336);
        assertThrows(IllegalArgumentException.class, () -> ReleaseCollectionProjection12003.decode(
                StrictJson.canonical(badEpoch), SupportedBuild.CK3_12004, FRAME));
        assertThrows(IllegalArgumentException.class, () -> SupportedBuild.exact("1.20.0.4",
                SupportedBuild.CK3_12003.executableSha256()));
    }

    @Test
    void realSchemaSevenKinshipProducerKeepsUnknownSeparateFromFalse() throws IOException {
        for (String name : List.of("nonchild_close_family", "unrelated", "sample_drift",
                "wrong_generation", "wrong_jailer", "not_paused")) {
            byte[] raw = resource("kinship12003/" + name + ".json");
            JsonNode root = StrictJson.parse(raw, ReleaseCollectionProjection12003.MAX_BYTES);
            ReleaseCollectionProjection12003.Observation collection = ReleaseCollectionProjection12003.decode(
                    raw, SupportedBuild.CK3_12003, FRAME);
            for (int ordinal = 0; ordinal < 4; ordinal++) {
                NativeKinship12003 kinship = collection.rows().get(ordinal).nativeKinship();
                assertEquals(root.get("player_prisoner_collection").get("prisoners").get(ordinal).get("native_kinship"),
                        NativeKinshipCodec12003.toNode(kinship));
            }
            NativeKinship12003 selected = collection.rows().get(2).nativeKinship();
            if ("nonchild_close_family".equals(name)) {
                assertTrue(assertInstanceOf(NativeKinship12003.Available.class, selected).closeFamily());
            } else if ("unrelated".equals(name)) {
                assertFalse(assertInstanceOf(NativeKinship12003.Available.class, selected).closeFamily());
            } else { assertInstanceOf(NativeKinship12003.Unavailable.class, selected); }
        }
    }

    private static String directory(SupportedBuild build) {
        return build == SupportedBuild.CK3_12003 ? "native12003" : "native12004";
    }
    private static ObjectNode nativeRoot(String name) throws IOException {
        return (ObjectNode) StrictJson.parse(resource("native12004/" + name + ".json"), 131_072);
    }
    private static JsonNode selectedLeaf(JsonNode root) {
        return root.get("player_prisoner_collection").get("prisoners").get(2).get("unconditional_release_preview");
    }
    private static ObjectNode available() throws IOException {
        return (ObjectNode) selectedLeaf(nativeRoot("gate_true")).deepCopy();
    }
    private static byte[] resource(String name) throws IOException {
        try (InputStream input = ReleasePreview12003Test.class.getResourceAsStream("/releasepreview/" + name)) {
            if (input == null) { throw new IOException("required real-producer golden is absent: " + name); }
            return input.readAllBytes();
        }
    }
    private static String hash(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }
}
