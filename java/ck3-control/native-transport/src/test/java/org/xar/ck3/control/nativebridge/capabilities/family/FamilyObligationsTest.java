package org.xar.ck3.control.nativebridge.capabilities.family;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligations.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original native .2 packets and original Python consumer; current .4 cases are explicitly synthetic codec cases. */
final class FamilyObligationsTest {
    private static final String BASE = "ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_family_obligations_";
    private static final String TRANSPORT = "ck3_autonomous_player/src/xar_autoplayer/bridge/family_obligations_private_transport.py";
    private static final List<Pin> PINS = List.of(
            new Pin(BASE + "mailbox.json", 1251, "57efb23b0fc41ab3b7f5964e9c213394c10c9c9012bb68065e81c3467363f773"),
            new Pin(BASE + "terms.json", 2258, "976bdcab97490b0eba91e704d146af87bc85221bbb75511b2a9d7366d90a3ce2"),
            new Pin(TRANSPORT, 18239, "20868ed7178205ca00c2813741a53c5f7a5dbb4fa27e30bb83dc705ac1e48d1a"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/g2_private_query_transport.py", 4533, "02db15ca2b070f814df06cad10da2bb9b4c8e2e1aec621f9228a5ab12f971315"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py", 2114, "9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py", 2663, "fe1a53ca0f01e60ae37231e3b1a566442454f3bb77afd33b616849b25f6d53e9"),
            new Pin("ck3_autonomous_player/native_bridge/src/ck3_12002_family_obligations_wire.cpp", 14535, "df76a9addb359dfb07bdf9e49191434c8326a745296c57050af9016c929d34cd"),
            new Pin("ck3_autonomous_player/native_bridge/src/ck3_12002_family_obligations_mailbox.cpp", 11282, "bc89b4a54b1960d99d4062b9254180b2ce48a8e1ab0e58aa45c6d39f87f0c71c"),
            new Pin("ck3_autonomous_player/native_bridge/src/ck3_12004_family_obligations_alliance.cpp", 3938, "d4bb07567ef1da44731a14c59adc0e25a7e9502dcb54ad3f5c9650fc9c6b9682"),
            new Pin("ck3_autonomous_player/native_bridge/src/ck3_12004_adapter.cpp", 22031, "38faf84e616608b49c3c4d39698c884229347cc630f612a6af0b371ceb33b972"));
    private record Pin(String path, long bytes, String sha256) { }

    @Test void originalNativePacketsKeepCompleteLineageBreakAndPenaltyRoundtrip() throws Exception {
        verifyPins();
        for (String name : List.of("mailbox", "terms")) {
            ObjectNode raw = packet(name); Request request = request(raw); Observation result = decode(raw, request, Build.ORIGINAL2);
            assertArrayEquals(StrictJson.canonical(raw), FamilyObligationsCodec.encodeNative(result).bytes());
            assertEquals(result, FamilyObligationsCodec.decodeNative(FamilyObligationsCodec.encodeNative(result), result.binding(), request));
            assertTrue(result.lineage().terms().orElseThrow().selectedMatrilineal());
            assertFalse(result.lineage().terms().orElseThrow().effectiveMatrilinealIfAccepted());
            assertFalse(result.businessPostconditionVerified()); assertFalse(result.fullProductAcceptanceCredit());
        }
        Observation result = decode(packet("terms"), request(packet("terms")), Build.ORIGINAL2);
        BreakValues values = result.betrothalBreak().values().orElseThrow();
        assertEquals(0L, values.sendCosts().orElseThrow().slots().get(1));
        assertEquals(-8_000_000L, values.outcomePenalty().terms().orElseThrow().stockPrestigeEffectRaw());
        assertFalse(values.outcomePenalty().effectsComplete()); assertTrue(result.lineage().terms().orElseThrow().dynasty().isEmpty());
        verifyPins();
    }
    @Test void samePacketsPassOriginalPythonNormalizerAndPreserveEveryField() throws Exception {
        verifyPins(); String executable = requiredProperty("xar.python"); Path root = repository();
        String script = """
                import json, pathlib, sys
                root=pathlib.Path(sys.argv[1])
                sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.bridge.family_obligations_private_transport import normalize_family_obligations_private_v1
                output=[]
                for name in ('mailbox','terms'):
                    value=json.loads((root/('ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_family_obligations_'+name+'.json')).read_text(encoding='utf-8'))['result']
                    frame=value['frame']; lineage=value['native_child_house_preview']; terms=value['betrothal_break_terms']
                    snapshot={'native_revision':frame['snapshot_revision'],'date_raw':frame['date_raw'],'played_character':{'character_id':frame['played_character_id']},'diagnostics':{'hello':{'expected_ck3_version':value['game_version'],'expected_ck3_sha256':value['executable_sha256']}}}
                    args={'subject_character_id':lineage['subject_character_id'],'candidate_character_id':lineage['candidate_character_id'],'request_matrilineal_option':lineage['requested_matrilineal_option']}
                    if terms['status']!='not_requested': args['break_recipient_character_id']=terms['requested_recipient_character_id']
                    output.append(normalize_family_obligations_private_v1(value,snapshot=snapshot,**args))
                print(json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')))
                """;
        ProcessBuilder builder = new ProcessBuilder(executable, "-B", "-c", script, root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.redirectErrorStream(true);
        Process process = builder.start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new AssertionError("original Python normalizer timed out"); }
        byte[] output = process.getInputStream().readNBytes(65_537); assertEquals(0, process.exitValue(), new String(output, StandardCharsets.UTF_8)); assertTrue(output.length <= 65_536);
        JsonNode rows = StrictJson.parse(output); assertTrue(rows.isArray()); assertEquals(2, rows.size());
        int index = 0; for (String name : List.of("mailbox", "terms")) {
            ObjectNode original = packet(name); assertEquals(original, rows.get(index++));
            Observation result = decode(original, request(original), Build.ORIGINAL2);
            assertEquals(original, StrictJson.parse(FamilyObligationsCodec.encodeNative(result).bytes()));
        }
        verifyPins();
    }
    @Test void currentSyntheticBuildKeepsHistoricalPenaltySourceAndRejectsMixedBuild() throws Exception {
        ObjectNode n = current(packet("terms")); Request request = request(n); Observation result = decode(n, request, Build.CURRENT4);
        assertEquals("stock_branch_projection_1.20.0.2", result.betrothalBreak().values().orElseThrow().outcomePenalty().source());
        ObjectNode mixed = n.deepCopy().put("executable_sha256", Build.ORIGINAL2.sha256()); assertThrows(IllegalArgumentException.class, () -> decode(mixed, request, Build.CURRENT4));
        ObjectNode missing = n.deepCopy(); missing.remove("current_native_allies"); assertThrows(IllegalArgumentException.class, () -> decode(missing, request, Build.CURRENT4));
        assertEquals(result, decode(n, request, Build.CURRENT4));
    }
    @Test void fullSyntheticAllianceCarriesIndependentRawAnswersAllCostsAndC88Text() throws Exception {
        ObjectNode n = alliancePacket(); Request request = allianceRequest(); Observation result = decode(n, request, Build.CURRENT4);
        War first = result.alliance().terms().orElseThrow().firstWars().getFirst();
        assertEquals(Answer.RAW_0, first.selectedTerms().orElseThrow().recipientAnswer());
        assertEquals(Answer.RAW_2, first.diagnostics().orElseThrow().values().orElseThrow().sendAnswer());
        assertEquals(9_007_199_254_740_993L, first.selectedTerms().orElseThrow().recipientAcceptanceRaw());
        assertEquals(Long.MIN_VALUE, first.selectedTerms().orElseThrow().sendCosts().slots().getFirst());
        assertEquals(Long.MAX_VALUE, first.selectedTerms().orElseThrow().sendCosts().slots().get(1));
        assertEquals("", first.c88Description().orElseThrow().values().orElseThrow().text().orElseThrow());
        assertTrue(result.currentAllies().orElseThrow().terms().orElseThrow().unresolvedSourceIds().contains(901L));
        assertEquals(n, StrictJson.parse(FamilyObligationsCodec.encodeNative(result).bytes()));
        ObjectNode bad = n.deepCopy(); ((ObjectNode) bad.path("alliance_obligations").path("first_wars").get(0)).put("native_send_answer_status_raw", true);
        assertThrows(IllegalArgumentException.class, () -> decode(bad, request, Build.CURRENT4));
    }
    @Test void syntheticUnselectedWarKeepsExplicitNullAndMissingAdditiveGroupsSeparate() throws Exception {
        ObjectNode n = alliancePacket(); ObjectNode war = (ObjectNode) n.path("alliance_obligations").path("first_wars").get(0);
        war.put("native_selected_target_context_available", false).put("native_target_can_be_picked", false).put("native_target_row_selectable", false);
        for (String field : List.of("native_complete_can_send", "send_cost_raw", "recipient_acceptance_raw", "recipient_answer_status_raw", "native_auto_accept",
                "native_send_answer_status_raw", "native_send_precheck_passed", "native_send_setup_passed", "native_send_availability_passed", "native_send_pair_restriction_blocked", "native_send_diplomatic_range_passed", "native_send_already_considering_blocked", "native_send_definition_gate_results", "native_first_failed_send_stage", "native_c88_failure_description_status", "native_c88_failure_description_text")) war.putNull(field);
        Request request = allianceRequest(); Observation result = decode(n, request, Build.CURRENT4); War decoded = result.alliance().terms().orElseThrow().firstWars().getFirst();
        assertTrue(decoded.selectedTerms().isEmpty()); assertTrue(decoded.diagnostics().orElseThrow().values().isEmpty()); assertTrue(decoded.c88Description().orElseThrow().values().isEmpty());
        ObjectNode bad = n.deepCopy(); ((ObjectNode) bad.path("alliance_obligations").path("first_wars").get(0)).remove("send_cost_raw"); assertThrows(IllegalArgumentException.class, () -> decode(bad, request, Build.CURRENT4));
        ObjectNode absent = alliancePacket(); ObjectNode legacy = (ObjectNode) absent.path("alliance_obligations").path("first_wars").get(0);
        legacy.remove(List.of("native_selected_target_context_available", "native_send_answer_status_raw", "native_send_precheck_passed", "native_send_setup_passed", "native_send_availability_passed", "native_send_pair_restriction_blocked", "native_send_diplomatic_range_passed", "native_send_already_considering_blocked", "native_send_definition_gate_results", "native_first_failed_send_stage", "native_c88_failure_description_status", "native_c88_failure_description_text"));
        War old = decode(absent, request, Build.CURRENT4).alliance().terms().orElseThrow().firstWars().getFirst();
        assertTrue(old.selectedContextAvailable().isEmpty()); assertTrue(old.diagnostics().isEmpty()); assertTrue(old.selectedTerms().isPresent());
    }
    @Test void requestRejectsNullBoolFloatPartialPairUnknownFieldAndWrongRevision() {
        for (String raw : List.of("{}", "{\"expected_revision\":true}", "{\"expected_revision\":1.0}", "{\"expected_revision\":54,\"subject_character_id\":1}",
                "{\"expected_revision\":54,\"ally_character_id\":null}", "{\"expected_revision\":54,\"ally_character_id\":1,\"enumerate_current_allies\":null}",
                "{\"expected_revision\":54,\"ally_character_id\":1,\"unscoped\":1}", "{\"expected_revision\":54,\"ally_character_id\":1,\"request_matrilineal_option\":true}")) {
            assertThrows(IllegalArgumentException.class, () -> FamilyObligationsCodec.decodeRequest(raw.getBytes(StandardCharsets.UTF_8)), raw);
        }
        Request request = new Request(BigInteger.valueOf(54), Optional.empty(), false, OptionalLong.empty(), OptionalLong.of(3), true);
        assertEquals(request, FamilyObligationsCodec.decodeRequest(FamilyObligationsCodec.encodeRequest(request).bytes()));
        assertFalse(FamilyObligationsCodec.wireFields(request).has("expected_revision"));
    }
    @Test void wrongFieldTypeMissingAndAvailabilityDriftCannotBecomeUsableValues() throws Exception {
        ObjectNode n = current(packet("terms")); Request request = request(n);
        ObjectNode missing = n.deepCopy(); ((ObjectNode) missing.get("native_child_house_preview")).remove("house_id"); assertThrows(IllegalArgumentException.class, () -> decode(missing, request, Build.CURRENT4));
        ObjectNode boolId = n.deepCopy(); ((ObjectNode) boolId.get("frame")).put("played_character_id", true); assertThrows(IllegalArgumentException.class, () -> decode(boolId, request, Build.CURRENT4));
        ObjectNode decimalCost = n.deepCopy(); ((com.fasterxml.jackson.databind.node.ArrayNode) decimalCost.path("betrothal_break_terms").path("native_send_costs_raw")).set(0, StrictJson.parse("1.0".getBytes(StandardCharsets.UTF_8))); assertThrows(IllegalArgumentException.class, () -> decode(decimalCost, request, Build.CURRENT4));
        ObjectNode changed = n.deepCopy().put("query_status", "partial"); assertThrows(IllegalArgumentException.class, () -> decode(changed, request, Build.CURRENT4));
        ObjectNode extra = n.deepCopy().put("postcondition", true); assertThrows(IllegalArgumentException.class, () -> decode(extra, request, Build.CURRENT4));
        ObjectNode crossFrame = n.deepCopy(); ((ObjectNode) crossFrame.get("frame")).put("snapshot_revision", 54); assertThrows(IllegalArgumentException.class, () -> decode(crossFrame, request, Build.CURRENT4));
    }
    @Test void installedContractUsesOneGuardedReadAndOriginalOrdinaryConsumerShape() throws Exception {
        Path p = repository().resolve(TRANSPORT); byte[] body = Files.readAllBytes(p); ExactRef source = new ExactRef(p.toString(), body.length, digest(body));
        var contract = FamilyObligationsQueries.contract(source, (actual, arguments) -> { throw new IllegalStateException("unqualified actual Root admission"); });
        assertEquals(FamilyObligations.STEP, contract.operation().value()); assertEquals(FamilyObligations.PERMISSION, contract.permissionKey());
        assertEquals(org.xar.ck3.control.application.action.ReadContract.WireProfile.G2_PRIVATE_QUERY, contract.wireProfile());
        ObjectNode n = current(packet("mailbox")); Observation observation = decode(n, request(n), Build.CURRENT4);
        var projected = FamilyObligationsQueries.project(observation); ObjectNode expected = n.deepCopy().put("queried_snapshot_id", "native:53").put("queried_revision", 54).put("queried_native_revision", 53);
        assertEquals(expected, OpportunityJson.toNode(projected)); assertEquals(FamilyObligationsQueries.arguments(observation.request()), OpportunityJson.parse(FamilyObligationsCodec.encodeRequest(observation.request()).bytes()));
    }
    private static ObjectNode packet(String name) throws Exception { return (ObjectNode) StrictJson.parse(Files.readAllBytes(repository().resolve(BASE + name + ".json"))).get("result"); }
    private static Request request(ObjectNode packet) {
        JsonNode lineage = packet.get("native_child_house_preview"), terms = packet.get("betrothal_break_terms");
        return new Request(BigInteger.valueOf(54), Optional.of(new Pair(lineage.get("subject_character_id").longValue(), lineage.get("candidate_character_id").longValue())), lineage.get("requested_matrilineal_option").booleanValue(),
                terms.get("status").asText().equals("not_requested") ? OptionalLong.empty() : OptionalLong.of(terms.get("requested_recipient_character_id").longValue()), OptionalLong.empty(), false);
    }
    private static Observation decode(ObjectNode packet, Request request, Build build) {
        return FamilyObligationsCodec.decodeNative(new RawJson(StrictJson.canonical(packet)), new Binding(build, "native:53", BigInteger.valueOf(54), BigInteger.valueOf(53), 53220000, 16777217), request);
    }
    private static ObjectNode current(ObjectNode n) {
        n.put("game_version", Build.CURRENT4.version()).put("executable_sha256", Build.CURRENT4.sha256());
        n.set("current_native_allies", StrictJson.object().put("status", "not_requested").put("reason", "").put("played_character_id", 16777217)); return n;
    }
    private static Request allianceRequest() { return new Request(BigInteger.valueOf(54), Optional.of(new Pair(16777218, 16777219)), true, OptionalLong.empty(), OptionalLong.of(44), true); }
    private static ObjectNode alliancePacket() throws Exception {
        ObjectNode n = current(packet("mailbox")); ObjectNode alliance = StrictJson.object().put("status", "available").put("reason", "").put("first_character_id", 16777217).put("second_character_id", 44).put("first_has_second", true).put("second_has_first", false).put("raw_scale", 100000);
        var keys = alliance.putArray("send_cost_slot_keys"); for (String key : "gold prestige piety renown influence herd treasury treasury_or_gold merit barter_goods".split(" ")) keys.add(key);
        alliance.putArray("first_wars").add(war(16777217, 44)); alliance.putArray("second_wars"); n.set("alliance_obligations", alliance);
        ObjectNode allies = StrictJson.object().put("status", "available").put("reason", "").put("played_character_id", 16777217);
        allies.putArray("source_character_ids").add(44).add(901).add(902); allies.putArray("unresolved_source_character_ids").add(901); allies.putArray("dead_source_character_ids").add(902);
        allies.putArray("allies").add(StrictJson.object().put("character_id", 44).put("player_has_ally", true).put("ally_has_player", true).put("has_realm_data", false)); n.set("current_native_allies", allies); return n;
    }
    private static ObjectNode war(long caller, long recipient) {
        ObjectNode n = StrictJson.object().put("war_id", 71).put("caller_character_id", caller).put("recipient_character_id", recipient).put("caller_side", "defender").put("recipient_side", "absent").put("primary_attacker_character_id", 72).put("primary_defender_character_id", caller);
        n.putArray("attacker_character_ids").add(72); n.putArray("defender_character_ids").add(caller);
        n.put("caller_is_primary_war_leader", true).put("recipient_was_called", false).put("native_target_can_be_picked", true).put("native_target_row_selectable", false).put("native_selected_target_context_available", true).put("native_complete_can_send", false);
        var costs = n.putArray("send_cost_raw"); costs.add(Long.MIN_VALUE).add(Long.MAX_VALUE); for (int index = 2; index < 10; index++) costs.add(index);
        n.put("recipient_acceptance_raw", 9_007_199_254_740_993L).put("recipient_answer_status_raw", 0).put("native_auto_accept", false).put("native_send_answer_status_raw", 2)
                .put("native_send_precheck_passed", false).put("native_send_setup_passed", true).put("native_send_availability_passed", true).put("native_send_pair_restriction_blocked", false).put("native_send_diplomatic_range_passed", true).put("native_send_already_considering_blocked", false);
        var gates = n.putArray("native_send_definition_gate_results"); for (int index = 0; index < 7; index++) gates.add(index != 1);
        n.put("native_first_failed_send_stage", "definition_c88").put("native_c88_failure_description_status", "observed").put("native_c88_failure_description_text", ""); return n;
    }
    private static void verifyPins() throws Exception {
        for (Pin pin : PINS) { byte[] body = Files.readAllBytes(repository().resolve(pin.path())); assertEquals(pin.bytes(), body.length, pin.path()); assertEquals(pin.sha256(), digest(body), pin.path()); }
    }
    private static String digest(byte[] body) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)); }
    private static Path repository() { return Path.of(requiredProperty("xar.repository.root")).toAbsolutePath().normalize(); }
    private static String requiredProperty(String key) { String value = System.getProperty(key); assertNotNull(value, "required CI property: " + key); assertFalse(value.isBlank(), "required CI property: " + key); return value; }
}
