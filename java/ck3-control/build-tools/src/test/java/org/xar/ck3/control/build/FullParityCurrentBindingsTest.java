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
        Path snapshot = Path.of(selected.compiledJavaRoot());
        return ControlBuild.reactorVerifyArguments(config(Path.of(inputs.selectedJavaRoot())), temporary.resolve("settings.xml"), snapshot, temporary.resolve("build"), inputs.originalR2().python(), selected);
    }
    private ControlBuild.Config config(Path snapshot) {
        return new ControlBuild.Config(snapshot, temporary.resolve("work"), temporary.resolve("capacity-release.json"),
                "r3-oracle-abi", "fixture-owner", null, temporary.resolve("java21"), "3.10.0", 900, ControlBuild.TargetKind.SERVICE_FAST_JAR, R3);
    }
    @Test void originalV1PersistsAndReplaysButCannotQualifyNewLiveFeatureInputs() throws Exception {
        var current = inputs(); var oldRoles = current.additionalFixtures().stream().filter(value -> !value.role().domainExtension()).toList();
        var old = new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.ORIGINAL_SCHEMA, current.machineId(), current.observedAtUtc(), current.originalR2(), current.pythonRef(),
                current.nativeProducerRef(), current.selectedJavaRoot(), current.managersSource(), current.detachmentSource(), oldRoles, current.first7Root(), current.nativePublications());
        Path input = temporary.resolve("original-v1.json"); Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(old));
        assertEquals(old, FullParityCurrentBindings.readInputs(ControlBuild.FileRef.measure(input)));
        var recorded = bindings(old, ControlBuild.FileRef.measure(input));
        assertEquals(recorded, FullParityCurrentBindings.fromRecordedArguments(wholeMavenArguments(old, recorded)));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireLiveVersion(old));
        assertDoesNotThrow(() -> FullParityCurrentBindings.requireLiveVersion(current));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireExecutedInputs(current, recorded));
    }
    @Test void everyNewMandatoryDomainRoleFlowsIntoVersionedMavenArgumentsWithoutPartialFallback() throws Exception {
        var current = inputs(); var selected = bindings(current, new ControlBuild.FileRef(temporary.resolve("version2.json").toString(), 1, "a".repeat(64)));
        for (var role : FullParityCurrentBindings.Role.values()) if (role.domainExtension()) {
            assertTrue(selected.mavenArguments().contains("-D" + role.pathProperty() + "=" + current.additionalFixtures().stream().filter(row -> row.role() == role).findFirst().orElseThrow().source().path()));
            var missing = current.additionalFixtures().stream().filter(row -> row.role() != role).toList();
            assertThrows(IllegalArgumentException.class, () -> new FullParityCurrentBindings.Inputs(current.schema(), current.machineId(), current.observedAtUtc(), current.originalR2(), current.pythonRef(), current.nativeProducerRef(),
                    current.selectedJavaRoot(), current.managersSource(), current.detachmentSource(), missing, current.first7Root(), current.nativePublications()));
            var incompleteArguments = wholeMavenArguments(current, selected).stream().filter(arg -> !arg.startsWith("-D" + role.shaProperty() + "=")).toList();
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(incompleteArguments));
        }
    }
    @Test void originalV2RemainsExactArchiveReplayAndCannotBecomeCurrentLiveInputs() throws Exception {
        var current = inputs(); var previousRoles = current.additionalFixtures().stream().filter(value -> value.role().generation() <= 2).toList();
        var previous = new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.PREVIOUS_SCHEMA, current.machineId(), current.observedAtUtc(), current.originalR2(), current.pythonRef(),
                current.nativeProducerRef(), current.selectedJavaRoot(), current.managersSource(), current.detachmentSource(), previousRoles, current.first7Root(), current.nativePublications());
        Path input = temporary.resolve("previous-v2.json"); Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(previous));
        assertEquals(previous, FullParityCurrentBindings.readInputs(ControlBuild.FileRef.measure(input)));
        var recorded = bindings(previous, ControlBuild.FileRef.measure(input)); var arguments = wholeMavenArguments(previous, recorded);
        Files.delete(input); assertEquals(recorded, FullParityCurrentBindings.fromRecordedArguments(arguments));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireLiveVersion(previous));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireExecutedInputs(current, recorded));
        assertEquals(25, previousRoles.size()); assertEquals(42, current.additionalFixtures().size());
    }
    @Test void actualCompiledSourceRebindingFeedsTheWholeCommandAndRefusesArbitraryOrDriftingSource() throws Exception {
        var inputs = inputs(); Path compiled = Files.createDirectory(temporary.resolve("compiled-source"));
        for (String target : List.of(FullParityCurrentBindings.MANAGERS_TARGET, FullParityCurrentBindings.DETACHMENT_TARGET, FullParityCurrentBindings.PORTABLE_METHODS_TARGET)) {
            Path output = compiled.resolve(target); Files.createDirectories(output.getParent()); Files.copy(Path.of(inputs.selectedJavaRoot()).resolve(target), output);
        }
        var fixtures = FullParityCurrentBindings.compiledFixtures(inputs.selectedJavaRoot(), compiled, inputs.additionalFixtures());
        var executed = new FullParityCurrentBindings.Bindings(new ControlBuild.FileRef(temporary.resolve("feature-v3.json").toString(), 1, "a".repeat(64)), inputs.machineId(), inputs.originalR2(), inputs.selectedJavaRoot(), compiled.toString(),
                ControlBuild.FileRef.measure(compiled.resolve(FullParityCurrentBindings.MANAGERS_TARGET)), ControlBuild.FileRef.measure(compiled.resolve(FullParityCurrentBindings.DETACHMENT_TARGET)), fixtures, inputs.first7Root(), softwareArguments(inputs));
        FullParityCurrentBindings.requireExecutedInputs(inputs, executed);
        var arguments = wholeMavenArguments(inputs, executed); assertEquals(executed, FullParityCurrentBindings.fromRecordedArguments(arguments));
        var role = FullParityCurrentBindings.Role.PORTABLE_METHODS_COMPILED_JAVA_SOURCE;
        var actual = fixtures.stream().filter(value -> value.role() == role).findFirst().orElseThrow().source();
        assertTrue(arguments.contains("-D" + role.pathProperty() + "=" + compiled.resolve(FullParityCurrentBindings.PORTABLE_METHODS_TARGET)));
        assertTrue(arguments.contains("-Dxar.portable.evidence.methods.source.bytes=" + actual.bytes()));
        assertThrows(IllegalArgumentException.class, role::environment, "compiled source cannot be selected by ambient path");
        assertEquals("xar.warEntry.fullPower.nativeWireBytes", FullParityCurrentBindings.Role.WAR_ENTRY_FULL_POWER_12004_WIRE.bytesProperty());
        Path arbitrary = temporary.resolve("arbitrary.java"); Files.copy(compiled.resolve(FullParityCurrentBindings.PORTABLE_METHODS_TARGET), arbitrary);
        var crossed = fixtures.stream().map(value -> value.role() == role ? new FullParityCurrentBindings.Fixture(role, new ControlBuild.FileRef(arbitrary.toString(), actual.bytes(), actual.sha256())) : value).toList();
        assertThrows(IllegalArgumentException.class, () -> new FullParityCurrentBindings.Bindings(executed.inputsRef(), executed.machineId(), executed.originalR2(), executed.selectedJavaRoot(), executed.compiledJavaRoot(), executed.managersSource(), executed.detachmentSource(), crossed, executed.first7Root()));
        Files.writeString(compiled.resolve(FullParityCurrentBindings.PORTABLE_METHODS_TARGET), "different compiled producer");
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.compiledFixtures(inputs.selectedJavaRoot(), compiled, inputs.additionalFixtures()));
    }
    @Test void originalV3ExactReplayRetainsItsNativeInputsButCannotBecomeLiveWithoutActualSourceGraphPair() throws Exception {
        var current = inputs(); var previousRoles = current.additionalFixtures().stream().filter(value -> value.role().generation() <= 3).toList();
        var previous = new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.FEATURE_SCHEMA, current.machineId(), current.observedAtUtc(), current.originalR2(), current.pythonRef(),
                current.nativeProducerRef(), current.selectedJavaRoot(), current.managersSource(), current.detachmentSource(), previousRoles, current.first7Root(), current.nativePublications());
        Path input = temporary.resolve("previous-v3.json"); Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(previous));
        assertEquals(previous, FullParityCurrentBindings.readInputs(ControlBuild.FileRef.measure(input)));
        var recorded = bindings(previous, ControlBuild.FileRef.measure(input)); var arguments = wholeMavenArguments(previous, recorded);
        Files.delete(input); assertEquals(recorded, FullParityCurrentBindings.fromRecordedArguments(arguments));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireLiveVersion(previous));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireExecutedInputs(current, recorded));
        assertEquals(30, previousRoles.size());
        var selected = bindings(current, recorded.inputsRef()); var complete = wholeMavenArguments(current, selected);
        for (String prefix : List.of("xar.sourceIndex.actualInput", "xar.sourceIndex.actualPlan")) {
            for (String suffix : List.of("path", "bytes", "sha256")) {
                String property = "-D" + prefix + "." + suffix + "=";
                assertEquals(1, complete.stream().filter(value -> value.startsWith(property)).count());
                var missing = complete.stream().filter(value -> !value.startsWith(property)).toList();
                assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(missing), property);
            }
        }
    }
    @Test void originalV4ArchivesRemainExactAndNewBundlePropertiesReachTheCompleteRecordedConsumer() throws Exception {
        var current = inputs(); var oldRoles = current.additionalFixtures().stream().filter(value -> value.role().generation() <= 4).toList();
        var old = new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.GRAPH_SCHEMA, current.machineId(), current.observedAtUtc(), current.originalR2(), current.pythonRef(),
                current.nativeProducerRef(), current.selectedJavaRoot(), current.managersSource(), current.detachmentSource(), oldRoles, current.first7Root(), current.nativePublications());
        Path input = temporary.resolve("previous-v4.json"); Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(old));
        var oldBindings = bindings(old, ControlBuild.FileRef.measure(input)); var oldArguments = wholeMavenArguments(old, oldBindings);
        assertEquals(old, FullParityCurrentBindings.readInputs(ControlBuild.FileRef.measure(input)));
        Files.delete(input); assertEquals(oldBindings, FullParityCurrentBindings.fromRecordedArguments(oldArguments));
        assertTrue(oldArguments.stream().noneMatch(value -> value.startsWith("-Dxar.fullParity.current.schema=")), "archive argv stays exact");
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireLiveVersion(old));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireExecutedInputs(current, oldBindings));
        assertEquals(32, oldRoles.size()); assertEquals(42, current.additionalFixtures().size());
        var selected = bindings(current, oldBindings.inputsRef()); var complete = wholeMavenArguments(current, selected);
        assertEquals(selected, FullParityCurrentBindings.fromRecordedArguments(complete));
        assertTrue(complete.contains("-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v10"));
        var prefixes = List.of("xar.public.mcp.tools", "xar.original.driver.cold.fixture", "xar.original.driver.adoption.fixture");
        for (String prefix : prefixes) {
            String path = prefix.equals("xar.public.mcp.tools") ? prefix + ".path" : prefix;
            for (String property : List.of(path, prefix + ".bytes", prefix + ".sha256")) {
                String start = "-D" + property + "=";
                assertEquals(1, complete.stream().filter(value -> value.startsWith(start)).count());
                assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(complete.stream().filter(value -> !value.startsWith(start)).toList()), property);
            }
        }
        assertEquals("xar.pairAppend12004.nativeWire", FullParityCurrentBindings.Role.PAIR_APPEND_OBSERVATION_12004_WIRE.pathProperty());
        assertEquals("xar.pairAppend12004.nativeWireSha256", FullParityCurrentBindings.Role.PAIR_APPEND_OBSERVATION_12004_WIRE.shaProperty());
        for (var value : current.additionalFixtures()) if (value.role().generation() >= 5) {
            var original = value.source();
            assertThrows(IllegalArgumentException.class, () -> new FullParityCurrentBindings.Fixture(value.role(), new ControlBuild.FileRef(original.path(), value.role().maxBytes() + 1, original.sha256())));
        }
        var withoutNewRoles = complete.stream().filter(value -> current.additionalFixtures().stream().filter(row -> row.role().generation() >= 5)
                .noneMatch(row -> value.startsWith("-D" + row.role().pathProperty() + "=") || value.startsWith("-D" + row.role().bytesProperty() + "=") || value.startsWith("-D" + row.role().shaProperty() + "="))).toList();
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(withoutNewRoles), "explicit v7 marker cannot downgrade missing full new group to v4 archive");
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(complete.stream().filter(value -> !value.startsWith("-Dxar.fullParity.current.schema=")).toList()));
    }
    @Test void originalV5MarkerRemainsExactArchiveAndActualCaptureReceiptRequiresOneCompleteTriple() throws Exception {
        var current = inputs(); var previousRoles = current.additionalFixtures().stream().filter(value -> value.role().generation() <= 5).toList();
        var previous = new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.BUNDLE_SCHEMA,current.machineId(),current.observedAtUtc(),current.originalR2(),current.pythonRef(),current.nativeProducerRef(),current.selectedJavaRoot(),current.managersSource(),current.detachmentSource(),previousRoles,current.first7Root(),current.nativePublications());
        Path path=temporary.resolve("previous-v5.json");Files.write(path,ControlBuild.strictMapper().writeValueAsBytes(previous));
        var archived=bindings(previous,ControlBuild.FileRef.measure(path));var arguments=wholeMavenArguments(previous,archived);
        assertTrue(arguments.contains("-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v5"));
        assertEquals(previous,FullParityCurrentBindings.readInputs(ControlBuild.FileRef.measure(path)));Files.delete(path);
        assertEquals(archived,FullParityCurrentBindings.fromRecordedArguments(arguments));
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.requireLiveVersion(previous));
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.requireExecutedInputs(current,archived));
        var selected=bindings(current,archived.inputsRef());var complete=wholeMavenArguments(current,selected);
        assertEquals(selected,FullParityOracleBindings.fromRecordedArguments(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4,complete));
        var role=FullParityCurrentBindings.Role.ORIGINAL_MCP_CAPTURE_RECEIPT;
        assertEquals("XAR_ORIGINAL_MCP_CAPTURE_RECEIPT",role.environment());assertEquals(1L<<20,role.maxBytes());
        for(String property:List.of(role.pathProperty(),role.bytesProperty(),role.shaProperty())){
            String prefix="-D"+property+"=";assertEquals(1,complete.stream().filter(value->value.startsWith(prefix)).count());
            assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(complete.stream().filter(value->!value.startsWith(prefix)).toList()));
        }
        var wrongMarker=complete.stream().map(value->value.startsWith("-Dxar.fullParity.current.schema=")?"-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v5":value).toList();
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(wrongMarker));
        assertEquals(36,previousRoles.size());assertEquals(42,current.additionalFixtures().size());
    }
    @Test void originalV6ArchiveKeepsItsMarkerAndRuntimeConfigurationIsOneExactRequiredFileRef() throws Exception {
        var current=inputs();var previousRoles=current.additionalFixtures().stream().filter(value->value.role().generation()<=6).toList();
        var previous=new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.CAPTURE_SCHEMA,current.machineId(),current.observedAtUtc(),current.originalR2(),current.pythonRef(),current.nativeProducerRef(),current.selectedJavaRoot(),current.managersSource(),current.detachmentSource(),previousRoles,current.first7Root(),current.nativePublications());
        Path path=temporary.resolve("previous-v6.json");Files.write(path,ControlBuild.strictMapper().writeValueAsBytes(previous));
        var archived=bindings(previous,ControlBuild.FileRef.measure(path));var archivedArguments=wholeMavenArguments(previous,archived);
        assertEquals(previous,FullParityCurrentBindings.readInputs(ControlBuild.FileRef.measure(path)));Files.delete(path);
        assertTrue(archivedArguments.contains("-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v6"));
        assertEquals(archived,FullParityCurrentBindings.fromRecordedArguments(archivedArguments));
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.requireLiveVersion(previous));
        var selected=bindings(current,archived.inputsRef());var complete=wholeMavenArguments(current,selected);
        assertEquals(selected,FullParityOracleBindings.fromRecordedArguments(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4,complete));
        var role=FullParityCurrentBindings.Role.ORIGINAL_ROOT_RUNTIME_DEFINITIONS;
        assertEquals("XAR_ORIGINAL_ROOT_RUNTIME_DEFINITIONS",role.environment());assertEquals(1L<<20,role.maxBytes());
        assertEquals(List.of("xar.root.runtime.definitions.path","xar.root.runtime.definitions.bytes","xar.root.runtime.definitions.sha256"),List.of(role.pathProperty(),role.bytesProperty(),role.shaProperty()));
        for(String property:List.of(role.pathProperty(),role.bytesProperty(),role.shaProperty())){
            String prefix="-D"+property+"=";String actual=complete.stream().filter(value->value.startsWith(prefix)).findFirst().orElseThrow();
            assertEquals(1,complete.stream().filter(value->value.startsWith(prefix)).count());
            assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(complete.stream().filter(value->!value.startsWith(prefix)).toList()));
            var duplicate=new ArrayList<>(complete);duplicate.add(actual);assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(duplicate));
            assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(complete.stream().map(value->value.startsWith(prefix)?prefix:value).toList()));
        }
        var wrongMarker=complete.stream().map(value->value.startsWith("-Dxar.fullParity.current.schema=")?"-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v6":value).toList();
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(wrongMarker));
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.requireExecutedInputs(current,archived));
        assertEquals(37,previousRoles.size());assertEquals(42,current.additionalFixtures().size());
    }
    @Test void v7ArchiveAndPublicationRequestKeepSeparateExactTriplesThroughWholeArguments() throws Exception {
        var current=inputs();var oldRoles=current.additionalFixtures().stream().filter(value->value.role().generation()<=7).toList();
        var old=new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.RUNTIME_SCHEMA,current.machineId(),current.observedAtUtc(),current.originalR2(),current.pythonRef(),current.nativeProducerRef(),current.selectedJavaRoot(),current.managersSource(),current.detachmentSource(),oldRoles,current.first7Root(),current.nativePublications());
        Path oldPath=temporary.resolve("previous-v7.json");Files.write(oldPath,ControlBuild.strictMapper().writeValueAsBytes(old));
        var archived=bindings(old,ControlBuild.FileRef.measure(oldPath));var oldArguments=wholeMavenArguments(old,archived);
        assertEquals(old,FullParityCurrentBindings.readInputs(archived.inputsRef()));Files.delete(oldPath);
        assertTrue(oldArguments.contains("-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v7"));
        assertEquals(archived,FullParityCurrentBindings.fromRecordedArguments(oldArguments));
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.requireLiveVersion(old));
        Path currentPath=temporary.resolve("current-v9.json");Files.write(currentPath,ControlBuild.strictMapper().writeValueAsBytes(current));
        var selected=bindings(current,ControlBuild.FileRef.measure(currentPath));var arguments=wholeMavenArguments(current,selected);
        assertEquals(current,FullParityCurrentBindings.readInputs(selected.inputsRef()));Files.delete(currentPath);
        assertEquals(selected,FullParityOracleBindings.fromRecordedArguments(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4,arguments));
        assertDoesNotThrow(()->FullParityCurrentBindings.requireExecutedInputs(current,selected));
        var role=FullParityCurrentBindings.Role.ORIGINAL_ROOT_RUNTIME_DEFINITIONS_PUBLICATION_REQUEST;
        var request=current.additionalFixtures().stream().filter(value->value.role()==role).findFirst().orElseThrow().source();
        var definitions=current.additionalFixtures().stream().filter(value->value.role()==FullParityCurrentBindings.Role.ORIGINAL_ROOT_RUNTIME_DEFINITIONS).findFirst().orElseThrow().source();
        assertNotEquals(request.path(),definitions.path());assertEquals(8,role.generation());assertEquals(1L<<20,role.maxBytes());
        assertEquals("XAR_ORIGINAL_ROOT_RUNTIME_DEFINITIONS_PUBLICATION_REQUEST",role.environment());
        assertEquals(List.of("xar.root.runtime.definitions.publication.request.path","xar.root.runtime.definitions.publication.request.bytes","xar.root.runtime.definitions.publication.request.sha256"),List.of(role.pathProperty(),role.bytesProperty(),role.shaProperty()));
        for(String property:List.of(role.pathProperty(),role.bytesProperty(),role.shaProperty())){
            String prefix="-D"+property+"=";String value=arguments.stream().filter(arg->arg.startsWith(prefix)).findFirst().orElseThrow();
            assertEquals(1,arguments.stream().filter(arg->arg.startsWith(prefix)).count());
            assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(arguments.stream().filter(arg->!arg.startsWith(prefix)).toList()));
            var duplicate=new ArrayList<>(arguments);duplicate.add(value);assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(duplicate));
            assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(arguments.stream().map(arg->arg.startsWith(prefix)?prefix:arg).toList()));
        }
        for(String bad:List.of("0","01","true","1.0","1048577"))assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(arguments.stream().map(arg->arg.startsWith(role.bytesArgument())?role.bytesArgument()+bad:arg).toList()));
        assertThrows(IllegalArgumentException.class,()->new FullParityCurrentBindings.Fixture(role,new ControlBuild.FileRef(request.path(),role.maxBytes()+1,request.sha256())));
        var wrongMarker=arguments.stream().map(arg->arg.startsWith("-Dxar.fullParity.current.schema=")?"-Dxar.fullParity.current.schema="+FullParityCurrentBindings.RUNTIME_SCHEMA:arg).toList();
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(wrongMarker));
        var missingRequest=oldArguments.stream().map(arg->arg.startsWith("-Dxar.fullParity.current.schema=")?"-Dxar.fullParity.current.schema="+FullParityCurrentBindings.SCHEMA:arg).toList();
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(missingRequest));
        var substituted=arguments.stream().map(arg->arg.startsWith(role.pathArgument())?role.pathArgument()+definitions.path():arg).toList();
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.requireExecutedInputs(current,FullParityCurrentBindings.fromRecordedArguments(substituted)));
        assertEquals(38,oldRoles.size());assertEquals(44,current.additionalFixtures().size());
    }
    @Test void v8PublicationArchiveRemainsExactAndCannotSubstituteForMandatorySoftwareFixtures() throws Exception {
        var current = inputs(); var oldRoles = current.additionalFixtures().stream().filter(value -> value.role().generation() <= 8).toList();
        var old = new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.PUBLICATION_SCHEMA, current.machineId(), current.observedAtUtc(), current.originalR2(),
                current.pythonRef(), current.nativeProducerRef(), current.selectedJavaRoot(), current.managersSource(), current.detachmentSource(), oldRoles, current.first7Root(), current.nativePublications());
        var recorded = bindings(old, new ControlBuild.FileRef(temporary.resolve("archive-v8.json").toString(), 1, "a".repeat(64)));
        var arguments = wholeMavenArguments(old, recorded);
        assertTrue(arguments.contains("-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v8"));
        assertNull(recorded.softwareFixtureArguments()); assertEquals(recorded, FullParityCurrentBindings.fromRecordedArguments(arguments));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireLiveVersion(old));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireExecutedInputs(current, recorded));
        assertThrows(IllegalArgumentException.class, () -> new FullParityCurrentBindings.Bindings(recorded.inputsRef(), current.machineId(), current.originalR2(),
                current.selectedJavaRoot(), current.selectedJavaRoot(), current.managersSource(), current.detachmentSource(), current.additionalFixtures(), current.first7Root()));
    }
    @Test void oneSoftwareBundleFeedsAllActualPropertyConsumersAndColdReplayRejectsCrossedOrPartialArguments() throws Exception {
        var current = inputs(); var selected = bindings(current, new ControlBuild.FileRef(temporary.resolve("software-v9.json").toString(), 1, "b".repeat(64)));
        var arguments = wholeMavenArguments(current, selected); var software = softwareArguments(current);
        assertEquals(11, software.mavenArguments().size());
        assertEquals(software, SdkFixtureProductionInputs.fromRecordedArguments(arguments));
        assertEquals(selected, FullParityCurrentBindings.fromRecordedArguments(arguments));
        String guiBytes = "-D" + GuiEightOracleFixture.PROPERTY + ".bytes=";
        for (String bad : List.of("0", "01", "true", "1.0", "65537"))
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(arguments.stream()
                    .map(value -> value.startsWith(guiBytes) ? guiBytes + bad : value).toList()));
        for (String argument : software.mavenArguments()) {
            String prefix = argument.substring(0, argument.indexOf('=') + 1);
            assertEquals(List.of(argument), arguments.stream().filter(value -> value.startsWith(prefix)).toList());
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(arguments.stream().filter(value -> !value.startsWith(prefix)).toList()), prefix);
            var duplicate = new ArrayList<>(arguments); duplicate.add(argument);
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(duplicate), prefix);
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(arguments.stream().map(value -> value.startsWith(prefix) ? prefix : value).toList()), prefix);
        }
        String gui = "-D" + GuiEightOracleFixture.PROPERTY + "=";
        var bundleRole = FullParityCurrentBindings.Role.SOFTWARE_FIXTURE_INPUTS;
        var downgraded = arguments.stream().filter(value -> !value.startsWith(bundleRole.pathArgument())
                && !value.startsWith(bundleRole.bytesArgument()) && !value.startsWith(bundleRole.shaArgument()))
                .map(value -> value.startsWith("-Dxar.fullParity.current.schema=")
                        ? "-Dxar.fullParity.current.schema=" + FullParityCurrentBindings.PUBLICATION_SCHEMA : value).toList();
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(downgraded));
        var crossed = arguments.stream().map(value -> value.startsWith(gui) ? gui + temporary.resolve("different-config.json") : value).toList();
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireExecutedInputs(current, FullParityCurrentBindings.fromRecordedArguments(crossed)));
        var bundleRef = current.additionalFixtures().stream().filter(value -> value.role() == FullParityCurrentBindings.Role.SOFTWARE_FIXTURE_INPUTS).findFirst().orElseThrow().source();
        var bundle = SdkFixtureProductionInputs.read(bundleRef);
        assertEquals(bundle, SdkFixtureProductionInputs.decode(SdkFixtureProductionInputs.encode(bundle)));
        var mapper = ControlBuild.strictMapper(); var raw = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.valueToTree(bundle);
        for (String name : List.of("gui_configuration_ref", "law_wires", "law_scratch_directory", "nested_quantity_wire_ref", "lobby_wires")) {
            var missing = raw.deepCopy(); missing.remove(name);
            assertThrows(IOException.class, () -> mapper.treeToValue(missing, SdkFixtureProductionInputs.Inputs.class), name);
        }
        var unknown = raw.deepCopy(); unknown.put("native_current_authority", true);
        assertThrows(IOException.class, () -> mapper.treeToValue(unknown, SdkFixtureProductionInputs.Inputs.class));
        var bool = raw.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) bool.path("nested_quantity_wire_ref")).put("bytes", true);
        assertThrows(IOException.class, () -> mapper.treeToValue(bool, SdkFixtureProductionInputs.Inputs.class));
        Files.delete(Path.of(bundleRef.path()));
        assertEquals(selected, FullParityCurrentBindings.fromRecordedArguments(arguments), "completed replay opens no current bundle or environment");
    }
    @Test void legacyThreePackageRecordedProjectionRemainsDataAndV2CannotPartiallyDowngrade() throws Exception {
        var current = inputs(); var software = softwareArguments(current);
        var oldArguments = software.mavenArguments().stream().filter(value -> !value.startsWith("-D" + SdkFixtureProductionInputs.BUNDLE_SCHEMA_PROPERTY + "=")
                && !value.startsWith("-D" + SdkFixtureProductionInputs.LOBBY_DIRECTORY + "=")).toList();
        var old = SdkFixtureProductionInputs.fromRecordedArguments(oldArguments);
        assertEquals(SdkFixtureProductionInputs.Generation.V1_THREE, old.generation());
        assertEquals(oldArguments, old.mavenArguments());
        assertEquals(9, old.mavenArguments().size());
        assertEquals(SdkFixtureProductionInputs.Generation.V2_FOUR, software.generation());
        assertNotEquals(old, software);
        var bundleRef = current.additionalFixtures().stream().filter(value -> value.role() == FullParityCurrentBindings.Role.SOFTWARE_FIXTURE_INPUTS).findFirst().orElseThrow().source();
        var bundle = SdkFixtureProductionInputs.read(bundleRef);
        var legacy = new SdkFixtureProductionInputs.Inputs(SdkFixtureProductionInputs.LEGACY_SCHEMA, bundle.machineId(), bundle.reviewAtUtc(),
                bundle.guiConfigurationRef(), bundle.lawWires(), bundle.lawScratchDirectory(), bundle.nestedQuantityWireRef(), null);
        assertEquals(legacy, SdkFixtureProductionInputs.decode(SdkFixtureProductionInputs.encode(legacy)));
        assertThrows(IllegalArgumentException.class, () -> SdkFixtureProductionInputs.requireCurrent(legacy));
        assertEquals(old, SdkFixtureProductionInputs.commandArguments(legacy));
        var wrongMarker = software.mavenArguments().stream().map(value -> value.startsWith("-D" + SdkFixtureProductionInputs.BUNDLE_SCHEMA_PROPERTY + "=")
                ? "-D" + SdkFixtureProductionInputs.BUNDLE_SCHEMA_PROPERTY + "=" + SdkFixtureProductionInputs.LEGACY_SCHEMA : value).toList();
        assertThrows(IllegalArgumentException.class, () -> SdkFixtureProductionInputs.fromRecordedArguments(wrongMarker));
    }
    @Test void currentSourceDeclarationAndProvisionalDefinitionRolesRoundtripThroughExactMavenArguments() throws Exception {
        var current=inputs();var bindings=bindings(current,new ControlBuild.FileRef(temporary.resolve("source-v10.json").toString(),1,"b".repeat(64)));
        var arguments=wholeMavenArguments(current,bindings);
        assertEquals("xar.full-parity-current-oracle-inputs/v11",FullParityCurrentBindings.SCHEMA);
        for(var role:List.of(FullParityCurrentBindings.Role.ORIGINAL_ROOT_RUNTIME_DEFINITIONS_SOURCE_DECLARATION,
                FullParityCurrentBindings.Role.ORIGINAL_ROOT_PUBLIC_MCP_PROVISIONAL_DEFINITIONS)) {
            assertEquals(10,role.generation());assertEquals(1L<<20,role.maxBytes());
            var original=current.additionalFixtures().stream().filter(row->row.role()==role).findFirst().orElseThrow().source();
            for(String value:List.of(role.pathArgument()+original.path(),role.bytesArgument()+original.bytes(),role.shaArgument()+original.sha256())) {
                assertTrue(arguments.contains(value));
                assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(arguments.stream().filter(arg->!arg.equals(value)).toList()));
                var duplicate=new ArrayList<>(arguments);duplicate.add(value);
                assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(duplicate));
            }
        }
        assertEquals(bindings,FullParityCurrentBindings.fromRecordedArguments(arguments));
        var source=FullParityCurrentBindings.Role.ORIGINAL_ROOT_RUNTIME_DEFINITIONS_SOURCE_DECLARATION;
        assertEquals("XAR_ORIGINAL_ROOT_RUNTIME_DEFINITIONS_SOURCE_DECLARATION",source.environment());
        assertEquals(List.of("xar.root.runtime.definitions.source.declaration.path","xar.root.runtime.definitions.source.declaration.bytes",
                "xar.root.runtime.definitions.source.declaration.sha256"),List.of(source.pathProperty(),source.bytesProperty(),source.shaProperty()));
        var provisional=FullParityCurrentBindings.Role.ORIGINAL_ROOT_PUBLIC_MCP_PROVISIONAL_DEFINITIONS;
        assertEquals("XAR_ORIGINAL_ROOT_PUBLIC_MCP_PROVISIONAL_DEFINITIONS",provisional.environment());
        assertEquals(List.of("xar.root.public.mcp.provisional.definitions.path","xar.root.public.mcp.provisional.definitions.bytes",
                "xar.root.public.mcp.provisional.definitions.sha256"),List.of(provisional.pathProperty(),provisional.bytesProperty(),provisional.shaProperty()));
        var downgraded=arguments.stream().map(arg->arg.startsWith("-Dxar.fullParity.current.schema=")
                ?"-Dxar.fullParity.current.schema="+FullParityCurrentBindings.SOFTWARE_SCHEMA:arg).toList();
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(downgraded));
    }

    @Test void historicalV9SoftwareInputsRetainTheirOriginalSerdeAndReplayWithoutNewSourceRoles() throws Exception {
        var current=inputs();var oldRoles=current.additionalFixtures().stream().filter(row->row.role().generation()<=9).toList();
        var legacy=new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.SOFTWARE_SCHEMA,current.machineId(),current.observedAtUtc(),
                current.originalR2(),current.pythonRef(),current.nativeProducerRef(),current.selectedJavaRoot(),current.managersSource(),
                current.detachmentSource(),oldRoles,current.first7Root(),current.nativePublications());
        Path path=temporary.resolve("archive-v9.json");Files.write(path,ControlBuild.strictMapper().writeValueAsBytes(legacy));
        var original=ControlBuild.FileRef.measure(path);assertEquals(legacy,FullParityCurrentBindings.readInputs(original));
        var binding=bindings(legacy,original);var arguments=wholeMavenArguments(legacy,binding);
        assertTrue(arguments.contains("-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v9"));
        assertFalse(arguments.stream().anyMatch(arg->arg.startsWith("-Dxar.root.runtime.definitions.source.declaration.")
                ||arg.startsWith("-Dxar.root.public.mcp.provisional.definitions.")));
        assertEquals(binding,FullParityCurrentBindings.fromRecordedArguments(arguments));
        FullParityCurrentBindings.requireExecutedInputs(legacy,binding);
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.requireLiveVersion(legacy));
        var falseUpgrade=arguments.stream().map(arg->arg.startsWith("-Dxar.fullParity.current.schema=")
                ?"-Dxar.fullParity.current.schema="+FullParityCurrentBindings.SCHEMA:arg).toList();
        assertThrows(IllegalArgumentException.class,()->FullParityCurrentBindings.fromRecordedArguments(falseUpgrade));
    }

    private SdkFixtureProductionInputs.CommandArguments softwareArguments(FullParityCurrentBindings.Inputs inputs) throws IOException {
        if (!FullParityCurrentBindings.SCHEMA.equals(inputs.schema()) && !FullParityCurrentBindings.SOURCE_DECLARATION_SCHEMA.equals(inputs.schema())
                && !FullParityCurrentBindings.SOFTWARE_SCHEMA.equals(inputs.schema())) return null;
        var ref = inputs.additionalFixtures().stream().filter(value -> value.role() == FullParityCurrentBindings.Role.SOFTWARE_FIXTURE_INPUTS).findFirst().orElseThrow().source();
        return SdkFixtureProductionInputs.commandArguments(SdkFixtureProductionInputs.read(ref));
    }
    /** Pure command/serde fixtures; no GUI oracle, native producer or private Root is executed or qualified. */
    private byte[] softwareBundle(Path repo) throws IOException {
        Path law = Files.createDirectory(repo.resolve("original-law-contract-inputs")); var originals = new ArrayList<ControlBuild.FileRef>();
        for (String name : List.of("query.json", "pending.json", "unchanged.json", "enacted.json")) {
            Path file = law.resolve(name); Files.writeString(file, "metadata command contract only"); originals.add(ControlBuild.FileRef.measure(file));
        }
        Path gui = repo.resolve("gui-original-config-contract.json"), wire = repo.resolve("nested-wire-contract.json");
        Files.writeString(gui, "metadata command contract only"); Files.writeString(wire, "metadata command contract only");
        Path scratch = Files.createDirectory(repo.resolve("owned-law-contract-scratch"));
        Path lobby = Files.createDirectory(repo.resolve("owned-lobby-contract-inputs")); var lobbyRefs = new ArrayList<ControlBuild.FileRef>();
        for (String name : SdkFixtureProductionInputs.LOBBY_NAMES) {
            Path file = lobby.resolve(name); Files.writeString(file, "metadata command contract only"); lobbyRefs.add(ControlBuild.FileRef.measure(file));
        }
        return SdkFixtureProductionInputs.encode(new SdkFixtureProductionInputs.Inputs(SdkFixtureProductionInputs.SCHEMA, "contract-fixture",
                "2030-01-01T00:00:00Z", ControlBuild.FileRef.measure(gui), new SdkFixtureProductionInputs.LawWireSet(law.toString(), originals),
                scratch.toString(), ControlBuild.FileRef.measure(wire), new SdkFixtureProductionInputs.LobbyWireSet(lobby.toString(), lobbyRefs)));
    }
    @Test void currentConstructionPairsFlowFromEnvironmentThroughWholeCommandAndRecordedConsumer() throws Exception {
        var current = inputs(); var environment = new TreeMap<String, String>();
        for (var fixture : current.additionalFixtures()) if (!fixture.role().compiledJavaSource())
            environment.put(fixture.role().environment(), fixture.source().path());
        // Real producer loop over controlled metadata files: this grants no Native packet execution credit.
        assertEquals(current.additionalFixtures(), FullParityCurrentBindings.collectAdditionalFixtures(
                Path.of(current.selectedJavaRoot()), environment));
        Path input = temporary.resolve("construction-current.json");
        Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(current));
        var inputRef = ControlBuild.FileRef.measure(input);
        var reread = FullParityCurrentBindings.readInputs(inputRef); assertEquals(current, reread);
        var selected = bindings(reread, inputRef);
        var produced = wholeMavenArguments(reread, selected);
        List<String> arguments = ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(produced),
                new com.fasterxml.jackson.core.type.TypeReference<List<String>>() { });
        assertEquals(selected, FullParityCurrentBindings.fromRecordedArguments(arguments));
        assertTrue(arguments.contains("-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v11"));
        for (var role : List.of(FullParityCurrentBindings.Role.CONSTRUCTION_REFUND_NATIVE_PACKETS,
                FullParityCurrentBindings.Role.CONSTRUCTION_REFUND_SIGNED_GOLDEN)) {
            var exact = current.additionalFixtures().stream().filter(row -> row.role() == role).findFirst().orElseThrow().source();
            for (String property : List.of(role.pathArgument() + exact.path(), role.shaArgument() + exact.sha256())) {
                assertEquals(1, arguments.stream().filter(property::equals).count());
                String prefix = property.substring(0, property.indexOf('=') + 1);
                assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(
                        arguments.stream().filter(value -> !value.startsWith(prefix)).toList()));
                var duplicate = new ArrayList<>(arguments); duplicate.add(property);
                assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(duplicate));
            }
            var missing = new TreeMap<>(environment); missing.remove(role.environment());
            assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.collectAdditionalFixtures(
                    Path.of(current.selectedJavaRoot()), missing));
            assertFalse(current.originalR2().mavenArguments().stream().anyMatch(value ->
                    value.startsWith(role.pathArgument()) || value.startsWith(role.shaArgument())));
        }
        var packets = FullParityCurrentBindings.Role.CONSTRUCTION_REFUND_NATIVE_PACKETS;
        var signed = current.additionalFixtures().stream().filter(row -> row.role() ==
                FullParityCurrentBindings.Role.CONSTRUCTION_REFUND_SIGNED_GOLDEN).findFirst().orElseThrow().source();
        var crossed = arguments.stream().map(value -> value.startsWith(packets.pathArgument())
                ? packets.pathArgument() + signed.path() : value).toList();
        var executed = FullParityCurrentBindings.fromRecordedArguments(crossed);
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireExecutedInputs(current, executed));
        assertEquals(List.of(FullParityOracleBindings.ResumedFixtureRole.values()),
                current.originalR2().nativeFixtures().stream().map(FullParityOracleBindings.ResumedFixture::role).toList());
    }

    @Test void historicalV10RetainsExactRolesAndCannotRelabelConstructionPairs() throws Exception {
        var current = inputs(); var oldRoles = current.additionalFixtures().stream().filter(row -> row.role().generation() <= 10).toList();
        var historical = new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.SOURCE_DECLARATION_SCHEMA,
                current.machineId(), current.observedAtUtc(), current.originalR2(), current.pythonRef(), current.nativeProducerRef(),
                current.selectedJavaRoot(), current.managersSource(), current.detachmentSource(), oldRoles, current.first7Root(), current.nativePublications());
        Path input = temporary.resolve("archive-v10.json"); Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(historical));
        var inputRef = ControlBuild.FileRef.measure(input); assertEquals(historical, FullParityCurrentBindings.readInputs(inputRef));
        var archived = bindings(historical, inputRef); var oldArguments = wholeMavenArguments(historical, archived);
        assertEquals(42, oldRoles.size());
        assertTrue(oldArguments.contains("-Dxar.fullParity.current.schema=xar.full-parity-current-oracle-inputs/v10"));
        assertFalse(oldArguments.stream().anyMatch(value -> value.startsWith("-Dxar.construction.refund.native.packets=")
                || value.startsWith("-Dxar.construction.refund.signed.golden=")));
        assertEquals(archived, FullParityCurrentBindings.fromRecordedArguments(oldArguments));
        assertEquals(current.originalR2(), FullParityOracleBindings.fromRecordedArguments(
                ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2, oldArguments));
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.requireLiveVersion(historical));
        assertDoesNotThrow(() -> FullParityCurrentBindings.requireLiveVersion(current));
        var falseUpgrade = oldArguments.stream().map(value -> value.startsWith("-Dxar.fullParity.current.schema=")
                ? "-Dxar.fullParity.current.schema=" + FullParityCurrentBindings.SCHEMA : value).toList();
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(falseUpgrade));
        var currentArguments = wholeMavenArguments(current, bindings(current, inputRef));
        var falseDowngrade = currentArguments.stream().map(value -> value.startsWith("-Dxar.fullParity.current.schema=")
                ? "-Dxar.fullParity.current.schema=" + FullParityCurrentBindings.SOURCE_DECLARATION_SCHEMA : value).toList();
        assertThrows(IllegalArgumentException.class, () -> FullParityCurrentBindings.fromRecordedArguments(falseDowngrade));
    }

    private FullParityCurrentBindings.Bindings bindings(FullParityCurrentBindings.Inputs inputs, ControlBuild.FileRef input) throws IOException {
        return new FullParityCurrentBindings.Bindings(input, inputs.machineId(), inputs.originalR2(), inputs.selectedJavaRoot(), inputs.selectedJavaRoot(), inputs.managersSource(), inputs.detachmentSource(), inputs.additionalFixtures(), inputs.first7Root(), softwareArguments(inputs));
    }
    private FullParityCurrentBindings.Inputs inputs() throws Exception {
        ProjectStoragePolicy.requireBulkOutput(temporary);
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
        for (var role : FullParityCurrentBindings.Role.values()) { Path source = role.compiledJavaSource() ? repo.resolve(FullParityCurrentBindings.PORTABLE_METHODS_TARGET) : repo.resolve(role.name() + ".role"); Files.createDirectories(source.getParent()); if (role == FullParityCurrentBindings.Role.SOFTWARE_FIXTURE_INPUTS) Files.write(source, softwareBundle(repo));
            else Files.writeString(source, "metadata contract only; no execution qualification"); roles.add(new FullParityCurrentBindings.Fixture(role, ControlBuild.FileRef.measure(source))); }
        Path managers = repo.resolve(FullParityCurrentBindings.MANAGERS_TARGET), detachment = repo.resolve(FullParityCurrentBindings.DETACHMENT_TARGET); Files.createDirectories(managers.getParent());
        Files.writeString(managers, "selected managers compiler input"); Files.writeString(detachment, "selected detachment compiler input");
        return new FullParityCurrentBindings.Inputs(FullParityCurrentBindings.SCHEMA, "contract-fixture", "2026-10-24T00:00:00Z", r2, ControlBuild.FileRef.measure(python), ControlBuild.FileRef.measure(nativeSource),
                repo.toString(), ControlBuild.FileRef.measure(managers), ControlBuild.FileRef.measure(detachment), roles, repo.resolve("first7").toString(),
                java.util.Arrays.stream(NativeFixtureCorpora.Kind.values()).map(kind -> new FullParityCurrentBindings.NativePublication(kind, roles.getFirst().source(), roles.getFirst().source())).toList());
    }
}


