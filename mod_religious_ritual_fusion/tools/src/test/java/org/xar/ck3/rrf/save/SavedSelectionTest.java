package org.xar.ck3.rrf.save;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.ExpectedSelection;
import org.xar.ck3.rrf.ExpectedSelection.TenetKey;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.acceptance.FixtureContracts;
import org.xar.ck3.rrf.acceptance.FixtureEmitter;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader;
import org.xar.ck3.rrf.save.SaveContracts.FusionSelection;
import org.xar.ck3.rrf.save.SaveContracts.Layout;
import org.xar.ck3.rrf.save.SaveContracts.NativeId;
import org.xar.ck3.rrf.save.SaveContracts.Pin;
import org.xar.ck3.rrf.save.SaveContracts.Report;
import org.xar.ck3.rrf.save.SaveContracts.Request;
import org.xar.ck3.rrf.save.SaveContracts.Selection;
import org.xar.ck3.rrf.save.SaveContracts.SelectionVerified;
import org.xar.ck3.rrf.save.SaveContracts.Scope;

/** Authored save bytes; the real fixture producer, decoder child, AST reader and comparator all execute. */
final class SavedSelectionTest {
    @TempDir Path directory;
    @Test void coldSnapshotManifestAndPreparedRequestReachTheRealDecoderAndRejectWalletEvidenceDriftBeforeLaunch() throws Exception {
        Inputs original = inputs("core-rite", "wallet-parent");
        ExpectedSelection selection = new ExpectedSelection(List.of(new TenetKey("tenet_esotericism"), new TenetKey("tenet_astrology"), new TenetKey("tenet_communal_identity")));
        String common = saved(selection).replace("date=1066.9.16", "playthrough_id=\"authored-cold-campaign\" date=1066.9.17")
                .replace("alive_data={variables={data={", "alive_data={piety={currency=5400} variables={data={"
                        + "{flag=\"rrfa_piety_before\" data={type=value identity=600000000}}{flag=\"rrf_charged_cost\" data={type=value identity=50000000}}");
        FixtureContracts.FilePin before = coldReport(original.repository(), "wallet-before", common.replace("currency=5400", "currency=6000")
                .replace("living={31254={rite=153", "living={31254={rite=150").replace(reference("rrf_last_result_rite", "153"), ""));
        FixtureContracts.FilePin after = coldReport(original.repository(), "wallet-after", common.replace("currency=5400", "currency=5500"));
        FixtureContracts.FilePin current = coldReport(original.repository(), "wallet-current", common);
        var observed = org.xar.ck3.save.SaveJson.read(Files.readAllBytes(Path.of(current.path())), org.xar.ck3.save.Inspection.Report.class);
        var source = observed.decoded().save();
        var setup = new FixtureContracts.SavedSnapshotSetup(new org.xar.ck3.save.SaveContracts.NativeId("31254"),
                new FixtureContracts.FilePin(source.path(), source.bytes(), source.sha256()), current, new FixtureContracts.PietyAmount("5400"),
                new FixtureContracts.CreationWalletHistory(new FixtureContracts.PietyAmount("6000"), new FixtureContracts.PietyAmount("5500"), 500, before, after));
        var fixtureRequest = new FixtureContracts.Request(4, FixtureContracts.CaseKind.COLD_RELOAD, FixtureContracts.Mode.RITE,
                new FixtureContracts.ActorHistoryId("1128"), setup, selection);
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(original.repository(), directory.resolve("cold-wallet-fixture"), original.request().machineId(), fixtureRequest);
        Request request = new Request(2, original.request().machineId(), original.request().repository(),
                new Pin(source.path(), source.bytes(), source.sha256()), original.request().decoder(), original.request().layout(), original.request().selection(),
                new FusionSelection(SaveInspector.pin(emitted.manifest()), authoredPrepared(emitted, "cold-wallet"), new NativeId("153")));
        Report report = SaveInspector.inspect(request, decoder());
        assertTrue(report.assessment() instanceof SelectionVerified);
        assertEquals(new NativeId("153"), ((SelectionVerified) report.assessment()).resultRiteId());
        Path copied = directory.resolve("cold-wallet-profile/mod-content/fixture/" + FixtureContracts.REQUEST_FILE);
        assertEquals(fixtureRequest, Json.read(Files.readAllBytes(copied), FixtureContracts.Request.class));
        assertEquals(8, emitted.payload().files().size());
        AtomicBoolean launched = new AtomicBoolean();
        byte[] bytes = Files.readAllBytes(Path.of(current.path()));
        Files.writeString(Path.of(current.path()), "{}");
        assertThrows(IOException.class, () -> SaveInspector.inspect(request, (a, b) -> { launched.set(true); throw new IOException("must not launch"); }));
        assertFalse(launched.get()); Files.write(Path.of(current.path()), bytes);
        Files.writeString(copied, Files.readString(copied) + " ");
        assertThrows(IOException.class, () -> SaveInspector.inspect(request, (a, b) -> { launched.set(true); throw new IOException("must not launch"); }));
        assertFalse(launched.get());
    }
    private FixtureContracts.FilePin coldReport(Path repository, String name, String text) throws IOException {
        Path save = directory.resolve(name + ".ck3"); Files.writeString(save, text);
        var selection = new org.xar.ck3.save.SaveContracts.Selection(List.of(new org.xar.ck3.save.SaveContracts.TableSelection(
                org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR, List.of("living"), List.of(new org.xar.ck3.save.SaveContracts.NativeId("31254")), true)), List.of(), true, false, List.of());
        var pin = org.xar.ck3.save.FilePins.pin(save);
        var request = new org.xar.ck3.save.Inspection.Request(4, "synthetic-fixture-machine", repository.toString(), pin, pin, selection);
        var projection = new org.xar.ck3.save.SaveStream(new java.io.StringReader(text), selection).read();
        var bytes = text.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var decoded = new org.xar.ck3.save.SaveContracts.Decoded(pin, pin, 0, "", org.xar.ck3.save.FilePins.sha256(bytes), Integer.toString(bytes.length), projection, true);
        var report = new org.xar.ck3.save.Inspection.Report("ck3-save-inspection-v4", request.machineId(), "2026-10-27T00:00:00Z", request, decoded,
                org.xar.ck3.save.ProducerSources.verify(repository), org.xar.ck3.save.Inspection.BusinessAssessment.NOT_ASSESSED, false);
        Path target = directory.resolve(name + ".report.json"); Files.write(target, org.xar.ck3.save.SaveJson.write(report));
        var result = org.xar.ck3.save.FilePins.pin(target);
        return new FixtureContracts.FilePin(result.path(), result.bytes(), result.sha256());
    }
    private record Inputs(Path repository, FixtureEmitter.Emission fixture, Request request) { }
    private sealed interface AuthoredEmission permits AuthoredEmitter, AuthoredSnapshotEmitter { }
    private record AuthoredEmitter(Pin manifest) implements AuthoredEmission { }
    private record AuthoredSnapshotEmitter(Pin manifest,
            @com.fasterxml.jackson.annotation.JsonProperty("input_receipt") Pin inputReceipt,
            @com.fasterxml.jackson.annotation.JsonProperty("fixture_request") Pin fixtureRequest,
            @com.fasterxml.jackson.annotation.JsonProperty("input_pins") List<FixtureContracts.FilePin> inputPins) implements AuthoredEmission { }
    private record AuthoredCompiled(String schema, String product, @com.fasterxml.jackson.annotation.JsonProperty("case") String caseId, AuthoredEmission emitter) { }
    private record AuthoredPrepared(String schema, @com.fasterxml.jackson.annotation.JsonProperty("runtime_status") String runtimeStatus,
                                   @com.fasterxml.jackson.annotation.JsonProperty("business_acceptance") String businessAcceptance,
                                   @com.fasterxml.jackson.annotation.JsonProperty("profile_dir") String profileDir, Map<String, Pin> files) { }
    private record CompletedOriginEvidence(int schemaVersion, String machineId, String observedAtUtc,
                                           Pin originalReport, Pin originalSave, Pin originalDecoder,
                                           NativeId resultRiteId, String nativeEditStatus, List<Scope> scopes) { }
    @Test void retainedCompletedCreateProjectionUsesActualTypeKeyOriginEncodingWithoutNativeEditCredit() throws Exception {
        CompletedOriginEvidence evidence;
        try (var stream = SavedSelectionTest.class.getResourceAsStream("/save/rrf-origin-core-r0015.original.json")) {
            if (stream == null) throw new IOException("retained original origin-list evidence required");
            evidence = Json.read(stream.readAllBytes(), CompletedOriginEvidence.class);
        }
        assertEquals(1, evidence.schemaVersion()); assertEquals("4-8e1c2f1861", evidence.machineId());
        assertEquals("2026-10-25T16:36:48.610936200Z", evidence.observedAtUtc());
        assertEquals("6b3162ca36efa54ad43eabed711178a123a2473dc7bd2202e365500e4199b780", evidence.originalReport().sha256());
        assertEquals("c903190f35fe8976f3ca4354519fb2a7495a53f91a39f5cdd33388fbd029ee3f", evidence.originalSave().sha256());
        assertEquals("9d3404f6eb08db3a3d2196a5b2e1ce9b4c8687f2d7df60a4f79cafe75f043101", evidence.originalDecoder().sha256());
        assertEquals("INCOMPLETE_NOT_QUALIFIED", evidence.nativeEditStatus());
        Inputs inputs = inputs("core-rite", "retained-origin");
        FixtureContracts.FilePin manifest = new FixtureContracts.FilePin(inputs.fixture().manifest().toRealPath().toString(), Files.size(inputs.fixture().manifest()), org.xar.ck3.rrf.ReleaseBuilder.sha256(Files.readAllBytes(inputs.fixture().manifest())));
        var fixture = FrozenFixtureReader.read(manifest, inputs.request().machineId(), inputs.repository());
        FusionSelection expected = (FusionSelection) inputs.request().expectation();
        Pin inventory = expected.preparedProfileInventory();
        var prepared = FrozenFixtureReader.readPrepared(new FixtureContracts.FilePin(inventory.path(), inventory.bytes(), inventory.sha256()), fixture);
        SelectionVerified actual = SavedSelectionComparator.compare(inputs.request(), evidence.scopes(), fixture, prepared, evidence.resultRiteId());
        assertEquals(new NativeId("153"), actual.resultRiteId());
        assertEquals(3, actual.expectedSelection().coreTenets().size());
        // This consumes unchanged original saved scopes; it does not decode the old save anew or qualify editing/reload/fees.
    }
    @Test void realProducerToCompleteDecoderAndFrozenSelectionConsumerAcceptsThreeAndFourWithoutCountClaimsBeyondFour() throws Exception {
        for (String recipe : List.of("core-rite", "core-rite-four")) {
            Inputs inputs = inputs(recipe, recipe);
            Report report = SaveInspector.inspect(inputs.request(), decoder());
            assertEquals(report, Json.read(Json.write(report), Report.class));
            SelectionVerified verified = (SelectionVerified) report.assessment();
            assertEquals(inputs.fixture().payload().files().get(FixtureContracts.REQUEST_FILE).sha256(), verified.fixtureRequest().sha256());
            assertEquals(recipe.endsWith("four") ? 4 : 3, verified.expectedSelection().coreTenets().size());
            assertEquals(new NativeId("153"), verified.resultRiteId());
            assertEquals(new NativeId("150"), verified.sourceARiteId()); assertEquals(new NativeId("151"), verified.sourceBRiteId());
            assertTrue(report.saveUnchanged()); assertFalse(report.gameStarted());
        }
    }
    @Test void completeSavedAstRejectsExtraMissingDuplicateMismatchedOriginAndChangedSourceOrResultBindings() throws Exception {
        Inputs inputs = inputs("core-rite-four", "negative");
        String original = Files.readString(Path.of(inputs.request().save().path()));
        FixtureContracts.Request fixtureRequest = Json.read(Files.readAllBytes(inputs.fixture().requestSnapshot()), FixtureContracts.Request.class);
        String originItem = "item={type=tenet key=\"tenet_esotericism\"}";
        List<String> invalid = List.of(
                original.replace("tenet_legalism", "tenet_esotericism"),
                original.replace("name=\"rrf_origin_core_tenets\"", "name=\"rrf_origin_core_tenets\" " + originItem),
                original.replace(originItem, ""),
                original.replace(originItem, "item={type=tenet key=\"tenet_unknown\"}"),
                original.replace("type=tenet key=", "type=rite key="),
                original.replace("type=tenet key=", "type=tenet flag="),
                original.replace(originItem, "item={type=tenet key=\"tenet_esotericism\" extra=yes}"),
                original.replace("flag=\"rrf_origin_a\" data={type=rite identity=150}", "flag=\"rrf_origin_a\" data={type=rite identity=151}"),
                original.replace("living={31254={rite=153", "living={31254={rite=152"),
                original.replace("tenet=\"tenet_communal_identity\" status=core", "tenet=\"tenet_communal_identity\" status=known"),
                saved(fixtureRequest.expectedSelection(), true),
                original.replace("153={faith=13", "153={variables={} faith=13"));
        int index = 0;
        for (String text : invalid) {
            assertFalse(original.equals(text));
            Path save = directory.resolve("invalid-" + index++ + ".ck3"); Files.writeString(save, text);
            Request request = withSave(inputs.request(), save);
            assertThrows(IOException.class, () -> SaveInspector.inspect(request, decoder()));
        }
        Inputs three = inputs("core-rite", "three");
        assertThrows(IOException.class, () -> SaveInspector.inspect(withSave(three.request(), Path.of(inputs.request().save().path())), decoder()));
    }
    @Test void manifestMetadataTamperAndMissingSelectionFailBeforeDecoderRatherThanUsingDetachedSidecar() throws Exception {
        Inputs inputs = inputs("core-rite-four", "tampered"); AtomicBoolean launched = new AtomicBoolean();
        Path metadata = inputs.fixture().fixture().resolve(FixtureContracts.REQUEST_FILE);
        Files.writeString(metadata, "{}");
        assertThrows(IOException.class, () -> SaveInspector.inspect(inputs.request(), (decoder, save) -> { launched.set(true); throw new IOException("must not launch"); }));
        assertFalse(launched.get());
        // The unchanged sibling .request.json is intentionally still present and must never be used.
        assertTrue(Files.isRegularFile(inputs.fixture().requestSnapshot()));
        String json = new String(Json.write(inputs.request()), java.nio.charset.StandardCharsets.UTF_8);
        for (String invalid : List.of(json.replace("\"expectation\"", "\"unknownExpectation\""), json.replace("\"fusion_selection\"", "\"unknown_selection\""), json.replace("\"resultRiteId\" : \"153\"", "\"resultRiteId\" : 153"))) {
            assertThrows(IOException.class, () -> Json.read(invalid.getBytes(java.nio.charset.StandardCharsets.UTF_8), Request.class));
        }
        Selection absent = new Selection(inputs.request().selection().actorId(), List.of(new NativeId("150"), new NativeId("151")), List.of(), List.of());
        assertThrows(IllegalArgumentException.class, () -> new Request(2, inputs.request().machineId(), inputs.request().repository(), inputs.request().save(), inputs.request().decoder(), inputs.request().layout(), absent, inputs.request().expectation()));
    }
    @Test void changedManifestProducerPinIsRejectedEvenIfCallerRepinsTheManifest() throws Exception {
        Inputs inputs = inputs("core-rite-four", "bad-source"); FixtureContracts.Manifest old = inputs.fixture().payload();
        List<FixtureContracts.FilePin> sources = new ArrayList<>(old.producerSourcePins()); FixtureContracts.FilePin first = sources.getFirst();
        sources.set(0, new FixtureContracts.FilePin(first.path(), first.bytes(), "0".repeat(64)));
        FixtureContracts.Manifest changed = new FixtureContracts.Manifest(old.schema(), old.product(), old.caseId(), old.machineId(), old.observedAtUtc(), old.fixtureRoot(), sources, old.files(), old.receipt());
        Files.write(inputs.fixture().manifest(), Json.write(changed));
        FusionSelection oldExpected = (FusionSelection) inputs.request().expectation();
        Request request = new Request(2, inputs.request().machineId(), inputs.request().repository(), inputs.request().save(), inputs.request().decoder(), inputs.request().layout(), inputs.request().selection(), new FusionSelection(SaveInspector.pin(inputs.fixture().manifest()), oldExpected.preparedProfileInventory(), new NativeId("153")));
        AtomicBoolean launched = new AtomicBoolean();
        assertThrows(IOException.class, () -> SaveInspector.inspect(request, (decoder, save) -> { launched.set(true); throw new IOException("must not launch"); }));
        assertFalse(launched.get());
    }
    @Test void fourCoreExpectationCannotSubstituteAThreeCorePreparedScene() throws Exception {
        Inputs three = inputs("core-rite", "prepared-three"), four = inputs("core-rite-four", "prepared-four");
        FusionSelection first = (FusionSelection) three.request().expectation(), second = (FusionSelection) four.request().expectation();
        Request crossed = new Request(2, four.request().machineId(), four.request().repository(), four.request().save(), four.request().decoder(), four.request().layout(), four.request().selection(),
                new FusionSelection(second.fixtureManifest(), first.preparedProfileInventory(), new NativeId("153")));
        AtomicBoolean launched = new AtomicBoolean();
        assertThrows(IOException.class, () -> SaveInspector.inspect(crossed, (decoder, save) -> { launched.set(true); throw new IOException("must not launch"); }));
        assertFalse(launched.get());
        Path metadata = directory.resolve("prepared-four-profile/mod-content/fixture/" + FixtureContracts.REQUEST_FILE);
        Files.writeString(metadata, "{}");
        assertThrows(IOException.class, () -> SaveInspector.inspect(four.request(), (decoder, save) -> { launched.set(true); throw new IOException("must not launch"); }));
        assertFalse(launched.get());
    }
    private Inputs inputs(String recipe, String name) throws IOException {
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        FixtureContracts.Request fixtureRequest = Json.read(Files.readAllBytes(repository.resolve("mod_religious_ritual_fusion/tools/src/main/resources/acceptance/requests/" + recipe + ".json")), FixtureContracts.Request.class);
        FixtureEmitter.Emission emission = FixtureEmitter.emit(repository, directory.resolve(name + "-fixture"), "synthetic-fixture-machine", fixtureRequest);
        Path save = directory.resolve(name + ".ck3"); Files.writeString(save, saved(fixtureRequest.expectedSelection()));
        Path java = Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        Request request = new Request(2, "synthetic-fixture-machine", repository.toString(), SaveInspector.pin(save), SaveInspector.pin(java),
                new Layout(List.of("living"), List.of("rites", "database"), List.of("faiths", "database"), List.of("religion", "religions")),
                new Selection(new NativeId("31254"), List.of(new NativeId("150"), new NativeId("151"), new NativeId("153")), List.of(new NativeId("13")), List.of(new NativeId("8"))),
                new FusionSelection(SaveInspector.pin(emission.manifest()), authoredPrepared(emission, name), new NativeId("153")));
        return new Inputs(repository, emission, request);
    }
    private Pin authoredPrepared(FixtureEmitter.Emission fixture, String name) throws IOException {
        Path profile = directory.resolve(name + "-profile"), copied = profile.resolve("mod-content/fixture"); Files.createDirectories(copied);
        Path metadata = copied.resolve(FixtureContracts.REQUEST_FILE); Files.copy(fixture.fixture().resolve(FixtureContracts.REQUEST_FILE), metadata);
        Path compiled = copied.resolve("_case_contract.json");
        AuthoredEmission emitter = new AuthoredEmitter(SaveInspector.pin(fixture.manifest()));
        Path sidecar = Path.of(fixture.fixture() + ".inputs.json");
        if (Files.exists(sidecar)) {
            FixtureContracts.PrebuiltInputs inputs = Json.read(Files.readAllBytes(sidecar), FixtureContracts.PrebuiltInputs.class);
            emitter = new AuthoredSnapshotEmitter(SaveInspector.pin(fixture.manifest()), SaveInspector.pin(sidecar),
                    SaveInspector.pin(fixture.fixture().resolve(FixtureContracts.REQUEST_FILE)), inputs.inputPins());
        }
        Files.write(compiled, Json.write(new AuthoredCompiled("ck3-mod-acceptance-product-assertions-v1", "religious-ritual-fusion", fixture.payload().caseId(), emitter)));
        Path inventory = directory.resolve(name + "-AUTHORED-profile-preparation.json");
        Files.write(inventory, Json.write(new AuthoredPrepared("ck3-mod-acceptance-prepared-fixture-v1", "NOT_RUN", "NOT_ASSESSED", profile.toString(),
                Map.of("mod-content/fixture/" + FixtureContracts.REQUEST_FILE, SaveInspector.pin(metadata), "mod-content/fixture/_case_contract.json", SaveInspector.pin(compiled)))));
        return SaveInspector.pin(inventory);
    }
    private static Request withSave(Request old, Path save) throws IOException { return new Request(2, old.machineId(), old.repository(), SaveInspector.pin(save), old.decoder(), old.layout(), old.selection(), old.expectation()); }
    private static SaveInspector.DecoderLauncher decoder() throws java.net.URISyntaxException {
        String classes = Path.of(SaveInspectionTest.DecoderFixture.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString();
        return (decoder, save) -> new ProcessBuilder(decoder.toString(), "-cp", classes, SaveInspectionTest.DecoderFixture.class.getName(), save.toString(), "ok").start();
    }
    private static String saved(ExpectedSelection expected) { return saved(expected, false); }
    private static String saved(ExpectedSelection expected, boolean misplacedRiteVariables) {
        String actor = "living={31254={rite=153 alive_data={variables={data={" + reference("rrfa_source_a", "150") + reference("rrfa_expected_b", "151") + reference("rrf_last_result_rite", "153") + "}}}}}";
        StringBuilder items = new StringBuilder();
        for (TenetKey key : expected.coreTenets()) items.append("item={type=tenet key=\"").append(key.value()).append("\"}");
        String variables = "variables={data={" + reference("rrf_origin_a", "150") + reference("rrf_origin_b", "151") + "} list={{name=\"rrf_origin_core_tenets\" " + items + "}}}";
        return "meta_data={version=\"1.20.0.4\"} date=1066.9.16 " + actor + " religion={religions={8={key=\"christianity\"}}} faiths={database={13={religion=8 main_rite=0}}} rites={database={"
                + rite("150", FixtureContracts.SOURCE_A, "") + rite("151", FixtureContracts.SOURCE_B, "") + rite("153", expected.coreTenets(), variables, misplacedRiteVariables) + "}}";
    }
    private static String reference(String name, String id) { return "{flag=\"" + name + "\" data={type=rite identity=" + id + "}}"; }
    private static String rite(String id, List<TenetKey> cores, String variables) {
        return rite(id, cores, variables, false);
    }
    private static String rite(String id, List<TenetKey> cores, String variables, boolean misplacedVariables) {
        StringBuilder status = new StringBuilder(), direct = new StringBuilder();
        for (TenetKey key : cores) {
            status.append("{tenet=\"").append(key.value()).append("\" status=core}");
            direct.append("tenet=\"").append(key.value()).append("\" ");
        }
        return id + "={faith=13 data={tenets={" + status + "} " + direct + (misplacedVariables ? variables : "") + "} " + (misplacedVariables ? "" : variables) + "}";
    }
}
