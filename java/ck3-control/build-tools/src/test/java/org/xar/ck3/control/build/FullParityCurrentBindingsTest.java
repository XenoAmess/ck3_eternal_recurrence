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

/** Contract and original-command replay only; controlled fixture bytes grant no Native or Game coverage. */
final class FullParityCurrentBindingsTest {
    @TempDir Path temporary;
    private static final ControlBuild.SourceLimitProfile R3 = ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3;

    @Test void newGenerationRetainsEveryOriginalLimitAndWholeReactorTestConsumer() throws Exception {
        var old = CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024;
        var r2 = CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R2;
        var r3 = CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R3;
        assertEquals(3072, old.maxFiles()); assertEquals(40L << 20, old.maxLogicalBytes()); assertEquals(56L << 20, old.maxNativeBytes());
        assertEquals(r2.maxFiles(), r3.maxFiles()); assertEquals(4096, r3.maxFiles()); assertEquals(64L << 20, r3.maxLogicalBytes()); assertEquals(80L << 20, r3.maxNativeBytes());
        assertEquals(16 << 20, r3.copyProofMaxBytes()); assertEquals(4 << 20, ControlBuild.receiptMaxBytes(R3));
        assertEquals(CompleteSourceGraph.modules(r2), CompleteSourceGraph.modules(r3)); assertEquals(35, R3.maxReactorProjects());
        assertEquals(ReactorTestClosure.g2FullParityCurrentRequirements(), ControlCi.httpRequirements(R3));
        assertTrue(ControlCi.httpRequirements(R3).containsAll(ReactorTestClosure.g2FullParityResumeRequirements()));
        assertThrows(IOException.class, () -> ControlCi.requireFullParityFixtureProduction(R3, null));
    }

    @Test void actualR2InputProducerFeedsNewTypedBindingsAndRecordedConsumerWithoutCurrentEnvironment() throws Exception {
        var inputs = inputs(); var mapper = ControlBuild.strictMapper(); Path input = temporary.resolve("current.json");
        Files.write(input, mapper.writeValueAsBytes(inputs)); var inputRef = ControlBuild.FileRef.measure(input);
        assertEquals(inputs, FullParityCurrentBindings.readInputs(inputRef));
        var selected = bindings(inputs, inputRef);
        // The original failure handed a role fragment to a complete recorded-command reader.
        // Execute the real complete producer, then persist/parse its exact argv before either consumer.
        var producedArguments = wholeMavenArguments(inputs, selected);
        var arguments = mapper.readValue(mapper.writeValueAsBytes(producedArguments), new com.fasterxml.jackson.core.type.TypeReference<List<String>>() { });
        assertEquals(producedArguments, arguments);
        assertEquals("verify", arguments.getLast());
        assertFalse(arguments.stream().anyMatch(value -> value.equals("-pl") || value.startsWith("-Dtest=") || value.startsWith("-DskipTests=")));
        assertEquals(selected, FullParityCurrentBindings.fromRecordedArguments(arguments));
        FullParityCurrentBindings.requireExecutedInputs(inputs, selected);
        assertEquals(30, inputs.originalR2().mavenArguments().size());
        assertEquals(inputs.originalR2(), FullParityOracleBindings.fromRecordedArguments(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2, arguments));
        assertEquals(selected, mapper.readValue(mapper.writeValueAsBytes(selected), FullParityCurrentBindings.Bindings.class));
        Files.delete(input); for (var fixture : inputs.additionalFixtures()) Files.delete(Path.of(fixture.source().path()));
        assertEquals(selected, FullParityOracleBindings.fromRecordedArguments(R3, arguments), "completed replay uses original values, not current process configuration or files");
    }

    @Test void liveInputProducerRejectsMissingActualRolesAndNeverAdmitsAMetadataOnlyFirstCorpus() throws Exception {
        var inputs = inputs(); Map<String, String> env = new TreeMap<>();
        env.put("XAR_ORACLE_PYTHON", inputs.originalR2().python()); env.put("XAR_ORACLE_REPO", inputs.originalR2().repositoryRoot()); env.put("XAR_REPO_ROOT", inputs.originalR2().repositoryRoot());
        Path output = temporary.resolve("must-not-be-published.json");
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.produce(Path.of(inputs.selectedJavaRoot()), env, output)); assertFalse(Files.exists(output));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromEnvironment(Map.of(), Path.of(inputs.selectedJavaRoot())));
        assertThrows(IllegalArgumentException.class, () -> FullParityOracleBindings.fromEnvironment(R3, env));
        Path raw = temporary.resolve("unqualified.json"); Files.writeString(raw, "{}"); env.put("XAR_FULL_PARITY_CURRENT_INPUTS", raw.toString());
        env.put("XAR_FULL_PARITY_CURRENT_INPUTS_SHA256", ControlBuild.FileRef.measure(raw).sha256());
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromEnvironment(env, Path.of(inputs.selectedJavaRoot())));
    }

    @Test void everyTypedRoleAndCompiledSourcePathIsRequiredAndStrictSerializationRejectsAmbiguity() throws Exception {
        var inputs = inputs(); var mapper = ControlBuild.strictMapper(); var raw = mapper.valueToTree(inputs);
        for (String field : List.of("python_ref", "additional_fixtures", "first7_root")) {
            var bad = ((com.fasterxml.jackson.databind.node.ObjectNode)raw).deepCopy(); bad.remove(field);
            assertThrows(IOException.class, () -> mapper.treeToValue(bad, FullParityCurrentBindings.Inputs.class));
        }
        var bad = ((com.fasterxml.jackson.databind.node.ObjectNode)raw).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)bad.path("additional_fixtures").get(0).get("source")).put("bytes", true);
        assertThrows(IOException.class, () -> mapper.treeToValue(bad, FullParityCurrentBindings.Inputs.class));
        var selected = bindings(inputs, new ControlBuild.FileRef(temporary.resolve("pinned.json").toString(), 1, "a".repeat(64)));
        var whole = wholeMavenArguments(inputs, selected);
        var duplicate = new ArrayList<>(whole); duplicate.add(duplicate.stream().filter(arg -> arg.startsWith("-Dxar.ownerRecall12004.nativeWire=")).findFirst().orElseThrow());
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(duplicate));
        var missing = whole.stream().filter(arg -> !arg.startsWith("-Dxar.family.result.source.manifest.sha256=")).toList();
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(missing));
        assertThrows(IllegalArgumentException.class, () -> selected.requireCompiledRoot(temporary.resolve("another-source")));
        assertThrows(IllegalArgumentException.class, () -> new FullParityCurrentBindings.Bindings(selected.inputsRef(), selected.machineId(), selected.originalR2(), selected.selectedJavaRoot(), selected.compiledJavaRoot(),
                selected.detachmentSource(), selected.managersSource(), selected.additionalFixtures(), selected.first7Root()));
    }
    @Test void completeActualProducerKeepsTheMandatoryAbiUniqueAndRejectsCrossedMissingOrDuplicateRoles() throws Exception {
        var inputs = inputs(); var selected = bindings(inputs, new ControlBuild.FileRef(temporary.resolve("recorded-current.json").toString(), 1, "a".repeat(64)));
        List<String> arguments = wholeMavenArguments(inputs, selected);
        assertFalse(selected.mavenArguments().stream().anyMatch(value -> value.startsWith("-Dxar.rootContext.pythonExecutable=")), "only the complete shared producer owns the Root bootstrap role");
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(selected.mavenArguments()), "a role fragment cannot satisfy the complete recorded ABI");
        String otherPython = temporary.resolve("different-python.exe").toString();
        for (String property : List.of("-Dxar.rootContext.pythonExecutable=", "-Dxar.python=", "-Dxar.native.producer.python=")) {
            assertEquals(List.of(property + inputs.originalR2().python()), arguments.stream().filter(value -> value.startsWith(property)).toList());
            var crossed = arguments.stream().map(value -> value.startsWith(property) ? property + otherPython : value).toList();
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(crossed), property);
        }
        var mandatory = new ArrayList<>(selected.mavenArguments()); mandatory.add("-Dxar.rootContext.pythonExecutable=" + inputs.originalR2().python());
        for (String argument : mandatory) {
            String property = argument.substring(0, argument.indexOf('=') + 1);
            assertEquals(List.of(argument), arguments.stream().filter(value -> value.startsWith(property)).toList());
            var missing = arguments.stream().filter(value -> !value.startsWith(property)).toList();
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(missing), property);
            var duplicate = new ArrayList<>(arguments); duplicate.add(argument);
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(duplicate), property);
            var empty = arguments.stream().map(value -> value.startsWith(property) ? property : value).toList();
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(empty), property);
        }
        Path snapshot = Path.of(inputs.selectedJavaRoot());
        assertThrows(IllegalArgumentException.class, () -> ControlBuild.reactorVerifyArguments(config(snapshot), temporary.resolve("settings.xml"), snapshot,
                temporary.resolve("build"), otherPython, selected), "the actual producer rejects a crossed Root interpreter before launch");
    }
    private List<String> wholeMavenArguments(FullParityCurrentBindings.Inputs inputs, FullParityCurrentBindings.Bindings selected) {
        Path snapshot = Path.of(inputs.selectedJavaRoot());
        return ControlBuild.reactorVerifyArguments(config(snapshot), temporary.resolve("settings.xml"), snapshot, temporary.resolve("build"), inputs.originalR2().python(), selected);
    }
    private ControlBuild.Config config(Path snapshot) {
        return new ControlBuild.Config(snapshot, temporary.resolve("work"), temporary.resolve("capacity-release.json"),
                "r3-oracle-abi", "fixture-owner", null, temporary.resolve("java21"), "3.10.0", 900, ControlBuild.TargetKind.SERVICE_FAST_JAR, R3);
    }
    private FullParityCurrentBindings.Bindings bindings(FullParityCurrentBindings.Inputs inputs, ControlBuild.FileRef input) {
        return new FullParityCurrentBindings.Bindings(input, inputs.machineId(), inputs.originalR2(), inputs.selectedJavaRoot(), inputs.selectedJavaRoot(), inputs.managersSource(), inputs.detachmentSource(), inputs.additionalFixtures(), inputs.first7Root());
    }
    private FullParityCurrentBindings.Inputs inputs() throws Exception {
        Path repo = Files.createTempDirectory(temporary, "repo-"); Path python = repo.resolve("python.exe"); Files.writeString(python, "contract fixture never executed");
        Path workflow = repo.resolve(".github/workflows/static-ci.yml"); Files.createDirectories(workflow.getParent()); Files.writeString(workflow, "contract workflow");
        Path nativeSource = repo.resolve(FullParityOracleBindings.NATIVE_RELATIVE); Files.createDirectories(nativeSource.getParent()); Files.writeString(nativeSource, "original producer fixture");
        var env = new TreeMap<>(CanonicalOracleEnvironment.bind(repo, python, Map.of()));
        for (String key : List.of("XAR_M3_TIMELINE_NATIVE_WHOLE", "XAR_ARMY_DEFAULT_RAISE_FIXTURE", "XAR_BATTLE_CONTEXT_SOURCE_FIXTURE", "XAR_BATTLE_CONTEXT_ADMISSIONS_FIXTURE", "XAR_RELIGION_CONTEXT_SOURCE_MAP", "XAR_ARMY_STRENGTHS_ORACLE_MANIFEST", "XAR_CONSTRUCTION_REFUND_PRODUCER_GOLDEN")) {
            Path source = repo.resolve(key + ".original"); Files.writeString(source, "exact old R2 role input"); env.put(key, source.toString());
        }
        Path corpus = Files.createDirectory(repo.resolve("person10")); Files.writeString(corpus.resolve("whole.json"), "{\"original\":true}");
        Path corpusManifest = repo.resolve("person10.json"); Person10NativeCorpus.produce(corpus, corpusManifest); env.put("XAR_PERSON10_NATIVE_CORPUS_MANIFEST", corpusManifest.toString());
        var r2 = (FullParityOracleBindings.ResumedBindings)FullParityOracleBindings.fromEnvironment(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2, env);
        var roles = new ArrayList<FullParityCurrentBindings.Fixture>();
        for (var role : FullParityCurrentBindings.Role.values()) { Path source = repo.resolve(role.name() + ".role"); Files.writeString(source, "metadata contract only; no execution qualification"); roles.add(new FullParityCurrentBindings.Fixture(role, ControlBuild.FileRef.measure(source))); }
        Path managers = repo.resolve(FullParityCurrentBindings.MANAGERS_TARGET), detachment = repo.resolve(FullParityCurrentBindings.DETACHMENT_TARGET); Files.createDirectories(managers.getParent());
        Files.writeString(managers, "selected managers compiler input"); Files.writeString(detachment, "selected detachment compiler input");
        return new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.SCHEMA, "contract-fixture", "2026-10-24T00:00:00Z", r2, ControlBuild.FileRef.measure(python), ControlBuild.FileRef.measure(nativeSource),
                repo.toString(), ControlBuild.FileRef.measure(managers), ControlBuild.FileRef.measure(detachment), roles, repo.resolve("first7").toString(),
                java.util.Arrays.stream(NativeFixtureCorpora.Kind.values()).map(kind -> new FullParityCurrentBindings.NativePublication(kind, roles.getFirst().source(), roles.getFirst().source())).toList());
    }
}
