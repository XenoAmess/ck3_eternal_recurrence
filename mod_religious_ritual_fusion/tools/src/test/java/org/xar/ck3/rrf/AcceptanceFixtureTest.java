package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

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
import org.xar.ck3.rrf.acceptance.FixtureContracts.CaseKind;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FreshSetup;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Mode;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Request;
import org.xar.ck3.rrf.acceptance.FixtureContracts.SavedSetup;
import org.xar.ck3.rrf.acceptance.FixtureEmitter;

final class AcceptanceFixtureTest {
    @TempDir Path directory;
    @Test void realFixtureProducerCreatesExactSourcePinnedPublicImportAndReadOnlyObservations() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Request request = new Request(1, CaseKind.CORE, Mode.RITE, 29829, new FreshSetup(500));
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, directory.resolve("fixture"), "synthetic-fixture-machine", request);
        FixtureContracts.Manifest decoded = Json.read(Files.readAllBytes(emitted.manifest()), FixtureContracts.Manifest.class);
        assertEquals(decoded, emitted.payload()); assertEquals(7, decoded.files().size());
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
            Clausewitz.Block body = Clausewitz.parse(text); allKeys.addAll(keys(body));
            assertFalse(keys(body).contains("rrf_commit_effect"));
            if (relative.contains("observation")) assertReadOnly(keys(body));
        }
        assertEquals(3, allKeys.stream().filter("create_dynamic_rite"::equals).count());
        assertEquals(1, allKeys.stream().filter("detach_rite_to_new_faith"::equals).count());
        assertTrue(allKeys.contains("add_known_tenet")); assertTrue(allKeys.contains("add_known_doctrine"));
        assertThrows(IllegalArgumentException.class, () -> FixtureEmitter.emit(repository, emitted.fixture(), "synthetic-fixture-machine", request));
        assertEquals(67, ContentValidator.validate(repository.resolve("mod_religious_ritual_fusion")).runtimeFiles());
    }
    @Test void faithRejectionAndColdClosuresUseActualModeAndColdCannotSeed() throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        for (Request request : List.of(new Request(1, CaseKind.CORE, Mode.FAITH, 29829, new FreshSetup(1000)), new Request(1, CaseKind.UI_REJECTION, Mode.RITE, 29829, new FreshSetup(499)), new Request(1, CaseKind.COLD_RELOAD, Mode.RITE, 29829, new SavedSetup()), new Request(1, CaseKind.COLD_RELOAD, Mode.FAITH, 29829, new SavedSetup()))) {
            Path target = directory.resolve(request.kind().wire() + "-" + request.mode().wire());
            FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository, target, "synthetic-fixture-machine", request);
            assertEquals(request.kind().wire(), emitted.payload().caseId());
            if (request.kind() == CaseKind.COLD_RELOAD) {
                assertEquals(5, emitted.payload().files().size());
                assertFalse(emitted.payload().receipt().containsBusinessEffects());
                assertTrue(emitted.payload().files().keySet().stream().noneMatch(p -> p.contains("seed") || p.contains("fresh")));
                for (String relative : emitted.payload().files().keySet()) assertReadOnly(keys(Clausewitz.parse(Files.readString(target.resolve(relative)))));
            }
            assertTrue(Files.readString(target.resolve("events/rrfa_observation_events.txt")).contains(request.mode().wire() + "_persisted_readback"));
        }
    }
    @Test void strictInputTypesAndCampaignKindsRejectInvalidOrAmbiguousRecipes() throws IOException {
        Request valid = new Request(1, CaseKind.CORE, Mode.RITE, 29829, new FreshSetup(500));
        String json = new String(Json.write(valid), StandardCharsets.UTF_8);
        assertEquals(valid, Json.read(json.getBytes(StandardCharsets.UTF_8), Request.class));
        for (String invalid : List.of(json.replace("29829", "true"), json.replace("29829", "29829.0"), json.replace("\"piety\" : 500", "\"piety\" : 500.0"), json.replace("\"piety\" : 500", "\"piety\" : true"), json.replace("\"rite\"", "\"cross_religion\""), json.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : 1, \"extra\" : true"))) assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IllegalArgumentException.class, () -> new Request(1, CaseKind.CORE, Mode.RITE, 29829, new FreshSetup(499)));
        assertThrows(IllegalArgumentException.class, () -> new Request(1, CaseKind.COLD_RELOAD, Mode.RITE, 29829, new FreshSetup(500)));
        assertThrows(IllegalArgumentException.class, () -> new Request(1, CaseKind.CORE, Mode.RITE, 29829, new SavedSetup()));
        assertThrows(IllegalArgumentException.class, () -> new Request(1, CaseKind.CORE, Mode.RITE, 1, new FreshSetup(500)));
        assertThrows(IOException.class, () -> Json.read("{\"schemaVersion\":1,\"kind\":\"cold_reload\",\"mode\":\"rite\",\"actorId\":29829,\"setup\":{\"type\":\"saved\",\"piety\":500}}".getBytes(StandardCharsets.UTF_8), Request.class));
    }
    private static List<String> keys(Clausewitz.Block block) { List<String> keys = new ArrayList<>(); for (Clausewitz.Entry e : block.entries()) { keys.add(e.key()); if (e.value() instanceof Clausewitz.Block child) keys.addAll(keys(child)); } return keys; }
    private static void assertReadOnly(List<String> keys) {
        Set<String> writes = Set.of("set_variable", "add_character_flag", "remove_character_flag", "add_to_variable_list", "clear_variable_list", "add_piety", "set_character_rite", "change_rite_doctrine", "create_dynamic_rite", "detach_rite_to_new_faith", "add_known_tenet", "add_known_doctrine");
        assertTrue(keys.stream().noneMatch(writes::contains), keys.toString());
    }
}
