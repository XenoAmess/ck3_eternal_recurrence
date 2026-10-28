package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.Inspection;
import org.xar.ck3.save.SaveContracts.*;
import org.xar.ck3.save.SaveJson;

final class SharedSaveEntryTest {
    @TempDir Path directory;
    @Test void actualProductCliUsesSharedDecoderAndStrictTypedConsumer() throws Exception {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Path selectedCoreOutput = Path.of(System.getProperty("save.build.root",
                repository.resolve("java/ck3-save-core/target").toString())).toRealPath();
        var actualCore = org.xar.ck3.save.ProducerSources.verify(repository);
        assertFalse(actualCore.loadedCode().isEmpty());
        for (var code : actualCore.loadedCode()) {
            assertTrue(Path.of(code.path()).toRealPath().startsWith(selectedCoreOutput),
                    "shared save consumer must load this reactor output: " + code.path());
        }
        Path save = directory.resolve("authored.ck3");
        Files.writeString(save, "meta_data={version=authored} living={1={rite=155} 2={rite=155}} triggered_event={days=30} triggered_event={days=31}");
        Path javaExe = Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        Selection selection = new Selection(List.of(new TableSelection(ScopeKind.ACTOR, List.of("living"), List.of(new NativeId("1"), new NativeId("2")), true)),
                List.of(new ProjectionSelection("queue", ProjectionKind.SCHEDULED_EVENTS, List.of("triggered_event"), 2, 1024, true)), true, true, List.of(List.of("living"), List.of("triggered_event")));
        Inspection.Request request = new Inspection.Request(4, "synthetic-fixture-machine", repository.toString(), FilePins.pin(save), FilePins.pin(javaExe), selection);
        Path input = directory.resolve("inputs.json"), output = directory.resolve("report.json");
        Files.write(input, SaveJson.write(request));
        AtomicInteger launched = new AtomicInteger();
        String classes = Path.of(Decoder.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString();
        Command command = new Command((decoder, original) -> {
            launched.incrementAndGet();
            return new ProcessBuilder(decoder.toString(), "-cp", classes, Decoder.class.getName(), original.toString()).start();
        });
        assertEquals(0, command.run("inspect-save-v4", "--inputs", input.toString(), "--output", output.toString()));
        assertEquals(1, launched.get());
        Inspection.Report report = SaveJson.read(Files.readAllBytes(output), Inspection.Report.class);
        assertEquals(request, report.request()); assertEquals(2, report.decoded().projection().records().size());
        assertEquals(selection.structureRoots(), report.decoded().projection().structureCoverage().roots());
        assertEquals(List.of(0, 1), report.decoded().projection().projections().stream().map(ProjectionScope::occurrence).toList());
        assertEquals(report, SaveJson.read(SaveJson.write(report), Inspection.Report.class)); assertFalse(report.gameStarted());
        Path oldCommandOutput = directory.resolve("old-command-must-not-exist.json");
        assertEquals(1, command.run("inspect-save-v3", "--inputs", input.toString(), "--output", oldCommandOutput.toString()));
        assertFalse(Files.exists(oldCommandOutput)); assertEquals(1, launched.get());
        String json = new String(SaveJson.write(request), StandardCharsets.UTF_8);
        for (String bad : List.of(json.replace("\"schemaVersion\" : 4", "\"schemaVersion\" : 3"),
                json.replace("\"schemaVersion\" : 4", "\"schemaVersion\" : true"),
                json.replace("\"selection\"", "\"wrongSelection\""), json.replace("\"1\"", "1.0"))) {
            Files.writeString(input, bad); Path rejected = directory.resolve("must-not-exist.json");
            assertEquals(1, command.run("inspect-save-v4", "--inputs", input.toString(), "--output", rejected.toString()));
            assertFalse(Files.exists(rejected)); assertEquals(1, launched.get());
        }
        ObjectNode typed = assertInstanceOf(ObjectNode.class, SaveJson.read(SaveJson.write(request), JsonNode.class));
        ObjectNode typedSelection = assertInstanceOf(ObjectNode.class, typed.get("selection"));
        java.util.ArrayList<ObjectNode> invalidRoots = new java.util.ArrayList<>();
        ObjectNode missingRoots = typedSelection.deepCopy(); missingRoots.remove("structureRoots"); invalidRoots.add(missingRoots);
        ObjectNode emptyRoots = typedSelection.deepCopy(); emptyRoots.putArray("structureRoots"); invalidRoots.add(emptyRoots);
        ObjectNode wrongRoots = typedSelection.deepCopy(); wrongRoots.put("structureRoots", true); invalidRoots.add(wrongRoots);
        ObjectNode duplicateRoots = typedSelection.deepCopy();
        var duplicateArray = duplicateRoots.putArray("structureRoots");
        duplicateArray.addArray().add("living"); duplicateArray.addArray().add("living"); invalidRoots.add(duplicateRoots);
        ObjectNode disabledRoots = typedSelection.deepCopy(); disabledRoots.put("structureCensus", false); invalidRoots.add(disabledRoots);
        for (ObjectNode badSelection : invalidRoots) {
            ObjectNode badRequest = typed.deepCopy(); badRequest.set("selection", badSelection);
            Files.write(input, SaveJson.write(badRequest)); Path rejected = directory.resolve("roots-must-not-exist.json");
            assertEquals(1, command.run("inspect-save-v4", "--inputs", input.toString(), "--output", rejected.toString()));
            assertFalse(Files.exists(rejected)); assertEquals(1, launched.get());
        }
    }
    public static final class Decoder {
        private Decoder() { }
        public static void main(String[] args) throws IOException { System.out.write(Files.readAllBytes(Path.of(args[0]))); }
    }
}
