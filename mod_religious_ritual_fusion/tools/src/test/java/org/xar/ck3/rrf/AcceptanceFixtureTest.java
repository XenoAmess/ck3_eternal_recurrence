package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.acceptance.FixtureContracts;
import org.xar.ck3.rrf.acceptance.FixtureContracts.ActorHistoryId;
import org.xar.ck3.rrf.acceptance.FixtureContracts.CaseKind;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FreshSetup;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Mode;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Request;
import org.xar.ck3.rrf.acceptance.FixtureContracts.SavedSetup;
import org.xar.ck3.rrf.acceptance.FixtureEmitter;

final class AcceptanceFixtureTest {
    private static final ActorHistoryId ROBERT = new ActorHistoryId("1128");
    @TempDir Path directory;
    @Test void realFixtureProducerCreatesExactSourcePinnedPublicImportAndReadOnlyObservations() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Request request = bundledRequest(repository, "core-rite");
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, directory.resolve("fixture"), "synthetic-fixture-machine", request);
        FixtureContracts.Manifest decoded = Json.read(Files.readAllBytes(emitted.manifest()), FixtureContracts.Manifest.class);
        assertEquals(decoded, emitted.payload()); assertEquals(10, decoded.files().size());
        assertEquals(request, Json.read(Files.readAllBytes(emitted.requestSnapshot()), Request.class));
        assertEquals(List.of("RRFAT: TEST PASS fixture_ready", "RRFAT: TEST PASS rite_success_readback"), decoded.receipt().requiredMarkers());
        for (FixtureContracts.FilePin pin : decoded.producerSourcePins()) {
            assertTrue(Path.of(pin.path()).startsWith(repository));
            assertEquals(pin.sha256(), ReleaseBuilder.sha256(Files.readAllBytes(Path.of(pin.path()))));
        }
        assertEquals(decoded.files().keySet(), ContentValidator.inventory(emitted.fixture(), true).keySet());
        List<String> allKeys = new ArrayList<>();
        for (String relative : decoded.files().keySet()) {
            byte[] bytes = Files.readAllBytes(emitted.fixture().resolve(relative));
            assertEquals(decoded.files().get(relative).sha256(), ReleaseBuilder.sha256(bytes));
            String text = new String(bytes, StandardCharsets.UTF_8); assertFalse(text.contains("${"));
            if (!relative.equals("descriptor.mod")) assertTrue(text.startsWith("\ufeff"));
            if (relative.endsWith(".yml")) continue;
            Clausewitz.Block body = Clausewitz.parse(text); allKeys.addAll(keys(body));
            assertFalse(keys(body).contains("rrf_commit_effect"));
            if (relative.contains("observation")) assertReadOnly(keys(body));
        }
        assertEquals(3, allKeys.stream().filter("create_dynamic_rite"::equals).count());
        assertEquals(1, allKeys.stream().filter("detach_rite_to_new_faith"::equals).count());
        assertHistoryLinks(emitted.fixture(), decoded.files().keySet(), 6);
        JsonNode identityEvidence = Json.read(Files.readAllBytes(repository.resolve("mod_religious_ritual_fusion/tools/src/main/resources/acceptance/native-source-evidence.json")), JsonNode.class).path("actor_identity");
        assertEquals(request.actorHistoryId().value(), identityEvidence.path("actor_history_id").textValue());
        assertEquals(request.actorHistoryId().value(), identityEvidence.path("history_definition").path("definition_key").textValue());
        assertEquals(request.actorHistoryId().value(), identityEvidence.path("bookmark").path("history_id").textValue());
        assertEquals("character:" + request.actorHistoryId().value(), Clausewitz.parse(identityEvidence.path("native_script_link").path("clause").textValue()).atom("this", ""));
        assertObservationDecision(emitted.fixture(), request);
        assertTrue(allKeys.contains("add_known_tenet")); assertTrue(allKeys.contains("add_known_doctrine"));
        assertThrows(IllegalArgumentException.class, () -> FixtureEmitter.emit(repository, emitted.fixture(), "synthetic-fixture-machine", request));
        assertEquals(67, ContentValidator.validate(repository.resolve("mod_religious_ritual_fusion")).runtimeFiles());
    }
    @Test void faithRejectionAndColdClosuresUseActualModeAndColdCannotSeed() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        for (String recipe : List.of("core-faith", "ui-rejection", "cold-rite", "cold-faith")) {
            Request request = bundledRequest(repository, recipe);
            Path target = directory.resolve(request.kind().wire() + "-" + request.mode().wire());
            FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, target, "synthetic-fixture-machine", request);
            assertEquals(request.kind().wire(), emitted.payload().caseId());
            assertHistoryLinks(target, emitted.payload().files().keySet(), request.kind() == CaseKind.COLD_RELOAD ? 4 : 6);
            if (request.kind() == CaseKind.COLD_RELOAD) {
                assertEquals(Set.of("descriptor.mod", "common/scripted_triggers/rrfa_observation_triggers.txt",
                        "common/script_values/rrfa_observation_values.txt", "events/rrfa_observation_events.txt",
                        "common/decisions/rrfa_cold_observation_decisions.txt", "localization/english/rrfa_observation_l_english.yml",
                        "localization/simp_chinese/rrfa_observation_l_simp_chinese.yml"), emitted.payload().files().keySet());
                assertEquals(7, emitted.payload().files().size());
                assertEquals(emitted.payload(), Json.read(Files.readAllBytes(emitted.manifest()), FixtureContracts.Manifest.class));
                assertFalse(emitted.payload().receipt().containsBusinessEffects());
                assertTrue(emitted.payload().files().keySet().stream().noneMatch(p -> p.contains("seed") || p.contains("fresh") || p.contains("on_action")));
                for (String relative : emitted.payload().files().keySet()) if (!relative.endsWith(".yml")) {
                    List<String> coldKeys = keys(Clausewitz.parse(Files.readString(target.resolve(relative))));
                    assertReadOnly(coldKeys);
                    for (String registrar : List.of("on_actions", "on_game_start_after_lobby", "events")) assertFalse(coldKeys.contains(registrar));
                }
                assertObservationDecision(target, request);
            } else { assertEquals(10, emitted.payload().files().size()); assertObservationDecision(target, request); }
            assertTrue(Files.readString(target.resolve("events/rrfa_observation_events.txt")).contains(request.mode().wire() + "_persisted_readback"));
        }
    }
    @Test void strictInputTypesAndCampaignKindsRejectInvalidOrAmbiguousRecipes() throws IOException {
        Request valid = new Request(2, CaseKind.CORE, Mode.RITE, ROBERT, new FreshSetup(500));
        String json = new String(Json.write(valid), StandardCharsets.UTF_8);
        assertEquals(valid, Json.read(json.getBytes(StandardCharsets.UTF_8), Request.class));
        assertTrue(json.contains("\"actorHistoryId\" : \"1128\""));
        for (String identity : List.of("true", "1128", "1128.0", "null", "[]", "{}", "\"\"", "\"01128\"", "\"1128.0\"", "\"29829\"")) {
            String invalid = json.replace("\"1128\"", identity);
            assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Request.class), identity);
        }
        for (String invalid : List.of(json.replace("\"piety\" : 500", "\"piety\" : 500.0"), json.replace("\"piety\" : 500", "\"piety\" : true"), json.replace("\"rite\"", "\"cross_religion\""), json.replace("\"schemaVersion\" : 2", "\"schemaVersion\" : 1"), json.replace("\"schemaVersion\" : 2", "\"schemaVersion\" : 2, \"extra\" : true"), json.replace("\"actorHistoryId\" : \"1128\"", "\"actorId\" : 29829"), json.replace("\"actorHistoryId\" : \"1128\"", "\"actorHistoryId\" : \"1128\", \"actorId\" : 29829"), json.replace("  \"actorHistoryId\" : \"1128\",\n", ""))) assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, CaseKind.CORE, Mode.RITE, ROBERT, new FreshSetup(499)));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, CaseKind.COLD_RELOAD, Mode.RITE, ROBERT, new FreshSetup(500)));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, CaseKind.CORE, Mode.RITE, ROBERT, new SavedSetup()));
        assertThrows(IllegalArgumentException.class, () -> new Request(1, CaseKind.CORE, Mode.RITE, ROBERT, new FreshSetup(500)));
        assertThrows(IllegalArgumentException.class, () -> new ActorHistoryId("29829"));
        assertThrows(IOException.class, () -> Json.read("{\"schemaVersion\":1,\"kind\":\"cold_reload\",\"mode\":\"rite\",\"actorId\":29829,\"setup\":{\"type\":\"saved\"}}".getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IOException.class, () -> Json.read("{\"schemaVersion\":2,\"kind\":\"cold_reload\",\"mode\":\"rite\",\"actorHistoryId\":\"1128\",\"setup\":{\"type\":\"saved\",\"piety\":500}}".getBytes(StandardCharsets.UTF_8), Request.class));
    }
    private static List<String> keys(Clausewitz.Block block) { List<String> keys = new ArrayList<>(); for (Clausewitz.Entry e : block.entries()) { keys.add(e.key()); if (e.value() instanceof Clausewitz.Block child) keys.addAll(keys(child)); } return keys; }
    private static void assertObservationDecision(Path fixture, Request request) throws IOException {
        boolean cold = request.kind() == CaseKind.COLD_RELOAD;
        String key = cold ? "rrfa_observe_cold_decision" : "rrfa_observe_" + request.kind().wire() + "_decision";
        String decisionFile = cold ? "rrfa_cold_observation_decisions.txt" : "rrfa_observation_decisions.txt";
        Clausewitz.Block decision = Clausewitz.parse(Files.readString(fixture.resolve("common/decisions/" + decisionFile))).block(key);
        for (String gate : List.of("is_shown", "is_valid")) {
            assertEquals("no", decision.block(gate).atom("is_ai", ""));
            assertEquals("character:" + request.actorHistoryId().value(), decision.block(gate).atom("this", ""));
            assertEquals(cold ? "rrfa_mode" : "rrfa_seed_done", decision.block(gate).atom(cold ? "has_variable" : "has_character_flag", ""));
        }
        Clausewitz.Block effect = decision.block("effect"); assertEquals(1, effect.entries().size());
        assertEquals("trigger_event", effect.entries().getFirst().key());
        Clausewitz.Block trigger = effect.block("trigger_event"); assertEquals(1, trigger.entries().size());
        assertEquals(cold ? "rrfa.22" : request.kind() == CaseKind.UI_REJECTION ? "rrfa.30" : request.mode() == Mode.RITE ? "rrfa.20" : "rrfa.21", trigger.atom("id", ""));
        assertReadOnly(keys(effect));
        for (String forbidden : List.of("cost", "cooldown", "days")) assertFalse(keys(decision).contains(forbidden));
        Set<String> expected = Set.of(key, "rrfa_observation_decision_desc", "rrfa_observation_decision_tooltip", "rrfa_observation_decision_confirm");
        for (String language : List.of("english", "simp_chinese")) {
            String text = Files.readString(fixture.resolve("localization/" + language + "/rrfa_observation_l_" + language + ".yml"));
            assertTrue(text.startsWith("\ufeffl_" + language + ":\n"));
            Set<String> actual = new java.util.LinkedHashSet<>();
            for (String line : text.lines().skip(1).toList()) if (!line.isBlank()) { assertTrue(line.matches(" [A-Za-z_][A-Za-z0-9_]*:0 \\\".*\\\"")); actual.add(line.substring(1, line.indexOf(':'))); }
            assertEquals(expected, actual);
        }
    }
    private static void assertReadOnly(List<String> keys) {
        Set<String> writes = Set.of("set_variable", "add_character_flag", "remove_character_flag", "add_to_variable_list", "clear_variable_list", "add_piety", "set_character_rite", "change_rite_doctrine", "create_dynamic_rite", "detach_rite_to_new_faith", "add_known_tenet", "add_known_doctrine");
        assertTrue(keys.stream().noneMatch(writes::contains), keys.toString());
    }
    private static Request bundledRequest(Path repository, String recipe) throws IOException {
        Request request = Json.read(Files.readAllBytes(repository.resolve("mod_religious_ritual_fusion/tools/src/main/resources/acceptance/requests/" + recipe + ".json")), Request.class);
        assertEquals(2, request.schemaVersion()); assertEquals(ROBERT, request.actorHistoryId());
        return request;
    }
    private static void assertHistoryLinks(Path fixture, Set<String> files, int expectedCount) throws IOException {
        List<String> links = new ArrayList<>();
        for (String relative : files) if (relative.endsWith(".txt")) collectHistoryLinks(Clausewitz.parse(Files.readString(fixture.resolve(relative))), links);
        assertEquals(java.util.Collections.nCopies(expectedCount, "character:1128"), links);
    }
    private static void collectHistoryLinks(Clausewitz.Block block, List<String> links) {
        for (Clausewitz.Entry entry : block.entries()) {
            if (entry.key().startsWith("character:")) links.add(entry.key());
            if (entry.value() instanceof Clausewitz.Block child) collectHistoryLinks(child, links);
            else if (entry.value() instanceof Clausewitz.Atom atom && atom.token().startsWith("character:")) links.add(atom.token());
        }
    }
}
