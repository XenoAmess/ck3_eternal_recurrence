package org.xar.ck3.control.wave2.development.constructionscene;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneConsumer.*;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.*;

final class ConstructionScenePolicyTest {
    private static final String BASE = "{\"paused\":true,\"active_wars\":[],\"played_character\":{\"character_id\":29829},"
            + "\"native_revision\":3,\"revision\":3,\"snapshot_id\":\"native:3\",\"date_raw\":53178312}";
    private static final String ROOT = "{\"command\":\"query-campaign-root-context-v1\",\"ok\":true,\"result\":{\"campaign_root_context\":{"
            + "\"status\":\"available\",\"snapshot_revision\":3,\"date_raw\":53178312,\"player_character_id\":29829,"
            + "\"government\":{\"key\":\"feudal_government\",\"flags\":[\"government_is_feudal\"]}}}}";

    @TestFactory
    Stream<DynamicTest> actualOriginalProducerDifferentialAndOutputRoundTrip() throws IOException {
        JsonNode golden = golden(); assertEquals(64, golden.get("cases").size());
        return StreamSupport.stream(golden.get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            byte[] raw = utf8(row.get("input_json").textValue());
            boolean scene = row.get("kind").textValue().equals("scene");
            if (row.get("java_strict_reject").booleanValue()) {
                if (scene) { assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.scope(raw)); }
                else { assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.clanCashReason(raw)); }
                return;
            }
            byte[] actual = scene ? ConstructionSceneCodec.scope(raw) : ConstructionSceneCodec.clanCashReason(raw);
            assertEquals(row.get("expected"), StrictJson.parse(actual));
            if (scene) {
                Scope value = ConstructionScenePolicy.scope(ConstructionSceneCodec.decodeScene(raw));
                assertEquals(value, ConstructionSceneCodec.decodeScope(actual));
                SceneInput input = ConstructionSceneCodec.decodeScene(raw);
                assertEquals(input, ConstructionSceneCodec.decodeScene(ConstructionSceneCodec.encodeScene(input)));
                assertEquals(row.get("feudal_delegate_expected"), StrictJson.parse(ConstructionSceneCodec.encodeRootScope(
                        ConstructionScenePolicy.sameFrameRootScope(ConstructionSceneCodec.decodeScene(raw), false, true))));
                if (!row.get("expected").path("government_key").asText().equals("clan_government")) {
                    assertEquals(row.get("feudal_delegate_expected"), StrictJson.parse(actual));
                }
            } else {
                CashFrameResult value = ConstructionScenePolicy.clanCashFrame(ConstructionSceneCodec.decodeCash(raw));
                assertEquals(value, ConstructionSceneCodec.decodeCashResult(actual));
            }
        }));
    }

    @TestFactory
    Stream<DynamicTest> followsTheActualConstructionPlannerConsumerScopeBranches() throws IOException {
        JsonNode captured = golden();
        boolean referenceV2 = referenceCaptureV2(captured, "xar.construction-scene-original-producer-golden");
        return StreamSupport.stream(captured.get("consumer_cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            JsonNode selected = referenceV2 ? row.path("original_scope_prefix_result").path("plan") : row;
            if (referenceV2) { assertEquals(0, row.get("native_queries_executed").intValue()); }
            Scope scope = ConstructionScenePolicy.scope(ConstructionSceneCodec.decodeScene(utf8(row.get("scene_input_json").textValue())));
            ScopeDirective result = ConstructionSceneConsumer.afterScope(scope, false, row.get("root_query_available").booleanValue(), "1.20.0.4");
            switch (result) {
                case QueryRoot query -> {
                    assertEquals(selected.get("selected_step").textValue(), query.selectedStep()); assertEquals(selected.get("phase").textValue(), query.phase());
                    if (!referenceV2) { assertEquals(0, row.get("requests").size()); }
                }
                case OptionalSpendDeferred deferred -> {
                    assertEquals((referenceV2 ? selected.get("construction_spending_deferred_v1") : selected.get("deferred")).get("reason").textValue(), deferred.reason());
                    assertFalse((referenceV2 ? selected.get("construction_spending_deferred_v1") : selected.get("deferred")).get("business_submission").booleanValue());
                    assertEquals("life-advance", selected.get("selected_step").textValue()); if (!referenceV2) { assertEquals(0, row.get("requests").size()); }
                }
                case PreserveBaseline ignored -> {
                    assertEquals("life-advance", selected.get("selected_step").textValue()); if (referenceV2) { assertFalse(selected.has("phase")); } else { assertTrue(selected.get("phase").isNull()); }
                    if (!referenceV2) { assertEquals(0, row.get("requests").size()); }
                }
                case ReadCurrentCash cash -> {
                    assertInstanceOf(Admitted.class, cash.scene());
                    if (referenceV2) { assertTrue(row.get("original_scope_prefix_result").isNull()); }
                    else {
                        assertTrue(StreamSupport.stream(row.get("requests").spliterator(), false)
                                .anyMatch(value -> value.textValue().equals("g2_player_construction_view_probe_v1")));
                    }
                }
                case PrewarUnchanged ignored -> throw new IllegalStateException("ordinary captured consumer cannot take prewar branch");
            }
        }));
    }

    @Test
    void requiresActualGoldenSourceIdentityAndTheExistingTenCaseCompound() throws IOException {
        JsonNode root = golden();
        boolean referenceV2 = referenceCaptureV2(root, "xar.construction-scene-original-producer-golden");
        assertEquals("xenoamess-full-tower-eb9d2c1186", root.get("machine_id").textValue());
        StrictJson.utc(root.get("observed_at_utc").textValue());
        assertEquals("291061fe162835794b38baca35d8ccacc06f0b091d88a3a6268dcb80665cf1a0", root.get("source_refs").get(0).get("sha256").textValue());
        assertEquals("d971e1737acd5654a6fdd9c7219a3982a6bce3de44b0c95bc0fac735922b7df2", root.get("source_refs").get(1).get("sha256").textValue());
        assertEquals("90ff70251640abd243bea7a0194f057ab80b719899569e4ca3feaf53c29b9e3e", root.get("source_refs").get(2).get("sha256").textValue());
        if (referenceV2) {
            requiresActualHostModule(root, "existing_compound", "test_clan_construction_scope_cash_compound_v1.py");
            assertEquals(10, root.get("existing_compound").get("declared_scenarios").intValue());
        } else {
            assertEquals(10, root.get("existing_compound").get("cases").intValue()); assertTrue(root.get("existing_compound").get("completed").booleanValue());
        }
        assertEquals(5, root.get("consumer_cases").size());
    }

    @Test
    void rejectsOriginalRawFloatExponentBooleanAndStringTokensWithoutTreeReencoding() {
        for (String token : List.of("3.0", "3e0", "true", "\"3\"")) {
            assertThrows(IllegalArgumentException.class, () -> scope(BASE.replace("\"native_revision\":3", "\"native_revision\":" + token), ROOT), token);
            assertThrows(IllegalArgumentException.class, () -> scope(BASE, ROOT.replace("\"snapshot_revision\":3", "\"snapshot_revision\":" + token)), token);
        }
        for (String token : List.of("29829.0", "29829e0", "true", "\"29829\"")) {
            assertThrows(IllegalArgumentException.class, () -> scope(BASE.replace("\"character_id\":29829", "\"character_id\":" + token), ROOT), token);
            assertThrows(IllegalArgumentException.class, () -> scope(BASE, ROOT.replace("\"player_character_id\":29829", "\"player_character_id\":" + token)), token);
        }
        assertThrows(IllegalArgumentException.class, () -> scope(BASE.replace("\"date_raw\":53178312", "\"date_raw\":true"), ROOT));
        assertThrows(IllegalArgumentException.class, () -> scope(BASE.replace("\"paused\":true", "\"paused\":1"), ROOT));
    }

    @Test
    void preservesMissingNullAndEmptyWithoutMakingSdkContainersExact() {
        SceneInput missing = ConstructionSceneCodec.decodeScene(request("{}", ""));
        SceneInput nil = ConstructionSceneCodec.decodeScene(request("{\"active_wars\":null}", ""));
        SceneInput empty = ConstructionSceneCodec.decodeScene(request("{\"active_wars\":[]}", ""));
        assertEquals(Presence.MISSING, missing.snapshot().activeWarCount().presence());
        assertEquals(Presence.NULL, nil.snapshot().activeWarCount().presence());
        assertEquals(Field.of(0), empty.snapshot().activeWarCount()); assertNotEquals(missing, nil); assertNotEquals(nil, empty);
        String snapshot = BASE.substring(0, BASE.length() - 1) + ",\"sdk_extension\":{\"unconsumed_float\":1.25}}";
        assertInstanceOf(Admitted.class, scope(snapshot, ROOT));
        assertInstanceOf(Unavailable.class, scope(BASE, ROOT.replace("\"government\":{\"key\":\"feudal_government\",\"flags\":[\"government_is_feudal\"]}", "\"government\":null")));
    }

    @Test
    void validatesNativeWidthsAndRetainsTheWholeUnsignedRevision() {
        String maximum = "18446744073709551615";
        Scope admitted = scope(BASE.replace("\"native_revision\":3", "\"native_revision\":" + maximum)
                .replace("native:3", "native:" + maximum), ROOT.replace("\"snapshot_revision\":3", "\"snapshot_revision\":" + maximum));
        assertEquals(new BigInteger(maximum), assertInstanceOf(Admitted.class, admitted).revision());
        assertEquals(admitted, ConstructionSceneCodec.decodeScope(ConstructionSceneCodec.encodeScope(admitted)));
        assertInstanceOf(Unavailable.class, scope(BASE.replace("\"character_id\":29829", "\"character_id\":2147483648"), ROOT));
        assertInstanceOf(Unavailable.class, scope(BASE.replace("\"native_revision\":3", "\"native_revision\":18446744073709551616"), ROOT));
        assertInstanceOf(Unavailable.class, scope(BASE.replace("\"date_raw\":53178312", "\"date_raw\":2147483648"), ROOT));
    }

    @Test
    void rejectsMalformedWrappersOutputsAndBytes() {
        assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.decodeScene(utf8("{\"schema\":\"xar.construction-scene-input.v1\",\"schema\":\"xar.construction-scene-input.v1\",\"snapshot\":{},\"history\":[]}")));
        assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.decodeScene(utf8("{} {}")));
        assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.decodeScene(new byte[] {(byte) 0xC3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.decodeScene(new byte[ConstructionSceneCodec.MAX_BYTES + 1]));
        assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.decodeScene(utf8("{\"schema\":\"xar.construction-scene-input.v1\",\"snapshot\":{},\"history\":[],\"extra\":true}")));
        assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.decodeScope(utf8("{\"status\":\"admitted\",\"government_key\":\"tribal_government\"}")));
        assertThrows(IllegalArgumentException.class, () -> ConstructionSceneCodec.decodeCashResult(utf8("{\"reason\":\"GREEN\"}")));
    }

    @Test
    void defensivelyCopiesHistoryAndGovernmentFlagsAndValidatesDirectConstruction() {
        ArrayList<String> flags = new ArrayList<>(List.of("government_is_clan"));
        GovernmentObservation government = new GovernmentObservation(Field.of("clan_government"), Field.of(flags));
        flags.clear(); assertEquals(List.of("government_is_clan"), government.flags().value());
        assertThrows(UnsupportedOperationException.class, () -> government.flags().value().clear());
        ArrayList<HistoryRow> history = new ArrayList<>(ConstructionSceneCodec.decodeScene(request(BASE, ROOT)).history());
        SceneInput input = new SceneInput(ConstructionSceneCodec.decodeScene(request(BASE, ROOT)).snapshot(), history);
        history.clear(); assertEquals(1, input.history().size()); assertThrows(UnsupportedOperationException.class, () -> input.history().clear());
        assertThrows(IllegalArgumentException.class, () -> new Field<String>(Presence.MISSING, "invented"));
        assertThrows(IllegalArgumentException.class, () -> new Admitted(true, Government.CLAN, BigInteger.ONE, BigInteger.ONE, Field.nil()));
        assertThrows(IllegalArgumentException.class, () -> new Admitted(true, Government.FEUDAL, BigInteger.ZERO, BigInteger.ONE, Field.nil()));
    }

    @Test
    void consumerKeepsClanVersionCashAndPrewarGuardsWithoutActionAuthority() {
        Admitted feudal = assertInstanceOf(Admitted.class, scope(BASE, ROOT));
        Admitted clan = new Admitted(true, Government.CLAN, BigInteger.valueOf(3), BigInteger.valueOf(29829), Field.missing());
        assertInstanceOf(PreserveBaseline.class, ConstructionSceneConsumer.afterScope(clan, false, true, "1.20.1"));
        assertInstanceOf(ReadCurrentCash.class, ConstructionSceneConsumer.afterScope(clan, false, true, "1.20.0.4"));
        assertEquals(new PrewarUnchanged("feudal_root_query_unavailable"), ConstructionSceneConsumer.afterScope(new RootQueryNeeded(true), true, false, "1.20.0.4"));
        assertEquals(new PrewarUnchanged("scope_outside_scene"), ConstructionSceneConsumer.afterScope(new OutsideScene(true), true, true, "1.20.0.4"));
        CashFrameDeferred unknown = new CashFrameDeferred(CashReason.NET_UNOBSERVED);
        assertInstanceOf(ClanObservationDeferred.class, ConstructionSceneConsumer.afterCash(clan, unknown));
        assertInstanceOf(ReadNativeQuote.class, ConstructionSceneConsumer.afterCash(feudal, unknown));
        assertInstanceOf(ReadNativeQuote.class, ConstructionSceneConsumer.afterCash(clan, new CashFrameObserved()));
    }

    @Test
    void sharedRootHelperRetainsPeaceOrderingAndGenericPerkGovernment() {
        SceneInput war = ConstructionSceneCodec.decodeScene(request(BASE.replace("\"active_wars\":[]", "\"active_wars\":[{}]")
                .replace("\"native_revision\":3", "\"native_revision\":0"), ROOT));
        assertEquals(RootScopeStatus.OUTSIDE_SCENE, ConstructionScenePolicy.sameFrameRootScope(war, true, true).status());
        assertEquals(RootScopeStatus.SCOPE_UNAVAILABLE, ConstructionScenePolicy.sameFrameRootScope(war, false, true).status());
        SceneInput clan = ConstructionSceneCodec.decodeScene(request(BASE, ROOT.replace("feudal_government", "clan_government").replace("government_is_feudal", "government_is_clan")));
        assertEquals(RootScopeStatus.OUTSIDE_SCENE, ConstructionScenePolicy.sameFrameRootScope(clan, false, true).status());
        RootScope generic = ConstructionScenePolicy.sameFrameRootScope(clan, false, false);
        assertEquals(RootScopeStatus.ADMITTED, generic.status()); assertEquals("clan_government", generic.governmentKey());
        assertEquals(Presence.NULL, generic.collectTaxesActive().presence());
    }

    private static Scope scope(String snapshot, String root) { return ConstructionScenePolicy.scope(ConstructionSceneCodec.decodeScene(request(snapshot, root))); }
    private static byte[] request(String snapshot, String root) {
        return utf8("{\"schema\":\"xar.construction-scene-input.v1\",\"snapshot\":" + snapshot + ",\"history\":[" + root + "]}");
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden() throws IOException {
        try (InputStream input = ConstructionScenePolicyTest.class.getResourceAsStream("/constructionscene/original-producer-golden-v1.json")) {
            if (input == null) { throw new IOException("required actual original producer golden unavailable; no capture fallback or skip"); }
            return StrictJson.parse(input.readAllBytes(), 90_000);
        }
    }
    private static boolean referenceCaptureV2(JsonNode root, String baseSchema) {
        String schema = root.path("schema").asText();
        if ((baseSchema + ".v1").equals(schema)) { return false; }
        assertEquals(baseSchema + ".v2", schema, "unsupported reference capture version");
        assertEquals("REFERENCE_ORACLE", root.path("producer_role").asText());
        assertEquals("REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE", root.path("current_consumer_validation").asText());
        return true;
    }

    private static void requiresActualHostModule(JsonNode root, String field, String module) {
        JsonNode evidence = root.path(field);
        assertTrue(evidence.isObject());
        assertEquals("NOT_EXECUTED_REFERENCE_CAPTURE", evidence.path("status").asText());
        assertEquals(1, evidence.path("required_actual_host_modules").size());
        assertEquals(module, evidence.path("required_actual_host_modules").get(0).asText());
        for (String oldCredit : new String[]{"completed", "run", "failures", "errors", "skipped"}) {
            assertFalse(evidence.has(oldCredit), "reference producer cannot claim a current consumer run");
        }
    }

}
