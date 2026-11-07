package org.xar.ck3.control.wave3.development.wartimesequencing;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.function.Consumer;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryModel;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryPolicy;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCash;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;

/** Pure SDK DATA only: no PlanningRequest, clocks, permissions, writer, CAS, Native or Game.
 * The complete/packet/envelope/financing fixture is copied from the existing source-owned tests,
 * not linked to or RUN as an old test. Full app/material/cold-consumer custody is a separate unit.
 */
final class ConstructionFullOriginal113SdkTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final JsonNodeFactory N = JsonNodeFactory.instance;
    private static final int FULL = FullJsonTree.MAXIMUM_BYTES;
    private static final String V4 = "1.20.0.4";
    private static final String SHA4 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String DRIVER = "/org/xar/ck3/control/application/checkpoint/encoding102/driver1475.json.gz";

    @Test void smallFactoriesRetainSelectedQuoteAndExactComposedResult() throws Exception {
        ObjectNode input = complete();
        byte[] original = full(input);
        byte[] queryBytes = full(query(input));
        NativeQuote legacyQuote = new NativeQuote(queryBytes);
        NativeQuote fullQuote = NativeQuote.fromFullMaterial(queryBytes);
        assertTrue(legacyQuote.selected().isPresent(), "real exact_ample_threshold must reach SELECTED");
        assertNativeValue(legacyQuote, fullQuote);
        assertArrayEquals(queryBytes, fullQuote.original());
        assertArrayEquals(ConstructionQueryCodec.finalizeObservation(queryBytes),
                ConstructionQueryCodec.finalizeObservation(ConstructionQueryCodec.projectFullMaterialInput(queryBytes)));
        var legacy = new OrdinaryWartimeConstructionCodec.ObservedRequest(original);
        var exact = OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(original);
        Result expected = compose(legacy.input());
        assertEquals(Disposition.QUOTED_CANDIDATE, expected.disposition(), "positive composition must be reached before comparison");
        assertEquals(named("exact_ample_threshold").get("expected"),
                FullJsonTree.parse(WartimeConstructionCodec.encode(WartimeConstructionCash.observe(legacy.input().current())), FULL));
        assertComposedValue(expected, compose(exact.input()));
        assertNativeValue(legacyQuote, exact.input().quoted().orElseThrow().nativeQuote());
        assertArrayEquals(original, exact.original());
        assertArrayEquals(original, full(input));
    }

    @Test void fullOuterAndNestedQuoteRetain139RowSnapshotsAndDefensiveOriginals() throws Exception {
        ObjectNode small = complete();
        NativeQuote smallQuote = new NativeQuote(full(query(small)));
        Result expected = compose(new OrdinaryWartimeConstructionCodec.ObservedRequest(full(small)).input());
        assertTrue(smallQuote.selected().isPresent());
        assertEquals(Disposition.QUOTED_CANDIDATE, expected.disposition());
        ObjectNode input = small.deepCopy();
        ArrayNode history = retainedHistory139();
        int historyBytes = full(history).length;
        assertTrue(historyBytes > 3_000_000 && historyBytes < 4_000_000, "same project 139-row data, not repeated invented rows");
        for (String field : List.of("starting_snapshot", "ending_snapshot")) {
            ObjectNode snapshot = snapshot(query(input), field);
            snapshot.set("native_command_history", history);
            snapshot.set("opaque_full_original113", node("{\"z\":\"first\",\"a\":1.00,\"negative_zero\":-0.0,\"ordered\":[true,null,{\"second\":2,\"first\":1}]}"));
        }
        byte[] original = full(input);
        byte[] nested = full(query(input));
        assertTrue(original.length > 6_000_000 && original.length < 9_000_000);
        assertTrue(nested.length > ConstructionQueryCodec.MAX_BYTES);
        assertThrows(IllegalArgumentException.class, () -> new NativeQuote(nested));
        assertThrows(IllegalArgumentException.class, () -> ConstructionQueryCodec.decode(nested));
        assertThrows(IllegalArgumentException.class, () -> new OrdinaryWartimeConstructionCodec.ObservedRequest(original));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.decode(original));
        byte[] supplied = original.clone();
        var exact = OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(supplied);
        supplied[0] = '[';
        assertArrayEquals(original, exact.original(), "factory must own a clone before deriving typed state");
        byte[] leaked = exact.original();
        leaked[0] = '[';
        assertArrayEquals(original, exact.original(), "outer original getter must not expose its retained array");
        NativeQuote retained = exact.input().quoted().orElseThrow().nativeQuote();
        assertNativeValue(smallQuote, retained);
        assertArrayEquals(nested, retained.original(), "nested quote retains full tree encoding, never the SDK projection");
        byte[] quoteLeak = retained.original();
        quoteLeak[0] = '[';
        assertArrayEquals(nested, retained.original());
        byte[] suppliedQuery = nested.clone();
        NativeQuote direct = NativeQuote.fromFullMaterial(suppliedQuery);
        suppliedQuery[0] = '[';
        assertArrayEquals(nested, direct.original());
        assertNativeValue(smallQuote, direct);
        assertComposedValue(expected, compose(exact.input()));
        JsonNode replayedQuery = FullJsonTree.parse(retained.original(), FULL);
        assertMembers(query(input), replayedQuery);
        for (String field : List.of("starting_snapshot", "ending_snapshot")) {
            assertMembers(query(input).get(field), replayedQuery.get(field));
            assertEquals(139, replayedQuery.get(field).get("native_command_history").size());
            String marker = new String(full(replayedQuery.get(field).get("opaque_full_original113")), StandardCharsets.UTF_8);
            assertTrue(marker.contains("\"a\":1.00"));
            assertTrue(marker.contains("\"negative_zero\":-0.0"));
        }
        assertArrayEquals(full(small.get("cash_input")), full(input.get("cash_input")));
        assertArrayEquals(full(small.get("financing_request")), full(input.get("financing_request")));
        assertArrayEquals(full(query(small).get("native_envelope")), full(query(input).get("native_envelope")));
        assertArrayEquals(original, full(input));
        System.out.println("P113 SDK DATA history_rows=139 outer_original_bytes=" + original.length
                + " nested_original_bytes=" + nested.length + " outer_original_sha256=" + sha(original));
    }

    @Test void closedRootsAndConsumedTokenTypesRetainLegacyRejections() throws Exception {
        List<Consumer<ObjectNode>> malformedQuery = List.of(
                q -> q.put("unknown_root", true), q -> q.remove("expected_revision"),
                q -> q.put("schema", "wrong"), q -> q.putNull("schema"),
                q -> q.put("material_receipt", 1), q -> q.put("wartime_observation", "false"),
                q -> q.set("expected_revision", node("3.0")), q -> q.set("expected_revision", node("3e0")),
                q -> q.set("expected_revision", N.booleanNode(true)),
                q -> ((ObjectNode) q.get("native_envelope")).set("protocol_version", node("1.0")));
        for (Consumer<ObjectNode> mutate : malformedQuery) {
            ObjectNode q = query(complete()).deepCopy();
            mutate.accept(q);
            assertRejectedQuery(q);
        }
        for (String field : List.of("starting_snapshot", "ending_snapshot")) {
            for (JsonNode bad : List.of(N.nullNode(), N.numberNode(7), N.textNode("not-an-object"), N.arrayNode())) {
                ObjectNode q = query(complete()).deepCopy();
                q.set(field, bad);
                assertRejectedQuery(q);
            }
        }
        List<Consumer<ObjectNode>> malformedOuter = List.of(
                input -> input.put("unknown_root", true), input -> input.remove("cash_input"),
                input -> input.put("schema", "wrong"), input -> input.put("stage", "quoted_outlay"),
                input -> input.putNull("quoted_outlay"), input -> input.set("cash_input", N.numberNode(1)));
        for (Consumer<ObjectNode> mutate : malformedOuter) {
            ObjectNode input = complete();
            mutate.accept(input);
            assertRejectedOuter(input);
        }
        for (JsonNode root : List.of(N.nullNode(), N.numberNode(7), N.textNode("root"), N.arrayNode())) {
            byte[] raw = full(root);
            assertThrows(IllegalArgumentException.class, () -> NativeQuote.fromFullMaterial(raw));
            assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(raw));
        }
    }

    @Test void policyRefusalsAndBuildPresenceRetainLegacyMeaning() throws Exception {
        ObjectNode sourceModes = query(complete()).deepCopy();
        sourceModes.put("material_receipt", true).put("wartime_observation", true);
        NativeQuote modes = assertEquivalentQuery(sourceModes);
        assertFalse(modes.selected().isPresent());
        var refused = assertInstanceOf(ConstructionQueryModel.Rejected.class,
                ConstructionQueryPolicy.finalizeObservation(modes.observation()));
        assertEquals(ConstructionQueryModel.Rejection.SOURCE_MODES, refused.reason());
        ObjectNode wrongRequest = query(complete()).deepCopy();
        ((ObjectNode) wrongRequest.get("native_envelope")).put("request_id", "other-query");
        assertFalse(assertEquivalentQuery(wrongRequest).selected().isPresent());
        ObjectNode drift = query(complete()).deepCopy();
        snapshot(drift, "ending_snapshot").put("episode_run_id", "other-episode");
        assertFalse(assertEquivalentQuery(drift).selected().isPresent());
        for (boolean presentNull : List.of(false, true)) {
            ObjectNode q = query(complete()).deepCopy();
            if (presentNull) snapshot(q, "starting_snapshot").putNull("active_wars");
            else snapshot(q, "starting_snapshot").remove("active_wars");
            assertFalse(assertEquivalentQuery(q).selected().isPresent());
        }
        for (String field : List.of("expected_ck3_version", "expected_ck3_sha256")) {
            ObjectNode q = query(complete()).deepCopy();
            ObjectNode hello = snapshot(q, "starting_snapshot").withObject("/diagnostics/hello");
            hello.put("game_version", V4).put("executable_sha256", SHA4).putNull(field);
            assertRejectedQuery(q); // has(expected:null) must not silently use a valid fallback.
        }
        ObjectNode fallback = query(complete()).deepCopy();
        ObjectNode hello = snapshot(fallback, "starting_snapshot").withObject("/diagnostics/hello");
        hello.remove(List.of("expected_ck3_version", "expected_ck3_sha256"));
        hello.put("game_version", V4).put("executable_sha256", SHA4);
        NativeQuote admittedFallback = assertEquivalentQuery(fallback);
        assertTrue(admittedFallback.selected().isPresent());
        assertEquals("1.20.0.4", admittedFallback.observation().build().build().wire());
        for (JsonNode diagnostic : List.of(N.nullNode(), N.numberNode(1), N.textNode("not-object"), N.arrayNode(), N.objectNode())) {
            ObjectNode q = query(complete()).deepCopy();
            snapshot(q, "starting_snapshot").set("diagnostics", diagnostic);
            NativeQuote result = assertEquivalentQuery(q);
            assertEquals("1.19.0.6", result.observation().build().build().wire());
        }
        for (JsonNode malformedHello : List.of(N.nullNode(), N.numberNode(1), N.textNode("not-object"), N.arrayNode())) {
            ObjectNode q = query(complete()).deepCopy();
            snapshot(q, "starting_snapshot").withObject("/diagnostics").set("hello", malformedHello);
            NativeQuote result = assertEquivalentQuery(q);
            assertEquals("1.19.0.6", result.observation().build().build().wire());
        }
    }

    @Test void fullFactoriesDoNotProjectOtherLanesOrRaiseLegacySdkCaps() throws Exception {
        assertEquals(262_144, ConstructionQueryCodec.MAX_BYTES);
        assertEquals(262_144, OrdinaryWartimeConstructionCodec.MAX_BYTES);
        String oversized = "x".repeat(270_000);
        ObjectNode nativeEnvelope = query(complete()).deepCopy();
        ((ObjectNode) nativeEnvelope.get("native_envelope")).put("retained_native_unknown", oversized);
        assertRejectedQuery(nativeEnvelope);
        ObjectNode played = query(complete()).deepCopy();
        snapshot(played, "starting_snapshot").withObject("/played_character").put("retained_member", oversized);
        assertRejectedQuery(played);
        ObjectNode armies = query(complete()).deepCopy();
        snapshot(armies, "starting_snapshot").putArray("player_armies").addObject().put("retained_member", oversized);
        assertRejectedQuery(armies);
        ObjectNode wars = query(complete()).deepCopy();
        snapshot(wars, "starting_snapshot").putArray("active_wars").addObject().put("retained_member", oversized);
        assertRejectedQuery(wars);
        ObjectNode fullCash = complete();
        fullCash.withObject("/cash_input/snapshot").put("retained_cash_snapshot", oversized);
        assertRejectedOuter(fullCash);
        ObjectNode fullFinance = complete();
        fullFinance.withObject("/financing_request/gap_request/snapshot").put("retained_financing_snapshot", oversized);
        assertRejectedOuter(fullFinance);
        assertThrows(IllegalArgumentException.class, () -> NativeQuote.fromFullMaterial(new byte[0]));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(new byte[0]));
    }

    private static void assertNativeValue(NativeQuote expected, NativeQuote actual) {
        assertEquals(expected.observation(), actual.observation());
        assertEquals(expected.constructionKind(), actual.constructionKind());
        assertEquals(expected.selected().isPresent(), actual.selected().isPresent());
        if (expected.selected().isPresent()) {
            var before = expected.selected().orElseThrow();
            var after = actual.selected().orElseThrow();
            assertEquals(before.candidate(), after.candidate());
            assertEquals(before.sourceFrame(), after.sourceFrame());
            assertArrayEquals(before.original().bytes(), after.original().bytes());
        }
    }
    private static void assertComposedValue(Result expected, Result actual) {
        assertEquals(expected.originalSelection(), actual.originalSelection());
        assertEquals(expected.stage(), actual.stage());
        assertEquals(expected.disposition(), actual.disposition());
        assertEquals(expected.reason(), actual.reason());
        assertEquals(expected.cash().status(), actual.cash().status());
        assertEquals(expected.financing().status(), actual.financing().status());
        assertFalse(actual.canSubmitAction());
        assertArrayEquals(OrdinaryWartimeConstructionCodec.encode(expected), OrdinaryWartimeConstructionCodec.encode(actual));
    }
    private static NativeQuote assertEquivalentQuery(ObjectNode query) {
        byte[] raw = full(query);
        NativeQuote expected = new NativeQuote(raw);
        NativeQuote actual = NativeQuote.fromFullMaterial(raw);
        assertNativeValue(expected, actual);
        assertArrayEquals(raw, actual.original());
        return actual;
    }
    private static void assertRejectedQuery(ObjectNode query) {
        byte[] raw = full(query);
        assertThrows(IllegalArgumentException.class, () -> new NativeQuote(raw));
        assertThrows(IllegalArgumentException.class, () -> NativeQuote.fromFullMaterial(raw));
    }
    private static void assertRejectedOuter(ObjectNode input) {
        byte[] raw = full(input);
        assertThrows(IllegalArgumentException.class, () -> new OrdinaryWartimeConstructionCodec.ObservedRequest(raw));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(raw));
    }
    private static void assertMembers(JsonNode expected, JsonNode retained) {
        assertTrue(expected.isObject());
        assertTrue(retained.isObject());
        var expectedNames = new ArrayList<String>();
        var retainedNames = new ArrayList<String>();
        expected.properties().forEach(entry -> expectedNames.add(entry.getKey()));
        retained.properties().forEach(entry -> retainedNames.add(entry.getKey()));
        assertEquals(expectedNames, retainedNames, "every object member and its order must remain present");
        for (var entry : expected.properties()) assertArrayEquals(full(entry.getValue()), full(retained.get(entry.getKey())), entry.getKey());
    }
    private static ObjectNode query(ObjectNode input) { return (ObjectNode) input.get("quoted_outlay").get("query_observation"); }
    private static ObjectNode snapshot(ObjectNode query, String field) { return (ObjectNode) query.get(field); }
    private static JsonNode node(String json) { return FullJsonTree.parse(json.getBytes(StandardCharsets.UTF_8), FULL); }
    private static byte[] full(JsonNode node) { return FullJsonTree.encode(node, FULL); }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (java.security.NoSuchAlgorithmException failure) { throw new AssertionError(failure); }
    }
    private static byte[] resource(String path, int length, String expectedSha) throws IOException {
        byte[] bytes;
        try (var input = ConstructionFullOriginal113SdkTest.class.getResourceAsStream(path)) {
            if (input == null) throw new IOException("required unchanged DATA missing: " + path);
            bytes = input.readNBytes(length + 1);
        }
        assertEquals(length, bytes.length, path);
        assertEquals(expectedSha, sha(bytes), path);
        return bytes;
    }
    private static byte[] gunzip(byte[] bytes, int maximum) throws IOException {
        try (var input = new GZIPInputStream(new ByteArrayInputStream(bytes))) {
            byte[] raw = input.readNBytes(maximum + 1);
            assertTrue(raw.length <= maximum, "finite retained DATA inflation budget");
            return raw;
        }
    }
    private static JsonNode named(String name) throws IOException {
        byte[] compressed = resource("/m4producer/wartime-original02.json.gz", 6379,
                "4b3cf840085e5f3d53e290b4ea862e1357a3341a55180ff3670675caa5f6a585");
        JsonNode corpus = FullJsonTree.parse(gunzip(compressed, 524_288), FULL);
        assertEquals(31, corpus.get("cases").size());
        for (JsonNode row : corpus.get("cases")) if (name.equals(row.get("name").textValue())) return row;
        throw new IOException("required original vector absent: " + name);
    }
    private static ArrayNode retainedHistory139() throws Exception {
        byte[] compressed = resource(DRIVER, 328918, "0d4181fca4a76f55025ed6080b277877ef6a9da1b62ce6cbc11f9e1e97226184");
        var driver = DriverStateSnapshot.decodeComplete(gunzip(compressed, 8_388_608));
        assertTrue(driver.commandHistory().size() >= 139);
        ArrayNode rows = JSON.createArrayNode();
        for (int index = 0; index < 139; index++) rows.add(FullJsonTree.parse(driver.commandHistory().get(index).originalRow().json(), FULL));
        assertEquals(139, rows.size());
        return rows;
    }

    // Finite pure fixture copied from the two existing tests named in SOURCE-READY-DRAFT01.json.
    private static ObjectNode complete() throws Exception {
        ObjectNode input = (ObjectNode) named("exact_ample_threshold").get("request").deepCopy();
        ObjectNode request = envelope(input, true); ObjectNode outlay = request.withObject("/quoted_outlay");
        ObjectNode nativeInput = outlay.putObject("query_observation"); nativeInput.put("schema", "xar.construction-query-observation-input.v1");
        nativeInput.set("starting_snapshot", input.get("snapshot").deepCopy()); nativeInput.set("ending_snapshot", input.get("snapshot").deepCopy());
        nativeInput.put("expected_revision", 3); nativeInput.put("native_query_request_id", "new-controlled-query");
        nativeInput.put("material_receipt", false); nativeInput.put("wartime_observation", false);
        ObjectNode nativeEnvelope = nativeInput.putObject("native_envelope"); nativeEnvelope.put("type", "command_result");
        nativeEnvelope.put("protocol_version", 1); nativeEnvelope.put("request_id", "new-controlled-query"); nativeEnvelope.put("ok", true);
        ObjectNode result = nativeEnvelope.putObject("result"); result.put("step", "g2_player_construction_view_probe_v1"); result.put("accepted", true);
        ObjectNode probe = result.putObject("private_probe"); probe.put("advertised", false); probe.put("snapshot_revision", 3); probe.put("date_raw", 53288472); probe.put("proof_epoch", 1);
        ObjectNode world = probe.putObject("player_world_building_sources"); world.put("status", "source_available"); world.put("snapshot_revision", 3); world.put("date_raw", 53288472); world.put("player_character_id", 29829);
        world.put("native_final_legality_evaluated", true); world.put("native_cost_evaluated", true); world.put("player_gold_raw", 100_000_000);
        // The existing authored selector requires an observed idle barony, not an absent construction inventory.
        ObjectNode idle = world.putArray("active_constructions").addObject();
        idle.put("barony_title_id", 2103); idle.put("province_id", 2635); idle.put("active", false);
        world.put("completed_buildings_observed", true); world.putArray("completed_buildings"); world.put("positive_income_coverage_complete", true);
        ObjectNode sample = world.putArray("legal_samples").addObject(); sample.put("barony_title_id", 2103); sample.put("province_id", 2635);
        sample.put("building_type_id", 11); sample.put("slot_index", 0); sample.put("building_key", "farm_estates_01"); sample.put("native_cost_observed", true);
        var costs = sample.putArray("cost_raw_native"); costs.add(23_000_000); for (int i = 1; i < 10; i++) costs.add(0);
        ObjectNode observed = outlay.putObject("cash_observation"); observed.put("kind", "observed"); observed.put("reserve_gold_raw", 3_000_000); observed.set("cash", packet(input.get("snapshot")));
        return request;
    }
    private static ObjectNode packet(JsonNode snapshot) {
        ObjectNode cash = JSON.createObjectNode(); cash.put("schema", "xar.ck3.war-cash-current-resources.v1"); cash.put("read_only", true);
        cash.put("game_version", "1.20.0.4"); cash.put("executable_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        // The old source-owned packet fixture predates mandatory monthly-source metadata.
        // Complete explicit SOFTWARE DATA from this same unchanged original snapshot.
        cash.set("played_character_id", snapshot.get("played_character").get("character_id"));
        cash.set("snapshot_revision", snapshot.get("native_revision")); cash.set("date_raw", snapshot.get("date_raw"));
        cash.put("advertised", false).put("formal_action_ready", false).put("status", "available");
        ArrayNode wars = cash.putArray("active_war_ids");
        for (JsonNode war : snapshot.get("active_wars")) wars.add(war.get("war_id"));
        ArrayNode armies = cash.putArray("player_army_ids");
        for (JsonNode army : snapshot.get("player_armies")) armies.add(army.get("army_id"));
        cash.put("queried_snapshot_id", "native:3"); cash.put("queried_revision", 3); cash.put("queried_native_revision", 3);
        String[] fields = {"current_treasury", "player_monthly_gross_income", "player_monthly_total_expenses", "player_monthly_net_income"};
        long[] amounts = {100_000_000, 800_000, 1_000_000, -200_000};
        for (int i = 0; i < fields.length; i++) cash.putObject(fields[i]).put("raw", amounts[i]).put("scale", 100000);
        ObjectNode semantics = cash.putObject("monthly_income_semantics"); semantics.put("version", "ck3-1.20.0.4-native-income-minus-total-expenses-v2");
        semantics.put("time_basis", "month"); semantics.put("source_scope", "played_character_personal_gold"); semantics.put("income_source", "native_character_monthly_gold_income");
        semantics.put("expense_source", "native_character_monthly_total_gold_expenses"); semantics.put("military_expenses_included", true);
        ObjectNode readiness = cash.putObject("readiness"); for (String flag : List.of("current_treasury_ready", "monthly_gross_income_ready", "monthly_total_expenses_ready", "monthly_net_income_ready", "current_military_expenses_ready", "all_raised_military_expenses_ready", "same_frame_ready")) readiness.put(flag, true);
        ObjectNode military = cash.putObject("military_expenses");
        for (String kind : List.of("current", "all_raised")) {
            int cost = kind.equals("current") ? 500_000 : 800_000; ObjectNode row = military.putObject(kind); row.put("status", "available"); row.put("gold_raw", cost);
            row.set("owner_character_id", cash.get("played_character_id"));
            row.put("resource_id", cash.get("played_character_id").bigIntegerValue().toString());
            row.set("war_ids", wars.deepCopy()); row.put("raw_scale", 100000);
            row.put("time_basis", "month").put("source_scope", "actor_owned_military_once_across_all_wars");
            row.put("future_war_cost_upper_ready", false).put("treasury_raw", 0);
            row.put("resource_kind", kind);
            var vector = row.putArray("resource_raw_native"); vector.add(cost); for (int i = 1; i < 10; i++) vector.add(0);
        }
        // Use the existing normalizer against the complete original snapshot, not a projected cash role.
        return (ObjectNode) FullJsonTree.parse(RawCashCodec.normalize(full(cash), full(snapshot)).toJson(), FULL);
    }
    private static ObjectNode envelope(JsonNode cashInput, boolean quoted) {
        ObjectNode result = JSON.createObjectNode(); result.put("schema", OrdinaryWartimeConstructionCodec.SCHEMA);
        result.put("stage", quoted ? "QUOTED_OUTLAY" : "BEFORE_OPTIONAL_QUERY"); result.put("original_selected_step", "life-advance");
        result.putNull("original_phase");
        result.put("opportunity", "ORDINARY_ADVANCE"); result.set("cash_input", cashInput.deepCopy()); result.putNull("financing_request");
        if (quoted) result.putObject("quoted_outlay"); else result.putNull("quoted_outlay");
        attachCurrentFinancing(result); return result;
    }

    private static void attachCurrentFinancing(ObjectNode request) {
        ObjectNode financing = request.putObject("financing_request");
        financing.put("schema", "xar.emergency-financing-assessment.request.v1");
        ObjectNode gap = financing.putObject("gap_request"); gap.put("schema", "xar.war-financing-capability-gap.request.v1");
        gap.set("snapshot", request.path("cash_input").path("snapshot").deepCopy());
        gap.putNull("priority"); gap.putNull("root"); gap.putNull("construction_ledger"); gap.putNull("bridge_capabilities");
        financing.putNull("loan_request"); financing.putObject("pending_observation").put("status", "no_pending_action");
    }
}
