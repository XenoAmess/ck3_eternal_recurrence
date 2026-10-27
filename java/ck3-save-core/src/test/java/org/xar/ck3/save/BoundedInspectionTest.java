package org.xar.ck3.save;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.SaveContracts.*;

final class BoundedInspectionTest {
    @TempDir Path directory;
    private int saveOrdinal;
    private static final String MODIFIER = " temporary_opinion={modifier=\"authored_penalty\" value=-100 modify=-100 start_date=1066.9.22 expiration_date=9999.1.1 nested={key=one key=two}}";
    private static String world() {
        return "CK3txt meta_data={version=authored nested={preserved_by_old_metadata_contract=no}} date=1066.9.22 "
                + "living={1={house=3 repeated=one repeated=two list={1 2} nested={x=\"#{}\"}} 2={house=3}} "
                + "opinions={active_opinions={{owner=1 target=2" + MODIFIER + " temporary_opinion={modifier=other value=-100 modify=-100}}"
                + "{owner=4 target=2" + MODIFIER + "}{owner=2 target=1" + MODIFIER + "}"
                + "{owner=5 target=2 temporary_opinion={modifier=other value=-100 modify=-100}}}}";
    }
    private static NativeId id(String value) { return new NativeId(value); }
    private static OpinionInspection.Pair pair(String owner, OpinionInspection.Expectation expectation) {
        return new OpinionInspection.Pair(id(owner), id("2"), expectation);
    }
    private static OpinionInspection.Selection opinions() {
        return new OpinionInspection.Selection(List.of("opinions", "active_opinions"), "authored_penalty", "-100", "-100",
                List.of(pair("1", OpinionInspection.Expectation.EXACT_ONE), pair("4", OpinionInspection.Expectation.EXACT_ONE), pair("5", OpinionInspection.Expectation.ABSENT)),
                512 * 1024, 256 * 1024, 64);
    }
    private static Selection selected() {
        return new Selection(List.of(new TableSelection(ScopeKind.ACTOR, List.of("living"), List.of(id("1"), id("2")), true)), List.of(), true, false, List.of());
    }
    private Path save(String text) throws IOException { return Files.writeString(directory.resolve("save-" + saveOrdinal++ + ".ck3"), text); }
    private Inspection.Request selectedRequest(Path save) throws IOException {
        return new Inspection.Request(4, "authored-test-machine", repository().toString(), FilePins.pin(save), FilePins.pin(java()), selected());
    }
    private OpinionInspection.Request opinionRequest(Path save) throws IOException {
        return new OpinionInspection.Request(1, "authored-test-machine", repository().toString(), FilePins.pin(save), FilePins.pin(java()), opinions());
    }
    @Test void selectedActualProducerPreservesCompleteAstAndOmitsInventoryWithoutChangingOldReport() throws Exception {
        Inspection.Request request = selectedRequest(save(world()));
        Inspection.Report legacy = Inspection.inspect(request, (decoder, input) -> child("ok", input));
        SelectedInspection.Report report = SelectedInspection.inspect(request, (decoder, input) -> child("ok", input));
        assertEquals(legacy.decoded().projection().scopes(), report.selected().scopes());
        assertEquals(legacy.decoded().projection().records(), report.selected().records());
        assertEquals(report, SelectedInspection.readReport(SaveJson.write(report)));
        assertEquals(2, report.selected().scopes().stream().filter(s -> s.kind() == ScopeKind.ACTOR).count());
        Clausewitz.Block actor = report.selected().scopes().stream().filter(s -> s.path().equals(List.of("living", "1"))).findFirst().orElseThrow().ast();
        assertEquals(2, actor.named("repeated").size()); assertEquals("\"#{}\"", actor.block("nested").atom("x", ""));
        JsonNode wire = SaveJson.read(SaveJson.write(report), JsonNode.class);
        assertFalse(wire.path("selected").has("inventories")); assertEquals("OMITTED_NOT_QUALIFIED", wire.path("inventoryAssessment").textValue());
        assertTrue(report.decoder().completeStream()); assertTrue(report.decoder().originalWait().waited());
        assertEquals(0, report.decoder().originalWait().exitCode()); assertEquals(report.producerBefore(), report.producerAfter());
        assertFalse(report.gameStarted());
        assertEquals("ck3-save-inspection-v4", legacy.schema());
        assertFalse(legacy.decoded().projection().inventories().isEmpty());
    }
    @Test void actualSelectedTitleProducerPreservesFullIdAndHistoryWithoutChangingLegacyInventory() throws Exception {
        String record = "landed_titles={landed_titles={4294966784={key=e_des_procreation_papacy "
                + "coat_of_arms_id=17 history={1066.1.1=1 1066.1.2={type=destroyed}}} "
                + "17690={key=e_authored holder=1}}}";
        Selection titles = new Selection(List.of(new TableSelection(ScopeKind.TITLE,
                List.of("landed_titles", "landed_titles"), List.of(id("4294966784"), id("17690")), true)),
                List.of(), false, false, List.of());
        Path input = save(record);
        Inspection.Request request = new Inspection.Request(4, "authored-title-machine", repository().toString(),
                FilePins.pin(input), FilePins.pin(java()), titles);
        SelectedInspection.Report actual = SelectedInspection.inspect(request, (d, s) -> child("ok", s));
        assertEquals(actual, SelectedInspection.readReport(SaveJson.write(actual)));
        assertEquals(List.of("landed_titles", "landed_titles", "4294966784"), actual.selected().scopes().getFirst().path());
        assertEquals(2, actual.selected().scopes().getFirst().ast().block("history").entries().size());
        assertTrue(actual.decoder().completeStream()); assertEquals(0, actual.decoder().originalWait().exitCode());
        Projection legacy = new SaveStream(new StringReader(world()), selected()).read();
        assertEquals(7, legacy.inventories().size());
        assertTrue(legacy.inventories().stream().noneMatch(i -> i.kind() == ScopeKind.TITLE));
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(record.replace("17690=", "4294966784=")), titles).read());
    }
    @Test void selectedStrictConsumerRejectsDroppedAddedOrMislabeledAstAndInventories() throws Exception {
        SelectedInspection.Report report = SelectedInspection.inspect(selectedRequest(save(world())), (d, s) -> child("ok", s));
        ObjectNode valid = object(report);
        List<ObjectNode> invalid = new ArrayList<>();
        ObjectNode dropped = valid.deepCopy(); dropped.withObject("/selected").withArray("scopes").remove(1); invalid.add(dropped);
        ObjectNode extra = valid.deepCopy(); extra.withObject("/selected").withArray("scopes").add(extra.path("selected").path("scopes").get(1).deepCopy()); invalid.add(extra);
        ObjectNode coverage = valid.deepCopy(); ((ObjectNode) coverage.path("selected").path("scopes").get(1)).put("coverage", "DIRECT_SCALARS"); invalid.add(coverage);
        ObjectNode changedAst = valid.deepCopy(); ((ObjectNode) changedAst.path("selected").path("scopes").get(1)).put("canonicalTokenSha256", "0".repeat(64)); invalid.add(changedAst);
        ObjectNode inventories = valid.deepCopy(); inventories.withObject("/selected").putArray("inventories"); invalid.add(inventories);
        ObjectNode incomplete = valid.deepCopy(); incomplete.withObject("/decoder").put("completeStream", false); invalid.add(incomplete);
        ObjectNode badWait = valid.deepCopy(); badWait.withObject("/decoder").withObject("/originalWait").put("exitCode", 7); invalid.add(badWait);
        invalid.addAll(pinSwaps(valid));
        for (ObjectNode bad : invalid) assertThrows(IOException.class, () -> SelectedInspection.readReport(SaveJson.write(bad)));
        assertThrows(IOException.class, () -> SelectedInspection.readReport(new byte[1024 * 1024 + 1]));
    }
    @Test void actualEmittedProjectionsRequireCompleteAstTokenDigestWhileMetadataKeepsDirectScalars() throws Exception {
        Path input = save(world() + " triggered_event={days=30 payload={same=one same=two}} triggered_event={days=31}");
        Inspection.Request original = selectedRequest(input);
        Selection selection = new Selection(selected().tables(), List.of(new ProjectionSelection("queue", ProjectionKind.SCHEDULED_EVENTS,
                List.of("triggered_event"), 2, 4096, true)), true, false, List.of());
        Inspection.Request request = new Inspection.Request(4, original.machineId(), original.repository(), original.save(), original.decoder(), selection);
        SelectedInspection.Report report = SelectedInspection.inspect(request, (d, s) -> child("ok", s));
        assertEquals(report, SelectedInspection.readReport(SaveJson.write(report)));
        assertEquals(2, report.selected().projections().size());
        Scope metadata = report.selected().scopes().stream().filter(s -> s.kind() == ScopeKind.METADATA).findFirst().orElseThrow();
        assertEquals(Coverage.DIRECT_SCALARS, metadata.coverage()); assertTrue(metadata.ast().named("nested").isEmpty());
        ObjectNode valid = object(report);
        ObjectNode badHash = valid.deepCopy(); ((ObjectNode) badHash.path("selected").path("projections").get(0)).put("canonicalTokenSha256", "0".repeat(64));
        assertThrows(IOException.class, () -> SelectedInspection.readReport(SaveJson.write(badHash)));
        ObjectNode badAst = valid.deepCopy(); ((ObjectNode) badAst.path("selected").path("projections").get(0).path("ast")).withArray("entries").removeAll();
        assertThrows(IOException.class, () -> SelectedInspection.readReport(SaveJson.write(badAst)));
    }
    @Test void directedActualProducerToStrictConsumerRetainsFullMatchedRowsAndNamedSourceOnly() throws Exception {
        OpinionInspection.Report report = OpinionInspection.inspect(opinionRequest(save(world())), (d, s) -> child("ok", s));
        assertEquals(report, OpinionInspection.readReport(SaveJson.write(report)));
        assertEquals(4, report.projection().rowsScanned());
        List<OpinionInspection.Finding> findings = report.projection().findings();
        assertEquals(List.of(1, 1, 0), findings.stream().map(f -> f.modifiers().size()).toList());
        assertEquals(2, findings.getFirst().rows().getFirst().completeAst().named("temporary_opinion").size());
        assertEquals(2, findings.getFirst().modifiers().getFirst().completeAst().block("nested").named("key").size());
        assertEquals("1066.9.22", findings.getFirst().modifiers().getFirst().completeAst().atom("start_date", ""));
        assertEquals(id("1"), findings.getFirst().rows().getFirst().owner());
        assertEquals(id("2"), findings.getFirst().rows().getFirst().target());
        assertTrue(report.decoder().completeStream()); assertFalse(report.decoder().originalWait().timedOut());
        assertEquals(report.producerBefore(), report.producerAfter());
    }
    @Test void opinionsAreParameterizedAndThreeAbsentDirectionsDoNotBorrowReverseOrOtherSources() throws Exception {
        OpinionInspection.Selection absent = new OpinionInspection.Selection(opinions().tablePath(), "different_modifier", "-7", "-7",
                opinions().pairs().stream().map(p -> new OpinionInspection.Pair(p.owner(), p.target(), OpinionInspection.Expectation.ABSENT)).toList(), 4096, 16384, 4);
        OpinionInspection.Request original = opinionRequest(save(world()));
        OpinionInspection.Request request = new OpinionInspection.Request(1, "another-valid-machine", original.repository(), original.save(), original.decoder(), absent);
        OpinionInspection.Report report = OpinionInspection.inspect(request, (d, s) -> child("ok", s));
        assertTrue(report.projection().findings().stream().allMatch(f -> f.modifiers().isEmpty()));
        assertEquals(request, OpinionInspection.readReport(SaveJson.write(report)).request());
        String moved = world().replace("owner=1 target=2", "owner=2 target=1");
        assertThrows(IllegalArgumentException.class, () -> new OpinionStream(new StringReader(moved), opinions()).read());
    }
    @Test void missingWrongDuplicateAndMalformedOpinionSourcesFailClosed() {
        for (String text : List.of(world().replace("value=-100", "value=-99"), world().replace("modify=-100", "modify=-99"),
                world().replace("owner=1", "owner=1.0"), world().replace("owner=1", "owner={x=1}"), world().replace("owner=1", "owner=1 owner=1"),
                world().replace("target=2" + MODIFIER, "target=2" + MODIFIER + MODIFIER),
                world().replace("modifier=\"authored_penalty\"", "modifier={bad=1}"), world().replace("value=-100", "value=\"-100\""),
                world().replace(" value=-100", ""), world().replace(" modify=-100", " modify=-100 modify=-100"),
                world().replace("owner=1 target=2" + MODIFIER, "owner=1 target=2"), world().replace("active_opinions={", "active_opinions={bad=1 "),
                world().substring(0, world().length() - 1), world() + world(), world() + "bad=", "opinions={}", world().replace("active_opinions={", "active_opinions=5 ignored={"))) {
            Exception rejected = assertThrows(Exception.class, () -> new OpinionStream(new StringReader(text), opinions()).read(), text.substring(0, Math.min(100, text.length())));
            assertTrue(rejected instanceof IOException || rejected instanceof IllegalArgumentException);
        }
        OpinionInspection.Selection tiny = new OpinionInspection.Selection(opinions().tablePath(), "authored_penalty", "-100", "-100", opinions().pairs(), 16, 64, 1);
        assertThrows(IOException.class, () -> new OpinionStream(new StringReader(world()), tiny).read());
    }
    @Test void opinionStrictConsumerRecomputesCountsDirectionsAndAstRatherThanTrustingClaims() throws Exception {
        OpinionInspection.Report report = OpinionInspection.inspect(opinionRequest(save(world())), (d, s) -> child("ok", s));
        ObjectNode valid = object(report); List<ObjectNode> invalid = new ArrayList<>();
        ObjectNode dropped = valid.deepCopy(); ((ObjectNode) dropped.path("projection").path("findings").get(0)).withArray("modifiers").removeAll(); invalid.add(dropped);
        ObjectNode wrongDirection = valid.deepCopy(); ((ObjectNode) wrongDirection.path("projection").path("findings").get(0).path("pair")).put("owner", "2"); invalid.add(wrongDirection);
        ObjectNode fakeTotal = valid.deepCopy(); fakeTotal.withObject("/projection").put("rowsScanned", 0); invalid.add(fakeTotal);
        ObjectNode failure = valid.deepCopy(); failure.withObject("/decoder").withObject("/originalWait").put("waited", false); invalid.add(failure);
        ObjectNode falseComplete = valid.deepCopy(); falseComplete.withObject("/decoder").put("completeStream", false); invalid.add(falseComplete);
        invalid.addAll(pinSwaps(valid));
        for (ObjectNode bad : invalid) assertThrows(IOException.class, () -> OpinionInspection.readReport(SaveJson.write(bad)));
    }
    @Test void wrongJsonTypesMissingFieldsDuplicateDirectionsAndAliasesRejectBeforeLaunching() throws Exception {
        String json = new String(SaveJson.write(opinionRequest(save(world()))), StandardCharsets.UTF_8);
        for (String bad : List.of(json.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : 1.0"),
                json.replace("\"owner\" : \"1\"", "\"owner\" : true"), json.replace("\"maxRecordBytes\" : 524288", "\"maxRecordBytes\" : \"524288\""),
                json.replace("\"modifier\"", "\"sourceAlias\""), json.replace("\"expectation\" : \"EXACT_ONE\"", "\"expectation\" : null"),
                json.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : 1, \"schemaVersion\" : 1"))) {
            assertNotEquals(json, bad); assertThrows(IOException.class, () -> SaveJson.read(bad.getBytes(StandardCharsets.UTF_8), OpinionInspection.Request.class));
        }
        assertThrows(IllegalArgumentException.class, () -> new OpinionInspection.Selection(opinions().tablePath(), "authored_penalty", "-100", "-100",
                List.of(pair("1", OpinionInspection.Expectation.ABSENT), pair("1", OpinionInspection.Expectation.EXACT_ONE)), 4096, 4096, 4));
    }
    @Test void originalIndependentDecoderExitTruncationAndUnknownKeyFailureNeverProduceReport() throws Exception {
        Path input = save(world()); AtomicReference<Process> original = new AtomicReference<>();
        for (String mode : List.of("exit7", "truncated", "unknown", "unknown-zero")) {
            assertThrows(Exception.class, () -> OpinionInspection.inspect(opinionRequest(input), (d, s) -> {
                Process process = child(mode, s); original.set(process); return process;
            }));
            assertNotNull(original.get()); assertFalse(original.get().isAlive());
        }
        AtomicInteger launches = new AtomicInteger(); OpinionInspection.Request request = opinionRequest(input);
        OpinionInspection.Request wrong = new OpinionInspection.Request(1, request.machineId(), request.repository(),
                new Pin(request.save().path(), request.save().bytes(), "0".repeat(64)), request.decoder(), request.selection());
        assertThrows(IOException.class, () -> OpinionInspection.inspect(wrong, (d, s) -> { launches.incrementAndGet(); return child("ok", s); }));
        assertEquals(0, launches.get());
    }
    @Test void apiAndCliOutputBudgetsRefuseLargeSelectedAstWithoutDroppingAnyRecord() throws Exception {
        Path input = save(world().replace("house=3 repeated=one", "house=3 repeated=one payload={" + "a=x ".repeat(12000) + "}"));
        Inspection.Request request = selectedRequest(input);
        IOException oversized = assertThrows(IOException.class, () -> SelectedInspection.inspect(request, (d, s) -> child("ok", s)));
        assertTrue(oversized.getMessage().contains("one MiB"));
        Path requestFile = directory.resolve("oversized-request.json"), output = directory.resolve("oversized-report.json");
        Files.write(requestFile, SaveJson.write(request));
        assertEquals(1, SelectedInspection.run(new String[]{"--inputs", requestFile.toString(), "--output", output.toString()}, (d, s) -> child("ok", s)));
        assertFalse(Files.exists(output));
    }
    @Test void realSingletonEmptySlotShapesAreNotRecordsAndUnknownScalarsNeverDisappear() throws Exception {
        Selection slots = new Selection(List.of(
                new TableSelection(ScopeKind.DYNASTY, List.of("dynasties", "dynasties"), List.of(id("12157")), false),
                new TableSelection(ScopeKind.HOUSE, List.of("dynasties", "dynasty_house"), List.of(id("12761")), false)), List.of(), false, false, List.of());
        String text = "dynasties={dynasties={174={name=main} 12157=none} dynasty_house={174={dynasty=174} 12761=none}}";
        Projection result = new SaveStream(new StringReader(text), slots).read();
        assertEquals(List.of(RecordStatus.NOT_FOUND, RecordStatus.NOT_FOUND), result.records().stream().map(RecordObservation::status).toList());
        assertTrue(result.scopes().isEmpty());
        assertTrue(result.inventories().stream().filter(i -> i.kind() == ScopeKind.DYNASTY || i.kind() == ScopeKind.HOUSE).allMatch(i -> i.ids().equals(List.of(id("174")))));
        for (String bad : List.of(text.replace("12157=none", "12157=unknown"), text.replace("12761=none", "12761=\"none\""),
                text.replace("12157=none", "1.0=none"), text.replace("12157=none", "true=none"), text.replace("12157=none", "01=none"),
                text.replace("12157=none", "18446744073709551616=none"), text.replace("12157=none", "12157=none 12157=none"),
                text.replace("12157=none", "12157={} 12157=none"), text.replace("12761=none", "12761=none 12761={}"),
                text.replace("12157=none", "12157 none"))) {
            assertThrows(IOException.class, () -> new SaveStream(new StringReader(bad), slots).read());
        }
        Path input = save(text);
        Inspection.Request request = new Inspection.Request(4, "empty-slot-machine", repository().toString(), FilePins.pin(input), FilePins.pin(java()), slots);
        SelectedInspection.Report report = SelectedInspection.inspect(request, (d, s) -> child("ok", s));
        assertEquals(result.records(), SelectedInspection.readReport(SaveJson.write(report)).selected().records());
        Selection required = new Selection(List.of(new TableSelection(ScopeKind.DYNASTY, List.of("dynasties", "dynasties"), List.of(id("12157")), true)), List.of(), false, false, List.of());
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(text), required).read());
    }
    @Test void bothNewCliProducersRunInIndependentJavaProcessesAndRefuseOverwrite() throws Exception {
        Path save = save(world());
        for (String kind : List.of("selected", "opinions")) {
            Path input = directory.resolve(kind + "-request.json"), output = directory.resolve(kind + "-report.json");
            Files.write(input, SaveJson.write(kind.equals("selected") ? selectedRequest(save) : opinionRequest(save)));
            Process process = command(kind, input.toString(), output.toString()).start();
            try {
                assertTrue(process.waitFor(30, TimeUnit.SECONDS));
                assertEquals(0, process.exitValue(), new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8));
                byte[] bytes = Files.readAllBytes(output);
                if (kind.equals("selected")) assertEquals(selectedRequest(save), SelectedInspection.readReport(bytes).request());
                else assertEquals(opinionRequest(save), OpinionInspection.readReport(bytes).request());
                SaveDecoder.Launcher mustNotLaunch = (d, s) -> { throw new AssertionError("overwrite must reject before decoder"); };
                assertEquals(1, kind.equals("selected") ? SelectedInspection.run(new String[]{"--inputs", input.toString(), "--output", output.toString()}, mustNotLaunch)
                        : OpinionInspection.run(new String[]{"--inputs", input.toString(), "--output", output.toString()}, mustNotLaunch));
            } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(); } }
        }
    }
    private static ObjectNode object(Object value) throws IOException { return assertInstanceOf(ObjectNode.class, SaveJson.read(SaveJson.write(value), JsonNode.class)); }
    private static List<ObjectNode> pinSwaps(ObjectNode valid) {
        List<ObjectNode> bad = new ArrayList<>();
        ObjectNode save = valid.deepCopy(); save.withObject("/request").set("save", valid.path("request").path("decoder").deepCopy()); bad.add(save);
        ObjectNode decoder = valid.deepCopy(); decoder.withObject("/request").set("decoder", valid.path("request").path("save").deepCopy()); bad.add(decoder);
        ObjectNode evidenceSave = valid.deepCopy(); evidenceSave.withObject("/decoder").set("save", valid.path("request").path("decoder").deepCopy()); bad.add(evidenceSave);
        ObjectNode evidenceDecoder = valid.deepCopy(); evidenceDecoder.withObject("/decoder").set("decoder", valid.path("request").path("save").deepCopy()); bad.add(evidenceDecoder);
        return bad;
    }
    private static Path repository() throws IOException { return Path.of(System.getProperty("save.repository")).toRealPath(); }
    private static Path java() { return Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java"); }
    private static ProcessBuilder command(String... args) {
        List<String> command = new ArrayList<>(List.of(java().toString(), "-Xms16m", "-Xmx128m", "-cp", System.getProperty("java.class.path"), Child.class.getName()));
        command.addAll(List.of(args)); return new ProcessBuilder(command).redirectErrorStream(false);
    }
    private static Process child(String mode, Path save) throws IOException { return command(mode, save.toString()).start(); }
    public static final class Child {
        private Child() { }
        public static void main(String[] args) throws Exception {
            if (args[0].equals("selected") || args[0].equals("opinions")) {
                String[] argv = {"--inputs", args[1], "--output", args[2]};
                System.exit(args[0].equals("selected") ? SelectedInspection.run(argv, (d, s) -> child("ok", s)) : OpinionInspection.run(argv, (d, s) -> child("ok", s)));
            }
            if (args[0].equals("unknown")) { System.err.print("unknown key"); System.exit(9); }
            if (args[0].equals("unknown-zero")) System.err.print("unknown key");
            String text = Files.readString(Path.of(args[1]));
            if (args[0].equals("truncated")) text = text.substring(0, text.length() - 1);
            System.out.print(text); if (args[0].equals("exit7")) System.exit(7);
        }
    }
}
