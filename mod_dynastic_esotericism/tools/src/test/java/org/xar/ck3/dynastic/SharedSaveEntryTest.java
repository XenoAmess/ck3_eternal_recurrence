package org.xar.ck3.dynastic;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.Inspection;
import org.xar.ck3.save.SelectedInspection;
import org.xar.ck3.save.OpinionInspection;
import org.xar.ck3.save.SaveContracts.*;
import org.xar.ck3.save.SaveJson;

final class SharedSaveEntryTest {
    @TempDir Path directory;
    @Test void selectedAndDirectionalOpinionRoutesUseActualSharedProducerAndStrictConsumers() throws Exception {
        Path repository = Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
        Path save = directory.resolve("bounded.ck3");
        Files.writeString(save, "meta_data={version=authored} living={101={x=one x=two nested={a=b}} 202={x=other}} "
                + "opinions={active_opinions={{owner=101 target=202 temporary_opinion={modifier=authored_source value=-7 modify=-7 start_date=1066.9.22}}"
                + "{owner=202 target=101 temporary_opinion={modifier=authored_source value=-7 modify=-7}}}}");
        Path javaExe = Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        String classes = Path.of(Decoder.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString();
        AtomicInteger launches = new AtomicInteger();
        ReleaseCommand command = new ReleaseCommand((decoder, input) -> {
            launches.incrementAndGet(); return new ProcessBuilder(decoder.toString(), "-cp", classes, Decoder.class.getName(), input.toString()).start();
        });
        Selection selection = new Selection(List.of(new TableSelection(ScopeKind.ACTOR, List.of("living"), List.of(new NativeId("101"), new NativeId("202")), true)), List.of(), true, false, List.of());
        Inspection.Request selected = new Inspection.Request(4, "authored-route-machine", repository.toString(), FilePins.pin(save), FilePins.pin(javaExe), selection);
        OpinionInspection.Selection opinionSelection = new OpinionInspection.Selection(List.of("opinions", "active_opinions"), "authored_source", "-7", "-7",
                List.of(new OpinionInspection.Pair(new NativeId("101"), new NativeId("202"), OpinionInspection.Expectation.EXACT_ONE),
                        new OpinionInspection.Pair(new NativeId("303"), new NativeId("202"), OpinionInspection.Expectation.ABSENT)), 4096, 16384, 4);
        OpinionInspection.Request opinions = new OpinionInspection.Request(1, "authored-route-machine", repository.toString(), FilePins.pin(save), FilePins.pin(javaExe), opinionSelection);
        Path selectedInput = directory.resolve("selected-request.json"), selectedOutput = directory.resolve("selected-report.json");
        Files.write(selectedInput, SaveJson.write(selected));
        assertEquals(0, command.run("inspect-save-selected-v1", "--inputs", selectedInput.toString(), "--output", selectedOutput.toString()));
        SelectedInspection.Report selectedReport = SelectedInspection.readReport(Files.readAllBytes(selectedOutput));
        assertEquals(selected, selectedReport.request()); assertEquals(3, selectedReport.selected().scopes().size());
        assertEquals(2, selectedReport.selected().scopes().stream().filter(s -> s.kind() == ScopeKind.ACTOR).findFirst().orElseThrow().ast().named("x").size());
        assertEquals(SelectedInspection.InventoryAssessment.OMITTED_NOT_QUALIFIED, selectedReport.inventoryAssessment());
        Path opinionInput = directory.resolve("opinions-request.json"), opinionOutput = directory.resolve("opinions-report.json");
        Files.write(opinionInput, SaveJson.write(opinions));
        assertEquals(0, command.run("inspect-save-opinions-v1", "--inputs", opinionInput.toString(), "--output", opinionOutput.toString()));
        OpinionInspection.Report opinionReport = OpinionInspection.readReport(Files.readAllBytes(opinionOutput));
        assertEquals(opinions, opinionReport.request()); assertEquals(List.of(1, 0), opinionReport.projection().findings().stream().map(f -> f.modifiers().size()).toList());
        assertTrue(opinionReport.decoder().completeStream()); assertEquals(0, opinionReport.decoder().originalWait().exitCode()); assertEquals(2, launches.get());
        assertEquals(1, command.run("inspect-save-opinions-v1", "--inputs", opinionInput.toString(), "--output", opinionOutput.toString()));
        assertEquals(2, launches.get());
        String wrong = new String(SaveJson.write(opinions), StandardCharsets.UTF_8).replace("\"owner\" : \"101\"", "\"owner\" : 101");
        Files.writeString(opinionInput, wrong); Path rejected = directory.resolve("bad-report.json");
        assertEquals(1, command.run("inspect-save-opinions-v1", "--inputs", opinionInput.toString(), "--output", rejected.toString()));
        assertFalse(Files.exists(rejected)); assertEquals(2, launches.get());
        Files.write(opinionInput, SaveJson.write(opinions));
        AtomicReference<Process> exit = new AtomicReference<>();
        ReleaseCommand failed = new ReleaseCommand((decoder, input) -> {
            Process process = new ProcessBuilder(decoder.toString(), "-cp", classes, Decoder.class.getName(), input.toString(), "fail").start(); exit.set(process); return process;
        });
        assertEquals(1, failed.run("inspect-save-opinions-v1", "--inputs", opinionInput.toString(), "--output", rejected.toString()));
        assertNotNull(exit.get()); assertFalse(exit.get().isAlive()); assertEquals(7, exit.get().exitValue()); assertFalse(Files.exists(rejected));
    }
    @Test void actualProductCliUsesSharedDecoderAndStrictTypedConsumer() throws Exception {
        Path repository = Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
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
        ReleaseCommand command = new ReleaseCommand((decoder, original) -> {
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
        public static void main(String[] args) throws IOException {
            System.out.write(Files.readAllBytes(Path.of(args[0])));
            if (args.length == 2 && args[1].equals("fail")) System.exit(7);
        }
    }
}
