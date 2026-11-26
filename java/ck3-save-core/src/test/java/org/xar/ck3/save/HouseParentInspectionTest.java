package org.xar.ck3.save;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.SaveContracts.*;

final class HouseParentInspectionTest {
    @TempDir Path directory;
    private final AtomicInteger files = new AtomicInteger();
    private static final HouseParentInspection.Selection LAYOUT =
            new HouseParentInspection.Selection(List.of("world", "houses"), List.of("world", "dynasties"));

    private HouseParentInspection.Request request(String text) throws IOException {
        Path save = directory.resolve("authored-" + files.incrementAndGet() + ".ck3");
        Files.writeString(save, text, StandardCharsets.UTF_8);
        Path java = Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        return new HouseParentInspection.Request(1, "authored-house-machine", System.getProperty("save.repository"),
                FilePins.pin(save), FilePins.pin(java), LAYOUT);
    }
    private static Process child(Path java, Path input, String mode) throws IOException {
        try {
            String classes = Path.of(Decoder.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString();
            return new ProcessBuilder(java.toString(), "-cp", classes, Decoder.class.getName(), input.toString(), mode).start();
        } catch (java.net.URISyntaxException invalid) { throw new IOException(invalid); }
    }
    private static String smallWorld() {
        return "meta_data={version=authored} world={dynasties={1={} 2={}} "
                + "houses={12={dynasty=2 nested={dynasty=999}} 10={dynasty=1} 11={dynasty=1} 13=none}}";
    }

    @Test void actualProducerCompletesOneDecoderAndConsumerRechecksAllInventoryRows() throws Exception {
        AtomicInteger launches = new AtomicInteger();
        HouseParentInspection.Request request = request(smallWorld());
        HouseParentInspection.Report report = HouseParentInspection.inspect(request, (java, save) -> {
            launches.incrementAndGet(); return child(java, save, "ok");
        });
        assertEquals(1, launches.get()); assertEquals(request, report.request());
        assertTrue(report.decoder().completeStream()); assertTrue(report.decoder().originalWait().waited());
        assertEquals(0, report.decoder().originalWait().exitCode()); assertFalse(report.decoder().originalWait().timedOut());
        assertEquals(List.of(new NativeId("10"), new NativeId("11")), report.projection().housesInDynasty(new NativeId("1")));
        assertEquals(List.of(new NativeId("12")), report.projection().housesInDynasty(new NativeId("2")));
        assertEquals(3, report.projection().houseParents().size());
        assertThrows(IllegalArgumentException.class, () -> report.projection().housesInDynasty(new NativeId("3")));
        assertEquals(report, HouseParentInspection.readReport(SaveJson.write(report)));
        assertFalse(report.gameStarted()); assertEquals(Inspection.BusinessAssessment.NOT_ASSESSED, report.businessAssessment());
    }

    @Test void emptyTablesAndNativeNoneSlotsAreCompleteButMissingTablesAreNot() throws Exception {
        HouseParentInspection.Projection empty = HouseParentInspection.read(new StringReader(
                "world={dynasties={1=none} houses={2=none}}"), LAYOUT);
        assertTrue(empty.houseParents().isEmpty());
        assertTrue(empty.inventories().stream().allMatch(i -> i.availability() == Availability.OBSERVED && i.ids().isEmpty()));
        assertThrows(IOException.class, () -> HouseParentInspection.read(new StringReader("world={dynasties={}}"), LAYOUT));
        assertThrows(IOException.class, () -> HouseParentInspection.read(new StringReader("world={houses={}}"), LAYOUT));
    }

    @Test void parentFieldIdentityAndCompleteGrammarFailuresNeverBecomeOmissions() {
        List<String> bad = List.of(
                "world={dynasties={1={}} houses={10={}}}",
                "world={dynasties={1={}} houses={10={nested={dynasty=1}}}}",
                "world={dynasties={1={}} houses={10={dynasty=1 dynasty=1}}}",
                "world={dynasties={1={}} houses={10={dynasty=1 dynasty={x=y}}}}",
                "world={dynasties={1={}} houses={10={dynasty=1 dynasty}}}",
                "world={dynasties={1={}} houses={10={dynasty={identity=1}}}}",
                "world={dynasties={1={}} houses={10={dynasty=\"1\"}}}",
                "world={dynasties={1={}} houses={10={dynasty=1.0}}}",
                "world={dynasties={1={}} houses={10={dynasty=yes}}}",
                "world={dynasties={1={}} houses={10={dynasty=none}}}",
                "world={dynasties={1={}} houses={10={dynasty=-1}}}",
                "world={dynasties={1={}} houses={10={dynasty=2}}}",
                "world={dynasties={1={}} houses={10={dynasty=1} 10={dynasty=1}}}",
                "world={dynasties={1={}} houses={10=none 10={dynasty=1}}}",
                "world={dynasties={1={}} houses={01={dynasty=1}}}",
                "world={dynasties={1={}} houses={{dynasty=1}}}",
                "world={dynasties={{}} houses={}}",
                "world={dynasties={1={}} houses={10={dynasty=1}} houses={}}",
                "world={dynasties={1={}} houses=none}",
                smallWorld() + "trailing={",
                smallWorld() + "}");
        for (String text : bad) assertThrows(IOException.class, () -> HouseParentInspection.read(new StringReader(text), LAYOUT), text);
    }

    @Test void strictWireRejectsMissingDuplicateWrongDirectionAndNonStringRows() throws Exception {
        HouseParentInspection.Report report = HouseParentInspection.inspect(request(smallWorld()), (java, save) -> child(java, save, "ok"));
        ObjectNode original = SaveJson.read(SaveJson.write(report), ObjectNode.class);
        ArrayList<ObjectNode> bad = new ArrayList<>();
        ObjectNode missing = original.deepCopy();
        ArrayNode missingRows = assertInstanceOf(ArrayNode.class, missing.path("projection").path("houseParents")); missingRows.remove(0); bad.add(missing);
        ObjectNode duplicate = original.deepCopy();
        ArrayNode duplicateRows = assertInstanceOf(ArrayNode.class, duplicate.path("projection").path("houseParents"));
        duplicateRows.set(0, duplicateRows.get(1).deepCopy()); bad.add(duplicate);
        for (String shape : List.of("number", "boolean", "short", "long", "object", "dangling")) {
            ObjectNode changed = original.deepCopy();
            ArrayNode rows = assertInstanceOf(ArrayNode.class, changed.path("projection").path("houseParents"));
            ArrayNode row = assertInstanceOf(ArrayNode.class, rows.get(0));
            switch (shape) {
                case "number" -> row.set(0, com.fasterxml.jackson.databind.node.IntNode.valueOf(10));
                case "boolean" -> row.set(0, com.fasterxml.jackson.databind.node.BooleanNode.TRUE);
                case "short" -> row.remove(1);
                case "long" -> row.add("extra");
                case "object" -> rows.set(0, original.objectNode().put("houseId", "10").put("dynastyId", "1"));
                case "dangling" -> row.set(1, com.fasterxml.jackson.databind.node.TextNode.valueOf("999"));
                default -> throw new IllegalStateException(shape);
            }
            bad.add(changed);
        }
        ObjectNode missingInventory = original.deepCopy(); assertInstanceOf(ObjectNode.class, missingInventory.get("projection")).remove("inventories"); bad.add(missingInventory);
        ObjectNode wrongRequest = original.deepCopy(); assertInstanceOf(ObjectNode.class, wrongRequest.get("request")).put("schemaVersion", true); bad.add(wrongRequest);
        for (ObjectNode changed : bad) assertThrows(IOException.class, () -> HouseParentInspection.readReport(SaveJson.write(changed)));
        assertThrows(IOException.class, () -> HouseParentInspection.readReport(new byte[1024 * 1024 + 1]));
    }

    @Test void realChildNonzeroUnknownDiagnosticAndTruncatedEofDoNotWriteSuccess() throws Exception {
        for (String mode : List.of("fail", "unknown", "truncated")) {
            HouseParentInspection.Request request = request(smallWorld());
            Path input = directory.resolve(mode + "-request.json"), output = directory.resolve(mode + "-must-not-exist.json");
            Files.write(input, SaveJson.write(request));
            AtomicInteger launches = new AtomicInteger();
            assertEquals(1, HouseParentInspection.run(new String[]{"--inputs", input.toString(), "--output", output.toString()}, (java, save) -> {
                launches.incrementAndGet(); return child(java, save, mode);
            }));
            assertEquals(1, launches.get()); assertFalse(Files.exists(output));
        }
    }

    @Test void complete12760MappingFitsOriginalOperatorBudgetAndSelectsOnlyThreeFullHouseRecords() throws Exception {
        StringBuilder text = new StringBuilder("meta_data={version=authored} world={dynasties={");
        for (int i = 1; i <= 12156; i++) text.append(i).append("={} ");
        text.append("} houses={");
        for (int i = 1; i <= 12760; i++) text.append(i).append("={dynasty=")
                .append(i == 174 || i == 10436 || i == 10440 ? 174 : 1).append(" name=authored nested={keep=all}} ");
        text.append("}}");
        AtomicInteger launches = new AtomicInteger();
        SaveDecoder.Launcher launcher = (java, save) -> { launches.incrementAndGet(); return child(java, save, "ok"); };
        HouseParentInspection.Request request = request(text.toString());
        HouseParentInspection.Report report = HouseParentInspection.inspect(request, launcher);
        List<NativeId> related = report.projection().housesInDynasty(new NativeId("174"));
        assertEquals(List.of(new NativeId("174"), new NativeId("10436"), new NativeId("10440")), related);
        assertEquals(12760, report.projection().houseParents().size());
        assertEquals(report, HouseParentInspection.readReport(SaveJson.write(report)));
        assertTrue(SaveJson.write(new OperatorEnvelopeBudget(report, "x".repeat(128 * 1024))).length <= 1024 * 1024);
        SaveContracts.Selection selected = new SaveContracts.Selection(List.of(
                new TableSelection(ScopeKind.HOUSE, LAYOUT.houseTablePath(), related, true),
                new TableSelection(ScopeKind.DYNASTY, LAYOUT.dynastyTablePath(), List.of(new NativeId("174")), true)),
                List.of(), false, false, List.of());
        SelectedInspection.Report details = SelectedInspection.inspect(new Inspection.Request(4, request.machineId(), request.repository(),
                request.save(), request.decoder(), selected), launcher);
        assertEquals(3, details.selected().scopes().stream().filter(s -> s.kind() == ScopeKind.HOUSE && s.coverage() == SaveContracts.Coverage.FULL_RECORD).count());
        assertTrue(details.selected().scopes().stream().filter(s -> s.kind() == ScopeKind.HOUSE).allMatch(s -> s.ast().named("nested").size() == 1));
        assertEquals(details, SelectedInspection.readReport(SaveJson.write(details)));
        assertEquals(2, launches.get()); assertEquals(request.save(), details.decoder().save());
    }
    private record OperatorEnvelopeBudget(HouseParentInspection.Report report, String retainedOperatorEnvelope) { }
    public static final class Decoder {
        private Decoder() { }
        public static void main(String[] args) throws IOException {
            byte[] bytes = Files.readAllBytes(Path.of(args[0]));
            System.out.write(bytes, 0, args[1].equals("truncated") ? bytes.length - 1 : bytes.length);
            if (args[1].equals("unknown")) System.err.println("unknown key authored");
            if (args[1].equals("fail")) System.exit(7);
        }
    }
}
