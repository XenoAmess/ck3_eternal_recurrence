package org.xar.ck3.save;

import static org.junit.jupiter.api.Assertions.*;

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

/** Regression for R0029 unrelated dead_unprunable/40982 duplicate while selecting35899. */
final class CanonicalNativeDuplicateTest {
    @TempDir Path directory;
    private static final String BODY = "name=\"old\" x=one x=two nested={quoted=\"#{}\" members={1 2}}";
    private static Selection actors(String... selected) {
        return new Selection(List.of(new TableSelection(ScopeKind.ACTOR, List.of("dead_unprunable"),
                java.util.Arrays.stream(selected).map(NativeId::new).toList(), true)),
                List.of(), true, false, List.of());
    }
    private static String actorWorld(String second) {
        return "meta_data={version=authored} dead_unprunable={35899={rite=155} 40982={" + BODY
                + "} 40982={" + second + "}} trailing={complete=yes}";
    }
    private static Inventory inventory(Projection p, ScopeKind kind) {
        return p.inventories().stream().filter(i -> i.kind() == kind).findFirst().orElseThrow();
    }

    @Test void unrelatedCanonicalDuplicateCollapsesAfterCompleteBodiesWithoutSelectedEarlyExit() throws Exception {
        String text = actorWorld(BODY);
        Projection actual = new SaveStream(new StringReader(text), actors("35899")).read();
        assertEquals(List.of(new NativeId("35899"), new NativeId("40982")), inventory(actual, ScopeKind.ACTOR).ids());
        assertEquals(1, actual.records().size()); assertEquals(RecordStatus.FULL_RECORD, actual.records().getFirst().status());
        assertEquals(1, actual.scopes().stream().filter(s -> s.kind() == ScopeKind.ACTOR).count());
        assertTrue(actual.rootKeys().contains("trailing"));
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(text + "broken={"), actors("35899")).read());
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(text + "}"), actors("35899")).read());
    }

    @Test void selectedDuplicateAddsOneAstAndPreservesExistingCanonicalRecordDomain() throws Exception {
        Projection p = new SaveStream(new StringReader(actorWorld(BODY)), actors("40982")).read();
        List<Scope> found = p.scopes().stream().filter(s -> s.kind() == ScopeKind.ACTOR).toList();
        assertEquals(1, found.size()); assertEquals(2, found.getFirst().ast().named("x").size());
        assertEquals(CanonicalTokens.selectedRecordHash(found.getFirst().ast()), found.getFirst().canonicalTokenSha256());
        String canonical = "record = { name = \"old\" x = one x = two nested = { quoted = \"#{}\" members = { 1 2 } } } ";
        assertEquals(FilePins.sha256(canonical.getBytes(StandardCharsets.UTF_8)), found.getFirst().canonicalTokenSha256());
        Projection whitespace = new SaveStream(new StringReader(actorWorld(BODY.replace("x=one", "x = one # ignored comment\n"))), actors("40982")).read();
        assertEquals(found, whitespace.scopes().stream().filter(s -> s.kind() == ScopeKind.ACTOR).toList());
    }

    @Test void conflictingBodiesOrderQuotedLexemesLateThirdAndNoneCollisionsStillReject() {
        for (String body : List.of(BODY.replace("x=two", "x=three"),
                BODY.replace("x=one x=two", "x=two x=one"), BODY.replace("\"old\"", "\"different\""))) {
            IOException error = assertThrows(IOException.class, () -> new SaveStream(new StringReader(actorWorld(body)), actors("35899")).read());
            assertTrue(error.getMessage().contains("conflicting native ID block"));
            assertTrue(error.getMessage().contains("first start token")); assertTrue(error.getMessage().contains("duplicate start token"));
        }
        String valid = actorWorld(BODY);
        for (String suffix : List.of("40982=none", "1=none 1={}", "1={} 1=none", "1=none 1=none", "1=unknown", "01={}")) {
            String bad = valid.replace("} trailing=", " " + suffix + "} trailing=");
            assertThrows(IOException.class, () -> new SaveStream(new StringReader(bad), actors("35899")).read(), suffix);
        }
        String third = valid.replace("} trailing=", " 40982={different=yes}} trailing=");
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(third), actors("35899")).read());
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(valid + "dead_unprunable={}"), actors("35899")).read());
    }

    @Test void houseParentAndStructureCensusDoNotAccumulateEquivalentRowsTwice() throws Exception {
        String text = "meta_data={v=authored} world={dynasties={1={} 1={} 2={}} "
                + "houses={10={dynasty=1 nested={keep=yes}} 10={dynasty=1 nested={keep=yes}} 11={dynasty=2}}}";
        HouseParentInspection.Selection layout = new HouseParentInspection.Selection(List.of("world", "houses"), List.of("world", "dynasties"));
        HouseParentInspection.Projection parents = HouseParentInspection.read(new StringReader(text), layout);
        assertEquals(2, parents.houseParents().size()); assertEquals(List.of(new NativeId("10")), parents.housesInDynasty(new NativeId("1")));
        Selection counts = new Selection(List.of(new TableSelection(ScopeKind.HOUSE, layout.houseTablePath(), List.of(new NativeId("10")), true),
                new TableSelection(ScopeKind.DYNASTY, layout.dynastyTablePath(), List.of(new NativeId("1")), true)),
                List.of(), true, true, List.of(List.of("world")));
        Projection result = new SaveStream(new StringReader(text), counts).read();
        assertTrue(result.inventories().stream().filter(i -> i.kind() == ScopeKind.HOUSE || i.kind() == ScopeKind.DYNASTY).allMatch(i -> i.ids().size() == 2));
        assertEquals(2L, result.structures().stream().filter(s -> s.path().equals(layout.houseTablePath())).findFirst().orElseThrow().numericBlockChildren());
        assertEquals(2L, result.structures().stream().filter(s -> s.path().equals(layout.dynastyTablePath())).findFirst().orElseThrow().numericBlockChildren());
        assertThrows(IOException.class, () -> HouseParentInspection.read(new StringReader(text.replace("11={dynasty=2}", "11={dynasty=2} 10={dynasty=2}")), layout));
    }

    @Test void aggregateTypedSignatureLimitCountsUniqueRecordsAcrossKinds() throws Exception {
        assertEquals(200000, SaveStream.NativeSignatureLimits.standard().maxRecords());
        assertThrows(IllegalArgumentException.class, () -> new SaveStream.NativeSignatureLimits(0));
        assertThrows(IllegalArgumentException.class, () -> new SaveStream.NativeSignatureLimits(200001));
        Selection s = new Selection(List.of(new TableSelection(ScopeKind.ACTOR, List.of("living"), List.of(), true),
                new TableSelection(ScopeKind.DYNASTY, List.of("dynasties"), List.of(), true)), List.of(), false, false, List.of());
        SaveStream.NativeSignatureLimits limit = new SaveStream.NativeSignatureLimits(2);
        assertDoesNotThrow(() -> new SaveStream(new StringReader("living={1={} 1={}} dynasties={}"), s, null, limit).read());
        assertDoesNotThrow(() -> new SaveStream(new StringReader("living={1={} 1={}} dynasties={1={} 1={}}"), s, null, limit).read());
        IOException full = assertThrows(IOException.class, () -> new SaveStream(new StringReader("living={1={} 2={}} dynasties={1={}}"), s, null, limit).read());
        assertTrue(full.getMessage().contains("aggregate native signature cap exceeded"));
    }

    @Test void realProducerAndEverySharedSaveStreamConsumerRoundTripTheDuplicatePolicy() throws Exception {
        String text = actorWorld(BODY) + "world={dynasties={1={} 1={}} houses={10={dynasty=1} 10={dynasty=1}}}";
        Path save = directory.resolve("duplicate.ck3"); Files.writeString(save, text, StandardCharsets.UTF_8);
        Pin input = FilePins.pin(save), decoder = FilePins.pin(java());
        AtomicInteger launches = new AtomicInteger();
        SaveDecoder.Launcher launch = (d, s) -> { launches.incrementAndGet(); return child(s, "ok"); };
        Inspection.Request request = new Inspection.Request(4, "duplicate-fixture-machine", System.getProperty("save.repository"), input, decoder, actors("35899", "40982"));
        Inspection.Report legacy = Inspection.inspect(request, launch);
        assertEquals(legacy, SaveJson.read(SaveJson.write(legacy), Inspection.Report.class));
        SelectedInspection.Report selected = SelectedInspection.inspect(request, launch);
        assertEquals(selected, SelectedInspection.readReport(SaveJson.write(selected)));
        assertEquals(2, selected.selected().scopes().stream().filter(s -> s.kind() == ScopeKind.ACTOR).count());
        assertTrue(selected.decoder().completeStream()); assertEquals(0, selected.decoder().originalWait().exitCode());
        assertEquals(Long.toString(Files.size(save)), selected.decoder().streamBytes());
        Decoded decoded = SaveDecoder.inspect(input, decoder, request.selection(), DecoderLimits.standard(), launch);
        assertEquals(2, inventory(decoded.projection(), ScopeKind.ACTOR).ids().size());
        HouseParentInspection.Request parentsRequest = new HouseParentInspection.Request(1, request.machineId(), request.repository(), input, decoder,
                new HouseParentInspection.Selection(List.of("world", "houses"), List.of("world", "dynasties")));
        HouseParentInspection.Report parents = HouseParentInspection.inspect(parentsRequest, launch);
        assertEquals(parents, HouseParentInspection.readReport(SaveJson.write(parents)));
        assertEquals(1, parents.projection().houseParents().size()); assertTrue(parents.decoder().completeStream());
        assertEquals(4, launches.get());
    }

    @Test void decoderExitUnknownDiagnosticAndTruncationNeverPublishSelectedSuccess() throws Exception {
        Path save = directory.resolve("actual-input.ck3"); Files.writeString(save, actorWorld(BODY), StandardCharsets.UTF_8);
        Inspection.Request request = new Inspection.Request(4, "duplicate-cli-machine", System.getProperty("save.repository"),
                FilePins.pin(save), FilePins.pin(java()), actors("35899"));
        Path input = directory.resolve("request.json"); Files.write(input, SaveJson.write(request));
        for (String mode : List.of("exit7", "unknown", "truncated")) {
            AtomicReference<Process> actual = new AtomicReference<>();
            Path output = directory.resolve(mode + "-must-not-exist.json");
            assertEquals(1, SelectedInspection.run(new String[]{"--inputs", input.toString(), "--output", output.toString()}, (d, s) -> {
                Process process = child(s, mode); actual.set(process); return process;
            }));
            assertNotNull(actual.get()); assertTrue(actual.get().waitFor(10, TimeUnit.SECONDS));
            assertFalse(actual.get().isAlive()); assertFalse(Files.exists(output));
            if (mode.equals("exit7")) assertEquals(7, actual.get().exitValue());
        }
    }

    @Test void canonicalSignaturePreservesLexemeBoundariesAndDomainPrefixes() {
        CanonicalTokens.Accumulator first = new CanonicalTokens.Accumulator(), second = new CanonicalTokens.Accumulator();
        for (String t : List.of("{", "ab", "c", "}")) first.add(t);
        for (String t : List.of("{", "a", "bc", "}")) second.add(t);
        assertNotEquals(first.finish(), second.finish());
        assertThrows(IllegalStateException.class, first::finish);
        assertThrows(IllegalStateException.class, () -> first.add("late"));
        Clausewitz.Block body = Clausewitz.parse("x={a=1}").block("x");
        CanonicalTokens.Accumulator nativeBody = new CanonicalTokens.Accumulator();
        for (String t : List.of("{", "a", "=", "1", "}")) nativeBody.add(t);
        assertNotEquals(nativeBody.finish().sha256(), CanonicalTokens.selectedRecordHash(body));
    }

    private static Path java() {
        return Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
    }
    private static Process child(Path input, String mode) throws IOException {
        List<String> command = new ArrayList<>(List.of(java().toString(), "-Xms16m", "-Xmx64m", "-cp",
                System.getProperty("java.class.path"), Decoder.class.getName(), input.toString(), mode));
        return new ProcessBuilder(command).start();
    }
    public static final class Decoder {
        private Decoder() { }
        public static void main(String[] args) throws IOException {
            String text = Files.readString(Path.of(args[0]), StandardCharsets.UTF_8);
            if (args[1].equals("truncated")) text = text.substring(0, text.length() - 1);
            System.out.print(text);
            if (args[1].equals("unknown")) System.err.println("unknown authored key");
            if (args[1].equals("exit7")) System.exit(7);
        }
    }
}
