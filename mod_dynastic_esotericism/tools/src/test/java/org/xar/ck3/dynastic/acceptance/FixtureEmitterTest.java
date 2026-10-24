package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class FixtureEmitterTest {
    @TempDir Path temporary;

    private static Path repository() {
        return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
    }

    @Test
    void realProducerWritesExactManifestAndSeparateFixture() throws IOException, NoSuchAlgorithmException {
        FixtureEmitter.Emission result = FixtureEmitter.emit(repository(), temporary.resolve("fixture"), "authored-machine");
        JsonNode decoded = new ObjectMapper().readTree(result.manifest().toFile());
        assertEquals("ck3-mod-acceptance-prebuilt-fixture-v1", decoded.path("schema").textValue());
        assertEquals("dynastic-esotericism", decoded.path("product").textValue());
        assertEquals("core", decoded.path("case_id").textValue());
        assertEquals("authored-machine", decoded.path("machine_id").textValue());
        assertEquals(13, decoded.path("files").size());
        assertEquals(14, decoded.path("producer_source_pins").size());
        assertEquals(22, decoded.path("receipt").path("required_markers").size());
        assertTrue(decoded.path("receipt").path("fixture_contains_business_effects").booleanValue());
        for (var entry : result.payload().files().entrySet()) {
            byte[] bytes = Files.readAllBytes(result.fixture().resolve(entry.getKey()));
            assertEquals(bytes.length, entry.getValue().bytes());
            assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),
                    entry.getValue().sha256());
            if (entry.getKey().equals("descriptor.mod")) {
                assertEquals('n', bytes[0]);
            } else {
                assertArrayEquals(new byte[]{(byte) 0xef, (byte) 0xbb, (byte) 0xbf},
                        new byte[]{bytes[0], bytes[1], bytes[2]});
            }
        }
        assertFalse(Files.exists(result.fixture().resolve("_case_contract.json")));
        String events = Files.readString(result.fixture().resolve("events/des_acceptance_events.txt"), StandardCharsets.UTF_8);
        assertTrue(events.contains("rite_has_doctrine = des_doctrine_none"));
        assertTrue(events.contains("des_has_active_binding_trigger = yes"));
        String decisions = Files.readString(result.fixture().resolve("common/decisions/des_acceptance_decisions.txt"), StandardCharsets.UTF_8);
        assertTrue(decisions.contains("set_character_rite = rite:byzantine_rite"));
        assertFalse(events.contains("add_trait = des_apostate"));
        assertFalse(events.contains("des_sync_character_effect = yes"));
        assertThrows(IllegalArgumentException.class,
                () -> FixtureEmitter.emit(repository(), result.fixture(), "authored-machine"));
    }

    @Test
    void passiveColdAndBootstrapKeepNoColdRegistrarAndSeedHasNoProductState() throws IOException {
        for (FixtureEmitter.CaseKind kind : new FixtureEmitter.CaseKind[]{
                FixtureEmitter.CaseKind.COLD_RELOAD, FixtureEmitter.CaseKind.OLD_SAVE_BOOTSTRAP}) {
            FixtureEmitter.Emission result = FixtureEmitter.emit(repository(), temporary.resolve(kind.wireValue()), "authored-machine", kind);
            assertEquals(kind.wireValue(), result.payload().caseId());
            assertEquals(12, result.payload().files().size());
            for (String name : result.payload().files().keySet()) {
                if (name.endsWith(".txt")) {
                    assertFalse(Files.readString(result.fixture().resolve(name)).contains("on_game_start_after_lobby"));
                }
            }
        }
        FixtureEmitter.Emission seed = FixtureEmitter.emit(repository(), temporary.resolve("seed"), "authored-machine", FixtureEmitter.CaseKind.PRE_PRODUCT_SEED);
        assertEquals(2, seed.payload().files().size());
        assertFalse(seed.payload().receipt().containsBusinessEffects());
        String input = Files.readString(seed.fixture().resolve("common/on_action/des_acceptance_pre_product_seed.txt"));
        assertFalse(input.contains("set_variable"));
        assertFalse(input.contains("des_initialized"));
    }

    @Test
    void rejectsMissingSourcesInvalidMachineAndIncompleteOptions() {
        assertThrows(IOException.class,
                () -> FixtureEmitter.emit(temporary, temporary.resolve("missing-sources"), "authored-machine"));
        assertThrows(IllegalArgumentException.class,
                () -> FixtureEmitter.emit(repository(), temporary.resolve("invalid-machine"), ""));
        assertEquals(1, FixtureEmitter.run(new String[]{"--output", temporary.resolve("no-output").toString()}));
        assertFalse(Files.exists(temporary.resolve("no-output")));
    }
}
