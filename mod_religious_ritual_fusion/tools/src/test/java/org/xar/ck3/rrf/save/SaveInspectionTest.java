package org.xar.ck3.rrf.save;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.io.Reader;
import java.io.StringReader;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.save.SaveContracts.Atom;
import org.xar.ck3.rrf.save.SaveContracts.Block;
import org.xar.ck3.rrf.save.SaveContracts.Layout;
import org.xar.ck3.rrf.save.SaveContracts.NativeId;
import org.xar.ck3.rrf.save.SaveContracts.Pin;
import org.xar.ck3.rrf.save.SaveContracts.Report;
import org.xar.ck3.rrf.save.SaveContracts.Request;
import org.xar.ck3.rrf.save.SaveContracts.Scope;
import org.xar.ck3.rrf.save.SaveContracts.ScopeKind;
import org.xar.ck3.rrf.save.SaveContracts.Selection;

final class SaveInspectionTest {
    private static final String SAVE = """
        meta_data={version="1.20.0.4" portraits={ignored={nested=yes}}}
        date=1066.9.16
        living={31254={rite=150 alive_data={piety={currency=500.00001 accumulated=1350} variables={data={{flag="rrf_zero" data={type=value}}} list={{name="rrf_selected" item={type=rite identity=150} item={type=rite identity=9007199254740993} duration={3650}}}}}}}
        religion={religions={8={key="christianity"}}}
        faiths={database={13={religion=8 main_rite=0 name="Catholic"}}}
        rites={database={150={faith=13 data={doctrine="tenet_x" doctrine="tenet_y" unknown_jens="quoted # { \\"word\\" }"}} 9007199254740993={faith=13}}}
        """;
    @TempDir Path directory;

    @Test void actualChildProducerToTypedReportPreservesRawNumbersRepeatedKeysAndOrdering() throws Exception {
        Request request = request();
        Report report = SaveInspector.inspect(request, fixture("ok"));
        assertEquals(report, Json.read(Json.write(report), Report.class));
        assertEquals(List.of("150", "9007199254740993"), report.inventories().stream().filter(i -> i.kind() == ScopeKind.RITE).findFirst().orElseThrow().ids().stream().map(NativeId::value).toList());
        Scope actor = scope(report.scopes(), ScopeKind.ACTOR);
        assertEquals("150", atom(actor.ast(), "rite"));
        assertEquals("500.00001", atom(block(block(actor.ast(), "alive_data"), "piety"), "currency"));
        Scope rite = scope(report.scopes(), ScopeKind.RITE);
        Block data = block(rite.ast(), "data");
        assertEquals(List.of("\"tenet_x\"", "\"tenet_y\""), data.entries().stream().filter(e -> e.key().equals("doctrine")).map(e -> ((Atom) e.value()).raw()).toList());
        assertTrue(atom(data, "unknown_jens").contains("# {"));
        assertEquals(SaveContracts.Coverage.FULL_RECORD, actor.coverage());
        assertEquals(SaveContracts.Coverage.DIRECT_SCALARS, scope(report.scopes(), ScopeKind.METADATA).coverage());
        assertEquals(1, scope(report.scopes(), ScopeKind.METADATA).ast().entries().size());
        assertTrue(report.saveUnchanged()); assertFalse(report.gameStarted());
        assertEquals(request.save(), SaveInspector.pin(Path.of(request.save().path())));
        Path repository = Path.of(request.repository());
        assertEquals(13 + org.xar.ck3.save.ProducerSources.requiredSources(repository).size(), report.producerSources().size());
        assertTrue(report.producerSources().stream().allMatch(p -> Path.of(p.path()).startsWith(repository)));
        assertTrue(report.producerSources().stream().anyMatch(p -> p.path().replace((char) 92, '/').contains("java/ck3-save-core/src/main/java/")));
        assertEquals(Integer.toString(SAVE.getBytes(StandardCharsets.UTF_8).length), report.stream().bytes());
        assertTrue(new String(Json.write(report), StandardCharsets.UTF_8).contains("\"9007199254740993\""));
    }
    @Test void lexerConsumesSingleCharacterChunksAndManyUnrelatedRootDeathRecords() throws Exception {
        StringBuilder text = new StringBuilder(SAVE);
        for (int id = 100000; id < 101000; id++) text.append(id).append("={dead_data={date=1066.1.1}}\n");
        try (Reader oneCharacter = new Reader() {
            private final StringReader source = new StringReader(text.toString());
            @Override public int read(char[] buffer, int offset, int length) throws IOException { return source.read(buffer, offset, Math.min(1, length)); }
            @Override public void close() { source.close(); }
        }) {
            SaveStream.Projection projection = new SaveStream(oneCharacter, request()).read();
            assertEquals(5, projection.scopes().size());
            assertEquals(List.of("meta_data", "date", "living", "religion", "faiths", "rites"), projection.rootKeys());
        }
    }
    @Test void truncatedMalformedDuplicateMissingAndMismatchedLayoutsAreRejected() throws Exception {
        Request request = request();
        for (String text : List.of(SAVE.substring(0, SAVE.lastIndexOf('}')), SAVE + "}", SAVE + "broken =", SAVE + "unexpected", SAVE.replace("150={faith", "150={} 150={faith"))) {
            assertThrows(IOException.class, () -> new SaveStream(new StringReader(text), request).read());
        }
        Request oldLayout = new Request(2, request.machineId(), request.repository(), request.save(), request.decoder(), new Layout(List.of("living"), List.of("jens_180", "database"), List.of("faiths", "database"), List.of("religion", "religions")), request.selection(), request.expectation());
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(SAVE), oldLayout).read());
        Request missing = new Request(2, request.machineId(), request.repository(), request.save(), request.decoder(), request.layout(), new Selection(new NativeId("31254"), List.of(new NativeId("999")), List.of(), List.of()), request.expectation());
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(SAVE), missing).read());
    }
    @Test void strictInputSchemaRejectsLossyNativeIdentitiesUnknownFieldsAndOldTypes() throws Exception {
        Request request = request(); String json = new String(Json.write(request), StandardCharsets.UTF_8);
        assertEquals(request, Json.read(json.getBytes(StandardCharsets.UTF_8), Request.class));
        for (String value : List.of("31254", "31254.0", "true", "null", "{}", "[]", "\"031254\"", "\"18446744073709551616\"")) {
            assertThrows(IOException.class, () -> Json.read(json.replace("\"31254\"", value).getBytes(StandardCharsets.UTF_8), Request.class));
        }
        for (String invalid : List.of(json.replace("\"schemaVersion\" : 2", "\"schemaVersion\" : 1"), json.replace("\"schemaVersion\" : 2", "\"schemaVersion\" : 2, \"extra\" : true"), json.replace("\"actorId\"", "\"actorHistoryId\""), json.replace("\"actorId\" : \"31254\",", ""))) {
            assertThrows(IOException.class, () -> Json.read(invalid.getBytes(StandardCharsets.UTF_8), Request.class));
        }
        assertThrows(IllegalArgumentException.class, () -> new Selection(new NativeId("31254"), List.of(new NativeId("150"), new NativeId("150")), List.of(), List.of()));
    }
    @Test void pinMismatchRejectsBeforeDecoderAndActualChildFailuresCannotProduceEvidence() throws Exception {
        Request request = request(); AtomicBoolean launched = new AtomicBoolean();
        Request wrong = new Request(2, request.machineId(), request.repository(), new Pin(request.save().path(), request.save().bytes(), "0".repeat(64)), request.decoder(), request.layout(), request.selection(), request.expectation());
        assertThrows(IOException.class, () -> SaveInspector.inspect(wrong, (decoder, save) -> { launched.set(true); throw new IOException("must not launch"); }));
        assertFalse(launched.get());
        for (String mode : List.of("nonzero", "truncated", "stderr-overflow")) assertThrows(IOException.class, () -> SaveInspector.inspect(request, fixture(mode)));
    }
    @Test void nestingAndSelectedRecordCapsAreEnforcedWithoutWorldMaterialization() throws Exception {
        Request request = request();
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(SAVE + "noise={".repeat(130) + "}".repeat(130)), request).read());
        String large = SAVE.replace("rite=150", "rite=150 extra={" + "a=b ".repeat(150000) + "}");
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(large), request).read());
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(SAVE + "noise=\"" + "a".repeat(2 * 1024 * 1024 + 1) + "\""), request).read());
    }
    @Test void v2CanonicalRecordHashAndAstRemainTheHistoricalWireContract() throws Exception {
        String text = """
                meta_data={version="1.20.0.4" portrait={ignored=yes}}
                living={31254={rite=150}}
                religion={religions={8={key="christianity"}}}
                faiths={database={13={religion=8}}}
                rites={database={150={faith=13 doctrine="one" doctrine="two"}}}
                """;
        SaveStream.Projection projection = new SaveStream(new StringReader(text), request()).read();
        Scope actor = scope(projection.scopes(), ScopeKind.ACTOR);
        Scope rite = scope(projection.scopes(), ScopeKind.RITE);
        assertEquals(org.xar.ck3.rrf.ReleaseBuilder.sha256("record = { rite = 150 } ".getBytes(StandardCharsets.UTF_8)), actor.canonicalTokenSha256());
        assertEquals(org.xar.ck3.rrf.ReleaseBuilder.sha256("record = { faith = 13 doctrine = \"one\" doctrine = \"two\" } ".getBytes(StandardCharsets.UTF_8)), rite.canonicalTokenSha256());
        assertEquals(new Block(List.of(new SaveContracts.Entry("rite", "=", new Atom("150")))), actor.ast());
        assertEquals(List.of("\"one\"", "\"two\""), rite.ast().entries().stream().filter(e -> e.key().equals("doctrine")).map(e -> ((Atom) e.value()).raw()).toList());
        assertEquals(5, projection.scopes().size()); assertEquals(3, projection.inventories().size());
    }
    private Request request() throws IOException {
        Path save = directory.resolve("synthetic.ck3"); if (!Files.exists(save)) Files.writeString(save, SAVE);
        Path java = Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        return new Request(2, "synthetic-fixture-machine", Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent().toString(), SaveInspector.pin(save), SaveInspector.pin(java),
                new Layout(List.of("living"), List.of("rites", "database"), List.of("faiths", "database"), List.of("religion", "religions")), new Selection(new NativeId("31254"), List.of(new NativeId("150")), List.of(new NativeId("13")), List.of(new NativeId("8"))), new SaveContracts.InspectOnly());
    }
    private SaveInspector.DecoderLauncher fixture(String mode) throws URISyntaxException {
        String classes = Path.of(DecoderFixture.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString();
        return (decoder, save) -> new ProcessBuilder(decoder.toString(), "-cp", classes, DecoderFixture.class.getName(), save.toString(), mode).start();
    }
    public static final class DecoderFixture {
        private DecoderFixture() { }
        public static void main(String[] args) throws IOException {
            String text = Files.readString(Path.of(args[0]));
            if (args[1].equals("truncated")) text = text.substring(0, text.lastIndexOf('}'));
            if (args[1].equals("stderr-overflow")) System.err.print("x".repeat(70000));
            System.out.print(text); if (args[1].equals("nonzero")) System.exit(7);
        }
    }
    private static Scope scope(List<Scope> scopes, ScopeKind kind) { return scopes.stream().filter(s -> s.kind() == kind).findFirst().orElseThrow(); }
    private static Block block(Block block, String key) { return (Block) block.entries().stream().filter(e -> e.key().equals(key)).findFirst().orElseThrow().value(); }
    private static String atom(Block block, String key) { return ((Atom) block.entries().stream().filter(e -> e.key().equals(key)).findFirst().orElseThrow().value()).raw(); }
}
