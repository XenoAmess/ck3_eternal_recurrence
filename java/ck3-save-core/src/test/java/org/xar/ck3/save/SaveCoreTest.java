package org.xar.ck3.save;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.SaveContracts.*;

final class SaveCoreTest {
    @TempDir Path directory;
    private static String world() {
        StringBuilder actors = new StringBuilder();
        for (int id = 1; id <= 11; id++) actors.append(id).append("={dynasty=42 house=43 rite=155}\n");
        return """
                CK3txt
                meta_data={version="1.20.0.4" portrait={nested=ignored}}
                date=1066.9.16
                living={%s}
                rites={database={155={faith=13 data={doctrine="tenet_a" doctrine="tenet_b"}}}}
                faiths={database={13={religion=8}}}
                religion={religions={8={key="christianity"}}}
                dynasties={database={42={name="D" coat_of_arms=44}}}
                authored_house_table={43={name="H" dynasty=42}}
                coat_of_arms={database={44={pattern="pattern_solid.dds"}}}
                variables={data={flag="des_initialized"}}
                triggered_event={event="des_monthly_maintenance" days=30}
                triggered_event={event="des_monthly_maintenance" days=31}
                house_relations={unknown_structure={source=authored}}
                """.formatted(actors);
    }
    private static List<NativeId> ids(String... ids) { return Arrays.stream(ids).map(NativeId::new).toList(); }
    private static TableSelection table(ScopeKind kind, List<String> path, String... ids) { return new TableSelection(kind, path, ids(ids), true); }
    private static Selection selection() {
        List<NativeId> actors = new ArrayList<>();
        for (int id = 1; id <= 11; id++) actors.add(new NativeId(Integer.toString(id)));
        return new Selection(List.of(new TableSelection(ScopeKind.ACTOR, List.of("living"), actors, true),
                table(ScopeKind.RITE, List.of("rites", "database"), "155"),
                table(ScopeKind.FAITH, List.of("faiths", "database"), "13"),
                table(ScopeKind.RELIGION, List.of("religion", "religions"), "8"),
                table(ScopeKind.DYNASTY, List.of("dynasties", "database"), "42"),
                table(ScopeKind.HOUSE, List.of("authored_house_table"), "43"),
                table(ScopeKind.COAT_OF_ARMS, List.of("coat_of_arms", "database"), "44")),
                List.of(new ProjectionSelection("globals", ProjectionKind.GLOBAL_VARIABLES, List.of("variables"), 1, 4096, true),
                        new ProjectionSelection("queue", ProjectionKind.SCHEDULED_EVENTS, List.of("triggered_event"), 2, 4096, true)), true, true, List.of(List.of("dynasties"), List.of("coat_of_arms"), List.of("house_relations")));
    }
    @Test void oneDecodeSelectsEightRelativesThreeVassalsAndExplicitDynastyHouseCoa() throws Exception {
        Inspection.Request request = request();
        AtomicInteger launches = new AtomicInteger();
        Inspection.Report report = Inspection.inspect(request, (decoder, save) -> { launches.incrementAndGet(); return child("ok", save); });
        assertEquals(1, launches.get());
        assertEquals(11, report.decoded().projection().scopes().stream().filter(s -> s.kind() == ScopeKind.ACTOR).count());
        assertEquals(18, report.decoded().projection().scopes().size());
        assertEquals(report, SaveJson.read(SaveJson.write(report), Inspection.Report.class));
        String oldSchema = new String(SaveJson.write(report), StandardCharsets.UTF_8).replace("ck3-save-inspection-v4", "ck3-save-inspection-v3");
        assertThrows(IOException.class, () -> SaveJson.read(oldSchema.getBytes(StandardCharsets.UTF_8), Inspection.Report.class));
        assertEquals(List.of(0, 1), report.decoded().projection().projections().stream().filter(p -> p.name().equals("queue")).map(ProjectionScope::occurrence).toList());
        assertEquals(List.of("30", "31"), report.decoded().projection().projections().stream().filter(p -> p.name().equals("queue")).map(p -> p.ast().atom("days", "")).toList());
        assertFalse(report.gameStarted()); assertEquals(Inspection.BusinessAssessment.NOT_ASSESSED, report.businessAssessment());
        assertTrue(report.producer().loadedCode().stream().allMatch(p -> Files.isRegularFile(Path.of(p.path()))));
        assertTrue(report.decoded().projection().structures().stream().anyMatch(s -> s.path().equals(List.of("house_relations"))));
    }
    @Test void canonicalV2RecordTokensQuotedLexemesAndDuplicateKeysAreStable() throws Exception {
        Projection result = new SaveStream(new StringReader(world()), selection()).read();
        Scope rite = result.scopes().stream().filter(s -> s.kind() == ScopeKind.RITE).findFirst().orElseThrow();
        String legacy = "record = { faith = 13 data = { doctrine = \"tenet_a\" doctrine = \"tenet_b\" } } ";
        assertEquals(FilePins.sha256(legacy.getBytes(StandardCharsets.UTF_8)), rite.canonicalTokenSha256());
        assertEquals(List.of("\"tenet_a\"", "\"tenet_b\""), rite.ast().block("data").entries().stream().map(e -> ((Clausewitz.Atom) e.value()).token()).toList());
        Scope metadata = result.scopes().stream().filter(s -> s.kind() == ScopeKind.METADATA).findFirst().orElseThrow();
        assertEquals(Coverage.DIRECT_SCALARS, metadata.coverage()); assertEquals(1, metadata.ast().entries().size());
        Clausewitz.Block ast = Clausewitz.parse("x={a=\"\\\"#{}\\\"\" a=9007199254740993 list={1 2} p>=2}");
        assertEquals(ast, Clausewitz.parse(ast.body()));
        assertEquals(ast, SaveJson.read(SaveJson.write(ast), Clausewitz.Block.class));
    }
    @Test void unknownLayoutsMissingTablesAndMissingRecordsRemainDistinct() throws Exception {
        Selection none = new Selection(List.of(), List.of(), true, true, List.of(List.of("dynasties"), List.of("coat_of_arms"), List.of("house_relations")));
        Projection unknown = new SaveStream(new StringReader(world()), none).read();
        assertEquals(Availability.UNKNOWN_LAYOUT, unknown.inventories().stream().filter(i -> i.kind() == ScopeKind.HOUSE).findFirst().orElseThrow().availability());
        Selection absent = new Selection(List.of(new TableSelection(ScopeKind.HOUSE, List.of("not_a_house_db"), ids("43"), false)), List.of(), true, false, List.of());
        assertEquals(RecordStatus.UNKNOWN_TABLE, new SaveStream(new StringReader(world()), absent).read().records().getFirst().status());
        Selection missing = new Selection(List.of(new TableSelection(ScopeKind.HOUSE, List.of("authored_house_table"), ids("999"), false)), List.of(), true, false, List.of());
        assertEquals(RecordStatus.NOT_FOUND, new SaveStream(new StringReader(world()), missing).read().records().getFirst().status());
        // Identity 42 can occur in different kinds; duplicate IDs within one table are rejected.
        assertDoesNotThrow(() -> new Selection(List.of(table(ScopeKind.ACTOR, List.of("living"), "42"), table(ScopeKind.DYNASTY, List.of("dynasties"), "42")), List.of(), false, false, List.of()));
        assertThrows(IllegalArgumentException.class, () -> table(ScopeKind.ACTOR, List.of("living"), "1", "1"));
    }
    @Test void explicitCensusRootsExcludeThousandsOfUnrelatedNamedKeysButStillValidateTheirSyntax() throws Exception {
        List<List<String>> roots = List.of(List.of("dynasties"), List.of("coat_of_arms"));
        Selection scoped = new Selection(List.of(), List.of(), true, true, roots);
        Projection baseline = new SaveStream(new StringReader(world()), scoped).read();
        StringBuilder foreign = new StringBuilder("unrelated_named_container={scripted_variables={");
        for (int i = 0; i < 5000; i++) foreign.append("foreign_key_").append(i).append("=yes ");
        foreign.append("}}");
        Projection actual = new SaveStream(new StringReader(world() + foreign), scoped).read();
        assertEquals(roots, actual.structureCoverage().roots());
        assertEquals(4, actual.structureCoverage().maxRelativeNamedDepth());
        assertEquals(4096, actual.structureCoverage().maxKeys());
        assertEquals(baseline.structures(), actual.structures());
        assertEquals(4, actual.structures().size());
        assertTrue(actual.structures().stream().allMatch(s -> roots.stream().anyMatch(r -> s.path().size() >= r.size() && s.path().subList(0, r.size()).equals(r))));
        assertTrue(actual.tokens() > baseline.tokens());
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(world() + foreign + "malformed={"), scoped).read());
        Selection nested = new Selection(List.of(), List.of(), true, true, List.of(List.of("dynasties", "database")));
        Projection navigated = new SaveStream(new StringReader(world()), nested).read();
        assertEquals(List.of(List.of("dynasties", "database")), navigated.structures().stream().map(Structure::path).toList());
        // The limit remains enforced inside the selected root; this is not a larger global cap.
        StringBuilder dense = new StringBuilder("dynasties={named_fields={");
        for (int i = 0; i < 5000; i++) dense.append("field_").append(i).append("=yes ");
        dense.append("}}");
        IOException limit = assertThrows(IOException.class, () -> new SaveStream(new StringReader(dense.toString()),
                new Selection(List.of(), List.of(), false, true, List.of(List.of("dynasties")))).read());
        assertTrue(limit.getMessage().contains("structure key cap exceeded"));
    }
    @Test void censusRootContractRejectsMissingWrongEmptyDuplicateAndDisabledNonemptyRoots() throws Exception {
        ObjectNode template = assertInstanceOf(ObjectNode.class, SaveJson.read(SaveJson.write(request()), JsonNode.class));
        ObjectNode selected = assertInstanceOf(ObjectNode.class, template.get("selection"));
        List<ObjectNode> invalid = new ArrayList<>();
        ObjectNode missing = selected.deepCopy(); missing.remove("structureRoots"); invalid.add(missing);
        ObjectNode empty = selected.deepCopy(); empty.putArray("structureRoots"); invalid.add(empty);
        ObjectNode wrong = selected.deepCopy(); wrong.put("structureRoots", true); invalid.add(wrong);
        ObjectNode flat = selected.deepCopy(); flat.putArray("structureRoots").add("dynasties"); invalid.add(flat);
        ObjectNode numeric = selected.deepCopy(); numeric.putArray("structureRoots").addArray().add(1.0); invalid.add(numeric);
        ObjectNode emptyPath = selected.deepCopy(); emptyPath.putArray("structureRoots").addArray(); invalid.add(emptyPath);
        ObjectNode duplicate = selected.deepCopy();
        var duplicatedRoots = duplicate.putArray("structureRoots");
        duplicatedRoots.addArray().add("dynasties"); duplicatedRoots.addArray().add("dynasties"); invalid.add(duplicate);
        ObjectNode disabled = selected.deepCopy(); disabled.put("structureCensus", false); invalid.add(disabled);
        ObjectNode alias = selected.deepCopy(); alias.set("wrongStructureRoots", alias.remove("structureRoots")); invalid.add(alias);
        for (ObjectNode badSelection : invalid) {
            ObjectNode bad = template.deepCopy(); bad.set("selection", badSelection);
            assertThrows(IOException.class, () -> SaveJson.read(SaveJson.write(bad), Inspection.Request.class));
        }
        Selection disabledEmpty = new Selection(List.of(), List.of(), false, false, List.of());
        assertTrue(new SaveStream(new StringReader(world()), disabledEmpty).read().structures().isEmpty());
        assertEquals(List.of(), new SaveStream(new StringReader(world()), disabledEmpty).read().structureCoverage().roots());
    }
    @Test void malformedDuplicateMissingAndBoundedProjectionsFailClosed() {
        for (String text : List.of(world() + "}", world() + "broken =", world().replace("155={faith", "155={} 155={faith"), world().substring(0, world().lastIndexOf('}')))) {
            assertThrows(IOException.class, () -> new SaveStream(new StringReader(text), selection()).read());
        }
        for (ProjectionSelection bounded : List.of(
                new ProjectionSelection("q", ProjectionKind.SCHEDULED_EVENTS, List.of("triggered_event"), 1, 4096, true),
                new ProjectionSelection("q", ProjectionKind.SCHEDULED_EVENTS, List.of("triggered_event"), 2, 13, true),
                new ProjectionSelection("q", ProjectionKind.SCHEDULED_EVENTS, List.of("missing_queue"), 1, 4096, true))) {
            assertThrows(IOException.class, () -> new SaveStream(new StringReader(world()), new Selection(List.of(), List.of(bounded), true, false, List.of())).read());
        }
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(world() + "n={".repeat(130) + "}".repeat(130)), selection()).read());
        assertThrows(IOException.class, () -> new SaveStream(new StringReader(world().replace("rite=155", "rite=155 x={" + "a=b ".repeat(150000) + "}")), selection()).read());
    }
    @Test void realIndependentCliProducerToStrictConsumerAndNoOverwrite() throws Exception {
        Inspection.Request request = request();
        Path inputs = directory.resolve("request.json"), output = directory.resolve("report.json");
        Files.write(inputs, SaveJson.write(request));
        Process process = command("cli", inputs.toString(), output.toString()).start();
        try {
            assertTrue(process.waitFor(30, TimeUnit.SECONDS)); String stdout = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            assertEquals(0, process.exitValue(), stdout);
            Inspection.Report report = SaveJson.read(Files.readAllBytes(output), Inspection.Report.class);
            assertEquals(request, report.request()); assertEquals(11, report.request().selection().tables().getFirst().ids().size());
            assertEquals(FilePins.pin(output), SaveJson.read(stdout.getBytes(StandardCharsets.UTF_8), Inspection.Receipt.class).report());
            assertEquals(1, Inspection.run(new String[]{"--inputs", inputs.toString(), "--output", output.toString()}, (d, s) -> { throw new IOException("must not launch"); }));
        } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(); } }
    }
    @Test void requestTypesUnknownMissingAndDuplicateFieldsRejectBeforeDecode() throws Exception {
        String json = new String(SaveJson.write(request()), StandardCharsets.UTF_8);
        for (String replacement : List.of("3", "4.0", "true", "null", "\"4\"")) {
            String bad = json.replace("\"schemaVersion\" : 4", "\"schemaVersion\" : " + replacement);
            assertNotEquals(json, bad); assertThrows(IOException.class, () -> SaveJson.read(bad.getBytes(StandardCharsets.UTF_8), Inspection.Request.class));
        }
        for (String replacement : List.of("1", "1.0", "true", "null", "\"01\"")) {
            String bad = json.replace("\"1\"", replacement);
            assertNotEquals(json, bad); assertThrows(IOException.class, () -> SaveJson.read(bad.getBytes(StandardCharsets.UTF_8), Inspection.Request.class));
        }
        for (String bad : List.of(json.replace("\"selection\"", "\"oldSelection\""), json.replace("\"schemaVersion\" : 4,", ""), json.replace("\"schemaVersion\" : 4", "\"schemaVersion\" : 4, \"schemaVersion\" : 4"))) {
            assertThrows(IOException.class, () -> SaveJson.read(bad.getBytes(StandardCharsets.UTF_8), Inspection.Request.class));
        }
        for (String bad : List.of(json.replace("\"maxMatches\" : 2", "\"maxMatches\" : true"),
                json.replace("\"maxBytes\" : 4096", "\"maxBytes\" : 4096.5"),
                json.replace("\"structureCensus\" : true", "\"structureCensus\" : 1"),
                json.replace("\"required\" : true", "\"required\" : \"true\""))) {
            assertNotEquals(json, bad);
            assertThrows(IOException.class, () -> SaveJson.read(bad.getBytes(StandardCharsets.UTF_8), Inspection.Request.class));
        }
    }
    @Test void decoderOriginalFailuresAndTerminationAreNotSuccessfulEvidence() throws Exception {
        Inspection.Request request = request();
        for (String mode : List.of("nonzero", "truncated", "stderr", "utf8", "hang")) {
            AtomicReference<Process> actual = new AtomicReference<>();
            assertThrows(IOException.class, () -> SaveDecoder.inspect(request.save(), request.decoder(), selection(),
                    new DecoderLimits(512L * 1024 * 1024, 65536, Duration.ofSeconds(mode.equals("hang") ? 1 : 10)),
                    (decoder, save) -> { Process process = child(mode, save); actual.set(process); return process; }));
            assertNotNull(actual.get()); assertFalse(actual.get().isAlive());
        }
        AtomicInteger launches = new AtomicInteger();
        Pin wrong = new Pin(request.save().path(), request.save().bytes(), "0".repeat(64));
        assertThrows(IOException.class, () -> SaveDecoder.inspect(wrong, request.decoder(), selection(), DecoderLimits.standard(), (d, s) -> { launches.incrementAndGet(); return child("ok", s); }));
        assertEquals(0, launches.get());
    }
    @Test void loadedArtifactRejectsChangedOrMissingEmbeddedSourceClosure() throws Exception {
        Path repository = Path.of(System.getProperty("save.repository")).toRealPath();
        assertFalse(ProducerSources.verify(repository).loadedCode().isEmpty());
        Path other = directory.resolve("other");
        for (Path source : ProducerSources.requiredSources(repository)) {
            Path target = other.resolve(repository.relativize(source)); Files.createDirectories(target.getParent()); Files.copy(source, target);
        }
        assertDoesNotThrow(() -> ProducerSources.verify(other));
        Files.writeString(other.resolve("java/ck3-save-core/pom.xml"), "\n", StandardCharsets.UTF_8, java.nio.file.StandardOpenOption.APPEND);
        assertThrows(IOException.class, () -> ProducerSources.verify(other));
    }
    private Inspection.Request request() throws IOException {
        Path save = directory.resolve("synthetic.ck3"); if (!Files.exists(save)) Files.writeString(save, world());
        return new Inspection.Request(4, "synthetic-fixture-machine", Path.of(System.getProperty("save.repository")).toRealPath().toString(), FilePins.pin(save), FilePins.pin(java()), selection());
    }
    private static Path java() { return Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java"); }
    private static ProcessBuilder command(String... args) {
        List<String> command = new ArrayList<>(List.of(java().toString(), "-Xms16m", "-Xmx64m", "-cp", System.getProperty("surefire.test.class.path", System.getProperty("java.class.path")), Child.class.getName()));
        command.addAll(List.of(args)); return new ProcessBuilder(command).redirectErrorStream(true);
    }
    private static Process child(String mode, Path save) throws IOException {
        // Decoder stdout and stderr must stay separate.
        return command(mode, save.toString()).redirectErrorStream(false).start();
    }
    public static final class Child {
        private Child() { }
        public static void main(String[] args) throws Exception {
            if (args[0].equals("cli")) {
                System.exit(Inspection.run(new String[]{"--inputs", args[1], "--output", args[2]}, (decoder, save) -> child("ok", save)));
            }
            if (args[0].equals("hang")) { Thread.sleep(20000); return; }
            if (args[0].equals("utf8")) { System.out.write(new byte[]{(byte) 0xc3, (byte) 0x28}); return; }
            String text = Files.readString(Path.of(args[1]));
            if (args[0].equals("truncated")) text = text.substring(0, text.lastIndexOf('}'));
            if (args[0].equals("stderr")) System.err.print("x".repeat(70000));
            System.out.print(text);
            if (args[0].equals("nonzero")) System.exit(7);
        }
    }
}
