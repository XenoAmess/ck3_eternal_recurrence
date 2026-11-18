package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class AcceptanceFixtureTest {
    @TempDir Path temporary;
    private static Path repository() { return Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent(); }

    @Test void emittedManifestUsesTheExistingClosedPublicPrebuiltContract() throws IOException {
        var emission = FixtureEmitter.emit(repository(), temporary.resolve("observer"), "synthetic-fixture-machine", new AcceptanceContracts.Request(1, "1128"));
        var json = FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emission.manifest().path())));
        Set<String> actual = new HashSet<>(); json.fieldNames().forEachRemaining(actual::add);
        assertEquals(Set.of("schema", "product", "case_id", "machine_id", "observed_at_utc", "fixture_root", "producer_source_pins", "files", "receipt"), actual);
        assertEquals("ck3-mod-acceptance-prebuilt-fixture-v1", json.path("schema").textValue());
        assertEquals("financial-markets", json.path("product").textValue());
        assertEquals("core", json.path("case_id").textValue());
        assertEquals(4, json.path("producer_source_pins").size());
        assertFalse(json.path("receipt").path("fixture_contains_business_effects").booleanValue());
        assertFalse(emission.gameStarted()); assertEquals("NOT_RUN", emission.businessAcceptance());
        try (var files = Files.walk(Path.of(emission.fixture()))) {
            assertEquals(json.path("files").size(), files.filter(Files::isRegularFile).count());
        }
        var names = json.path("files").fieldNames();
        while (names.hasNext()) {
            String name = names.next(); var pin = FixtureEmitter.pin(Path.of(emission.fixture()).resolve(name));
            assertEquals(pin.bytes(), json.path("files").path(name).path("bytes").longValue());
            assertEquals(pin.sha256(), json.path("files").path(name).path("sha256").textValue());
        }
    }

    @Test void observerCannotWriteMoneyPositionsOrCallAProductionEffect() {
        Pattern variableWrite = Pattern.compile("(?:set_variable|change_variable)\\s*=\\s*\\{\\s*name\\s*=\\s*([a-z_]+)");
        Pattern effectCall = Pattern.compile("\\b(xfm_[a-z_]+_effect)\\s*=\\s*yes");
        ObservationScripts.render(new AcceptanceContracts.Request(1, "1128")).forEach((name, bytes) -> {
            if (name.endsWith(".txt") || name.endsWith(".mod")) {
                assertArrayEquals(new byte[]{(byte)0xef, (byte)0xbb, (byte)0xbf}, java.util.Arrays.copyOf(bytes, 3));
                String text = new String(bytes, StandardCharsets.UTF_8);
                var writes = variableWrite.matcher(text);
                while (writes.find()) assertTrue(writes.group(1).startsWith("xfma_"), writes.group(1));
                assertFalse(effectCall.matcher(text).find(), "observer invokes product business in " + name);
                assertFalse(text.contains("add_gold")); assertFalse(text.contains("change_gold"));
                assertFalse(text.contains("set_global_variable")); assertFalse(text.contains("add_to_global_variable_list"));
            }
        });
    }

    @Test void requestRejectsWrongJsonTypesDuplicateFieldsAndScriptInjection() throws IOException {
        List<String> invalid = List.of(
                "{\"schemaVersion\":true,\"actorHistoryId\":\"1128\"}",
                "{\"schemaVersion\":1.0,\"actorHistoryId\":\"1128\"}",
                "{\"schemaVersion\":\"1\",\"actorHistoryId\":\"1128\"}",
                "{\"schemaVersion\":null,\"actorHistoryId\":\"1128\"}",
                "{\"schemaVersion\":1,\"actorHistoryId\":1128}",
                "{\"schemaVersion\":1,\"actorHistoryId\":\"1128 } add_gold = 100 {\"}",
                "{\"schemaVersion\":1,\"actorHistoryId\":\"1128\",\"host\":\"other\"}",
                "{\"schemaVersion\":1,\"actorHistoryId\":\"1128\",\"actorHistoryId\":\"1\"}");
        int index = 0;
        for (String input : invalid) {
            Path path = temporary.resolve("invalid-" + index++ + ".json"); Files.writeString(path, input);
            assertThrows(IOException.class, () -> FixtureEmitter.readRequest(path), input);
        }
    }

    @Test void repeatedEmissionRefusesBeforeChangingExistingEvidence() throws IOException {
        Path output = temporary.resolve("observer");
        var initial = FixtureEmitter.emit(repository(), output, "synthetic-fixture-machine", new AcceptanceContracts.Request(1, "1128"));
        var before = FixtureEmitter.pin(Path.of(initial.manifest().path()));
        assertThrows(IllegalArgumentException.class, () -> FixtureEmitter.emit(repository(), output, "synthetic-fixture-machine", new AcceptanceContracts.Request(1, "1128")));
        assertEquals(before, FixtureEmitter.pin(Path.of(initial.manifest().path())));
    }

    @Test void stalePackagedProducerIsRejectedBeforeCreatingFixture() throws IOException {
        Path fake = temporary.resolve("fake-repo");
        Path source = Path.of("mod_financial_markets/tools/src/main/java/org/xar/ck3/markets/acceptance");
        Files.createDirectories(fake.resolve(source));
        for (String name : List.of("AcceptanceContracts.java", "ObservationScripts.java", "FixtureEmitter.java", "AcceptanceCommand.java")) {
            Files.copy(repository().resolve(source).resolve(name), fake.resolve(source).resolve(name));
        }
        Files.writeString(fake.resolve(source).resolve("ObservationScripts.java"), "// changed producer\n", java.nio.file.StandardOpenOption.APPEND);
        Path output = temporary.resolve("refused");
        assertThrows(IOException.class, () -> FixtureEmitter.emit(fake, output, "synthetic-fixture-machine", new AcceptanceContracts.Request(1, "1128")));
        assertFalse(Files.exists(output)); assertFalse(Files.exists(Path.of(output + ".fixture.json")));
    }

    @Test void outputInsideRepositoryAndInvalidMachineAreRejectedBeforeWriting() {
        Path output = repository().resolve("forbidden-fixture-output");
        assertThrows(IllegalArgumentException.class, () -> FixtureEmitter.emit(repository(), output, "synthetic-fixture-machine", new AcceptanceContracts.Request(1, "1128")));
        assertThrows(IllegalArgumentException.class, () -> FixtureEmitter.emit(repository(), temporary.resolve("bad-machine"), "bad machine", new AcceptanceContracts.Request(1, "1128")));
        assertFalse(Files.exists(output));
    }
}
