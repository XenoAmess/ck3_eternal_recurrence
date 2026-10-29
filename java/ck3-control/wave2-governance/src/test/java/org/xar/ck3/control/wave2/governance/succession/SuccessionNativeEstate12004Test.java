package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Arrays;
import org.xar.ck3.control.contracts.FullJsonTree;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Software fixtures only. These tests never invoke or qualify a Game. */
class SuccessionNativeEstate12004Test {
    @Test void originalNativeRootOpaqueNumbersReachRetainedEstateWireWithoutTokenLoss() throws Exception {
        ObjectNode nativeRoot = root(11, 2, false);
        ObjectNode secondaryTitle = object(nativeRoot.at("/campaign_root_context/held_title_partition/1/title"));
        JsonNode opaque = FullJsonTree.parse(
                "{\"negative_zero\":-0.0,\"huge\":1e999,\"integral\":9007199254740993,\"nullable\":null}"
                        .getBytes(java.nio.charset.StandardCharsets.UTF_8), SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
        secondaryTitle.set("opaque", opaque);
        byte[] original = FullJsonTree.encode(nativeRoot, SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
        var frozen = SuccessionNativeEstate12004.freeze(original, semantic(11, 2, false));
        assertArrayEquals(original, frozen.originalRootResult());
        assertEquals(java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(original)), frozen.originalRootSha256());
        JsonNode originalOpaque = FullJsonTree.parse(frozen.originalRootResult(), SuccessionNativeEstate12004.MAX_SOURCE_BYTES)
                .at("/campaign_root_context/held_title_partition/1/title/opaque");
        JsonNode retainedOpaque = FullJsonTree.parse(frozen.wire(), SuccessionCodec.MAX_BYTES)
                .at("/title_expectations/1/title/opaque");
        assertEquals("-0.0", originalOpaque.get("negative_zero").asText());
        assertEquals(opaque, retainedOpaque, "raw native title metadata must survive existing freeze and retained wire");
        assertEquals("-0.0", retainedOpaque.get("negative_zero").asText());
        assertEquals("1e999", retainedOpaque.get("huge").asText());
        assertTrue(retainedOpaque.get("negative_zero").isFloatingPointNumber());
        assertFalse(retainedOpaque.get("negative_zero").isIntegralNumber());
        assertTrue(retainedOpaque.get("huge").isFloatingPointNumber());
        assertTrue(retainedOpaque.get("integral").isIntegralNumber());
        assertTrue(retainedOpaque.get("nullable").isNull());
        assertFalse(retainedOpaque.has("missing"));
        for (String token : List.of("-0.0", "2.0", "true")) {
            ObjectNode wrongId = object(FullJsonTree.parse(original, SuccessionNativeEstate12004.MAX_SOURCE_BYTES));
            object(wrongId.get("campaign_root_context")).set("player_character_id",
                    FullJsonTree.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8), 16));
            assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(
                    FullJsonTree.encode(wrongId, SuccessionNativeEstate12004.MAX_SOURCE_BYTES), semantic(11, 2, false)), token);
        }

    }

    @Test void originalRootToExistingPolicyAndFullWireRetainsActualFinalFrame() {
        ObjectNode before = root(11, 2, false);
        byte[] semantic = semantic(11, 2, false);
        var retained = SuccessionNativeEstate12004.freeze(bytes(before), semantic);
        assertArrayEquals(SuccessionCodec.freeze(bytes(bundle(before, semantic)), "old-episode", 2), retained.wire());
        var compared = SuccessionNativeEstate12004.reconcile(retained, bytes(root(13, 3, true)), semantic(13, 3, true));
        assertEquals(SuccessionModel.Verdict.MATCHED, compared.comparison().verdict());
        JsonNode wire = StrictJson.parse(compared.wire());
        assertNotNull(StrictJson.object(wire, Set.of("schema", "status", "predecessor_binding", "successor_binding", "predecessor_character_id",
                "expected_successor_character_id", "actual_successor_character_id", "successor_match", "expected_inherited_title_ids",
                "matched_inherited_title_ids", "missing_expected_inherited_title_ids", "unexpected_retained_predecessor_title_ids",
                "expected_other_heir_title_ids", "expected_without_heir_title_ids", "observed_additional_successor_title_ids",
                "title_distribution_match", "verdict", "unavailable_reason")));
        assertEquals(13, wire.path("successor_binding").path("native_revision").intValue());
        assertEquals("actual-13", wire.path("successor_binding").path("snapshot_id").textValue());
        assertEquals(List.of(10), compared.comparison().matchedInheritedTitleIds());
        assertEquals(List.of(20), compared.comparison().expectedOtherHeirTitleIds());
    }
    @Test void missingTitleAndDifferentActualActorRemainRealMismatches() {
        var retained = SuccessionNativeEstate12004.freeze(bytes(root(11, 2, false)), semantic(11, 2, false));
        ObjectNode lost = root(13, 3, true);
        ObjectNode title = (ObjectNode) lost.path("campaign_root_context").path("held_title_partition").get(0).path("title");
        title.put("title_id", 30); ((ObjectNode) lost.path("campaign_root_context").path("primary_title")).put("title_id", 30);
        var distribution = SuccessionNativeEstate12004.reconcile(retained, bytes(lost), semantic(13, 3, true));
        assertEquals(SuccessionModel.Verdict.TITLE_DISTRIBUTION_MISMATCH, distribution.comparison().verdict());
        assertEquals(List.of(10), distribution.comparison().missingExpectedInheritedTitleIds());
        var changed = SuccessionNativeEstate12004.reconcile(retained, bytes(root(13, 5, true)), semantic(13, 5, true));
        assertEquals(SuccessionModel.Verdict.UNEXPECTED_SUCCESSOR, changed.comparison().verdict());
    }
    @Test void rootAndSemanticMustBeTheSameActualFrameAndEpisode() {
        var retained = SuccessionNativeEstate12004.freeze(bytes(root(11, 2, false)), semantic(11, 2, false));
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.reconcile(retained, bytes(root(13, 3, true)), semantic(12, 3, true)));
        ObjectNode foreign = object(StrictJson.parse(semantic(13, 3, true))); foreign.put("episode_run_id", "different");
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.reconcile(retained, bytes(root(13, 3, true)), bytes(foreign)));
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.reconcile(retained, bytes(root(10, 3, true)), semantic(10, 3, true)));
    }
    @Test void consumedNativeFieldsRejectMissingNullBooleanFloatAndUnready() {
        for (JsonNode wrong : List.of(com.fasterxml.jackson.databind.node.BooleanNode.TRUE, com.fasterxml.jackson.databind.node.DoubleNode.valueOf(11.0), com.fasterxml.jackson.databind.node.NullNode.instance)) {
            ObjectNode source = root(11, 2, false); source.set("snapshot_revision", wrong);
            assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(bytes(source), semantic(11, 2, false)));
        }
        ObjectNode unready = root(11, 2, false); ((ObjectNode) unready.path("campaign_root_context").path("readiness")).put("held_title_partition_ready", false);
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(bytes(unready), semantic(11, 2, false)));
        ObjectNode incomplete = root(11, 2, false); ((ObjectNode) incomplete.path("campaign_root_context")).remove("held_title_partition");
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(bytes(incomplete), semantic(11, 2, false)));
        ObjectNode modifiedEnvelope = root(11, 2, false); modifiedEnvelope.set("binding", StrictJson.object());
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(bytes(modifiedEnvelope), semantic(11, 2, false)));
    }
    @Test void explicitFamilyNoProvinceVariantSharesTheSingleRowParser() {
        ObjectNode nativeRoot = root(11, 2, false);
        ObjectNode row = (ObjectNode) nativeRoot.path("campaign_root_context").path("held_title_partition").get(0);
        row.putNull("capital_province_id").put("capital_province_kind", "landless_noble_family_no_province").put("title_key", "c_family_01");
        assertEquals(2, SuccessionNativeEstate12004.freeze(bytes(nativeRoot), semantic(11, 2, false)).expectation().titleExpectations().size());
        assertArrayEquals(SuccessionCodec.freeze(bytes(bundle(nativeRoot, semantic(11, 2, false))), "old-episode", 2),
                SuccessionNativeEstate12004.freeze(bytes(nativeRoot), semantic(11, 2, false)).wire());
        row.put("capital_province_id", 6);
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(bytes(nativeRoot), semantic(11, 2, false)));
    }
    @Test void sourceArraysAreDetachedAndTitleHeirNeverGrantsNaturalAuthority() {
        byte[] raw = bytes(root(11, 2, false)), sem = semantic(11, 2, false);
        var retained = SuccessionNativeEstate12004.freeze(raw, sem); String digest = retained.originalRootSha256();
        raw[0] = 0; sem[0] = 0; retained.originalRootResult()[0] = 0;
        assertEquals(digest, retained.originalRootSha256());
        assertEquals(3, retained.expectation().expectedSuccessorCharacterId());
        ObjectNode changed = object(StrictJson.parse(semantic(13, 3, true))); changed.put("one_life_terminal", false).putNull("one_life_terminal_reason");
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.reconcile(retained, bytes(root(13, 3, true)), bytes(changed)));
    }
    @Test void missingNativeTerminalBooleanIsOnlyAnInternalActorReasonProjection() {
        ObjectNode before = object(StrictJson.parse(semantic(11, 2, false))); before.remove("one_life_terminal");
        ObjectNode after = object(StrictJson.parse(semantic(13, 3, true))); after.remove("one_life_terminal");
        byte[] rawBefore = bytes(before), rawAfter = bytes(after);
        var retained = SuccessionNativeEstate12004.freeze(bytes(root(11, 2, false)), rawBefore);
        var compared = SuccessionNativeEstate12004.reconcile(retained, bytes(root(13, 3, true)), rawAfter);
        assertEquals(SuccessionModel.Verdict.MATCHED, compared.comparison().verdict());
        assertArrayEquals(rawBefore, retained.originalSemantic()); assertArrayEquals(rawAfter, compared.originalSemantic());
        assertFalse(StrictJson.parse(compared.originalSemantic()).has("one_life_terminal"));
        after.putNull("one_life_terminal");
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.reconcile(retained, bytes(root(13, 3, true)), bytes(after)));
        after.remove("one_life_terminal"); after.putNull("one_life_terminal_reason");
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.reconcile(retained, bytes(root(13, 3, true)), bytes(after)));
    }
    @Test void completeSemanticAboveRootBudgetRetainsHistoryNumbersMissingNullAndOriginalBytes() {
        byte[] before = largeSemantic(11, 2, false), after = largeSemantic(13, 3, true);
        assertTrue(before.length > SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(before));
        var frozen = SuccessionNativeEstate12004.freeze(bytes(root(11, 2, false)), before);
        var compared = SuccessionNativeEstate12004.reconcile(frozen, bytes(root(13, 3, true)), after);
        assertEquals(SuccessionModel.Verdict.MATCHED, compared.comparison().verdict());
        assertArrayEquals(before, frozen.originalSemantic()); assertArrayEquals(after, compared.originalSemantic());
        JsonNode decoded = FullJsonTree.parse(frozen.originalSemantic(), FullJsonTree.MAXIMUM_BYTES);
        JsonNode originalHistory = decoded.get("command_history").get(0);
        assertEquals("x".repeat(SuccessionNativeEstate12004.MAX_SOURCE_BYTES + 16), originalHistory.get("raw_history").textValue());
        assertEquals(new BigInteger("90071992547409931234567890"), originalHistory.get("raw_identity").bigIntegerValue());
        assertTrue(originalHistory.get("ratio").isFloatingPointNumber()); assertFalse(originalHistory.get("ratio").isIntegralNumber());
        assertEquals("1.0", originalHistory.get("ratio").asText()); assertEquals(1.0, originalHistory.get("ratio").doubleValue());
        assertEquals("-0.0", originalHistory.get("negative_zero").asText());
        assertEquals(Double.doubleToRawLongBits(-0.0), Double.doubleToRawLongBits(originalHistory.get("negative_zero").doubleValue()));
        assertTrue(originalHistory.get("nullable").isNull()); assertFalse(originalHistory.has("missing"));
        assertFalse(decoded.has("one_life_terminal")); // Missing stays missing in the retained original.
        String digest = frozen.originalSemanticSha256(); before[0] = 0; frozen.originalSemantic()[0] = 0;
        assertEquals(digest, frozen.originalSemanticSha256());
        assertArrayEquals(after, compared.originalSemantic());
    }

    @Test void rawRootOneMiBAndFullSemanticSixtyFourMiBRemainDistinctExplicitDomains() {
        byte[] nativeRoot = bytes(root(11, 2, false)), semantic = semantic(11, 2, false);
        assertEquals(64 * 1024 * 1024, FullJsonTree.MAXIMUM_BYTES);
        assertDoesNotThrow(() -> SuccessionNativeEstate12004.freeze(
                padded(nativeRoot, SuccessionNativeEstate12004.MAX_SOURCE_BYTES), semantic));
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(
                padded(nativeRoot, SuccessionNativeEstate12004.MAX_SOURCE_BYTES + 1), semantic));
        byte[] tooLargeSemantic = padded(semantic, FullJsonTree.MAXIMUM_BYTES + 1);
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(nativeRoot, tooLargeSemantic));
    }

    @Test void completeSemanticStillRejectsWrongConsumedTypesDuplicateKeysTrailingAndInvalidUtf8() {
        byte[] original = largeSemantic(11, 2, false), nativeRoot = bytes(root(11, 2, false));
        for (String token : List.of("true", "11.0", "1e999", "\"11\"", "null")) {
            ObjectNode malformed = object(FullJsonTree.parse(original, FullJsonTree.MAXIMUM_BYTES));
            malformed.set("native_revision", FullJsonTree.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8), FullJsonTree.MAXIMUM_BYTES));
            byte[] raw = FullJsonTree.encode(malformed, FullJsonTree.MAXIMUM_BYTES);
            assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(nativeRoot, raw));
        }
        ObjectNode missing = object(FullJsonTree.parse(original, FullJsonTree.MAXIMUM_BYTES));
        missing.remove("one_life_terminal_reason");
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(nativeRoot,
                FullJsonTree.encode(missing, FullJsonTree.MAXIMUM_BYTES)));
        String text = new String(original, java.nio.charset.StandardCharsets.UTF_8);
        byte[] duplicate = (text.substring(0, text.length() - 1) + ",\"revision\":111}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(nativeRoot, duplicate));
        String overflow = text.replace("\"ratio\":1.0", "\"ratio\":1e999");
        assertNotEquals(text, overflow);
        byte[] opaque = overflow.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var originalToken = SuccessionNativeEstate12004.freeze(nativeRoot, opaque);
        assertArrayEquals(opaque, originalToken.originalSemantic());
        JsonNode hugeRatio = FullJsonTree.parse(originalToken.originalSemantic(), FullJsonTree.MAXIMUM_BYTES)
                .get("command_history").get(0).get("ratio");
        assertTrue(hugeRatio.isFloatingPointNumber()); assertFalse(hugeRatio.isIntegralNumber());
        assertEquals("1e999", hugeRatio.asText());
        byte[] roundTrip = FullJsonTree.encode(FullJsonTree.parse(opaque, FullJsonTree.MAXIMUM_BYTES), FullJsonTree.MAXIMUM_BYTES);
        assertEquals("1e999", FullJsonTree.parse(roundTrip, FullJsonTree.MAXIMUM_BYTES)
                .get("command_history").get(0).get("ratio").asText());
        byte[] trailing = (text + " null").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(nativeRoot, trailing));
        byte[] invalidUtf8 = original.clone(); invalidUtf8[0] = (byte) 0xc3; invalidUtf8[1] = 0x28;
        assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(nativeRoot, invalidUtf8));
    }

    @Test void completeSemanticKeepsConsumedUnsignedRevisionsAboveJavaScriptSafeRange() {
        ObjectNode nativeRoot = root(11, 2, false);
        BigInteger nativeRevision = StrictJson.UINT64_MAX.subtract(BigInteger.ONE);
        nativeRoot.put("snapshot_revision", nativeRevision);
        object(nativeRoot.get("campaign_root_context")).put("snapshot_revision", nativeRevision);
        ObjectNode semantic = object(FullJsonTree.parse(largeSemantic(11, 2, false), FullJsonTree.MAXIMUM_BYTES));
        semantic.put("revision", StrictJson.UINT64_MAX).put("native_revision", nativeRevision);
        var retained = SuccessionNativeEstate12004.freeze(bytes(nativeRoot), FullJsonTree.encode(semantic, FullJsonTree.MAXIMUM_BYTES));
        var decoded = SuccessionCodec.decodeExpectation(retained.wire());
        assertEquals(StrictJson.UINT64_MAX, decoded.binding().frame().revision());
        assertEquals(nativeRevision, decoded.binding().frame().nativeRevision());
    }

    @Test void signedNativeProducerFreezePortNormalizeAndActualFinalFramePreserveSevenRolePairs() {
        int[][] pairs = {{2, 0}, {2, -2}, {2, Integer.MIN_VALUE}, {2, Integer.MAX_VALUE},
                {0, 3}, {-2, 3}, {Integer.MIN_VALUE, 3}};
        for (int[] pair : pairs) {
            int predecessor = pair[0], successor = pair[1];
            ObjectNode before = root(11, predecessor, false);
            ObjectNode nativeRoot = object(before.get("campaign_root_context"));
            nativeRoot.putArray("primary_title_succession_character_ids").add(successor);
            object(nativeRoot.path("held_title_partition").get(0)).put("first_heir_character_id", successor);
            ObjectNode beforeSemantic = object(StrictJson.parse(semantic(11, predecessor, false)));
            beforeSemantic.put("episode_character_id", predecessor);
            byte[] originalBefore = bytes(before), originalSemantic = bytes(beforeSemantic);
            var frozen = SuccessionNativeEstate12004.freeze(originalBefore, originalSemantic);
            assertEquals(predecessor, frozen.expectation().predecessorCharacterId());
            assertEquals(predecessor, frozen.expectation().binding().episodeCharacterId());
            assertEquals(successor, frozen.expectation().expectedSuccessorCharacterId());
            assertArrayEquals(originalBefore, frozen.originalRootResult());
            var current = SuccessionNativeEstate12004.observeCurrentEpisode(originalBefore, originalSemantic);
            assertEquals(predecessor, current.snapshot().actor().characterId());
            assertEquals(predecessor, current.snapshot().episodeCharacterId());

            ObjectNode freezeRequest = StrictJson.object().put("schema", SuccessionConsumerPort.SCHEMA)
                    .put("operation", "freeze").put("episode_run_id", "old-episode")
                    .put("episode_character_id", predecessor);
            freezeRequest.set("turn_bundle", bundle(before, originalSemantic));
            byte[] portFrozen = SuccessionConsumerPort.apply(bytes(freezeRequest));
            assertArrayEquals(frozen.wire(), portFrozen);
            ObjectNode normalize = StrictJson.object().put("schema", SuccessionConsumerPort.SCHEMA).put("operation", "normalize");
            normalize.set("expectation", SuccessionCodec.parse(portFrozen));
            assertArrayEquals(portFrozen, SuccessionConsumerPort.apply(bytes(normalize)));

            ObjectNode afterSemantic = object(StrictJson.parse(semantic(13, successor, true)));
            afterSemantic.put("episode_character_id", predecessor);
            var result = SuccessionNativeEstate12004.reconcile(frozen, bytes(root(13, successor, true)), bytes(afterSemantic));
            assertEquals(SuccessionModel.Verdict.MATCHED, result.comparison().verdict());
            JsonNode wire = SuccessionCodec.parse(result.wire());
            assertEquals(predecessor, wire.path("predecessor_character_id").intValue());
            assertEquals(successor, wire.path("expected_successor_character_id").intValue());
            assertEquals(successor, wire.path("actual_successor_character_id").intValue());
            assertEquals(13, wire.path("successor_binding").path("native_revision").intValue());
        }
    }

    @Test void nativeSuccessionVectorValidatesSignedRolesInEveryPosition() {
        for (int role : new int[] {0, -2, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
            ObjectNode original = root(11, 2, false);
            ((ArrayNode) original.path("campaign_root_context").path("primary_title_succession_character_ids")).add(role);
            var frozen = SuccessionNativeEstate12004.freeze(bytes(original), semantic(11, 2, false));
            assertEquals(3, frozen.expectation().expectedSuccessorCharacterId());
        }
        for (String token : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "2.0", "\"2\"", "null")) {
            JsonNode invalid = FullJsonTree.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8), 32);
            for (int position : new int[] {0, 1}) {
                ObjectNode original = root(11, 2, false);
                ArrayNode heirs = (ArrayNode) original.path("campaign_root_context").path("primary_title_succession_character_ids");
                if (position == 0) {
                    heirs.set(0, invalid);
                    object(original.path("campaign_root_context").path("held_title_partition").get(0)).set("first_heir_character_id", invalid);
                } else { heirs.add(invalid); }
                byte[] raw = FullJsonTree.encode(original, SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
                assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(raw, semantic(11, 2, false)), token + "@" + position);
            }
        }
    }

    @Test void publicFreezePortRejectsSentinelWrongTokensOverflowAndUnsignedAlias() {
        for (String token : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "2.0", "\"2\"", "null")) {
            ObjectNode incoming = StrictJson.object().put("schema", SuccessionConsumerPort.SCHEMA)
                    .put("operation", "freeze").put("episode_run_id", "old-episode");
            incoming.set("turn_bundle", bundle(root(11, 2, false), semantic(11, 2, false)));
            incoming.set("episode_character_id", FullJsonTree.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8), 32));
            byte[] raw = FullJsonTree.encode(incoming, SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
            assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.decodeFreezeRequest(raw), token);
        }
    }

    private static byte[] largeSemantic(int revision, int actor, boolean changed) {
        ObjectNode source = object(FullJsonTree.parse(semantic(revision, actor, changed), FullJsonTree.MAXIMUM_BYTES));
        source.remove("one_life_terminal");
        source.putArray("command_history").addObject().put("raw_history", "x".repeat(SuccessionNativeEstate12004.MAX_SOURCE_BYTES + 16))
                .put("raw_identity", new BigInteger("90071992547409931234567890")).put("ratio", 1.0)
                .put("negative_zero", -0.0).putNull("nullable");
        return FullJsonTree.encode(source, FullJsonTree.MAXIMUM_BYTES);
    }
    private static byte[] padded(byte[] original, int length) {
        byte[] result = Arrays.copyOf(original, length); Arrays.fill(result, original.length, result.length, (byte) ' '); return result;
    }

    private static ObjectNode root(int revision, int actor, boolean after) {
        ObjectNode result = StrictJson.object().put("step", "query-campaign-root-context-v1").put("accepted", true).put("status", "available")
                .put("query_sequence", revision).put("snapshot_revision", revision).put("backend_id", "native-headless");
        ObjectNode root = result.putObject("campaign_root_context").put("schema_version", 1).put("status", "available")
                .put("snapshot_revision", revision).put("date_raw", 100).put("player_character_id", actor).put("player_character_alive", true).putNull("unavailable_reason");
        root.set("primary_title", title(10)); root.putArray("primary_title_succession_character_ids").add(after ? 6 : 3);
        ObjectNode provenance = root.putObject("provenance").put("game_version", "1.20.0.4").put("executable_sha256", SuccessionNativeEstate12004.EXECUTABLE_SHA256)
                .put("backend_id", "ck3-1.20.0.4-native-campaign-root-context-v1").put("held_title_ids_offset", "0x1E0").put("primary_title_rva", "0x289DA10");
        ObjectNode readiness = root.putObject("readiness");
        for (String key : List.of("player_identity_ready", "primary_title_ready", "primary_title_succession_ready", "held_title_partition_ready", "same_frame_ready")) readiness.put(key, true);
        ArrayNode rows = root.putArray("held_title_partition"); rows.add(row(10, after ? 6 : 3, true));
        if (!after) rows.add(row(20, 4, false));
        return result;
    }
    private static ObjectNode title(int id) { return StrictJson.object().put("title_id", id).put("tier_raw", 2).put("tier_key", "county"); }
    private static ObjectNode row(int id, int heir, boolean primary) {
        ObjectNode row = StrictJson.object().put("first_heir_character_id", heir).put("primary", primary).put("capital_province_id", id + 1); row.set("title", title(id)); return row;
    }
    private static byte[] semantic(int revision, int actor, boolean changed) {
        ObjectNode semantic = StrictJson.object().put("snapshot_id", "actual-" + revision).put("revision", revision + 100).put("native_revision", revision)
                .put("date_raw", 100).put("episode_run_id", "old-episode").put("episode_character_id", 2).put("paused", true).put("map_ready", true)
                .put("one_life_terminal", changed).putNull("active_event").putNull("pending_character_interaction");
        if (changed) semantic.put("one_life_terminal_reason", "played_character_changed"); else semantic.putNull("one_life_terminal_reason");
        semantic.putObject("played_character").put("character_id", actor).put("alive", true);
        semantic.putObject("succession_lifecycle").put("lifecycle", "ordinary_campaign_succession"); return bytes(semantic);
    }
    private static ObjectNode bundle(ObjectNode original, byte[] semanticBytes) {
        JsonNode semantic = StrictJson.parse(semanticBytes), root = original.get("campaign_root_context");
        ObjectNode bundle = StrictJson.object().put("schema", "xar.ck3.turn-bundle/v1").put("status", "available");
        ObjectNode binding = bundle.putObject("binding"); for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw")) binding.set(key, semantic.get(key));
        bundle.putObject("ruler_state").put("status", "available").set("value", semantic.get("played_character"));
        ObjectNode succession = bundle.putObject("succession_state").put("status", "available").putObject("value");
        succession.putObject("primary_title_heir_character_id").put("status", "available").set("value", root.path("primary_title_succession_character_ids").get(0));
        ObjectNode partition = succession.putObject("partition").put("status", "available").putObject("value").put("risk_state", "split_successors");
        partition.set("title_heirs", root.get("held_title_partition")); return bundle;
    }
    private static ObjectNode object(JsonNode value) { if (value instanceof ObjectNode object) return object; throw new IllegalArgumentException("object required"); }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value, SuccessionNativeEstate12004.MAX_SOURCE_BYTES); }
}
