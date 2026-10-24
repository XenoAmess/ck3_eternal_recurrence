package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Production binding/recorded consumer/strict corpus closure; fixture bytes grant no Native credit. */
final class FullParityResumeCiTest {
    @TempDir Path temporary;
    private static final ControlBuild.SourceLimitProfile R2 = ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2;

    @Test void resumedExtentAndFull35RetainAllHistoricalLimitsAndModules() throws Exception {
        var old = CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024;
        var resumed = CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R2;
        assertEquals(3072, old.maxFiles()); assertEquals(40L << 20, old.maxLogicalBytes()); assertEquals(56L << 20, old.maxNativeBytes());
        assertEquals(4096, resumed.maxFiles()); assertEquals(64L << 20, resumed.maxLogicalBytes()); assertEquals(80L << 20, resumed.maxNativeBytes());
        assertEquals(8 << 20, old.copyProofMaxBytes()); assertEquals(16 << 20, resumed.copyProofMaxBytes());
        assertEquals(2 << 20, ControlBuild.BUILD_RECEIPT_MAX_BYTES);
        assertEquals(CompleteSourceGraph.modules(old), CompleteSourceGraph.modules(resumed));
        assertEquals(34, resumed.childModules()); assertEquals(35, resumed.reactorProjects());
        assertEquals(35, R2.maxReactorProjects()); assertTrue(R2.fullParity());
        assertEquals(resumed.maxFiles(), R2.maxFiles()); assertEquals(resumed.maxLogicalBytes(), R2.maxBytes());
        CompleteSourceGraphMaterializer.requireProfileBudget(resumed, resumed.maxNativeBytes());
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.requireProfileBudget(resumed, old.maxNativeBytes()));
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.requireProfileBudget(old, resumed.maxNativeBytes()));
        var required = ReactorTestClosure.g2FullParityResumeRequirements();
        assertEquals(required, ControlCi.httpRequirements(R2));
        assertEquals(ReactorTestClosure.g2FullParityRequirements(), required.subList(0, ReactorTestClosure.g2FullParityRequirements().size()));
    }

    @Test void actualCanonicalProducerAndBothRoleConsumersRequireEveryExplicitEnvironment() throws Exception {
        Inputs inputs = inputs("canonical");
        var bound = CanonicalOracleEnvironment.bind(inputs.repo(), inputs.python(), Map.of());
        assertEquals(inputs.repo().toString(), CanonicalOracleEnvironment.require(bound).repositoryRoot());
        for (String missing : List.of("XAR_ORACLE_PYTHON", "XAR_ORACLE_REPO", "XAR_REPO_ROOT")) {
            Map<String, String> bad = new TreeMap<>(bound); bad.remove(missing);
            assertThrows(IOException.class, () -> CanonicalOracleEnvironment.require(bad));
        }
        Path other = Files.createDirectory(temporary.resolve("other-repo"));
        Map<String, String> drift = new TreeMap<>(bound); drift.put("XAR_REPO_ROOT", other.toString());
        assertThrows(IOException.class, () -> CanonicalOracleEnvironment.require(drift));
    }

    @Test void actualR2ProducerFeedsAllConsumersAndHistoricalReaderNeverRehashesOriginals() throws Exception {
        Inputs inputs = inputs("actual-r2");
        var live = FullParityOracleBindings.fromEnvironment(R2, inputs.environment());
        assertInstanceOf(FullParityOracleBindings.ResumedBindings.class, live);
        assertEquals(30, live.mavenArguments().size());
        var config = config(); Path settings = temporary.resolve("settings"), snapshot = temporary.resolve("snapshot"), build = temporary.resolve("build");
        List<String> capture = ControlBuild.reactorCaptureArguments(config, settings, snapshot, build, inputs.environment());
        assertEquals("package", capture.getLast()); assertTrue(capture.contains("-DskipTests=true"));
        assertFalse(capture.stream().anyMatch(argument -> argument.startsWith("-Dtest=") || argument.equals("-pl")));
        var recorded = FullParityOracleBindings.fromRecordedArguments(R2, capture);
        assertEquals(live, recorded);
        var mapper = ControlBuild.strictMapper();
        assertEquals(live, mapper.readValue(mapper.writeValueAsBytes(live), FullParityOracleBindings.ResumedBindings.class));
        for (Path file : inputs.originals()) Files.delete(file);
        assertEquals(capture, ControlBuild.completedCaptureArguments(config, settings, snapshot, build, capture));
        assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(R2, inputs.environment()));
    }

    @Test void missingRoleExtraCorpusOrChangedManifestCannotBeAcceptedAsCompleteR2() throws Exception {
        Inputs inputs = inputs("missing");
        for (String name : inputs.environment().keySet()) {
            Map<String, String> bad = new TreeMap<>(inputs.environment()); bad.remove(name);
            assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(R2, bad), name);
        }
        Files.writeString(inputs.corpus().resolve("unlisted.json"), "{}");
        assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(R2, inputs.environment()));
        Files.delete(inputs.corpus().resolve("unlisted.json"));
        Files.writeString(inputs.corpus().resolve("whole.json"), "{\"changed\":true}");
        assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(R2, inputs.environment()));
    }

    @Test void explicitProfilesDoNotUpgradeLegacyBindingsOrAcceptPartialOrDuplicateR2Arguments() throws Exception {
        Inputs inputs = inputs("generations");
        assertEquals(11, FullParityOracleBindings.fromEnvironment(inputs.environment()).mavenArguments().size());
        var config = config(); Path settings = temporary.resolve("s"), snapshot = temporary.resolve("t"), build = temporary.resolve("b");
        List<String> capture = ControlBuild.reactorCaptureArguments(config, settings, snapshot, build, inputs.environment());
        var missing = capture.stream().filter(value -> !value.startsWith("-Dxar.person10.nativeCorpus.manifest.sha256=")).toList();
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, missing));
        var duplicate = new ArrayList<>(capture); duplicate.add(capture.stream().filter(value -> value.startsWith("-Dxar.battle.context.source.fixture=")).findFirst().orElseThrow());
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, duplicate));
        var selected = new ArrayList<>(capture); selected.add("-Dtest=ChosenOnlyTest");
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(config, settings, snapshot, build, selected));
    }

    @Test void corpusManifestActualProducerStrictReaderAndContentRoundtripRemainBound() throws Exception {
        Inputs inputs = inputs("corpus"); var manifestRef = ControlBuild.FileRef.measure(inputs.manifest());
        var manifest = Person10NativeCorpus.require(manifestRef, inputs.corpus().toString());
        String raw = Files.readString(inputs.manifest()); var mapper = ControlBuild.strictMapper();
        assertEquals(manifest, mapper.readValue(raw, Person10NativeCorpus.Manifest.class));
        for (String wrong : List.of(raw.replace("\"machine_id\":", "\"unknown\":"),
                raw.replaceFirst("\"bytes\":[0-9]+", "\"bytes\":true"), raw.replaceFirst("\"bytes\":[0-9]+", "\"bytes\":1.0"),
                raw.replace("\"files\":[", "\"files\":null,\"duplicate\":[")))
            assertThrows(IOException.class, () -> mapper.readValue(wrong, Person10NativeCorpus.Manifest.class));
        assertThrows(IOException.class, () -> Person10NativeCorpus.require(manifestRef, inputs.repo().toString()));
        assertThrows(IOException.class, () -> Person10NativeCorpus.produce(inputs.corpus(), inputs.manifest()));
    }

    @Test void resumedCopyProofProducerReaderAndHistoricalEightMiBBoundRemainIndependent() throws Exception {
        Path metadata = Files.createDirectory(temporary.resolve("copy-proof"));
        Path output = metadata.resolve("proof.json.gz"), refused = metadata.resolve("old-proof.json.gz");
        String body = "x".repeat(9 << 20);
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.gzipBounded(refused, body, metadata, 1L << 20));
        CompleteSourceGraphMaterializer.gzipBounded(output, body, metadata, 1L << 20,
                CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R2.copyProofMaxBytes());
        var pin = ControlBuild.FileRef.measure(output);
        var type = new com.fasterxml.jackson.core.type.TypeReference<String>() { };
        assertEquals(body, CompleteSourceGraphMaterializer.readGzip(pin, type, 16 << 20));
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.readGzip(pin, type));
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.readGzip(pin, type, 32 << 20));
    }

    @Test void actualNegativeReceiptProducerAndTypedEnvelopeRetainIndependentTwoAndFourMiBBounds() throws Exception {
        byte[] original;
        try (var input = getClass().getResourceAsStream("/build-receipts/full-g2-capture01-red.json")) {
            assertNotNull(input); original = input.readNBytes((2 << 20) + 1);
        }
        assertEquals(1201708, original.length);
        assertEquals("c2423f9f849244232fe4a592113c01a3fbb45af77436952c5a7157da5fa93c42",
                java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(original)));
        var mapper = ControlBuild.strictMapper();
        var terminal = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(original).get("terminal");
        terminal.put("source_limit_profile", R2.name());
        terminal.put("error", "synthetic R2 envelope boundary padding; original terminal remains RED:" + "x".repeat(2 << 20));
        var receipt = mapper.treeToValue(terminal, ControlBuild.BuildReceipt.class);
        assertEquals("RED", receipt.status()); assertFalse(receipt.mavenResult().passed());
        byte[] bytes = ControlBuild.buildReceiptBytes(receipt);
        assertTrue(bytes.length > ControlBuild.BUILD_RECEIPT_MAX_BYTES);
        assertTrue(bytes.length <= ControlBuild.receiptMaxBytes(R2));
        Path path = temporary.resolve("r2-red-receipt.json"); Files.write(path, bytes);
        assertEquals(receipt, mapper.readValue(ControlBuild.readReceiptEnvelope(ControlBuild.FileRef.measure(path)), ControlBuild.BuildReceipt.class));
        assertThrows(IOException.class, () -> ControlBuild.readBuildReceiptEnvelope(path));
        assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(path));
        terminal.put("source_limit_profile", ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024.name());
        Files.write(path, mapper.writeValueAsBytes(terminal));
        assertThrows(IOException.class, () -> ControlBuild.readReceiptEnvelope(ControlBuild.FileRef.measure(path)));
        terminal.put("source_limit_profile", R2.name()); terminal.put("error", "x".repeat(4 << 20));
        var tooLarge = mapper.treeToValue(terminal, ControlBuild.BuildReceipt.class);
        assertThrows(IOException.class, () -> ControlBuild.buildReceiptBytes(tooLarge));
    }

    private record Inputs(Path python, Path repo, Path corpus, Path manifest, Map<String, String> environment, List<Path> originals) { }
    private Inputs inputs(String name) throws IOException {
        Path repo = Files.createDirectory(temporary.resolve(name)), python = repo.resolve("python.exe");
        Files.writeString(python, "binding fixture; never executed");
        Path workflow = repo.resolve(".github/workflows/static-ci.yml"); Files.createDirectories(workflow.getParent()); Files.writeString(workflow, "fixture workflow path binding only");
        Path producer = repo.resolve(FullParityOracleBindings.NATIVE_RELATIVE); Files.createDirectories(producer.getParent()); Files.writeString(producer, "# producer binding only");
        Map<String, String> environment = new TreeMap<>(CanonicalOracleEnvironment.bind(repo, python, Map.of()));
        List<Path> originals = new ArrayList<>(List.of(python, workflow, producer));
        String[] roles = {"XAR_M3_TIMELINE_NATIVE_WHOLE", "XAR_ARMY_DEFAULT_RAISE_FIXTURE", "XAR_BATTLE_CONTEXT_SOURCE_FIXTURE", "XAR_BATTLE_CONTEXT_ADMISSIONS_FIXTURE", "XAR_RELIGION_CONTEXT_SOURCE_MAP", "XAR_ARMY_STRENGTHS_ORACLE_MANIFEST", "XAR_CONSTRUCTION_REFUND_PRODUCER_GOLDEN"};
        for (String role : roles) { Path file = repo.resolve(role + ".fixture"); Files.writeString(file, "input binding only"); environment.put(role, file.toString()); originals.add(file); }
        Path corpus = Files.createDirectory(repo.resolve("original-corpus")); Path whole = corpus.resolve("whole.json"); Files.writeString(whole, "{\"original\":true}");
        Path manifest = repo.resolve("corpus-manifest.json"); Person10NativeCorpus.produce(corpus, manifest);
        environment.put("XAR_PERSON10_NATIVE_CORPUS_MANIFEST", manifest.toString()); originals.add(whole); originals.add(manifest);
        return new Inputs(python, repo, corpus, manifest, Map.copyOf(environment), List.copyOf(originals));
    }
    private ControlBuild.Config config() {
        return new ControlBuild.Config(temporary.resolve("source"), temporary.resolve("work"), temporary.resolve("release.json"),
                "resume-full35", "fixture-owner", null, temporary.resolve("java21"), "3.10.0", 900,
                ControlBuild.TargetKind.SERVICE_FAST_JAR, R2);
    }
}
