package org.xar.ck3.control.planning.warquerycadence;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class WarQueryCadenceTest {
    private record Vector(String name, ObjectNode input) { }

    @Test void originalProducerGoldenIncludesBothActualWarsAndAllBranches() throws Exception {
        JsonNode golden = resource("producer-golden.json");
        assertEquals("xar.ck3.war-query-cadence-golden/v1", golden.get("schema").textValue());
        assertEquals(7, golden.get("original_test_count").intValue());
        assertEquals(0, golden.get("original_skipped").intValue());
        assertNotNull(golden.get("machine_id"));
        List<Vector> vectors = vectors(); assertEquals(vectors.size(), golden.get("cases").size());
        for (int index = 0; index < vectors.size(); index++) {
            Vector vector = vectors.get(index); JsonNode expected = golden.get("cases").get(index);
            assertEquals(vector.name(), expected.get("name").textValue());
            byte[] input = StrictJson.canonical(vector.input());
            assertEquals(expected.get("input_sha256").textValue(), sha(input), vector.name() + " exact producer input");
            byte[] actual = WarQueryCadenceCodec.encodeDefer(WarQueryCadence.evaluate(WarQueryCadenceCodec.decode(input)));
            assertEquals(expected.get("expected"), StrictJson.parse(actual), vector.name());
        }
    }

    @Test void wireAndImmutableModelRoundTripPreserveEverySchedulingDecision() throws Exception {
        for (Vector vector : vectors()) {
            var request = WarQueryCadenceCodec.decode(StrictJson.canonical(vector.input()));
            var restored = WarQueryCadenceCodec.decode(WarQueryCadenceCodec.encodeRequest(request));
            assertEquals(request, restored, vector.name());
            assertEquals(WarQueryCadence.evaluate(request), WarQueryCadence.evaluate(restored), vector.name());
            assertThrows(UnsupportedOperationException.class, () -> request.activeWars().clear());
            assertThrows(UnsupportedOperationException.class, () -> request.recentRecords().clear());
        }
    }

    @Test void deferFieldsDenyFreshLegalityAndBusinessCredit() throws Exception {
        JsonNode response = StrictJson.parse(WarQueryCadenceCodec.encodeDefer(WarQueryCadence.evaluate(
                WarQueryCadenceCodec.decode(StrictJson.canonical(base(33554458))))));
        assertFalse(response.get("fresh_native_result").booleanValue()); assertTrue(response.get("native_legality").isNull());
        assertEquals(0, response.get("business_action_credit").intValue());
        assertEquals("unknown_without_fresh_native_query", response.get("current_cb_identity_status").textValue());
        assertEquals("history_policy_only", response.get("source").textValue());
    }

    @Test void boolFloatStringAndUnsafeIdentityCoercionsAreRejected() throws Exception {
        for (JsonNode wrong : List.of(StrictJson.parse("true".getBytes(StandardCharsets.UTF_8)),
                StrictJson.parse("33554458.0".getBytes(StandardCharsets.UTF_8)),
                StrictJson.parse("\"33554458\"".getBytes(StandardCharsets.UTF_8)),
                StrictJson.parse("18446744073709551616".getBytes(StandardCharsets.UTF_8)))) {
            ObjectNode input = base(33554458); object(input.get("war")).set("war_id", wrong);
            assertThrows(IllegalArgumentException.class, () -> WarQueryCadenceCodec.decode(StrictJson.canonical(input)));
        }
        ObjectNode input = base(33554458); latestResult(input).put("query_sequence", true);
        assertThrows(IllegalArgumentException.class, () -> WarQueryCadenceCodec.decode(StrictJson.canonical(input)));
    }

    @Test void missingNullableRequiredFieldAndNullCollectionHaveDistinctFailures() throws Exception {
        ObjectNode missing = base(33554458); object(missing.get("war")).remove("primary_opponent_character_id");
        assertThrows(IllegalArgumentException.class, () -> WarQueryCadenceCodec.decode(StrictJson.canonical(missing)));
        ObjectNode explicitUnknown = base(33554458); object(explicitUnknown.get("war")).putNull("primary_opponent_character_id");
        assertNull(WarQueryCadenceCodec.decode(StrictJson.canonical(explicitUnknown)).war().opponentId());
        ObjectNode nullArray = base(33554458); nullArray.putNull("active_wars");
        assertThrows(IllegalArgumentException.class, () -> WarQueryCadenceCodec.decode(StrictJson.canonical(nullArray)));
        ObjectNode emptyArray = base(33554458); emptyArray.putArray("active_wars");
        assertTrue(WarQueryCadence.evaluate(WarQueryCadenceCodec.decode(StrictJson.canonical(emptyArray))).isEmpty());
        ObjectNode unknownCb = base(33554458); ObjectNode options = object(latestResult(unknownCb).get("war_termination_options"));
        options.putNull("active_casus_belli_identity"); options.putNull("active_casus_belli_present");
        object(latestResult(unknownCb).get("termination_query_context")).set("negative_decision_signature", projectSignature(options));
        assertTrue(WarQueryCadence.evaluate(WarQueryCadenceCodec.decode(StrictJson.canonical(unknownCb))).isEmpty());
        ObjectNode unknownAccepted = base(33554458); latestResult(unknownAccepted).putNull("accepted");
        assertTrue(WarQueryCadence.evaluate(WarQueryCadenceCodec.decode(StrictJson.canonical(unknownAccepted))).isEmpty());
    }

    @Test void unknownRootDuplicateFieldsInvalidUtf8AndOversizedInputFailClosed() throws Exception {
        ObjectNode extra = base(33554458); extra.put("unexpected", 1);
        assertThrows(IllegalArgumentException.class, () -> WarQueryCadenceCodec.decode(StrictJson.canonical(extra)));
        assertThrows(IllegalArgumentException.class, () -> WarQueryCadenceCodec.decode("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> WarQueryCadenceCodec.decode(new byte[]{(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> WarQueryCadenceCodec.decode(new byte[65_537]));
    }

    @Test void querySpellingRequiresCanonicalFullGenerationWarId() {
        assertEquals(BigInteger.valueOf(33554458), WarQueryCadence.parseQueryWarId("query-war-termination-options-33554458"));
        assertEquals(BigInteger.valueOf(Integer.MAX_VALUE), WarQueryCadence.parseQueryWarId("query-war-termination-options-2147483647"));
        for (String invalid : List.of("0", "01", "-1", "+1", "2147483648", "１", "1.0", "1 ", "")) {
            assertNull(WarQueryCadence.parseQueryWarId("query-war-termination-options-" + invalid));
        }
    }

    @Test void duplicateLatestDateDoesNotConsumeTheSecondDistinctObservation() throws Exception {
        ObjectNode input = base(33554458); ArrayNode history = array(input.get("recent_records"));
        ObjectNode duplicate = object(history.get(0)).deepCopy(); object(duplicate.get("result")).put("query_sequence", 1);
        history.insert(1, duplicate);
        assertTrue(WarQueryCadence.evaluate(WarQueryCadenceCodec.decode(StrictJson.canonical(input))).isPresent());
        object(object(history.get(2)).get("result")).put("query_sequence", 216);
        assertTrue(WarQueryCadence.evaluate(WarQueryCadenceCodec.decode(StrictJson.canonical(input))).isEmpty());
    }

    @Test void barrierOlderThanSecondQueryIsNotInspected() throws Exception {
        ObjectNode input = base(33554458); array(input.get("recent_records")).addObject().put("step", "restore-checkpoint").put("ok", true);
        assertTrue(WarQueryCadence.evaluate(WarQueryCadenceCodec.decode(StrictJson.canonical(input))).isPresent());
    }


    @Test void legacyOptionConstructorAndWireKeepRolesUnknown() throws Exception {
        var option = new WarQueryCadence.OptionSignature("white_peace", "none", true, true, false,
                new WarQueryCadence.RecipientResponse("unavailable", null, null));
        assertInstanceOf(NativeInteractionRoles.LegacyWithoutRoles.class, option.recipientContext());
        var request = decodeRoles(base(33554458));
        for (var record : request.recentRecords()) {
            assertInstanceOf(NativeInteractionRoles.LegacyWithoutRoles.class,
                    record.query().options().signature().options().whitePeace().recipientContext());
        }
        byte[] encoded = WarQueryCadenceCodec.encodeRequest(request);
        assertArrayEquals(encoded, WarQueryCadenceCodec.encodeRequest(WarQueryCadenceCodec.decode(encoded)));
        assertFalse(new String(encoded, StandardCharsets.UTF_8).contains(NativeInteractionRoles.FIELD));
        JsonNode defer = StrictJson.parse(WarQueryCadenceCodec.encodeDefer(WarQueryCadence.evaluate(request)));
        assertTrue(defer.get("native_legality").isNull());
        assertEquals(0, defer.get("business_action_credit").intValue());
    }

    @Test void observedRolesRoundTripFullSignedIdentitiesThroughTheRealCadence() throws Exception {
        for (var roles : List.of(observedRoles(0, Integer.MIN_VALUE, null),
                observedRoles(0x01000010, 0x0100002a, -2),
                observedRoles(Integer.MIN_VALUE, 0, Integer.MAX_VALUE))) {
            var request = decodeRoles(withRoles(roles));
            assertEquals(roles, request.recentRecords().getFirst().query().options().signature()
                    .options().whitePeace().recipientContext());
            assertTrue(WarQueryCadence.evaluate(request).isPresent());
            var restored = WarQueryCadenceCodec.decode(WarQueryCadenceCodec.encodeRequest(request));
            assertEquals(request, restored);
            assertEquals(WarQueryCadence.evaluate(request), WarQueryCadence.evaluate(restored));
        }
    }

    @Test void changingAnyFullRoleIdentityCannotExtendTheOldNegativeLease() throws Exception {
        var original = observedRoles(0x01000010, 0x0100002a, 0x0100002b);
        assertTrue(WarQueryCadence.evaluate(decodeRoles(withRoles(original))).isPresent());
        for (String outcome : List.of("surrender", "white_peace", "victory")) {
            for (var changed : List.of(observedRoles(0x02000010, 0x0100002a, 0x0100002b),
                    observedRoles(0x01000010, 0x0200002a, 0x0100002b),
                    observedRoles(0x01000010, 0x0100002a, 0x0200002b),
                    observedRoles(0x01000010, 0x0100002a, null))) {
                ObjectNode input = withRoles(original);
                NativeInteractionRoles.putOption(option(latestResult(input), outcome), changed);
                refreshSignature(latestResult(input));
                assertTrue(WarQueryCadence.evaluate(decodeRoles(input)).isEmpty(), outcome + " " + changed);
            }
        }
    }

    @Test void unavailableOrMixedHistoryRolesNeverAcquireAReceiverLease() throws Exception {
        for (var reason : NativeInteractionRoles.Reason.values()) {
            assertTrue(WarQueryCadence.evaluate(decodeRoles(withRoles(
                    new NativeInteractionRoles.Unavailable(reason)))).isEmpty(), reason.name());
        }
        ObjectNode input = withRoles(observedRoles(0x01000010, 0x0100002a, null));
        NativeInteractionRoles.putOption(option(latestResult(input), "white_peace"),
                new NativeInteractionRoles.Unavailable(NativeInteractionRoles.Reason.IDENTITY_UNRESOLVED));
        refreshSignature(latestResult(input));
        assertTrue(WarQueryCadence.evaluate(decodeRoles(input)).isEmpty());
        input = base(33554458);
        putRoles(latestResult(input), observedRoles(0x01000010, 0x0100002a, null));
        assertTrue(WarQueryCadence.evaluate(decodeRoles(input)).isEmpty(),
                "legacy history cannot alias a new observed receiver");
        input = withRoles(observedRoles(0x01000010, 0x0100002a, null));
        putRoles(latestResult(input), new NativeInteractionRoles.LegacyWithoutRoles());
        assertTrue(WarQueryCadence.evaluate(decodeRoles(input)).isEmpty(),
                "a legacy observation cannot renew a new receiver lease");
    }

    @Test void roleValuesBindTheStoredContextToTheActualOptions() throws Exception {
        ObjectNode input = withRoles(observedRoles(0x01000010, 0x0100002a, null));
        ObjectNode context = object(latestResult(input).get("termination_query_context"));
        ObjectNode stored = object(context.get("negative_decision_signature").get("options").get("white_peace"));
        NativeInteractionRoles.putOption(stored, observedRoles(0x01000010, 0x0200002a, null));
        var request = decodeRoles(input);
        assertFalse(request.recentRecords().getFirst().query().context().negativeSignature()
                .equals(request.recentRecords().getFirst().query().options().signature()));
        assertTrue(WarQueryCadence.evaluate(request).isEmpty());
    }

    @Test void malformedOrPartiallyUpgradedRolesAreRejectedAtTheActualWireBoundary() throws Exception {
        for (String fault : List.of("null", "bool", "float", "sentinel", "missing", "version", "extra", "unavailable", "partial")) {
            ObjectNode input = withRoles(observedRoles(0x01000010, 0x0100002a, 0x0100002b));
            ObjectNode row = option(latestResult(input), "white_peace");
            ObjectNode roles = object(row.get(NativeInteractionRoles.FIELD));
            switch (fault) {
                case "null" -> row.putNull(NativeInteractionRoles.FIELD);
                case "bool" -> roles.put("actor_character_id", true);
                case "float" -> roles.set("recipient_character_id", new DecimalTokenNode("16777258.0"));
                case "sentinel" -> roles.put("intermediary_character_id", -1);
                case "missing" -> roles.remove("recipient_character_id");
                case "version" -> roles.put("schema_version", 2);
                case "extra" -> roles.put("uncontracted", true);
                case "unavailable" -> { roles.put("state", "unavailable"); roles.put("reason", "identity_unresolved"); }
                case "partial" -> row.remove(NativeInteractionRoles.FIELD);
                default -> throw new AssertionError(fault);
            }
            ObjectNode context = object(latestResult(input).get("termination_query_context"));
            ObjectNode stored = object(context.get("negative_decision_signature").get("options").get("white_peace"));
            if (row.has(NativeInteractionRoles.FIELD)) stored.set(NativeInteractionRoles.FIELD, row.get(NativeInteractionRoles.FIELD).deepCopy());
            else stored.remove(NativeInteractionRoles.FIELD);
            if (fault.equals("float")) assertTrue(input.toString().contains("16777258.0"));
            assertThrows(IllegalArgumentException.class, () -> decodeRoles(input), fault);
        }
    }

    private static NativeInteractionRoles.Observed observedRoles(int actor, int recipient, Integer intermediary) {
        return new NativeInteractionRoles.Observed(new NativeCharacterId(actor), new NativeCharacterId(recipient),
                intermediary == null ? Optional.empty() : Optional.of(new NativeCharacterId(intermediary)));
    }
    private static ObjectNode withRoles(NativeInteractionRoles roles) throws IOException {
        // Only role observations are synthetic; the retained query history and existing policy remain the producer fixture.
        ObjectNode input = base(33554458);
        for (JsonNode record : input.get("recent_records")) putRoles(object(record.get("result")), roles);
        return input;
    }
    private static void putRoles(ObjectNode result, NativeInteractionRoles roles) {
        for (String outcome : List.of("surrender", "white_peace", "victory"))
            NativeInteractionRoles.putOption(option(result, outcome), roles);
        refreshSignature(result);
    }
    private static ObjectNode option(ObjectNode result, String outcome) {
        return object(result.get("war_termination_options").get("options").get(outcome));
    }
    private static void refreshSignature(ObjectNode result) {
        object(result.get("termination_query_context")).set("negative_decision_signature",
                projectSignature(object(result.get("war_termination_options"))));
    }
    private static WarQueryCadence.Request decodeRoles(ObjectNode input) {
        return WarQueryCadenceCodec.decode(input.toString().getBytes(StandardCharsets.UTF_8));
    }

    private static List<Vector> vectors() throws IOException {
        List<Vector> result = new ArrayList<>(); add(result, "actual-war-33554458", base(33554458)); add(result, "actual-war-50331679", base(50331679));
        ObjectNode c = base(33554458); ArrayNode records = array(c.get("recent_records")); records.remove(1); add(result, "one-query", c);
        c = base(33554458); records = array(c.get("recent_records")); ObjectNode duplicate = object(records.get(0)).deepCopy();
        ObjectNode query = object(duplicate.get("result")); query.put("query_sequence", query.get("query_sequence").intValue() + 1);
        records.removeAll(); records.add(duplicate); records.add(base(33554458).get("recent_records").get(0)); add(result, "same-date-only", c);
        c = base(33554458); snapshot(c).put("date_raw", 53222016 + 720); add(result, "expiry-exact", c);
        c = base(33554458); snapshot(c).put("date_raw", 53222016); add(result, "same-current-date", c);
        c = base(33554458); snapshot(c).put("date_raw", 53222016 + 719); add(result, "before-expiry", c);
        c = base(33554458); snapshot(c).put("date_raw", 53222016 + 720); duplicate = latest(c).deepCopy(); query = object(duplicate.get("result"));
        query.put("query_sequence", query.get("query_sequence").intValue() + 100); object(query.get("termination_query_context")).put("queried_date_raw", 53222016 + 720);
        snapshot(c).put("date_raw", 53222016 + 720 + 168); array(c.get("recent_records")).insert(0, duplicate); add(result, "renewal", c);
        for (String name : List.of("actor-change", "episode-change", "connection-change", "terminal-score-positive", "terminal-score-negative", "role-change", "new-war")) {
            c = base(33554458);
            switch (name) {
                case "actor-change" -> object(snapshot(c).get("played_character")).put("character_id", 999);
                case "episode-change" -> snapshot(c).put("episode_run_id", "different");
                case "connection-change" -> object(snapshot(c).get("diagnostics")).put("connection_generation", 4);
                case "terminal-score-positive" -> object(c.get("war")).put("player_relative_war_score", 100);
                case "terminal-score-negative" -> object(c.get("war")).put("player_relative_war_score", -100);
                case "role-change" -> object(c.get("war")).put("player_is_primary_war_leader", false);
                case "new-war" -> { ObjectNode war = object(c.get("war")).deepCopy(); war.put("war_id", 999); array(c.get("active_wars")).add(war); }
                default -> throw new IllegalStateException(name);
            }
            add(result, name, c);
        }
        String[][] barriers = {{"write-barrier", "offer-white-peace-war-33554458"}, {"event-barrier", "resolve-current-event"},
                {"malformed-query", "query-war-termination-options-033554458"}, {"restore-barrier", "restore-checkpoint"}};
        for (String[] pair : barriers) { c = base(33554458); barrier(c, pair[1], false); add(result, pair[0], c); }
        c = base(33554458); barrier(c, "life-advance", true); add(result, "action-barrier", c);
        c = base(33554458); latest(c).put("ok", false); add(result, "failed-query", c);
        c = base(33554458); snapshot(c).putObject("active_event").put("event_id", 42); add(result, "active-event", c);
        c = base(33554458); snapshot(c).putObject("pending_character_interaction").put("interaction_id", 7); add(result, "pending-interaction", c);
        c = base(33554458); snapshot(c).putObject("top_exclusive_modal_choice_hint").put("status", "present"); add(result, "exclusive-modal", c);
        for (String name : List.of("positive-peace-response", "positive-autoaccept", "changed-cb")) {
            c = base(33554458); ObjectNode options = object(latestResult(c).get("war_termination_options")); ObjectNode peace = object(options.get("options").get("white_peace"));
            switch (name) {
                case "positive-peace-response" -> { ObjectNode response = peace.putObject("recipient_response"); response.put("status", "available"); response.put("would_accept_now", true); response.put("decision_status_raw", 1); }
                case "positive-autoaccept" -> { peace.put("auto_accept_observable", true); peace.put("auto_accept", true); }
                case "changed-cb" -> object(options.get("active_casus_belli_identity")).put("database_index", 71);
                default -> throw new IllegalStateException(name);
            }
            object(latestResult(c).get("termination_query_context")).set("negative_decision_signature", projectSignature(options)); add(result, name, c);
        }
        for (int days : List.of(365, 180)) {
            c = base(33554458); object(c.get("war")).put("player_side", "attacker");
            for (JsonNode record : c.get("recent_records")) {
                query = object(record.get("result")); ObjectNode options = object(query.get("war_termination_options")); ObjectNode context = object(query.get("termination_query_context"));
                options.put("player_side", "attacker"); options.put("player_is_primary_war_leader", true);
                ObjectNode cb = options.putObject("active_casus_belli_identity"); cb.put("database_index", 70); cb.put("canonical_key", days == 365 ? "claim_cb" : "individual_county_de_jure_cb");
                options.put("cb_allows_white_peace", true); options.put("war_duration_days", context.get("queried_date_raw").intValue() == 53222016 ? days - 5 : days - 12);
                for (JsonNode war : context.get("active_war_signature")) { if (war.get("war_id").intValue() == 33554458) { object(war).put("player_side", "attacker"); } }
                context.set("negative_decision_signature", projectSignature(options)); context.set("queried_war_duration_days", options.get("war_duration_days"));
            }
            snapshot(c).put("date_raw", 53222016 + 120); String name = days == 365 ? "claim-day-365" : "dejure-day-180"; add(result, name, c.deepCopy());
            snapshot(c).put("date_raw", 53222016 + 119); add(result, name + "-before", c);
        }
        return List.copyOf(result);
    }

    private static ObjectNode base(int warId) throws IOException {
        JsonNode rows = resource("termination_six_query_projection.json").get("rows"); JsonNode current = null;
        for (JsonNode row : rows) { if (row.get("source_sequence").intValue() == 1847) { current = row; } }
        if (current == null) { throw new IOException("retained source row missing"); }
        JsonNode frame = current.get("planning_source_frame"); ObjectNode root = StrictJson.object(); root.put("schema", WarQueryCadenceCodec.SCHEMA);
        ObjectNode snapshot = root.putObject("snapshot"); snapshot.put("paused", true); snapshot.put("map_ready", true);
        snapshot.putNull("active_event"); snapshot.putNull("pending_character_interaction"); snapshot.putNull("one_life_terminal_reason");
        snapshot.set("date_raw", frame.get("date_raw")); snapshot.set("episode_run_id", frame.get("episode_run_id"));
        ObjectNode actor = snapshot.putObject("played_character"); actor.set("character_id", frame.get("actor_character_id")); actor.put("alive", true);
        snapshot.putObject("diagnostics").set("connection_generation", frame.get("connection_generation"));
        ArrayNode wars = (ArrayNode) current.get("record").get("result").get("termination_query_context").get("active_war_signature").deepCopy();
        root.set("active_wars", wars); for (JsonNode war : wars) { if (war.get("war_id").intValue() == warId) { root.set("war", war); } }
        ArrayNode history = root.putArray("recent_records");
        for (int index = rows.size() - 1; index >= 0; index--) {
            JsonNode row = rows.get(index); if (row.get("source_sequence").intValue() < 1847
                    && row.get("record").get("result").get("war_termination_options").get("war_id").intValue() == warId) { history.add(row.get("record").deepCopy()); }
        }
        return root;
    }

    private static ObjectNode projectSignature(ObjectNode options) {
        ObjectNode node = StrictJson.object();
        for (String key : List.of("war_id", "player_side", "player_is_primary_war_leader", "player_relative_war_score", "absolute_war_scores_observable",
                "attacker_war_score", "defender_war_score", "war_score_breakdown", "active_casus_belli_present", "active_casus_belli_identity", "cb_allows_white_peace")) { node.set(key, options.get(key).deepCopy()); }
        ObjectNode rows = node.putObject("options"); for (String name : List.of("surrender", "white_peace", "victory")) {
            ObjectNode row = rows.putObject(name); for (String key : List.of("outcome", "hostage_variant", "context_constructed", "native_validator_passed", "available", "recipient_response")) {
                row.set(key, options.get("options").get(name).get(key).deepCopy());
            }
            NativeInteractionRoles.putOption(row, NativeInteractionRoles.fromOption(options.get("options").get(name)));
        }
        return node;
    }
    private static void barrier(ObjectNode input, String step, boolean action) {
        ObjectNode record = StrictJson.object(); record.put("step", step); record.put("ok", true); ObjectNode result = record.putObject("result");
        if (action) { result.putObject("war_action").put("status", "submitted"); } array(input.get("recent_records")).insert(0, record);
    }
    private static void add(List<Vector> vectors, String name, ObjectNode input) { vectors.add(new Vector(name, input)); }
    private static ObjectNode latest(ObjectNode input) { return object(input.get("recent_records").get(0)); }
    private static ObjectNode latestResult(ObjectNode input) { return object(latest(input).get("result")); }
    private static ObjectNode snapshot(ObjectNode input) { return object(input.get("snapshot")); }
    private static ObjectNode object(JsonNode value) { return (ObjectNode) value; }
    private static ArrayNode array(JsonNode value) { return (ArrayNode) value; }
    private static JsonNode resource(String name) throws IOException {
        try (InputStream stream = WarQueryCadenceTest.class.getResourceAsStream("/warquerycadence/" + name)) {
            if (stream == null) { throw new IOException("required committed golden missing: " + name); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static String sha(byte[] bytes) throws NoSuchAlgorithmException {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}
