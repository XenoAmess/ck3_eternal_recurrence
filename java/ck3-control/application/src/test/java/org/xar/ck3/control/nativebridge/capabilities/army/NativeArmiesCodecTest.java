package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.military.MilitaryPlanInputs;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

final class NativeArmiesCodecTest {
    private record Sample(String name, JsonNode input) { }
    private static final BigInteger HUGE = BigInteger.ONE.shiftLeft(100).add(BigInteger.valueOf(19));

    @Test void fullTypedProducerPreservesOrderOccurrencesAndOriginalIntegerDomains() {
        ObjectNode first = army(0).put("owner_character_id", HUGE).put("soldiers", HUGE)
                .put("current_province_id", HUGE).put("move_target_province_id", HUGE)
                .put("army_state_code", HUGE).put("siege_days_left", HUGE);
        first.put("army_state", " "); first.put("in_combat", false); first.put("retreating", true);
        first.put("siege_province_holder_character_id", Integer.MAX_VALUE).put("siege_province_in_player_subrealm", false);
        first.putArray("route_province_ids").add(3).add(3).add(1);
        first.put("source", "untrusted-extra").put("native_carmy_id", -2147483647);
        var decoded = NativeArmiesCodec.normalize(rows(first, army(1), army(0).put("owner_character_id", 2)));
        assertEquals(List.of(0, 1, 0), decoded.stream().map(row -> row.armyId().value()).toList());
        var value = decoded.getFirst();
        assertEquals(HUGE, value.ownerCharacterId()); assertEquals(HUGE, value.soldiers().orElseThrow());
        assertEquals(HUGE, value.currentProvinceId().orElseThrow()); assertEquals(HUGE, value.moveTargetProvinceId().orElseThrow());
        assertEquals(List.of(3, 3, 1), value.routeProvinceIds().orElseThrow());
        assertEquals(new Present<>(HUGE), value.siegeDaysLeft());
        assertEquals(new Present<>(false), value.siegeProvinceInPlayerSubrealm());
        ObjectNode encoded = NativeArmiesCodec.encodeArmy(value);
        assertEquals("native", encoded.get("source").textValue()); assertFalse(encoded.has("native_carmy_id"));
        assertEquals(decoded, NativeArmiesCodec.normalize(NativeArmiesCodec.encode(decoded)));
        first.put("owner_character_id", 3).withArray("route_province_ids").removeAll();
        assertEquals(HUGE, value.ownerCharacterId()); assertEquals(3, value.routeProvinceIds().orElseThrow().size());
        assertThrows(UnsupportedOperationException.class, () -> value.routeProvinceIds().orElseThrow().add(9));
        assertThrows(UnsupportedOperationException.class, () -> decoded.add(value));
    }

    @Test void missingNullEmptyAndObservedZeroHaveTheirOriginalCanonicalMeaning() {
        var missing = NativeArmiesCodec.normalize(rows(army(0))).getFirst();
        ObjectNode nullable = army(0).putNull("move_target_province_id").putNull("in_combat").putNull("retreating")
                .putNull("army_state").putNull("army_state_code").putNull("siege_days_left")
                .putNull("siege_province_holder_character_id").putNull("siege_province_in_player_subrealm");
        nullable.putArray("route_province_ids");
        var presentNull = NativeArmiesCodec.normalize(rows(nullable)).getFirst();
        assertFalse(missing.moveTargetObservable()); assertTrue(presentNull.moveTargetObservable());
        assertTrue(missing.routeProvinceIds().isEmpty()); assertEquals(List.of(), presentNull.routeProvinceIds().orElseThrow());
        assertInstanceOf(Missing.class, missing.siegeDaysLeft()); assertInstanceOf(NullValue.class, presentNull.siegeDaysLeft());
        ObjectNode canonical = NativeArmiesCodec.encodeArmy(presentNull);
        assertTrue(canonical.get("soldiers").isNull()); assertTrue(canonical.get("current_province_id").isNull());
        assertTrue(canonical.get("siege_days_left").isNull()); assertFalse(canonical.has("in_combat"));
        assertFalse(canonical.has("retreating")); assertFalse(canonical.has("army_state")); assertFalse(canonical.has("army_state_code"));
        var zero = NativeArmiesCodec.normalize(rows(army(0).put("soldiers", 0).put("current_province_id", 0)
                .put("army_state_code", 0).put("siege_days_left", 0))).getFirst();
        assertEquals(BigInteger.ZERO, zero.currentProvinceId().orElseThrow());
        assertEquals(new Present<>(BigInteger.ZERO), zero.siegeDaysLeft());
        assertEquals(List.of(), NativeArmiesCodec.normalize((JsonNode) null));
        assertEquals(List.of(), NativeArmiesCodec.normalize(NullNode.instance));
    }

    @Test void routeEvidenceRejectsMissingCountAndFalseEmptyProofBeforeThePlanner() {
        for (Sample sample : invalidCases())
            assertThrows(IllegalArgumentException.class, () -> NativeArmiesCodec.normalize(sample.input()), sample.name());
        for (Sample sample : validCases()) {
            var decoded = NativeArmiesCodec.normalize(sample.input());
            assertEquals(decoded, NativeArmiesCodec.normalize(NativeArmiesCodec.encode(decoded)), sample.name());
        }
        ObjectNode bad = route("complete_empty", 0, List.of(), null, false);
        bad.remove("route_source_count");
        assertThrows(IllegalArgumentException.class, () -> MilitaryPlanInputs.army(immutable(bad)));
        bad.put("route_source_count", 0).put("move_target_observable", true);
        assertThrows(IllegalArgumentException.class, () -> MilitaryPlanInputs.army(immutable(bad)));
    }

    @Test void actualPlannerConsumesTheSingleFullCanonicalArmyWithoutLosingSidecars() {
        ObjectNode raw = route("complete_empty", 0, List.of(), null, false).put("army_id", 0)
                .put("army_state", "regular").put("in_combat", false).put("retreating", false)
                .put("army_state_code", 0).put("siege_days_left", 0)
                .put("siege_province_holder_character_id", 1).put("siege_province_in_player_subrealm", false);
        var army = MilitaryPlanInputs.army(immutable(raw));
        assertEquals(0, army.id()); assertTrue(army.explicitIdle()); assertEquals("regular", army.tacticalState());
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.ZERO), army.raw().get("siege_days_left"));
        assertEquals(new OpportunityJson.Bool(false), army.raw().get("siege_province_in_player_subrealm"));
        assertEquals(immutable(NativeArmiesCodec.encodeArmy(NativeArmiesCodec.normalizeArmy(raw, "actual row"))), army.raw());
        ObjectNode moved = route("complete_nonempty", 3, List.of(4, 4, 2), 2, true).put("army_state", "moving");
        assertEquals(List.of(4, 4, 2), MilitaryPlanInputs.army(immutable(moved)).route().orElseThrow());
        assertFalse(MilitaryPlanInputs.army(immutable(moved)).explicitIdle());
        assertThrows(IllegalArgumentException.class, () -> MilitaryPlanInputs.army(immutable(army(0).put("current_province_id", HUGE))),
                "the full native domain must survive normalization; narrower strategy address cannot truncate it");
    }

    @Test void completeNormalizerAndOriginalRouteSuiteMatchThePinnedPythonProducer() throws Exception {
        String repositoryProperty = System.getProperty("xar.repository.root");
        assertNotNull(repositoryProperty, "whole CI requires xar.repository.root; missing oracle is RED");
        Path repository = Path.of(repositoryProperty).toRealPath();
        List<Path> sources = List.of(
                repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py"),
                repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py"),
                repository.resolve("ck3_autonomous_player/tests/unit/test_army_route_read_status_contract.py"));
        List<String> digests = List.of(
                "b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937",
                "0de76f3bf10ae24d3202177bb527bcb3ec903432a38af64f55e08c95698cab4e",
                "b411eab2ad5b6390817fc0917c5f6cd6a55a7f21ef4e35c479531d5d6338a9e3");
        for (int index = 0; index < sources.size(); index++) assertEquals(digests.get(index), sha(sources.get(index)));
        List<Sample> samples = new ArrayList<>(validCases()); samples.addAll(invalidCases());
        ObjectNode request = empty(); ArrayNode cases = request.putArray("cases");
        samples.forEach(sample -> cases.add(sample.input()));
        String script = """
                import contextlib,copy,json,pathlib,runpy,sys,unittest
                sys.dont_write_bytecode=True
                root=pathlib.Path(sys.argv[1])
                sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.bridge.war_contract import normalize_armies
                fixture=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_army_route_read_status_contract.py'))
                suite=unittest.defaultTestLoader.loadTestsFromTestCase(fixture['ArmyRouteReadStatusContractTests'])
                with contextlib.redirect_stdout(sys.stderr):
                    result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
                if not result.wasSuccessful() or result.skipped or result.testsRun!=3:
                    raise RuntimeError('original route tests failed/skipped/incomplete')
                replies=[]
                for raw in json.load(sys.stdin)['cases']:
                    original=copy.deepcopy(raw)
                    try:reply=dict(ok=True,value=normalize_armies(raw))
                    except (ValueError,TypeError):reply=dict(ok=False)
                    if raw!=original:raise RuntimeError('original normalizer mutated input')
                    replies.append(reply)
                print(json.dumps(dict(original_tests=result.testsRun,cases=replies),separators=(',',':')))
                """;
        ObjectNode reply = BattleOriginalOracle.call(script, request);
        JsonNode replies = reply.get("cases");
        assertEquals(3, reply.get("original_tests").intValue()); assertEquals(samples.size(), replies.size());
        for (int index = 0; index < samples.size(); index++) {
            Sample sample = samples.get(index); JsonNode expected = replies.get(index), before = sample.input().deepCopy();
            ArrayNode actual = null; boolean accepted;
            try { actual = NativeArmiesCodec.encode(NativeArmiesCodec.normalize(sample.input())); accepted = true; }
            catch (IllegalArgumentException rejected) { accepted = false; }
            assertEquals(expected.get("ok").booleanValue(), accepted, sample.name());
            if (accepted) {
                ObjectNode a = empty(), b = empty(); a.set("value", actual); b.set("value", expected.get("value"));
                assertEquals(parse(bytes(b)), parse(bytes(a)), sample.name());
            }
            assertEquals(before, sample.input(), "Java input immutability: " + sample.name());
        }
        for (int index = 0; index < sources.size(); index++) assertEquals(digests.get(index), sha(sources.get(index)));
    }

    private static List<Sample> validCases() {
        List<Sample> out = new ArrayList<>();
        out.add(new Sample("null collection", NullNode.instance)); out.add(new Sample("empty collection", rows()));
        out.add(new Sample("minimal omitted fields and public zero", rows(army(0))));
        out.add(new Sample("native occurrence order and duplicates", rows(army(3), army(1), army(3))));
        out.add(new Sample("public maximum", rows(army(Integer.MAX_VALUE))));
        out.add(new Sample("unbounded observation IDs and quantities", rows(army(0).put("owner_character_id", HUGE)
                .put("soldiers", HUGE).put("current_province_id", HUGE).put("move_target_province_id", HUGE)
                .put("army_state_code", HUGE).put("siege_days_left", HUGE))));
        out.add(new Sample("old input-only soldier spelling", rows(army(0).put("soldier_count", 6))));
        out.add(new Sample("old spelling after explicit null", rows(army(0).putNull("soldiers").put("soldier_count", 0))));
        out.add(new Sample("canonical soldiers wins", rows(army(0).put("soldiers", 1).put("soldier_count", false))));
        out.add(new Sample("unknown extras discarded", rows(army(0).put("source", "other").put("native_carmy_id", -1))));
        out.add(new Sample("explicit null target is observable without flag", rows(army(0).putNull("move_target_province_id"))));
        out.add(new Sample("explicit null observable falls back to target presence", rows(army(0).putNull("move_target_province_id").putNull("move_target_observable"))));
        out.add(new Sample("explicit false observable with no route evidence", rows(army(0).put("move_target_province_id", 4).put("move_target_observable", false))));
        ObjectNode nullable = army(0).putNull("soldiers").putNull("in_combat").putNull("retreating").putNull("army_state")
                .putNull("army_state_code").putNull("siege_days_left").putNull("siege_province_holder_character_id")
                .putNull("siege_province_in_player_subrealm");
        nullable.putArray("route_province_ids"); out.add(new Sample("missing null empty preservation", rows(nullable)));
        out.add(new Sample("whitespace state is nonempty in original", rows(army(0).put("army_state", " "))));
        out.add(new Sample("all optional exact flags", rows(army(0).put("in_combat", true).put("retreating", false))));
        for (String status : List.of("not_attempted", "invalid_header"))
            out.add(new Sample(status, rows(route(status, null, List.of(), null, false))));
        out.add(new Sample("complete_empty", rows(route("complete_empty", 0, List.of(), null, false))));
        out.add(new Sample("complete_nonempty repeated ordered route", rows(route("complete_nonempty", 3, List.of(4, 4, 1), 1, true))));
        out.add(new Sample("target_only province zero accepted original general ID", rows(route("target_only", 1, List.of(), 0, true))));
        out.add(new Sample("unresolved_entry", rows(route("unresolved_entry", 1, List.of(), null, false))));
        List<Integer> longRoute = java.util.Collections.nCopies(4096, Integer.MAX_VALUE);
        out.add(new Sample("maximum observed count", rows(route("complete_nonempty", 4096, longRoute, Integer.MAX_VALUE, true))));
        ObjectNode noEvidence = army(0); noEvidence.set("route_province_ids", numbers(java.util.Collections.nCopies(4097, 1)));
        out.add(new Sample("route absent evidence has no invented 4096 bound", rows(noEvidence)));
        out.add(new Sample("siege relation false still has holder", rows(army(0).put("siege_province_holder_character_id", 1)
                .put("siege_province_in_player_subrealm", false).put("siege_days_left", 0))));
        out.add(new Sample("siege relation null without holder", rows(army(0).putNull("siege_province_in_player_subrealm"))));
        return List.copyOf(out);
    }
    private static List<Sample> invalidCases() {
        List<Sample> out = new ArrayList<>();
        for (JsonNode value : List.of(empty(), JsonNodeFactory.instance.booleanNode(false),
                JsonNodeFactory.instance.numberNode(1), JsonNodeFactory.instance.textNode("x")))
            out.add(new Sample("collection wrong token " + out.size(), value));
        for (JsonNode value : List.of(NullNode.instance, rows(), JsonNodeFactory.instance.booleanNode(true),
                JsonNodeFactory.instance.numberNode(0), JsonNodeFactory.instance.textNode("x")))
            out.add(new Sample("row wrong token " + out.size(), rows(value)));
        for (String key : List.of("army_id", "owner_character_id", "controllable")) {
            ObjectNode missing = army(0); missing.remove(key); out.add(new Sample("missing " + key, rows(missing)));
            out.add(new Sample("null required " + key, rows(army(0).putNull(key))));
        }
        for (String key : List.of("army_id", "owner_character_id", "soldiers", "current_province_id",
                "move_target_province_id", "army_state_code", "siege_days_left", "siege_province_holder_character_id")) {
            for (JsonNode wrong : List.of(JsonNodeFactory.instance.booleanNode(true), JsonNodeFactory.instance.numberNode(1.0),
                    JsonNodeFactory.instance.numberNode(-1), JsonNodeFactory.instance.textNode("1"), rows())) {
                ObjectNode raw = army(0); raw.set(key, wrong);
                out.add(new Sample("wrong integer " + key + " " + out.size(), rows(raw)));
            }
        }
        out.add(new Sample("public high bit is not native signed FullId", rows(army(0).put("army_id", 2147483648L))));
        out.add(new Sample("positive holder excludes zero", rows(army(0).put("siege_province_holder_character_id", 0))));
        out.add(new Sample("positive holder excludes U32 high bit", rows(army(0).put("siege_province_holder_character_id", 2147483648L))));
        for (String key : List.of("controllable", "move_target_observable", "in_combat", "retreating", "siege_province_in_player_subrealm")) {
            out.add(new Sample("integer is not flag " + key, rows(army(0).put(key, 1))));
            out.add(new Sample("string is not flag " + key, rows(army(0).put(key, "true"))));
        }
        out.add(new Sample("empty state", rows(army(0).put("army_state", ""))));
        out.add(new Sample("boolean state", rows(army(0).put("army_state", false))));
        out.add(new Sample("observed relation true requires holder", rows(army(0).put("siege_province_in_player_subrealm", true))));
        out.add(new Sample("observed relation false requires holder", rows(army(0).putNull("siege_province_holder_character_id").put("siege_province_in_player_subrealm", false))));
        for (JsonNode wrong : List.of(NullNode.instance, empty(), JsonNodeFactory.instance.numberNode(0))) {
            ObjectNode raw = army(0); raw.set("route_province_ids", wrong); out.add(new Sample("route not array " + out.size(), rows(raw)));
        }
        for (JsonNode wrong : List.of(JsonNodeFactory.instance.numberNode(0), JsonNodeFactory.instance.numberNode(-1),
                JsonNodeFactory.instance.numberNode(2147483648L), JsonNodeFactory.instance.numberNode(1.0),
                JsonNodeFactory.instance.booleanNode(true), NullNode.instance)) {
            ObjectNode raw = army(0); raw.putArray("route_province_ids").add(wrong);
            out.add(new Sample("route positive int32 " + out.size(), rows(raw)));
        }
        ObjectNode missingCount = route("complete_empty", 0, List.of(), null, false); missingCount.remove("route_source_count");
        out.add(new Sample("status without count", rows(missingCount)));
        ObjectNode missingStatus = route("complete_empty", 0, List.of(), null, false); missingStatus.remove("route_read_status");
        out.add(new Sample("count without status", rows(missingStatus)));
        ObjectNode missingRoute = route("complete_empty", 0, List.of(), null, false); missingRoute.remove("route_province_ids");
        out.add(new Sample("evidence without array", rows(missingRoute)));
        for (JsonNode wrong : List.of(NullNode.instance, empty(), JsonNodeFactory.instance.booleanNode(true),
                JsonNodeFactory.instance.textNode("unknown"))) {
            ObjectNode raw = route("complete_empty", 0, List.of(), null, false); raw.set("route_read_status", wrong);
            out.add(new Sample("bad status token " + out.size(), rows(raw)));
        }
        for (JsonNode wrong : List.of(JsonNodeFactory.instance.numberNode(-1), JsonNodeFactory.instance.numberNode(4097),
                JsonNodeFactory.instance.numberNode(0.0), JsonNodeFactory.instance.booleanNode(false), JsonNodeFactory.instance.textNode("0"))) {
            ObjectNode raw = route("complete_empty", 0, List.of(), null, false); raw.set("route_source_count", wrong);
            out.add(new Sample("bad count token " + out.size(), rows(raw)));
        }
        for (ObjectNode wrong : List.of(route("complete_empty", 0, List.of(1), null, false),
                route("complete_empty", 0, List.of(), null, true), route("complete_empty", 0, List.of(), 1, false),
                route("complete_nonempty", 2, List.of(1), 1, true), route("complete_nonempty", 1, List.of(1), 2, true),
                route("complete_nonempty", 1, List.of(1), 1, false), route("target_only", 0, List.of(), 1, true),
                route("target_only", 1, List.of(1), 1, true), route("target_only", 1, List.of(), null, true),
                route("unresolved_entry", 1, List.of(), 1, true), route("invalid_header", 0, List.of(), null, false),
                route("not_attempted", null, List.of(1), null, false)))
            out.add(new Sample("inconsistent evidence " + out.size(), rows(wrong)));
        return List.copyOf(out);
    }
    private static ObjectNode army(int id) { return empty().put("army_id", id).put("owner_character_id", 0).put("controllable", true); }
    private static ObjectNode route(String status, Integer count, List<Integer> route, Integer target, boolean observable) {
        ObjectNode raw = army(0).put("route_read_status", status).put("move_target_observable", observable);
        if (count == null) raw.putNull("route_source_count"); else raw.put("route_source_count", count.intValue());
        if (target == null) raw.putNull("move_target_province_id"); else raw.put("move_target_province_id", target.intValue());
        raw.set("route_province_ids", numbers(route)); return raw;
    }
    private static ArrayNode numbers(List<Integer> numbers) {
        ArrayNode out = JsonNodeFactory.instance.arrayNode(); numbers.forEach(value -> out.add(value.intValue())); return out;
    }
    private static ArrayNode rows(JsonNode... rows) {
        ArrayNode out = JsonNodeFactory.instance.arrayNode(); for (JsonNode row : rows) out.add(row.deepCopy()); return out;
    }
    private static OpportunityJson.Obj immutable(ObjectNode raw) {
        return DriverJson.object(bytes(raw), DriverJson.MAX_NATIVE_BYTES);
    }
    private static String sha(Path source) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
    }
}

