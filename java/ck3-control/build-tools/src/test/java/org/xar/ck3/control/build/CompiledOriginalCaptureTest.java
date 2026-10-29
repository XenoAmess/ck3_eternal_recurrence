package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class CompiledOriginalCaptureTest {
    @TempDir Path temporary;

    @Test void typedOriginalRequestStrictRoundTripPreservesInvocationRoles() throws Exception {
        var request = request("unit-machine"); var mapper = ControlBuild.strictMapper();
        assertEquals(request, CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(request)));
        ObjectNode unknown = mapper.valueToTree(request); unknown.put("class_allowlist", "anything");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(unknown)));
        ObjectNode wrong = mapper.valueToTree(request);
        ((ObjectNode) wrong.path("profile").path("capture_receipt_ref")).put("bytes", true);
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(wrong)));
        ObjectNode missing = mapper.valueToTree(request); missing.remove("profile");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(missing)));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void typedArgvRejectsUnboundInputsAndSourceExportCannotBecomeASecondBootstrap() {
        var file = ref(temporary.resolve("input.json"));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Argument(
                CompiledOriginalCaptureProfile.ArgumentKind.INPUT_FILE, temporary.resolve("other.json").toString(), file));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Argument(
                CompiledOriginalCaptureProfile.ArgumentKind.LITERAL, file.path(), null));
        var good = request("unit-machine").profile();
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Profile(good.captureReceiptRef(),
                good.testCompilationRef(), good.callerToolsReceiptRef(), good.producerToolsReceiptRef(), good.selection(),
                CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, file, List.of(), List.of(), List.of(), null));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Profile(good.captureReceiptRef(),
                good.testCompilationRef(), good.callerToolsReceiptRef(), good.producerToolsReceiptRef(), good.selection(),
                CompiledOriginalCaptureProfile.InvocationKind.MAIN, file, List.of(), List.of(), List.of(), null));
        assertThrows(IllegalArgumentException.class, () -> new CompiledCaptureProcess.Environment("JAVA_TOOL_OPTIONS", "-javaagent:x"));
    }

    @Test void actualJavaCompilerInventoryIncludesNestedClassesAndCopiedResources() throws Exception {
        Fixture fixture = fixture(); var inventory = inventory(fixture);
        assertEquals(2, inventory.runtimeClasses().size()); assertEquals(1, inventory.runtimeResources().size());
        assertEquals("fixture.CaptureFixture", inventory.entrypoint().binaryName());
        assertEquals(fixture.source(), inventory.entrypoint().sourceRef());
        assertEquals(inventory, inventory(fixture));
        Path injected = fixture.root().resolve("injected.class");
        Files.copy(Path.of(inventory.runtimeClasses().getFirst().path()), injected);
        assertThrows(IOException.class, () -> inventory(fixture));
    }

    @Test void actualCompilerSourceAndClasspathResourceDriftAreRejected() throws Exception {
        Fixture fixture = fixture(); inventory(fixture);
        Files.writeString(fixture.root().resolve("data.txt"), "changed");
        assertThrows(IOException.class, () -> inventory(fixture));
        Files.writeString(fixture.root().resolve("data.txt"), "resource");
        Files.writeString(Path.of(fixture.source().path()), "changed");
        assertThrows(IOException.class, () -> inventory(fixture));
    }

    @Test void originalPublicSourceExportAndMainRunUnchangedWithoutInferringAnUnavailableEntry() throws Exception {
        Fixture fixture = fixture();
        try (var loader = new URLClassLoader(new java.net.URL[] { fixture.root().toUri().toURL() }, getClass().getClassLoader())) {
            Class<?> target = Class.forName("fixture.CaptureFixture", false, loader);
            Path text = temporary.resolve("source.txt");
            OriginalCaptureInvoker.invoke(target, fixture.root().toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, new String[0], text);
            assertEquals("ORIGINAL_SOURCE\n", Files.readString(text));
            Path main = temporary.resolve("main.txt");
            OriginalCaptureInvoker.invoke(target, fixture.root().toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.MAIN, new String[] {main.toString()}, main);
            assertEquals("ORIGINAL_MAIN\n", Files.readString(main));
            assertThrows(IOException.class, () -> OriginalCaptureInvoker.invoke(target, fixture.root().toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, new String[0], text));
            Class<?> noEntry = Class.forName("fixture.CaptureFixture$Nested", false, loader);
            assertThrows(NoSuchMethodException.class, () -> OriginalCaptureInvoker.invoke(noEntry, fixture.root().toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, new String[0], temporary.resolve("absent.txt")));
            assertThrows(IllegalArgumentException.class, () -> OriginalCaptureInvoker.invoke(target, temporary.toString(),
                    CompiledOriginalCaptureProfile.InvocationKind.MAIN, new String[] {main.toString()}, main));
        }
    }

    @Test void missingGenuineReceiptTraversesRealProducerAndConsumerWithoutStartingAChild() throws Exception {
        var request = request(WindowsJobProcess.currentMachineId()); Path requestPath = temporary.resolve("request.json");
        Files.write(requestPath, ControlBuild.strictMapper().writeValueAsBytes(request));
        var spec = new CompiledOriginalCapture.RunSpec(ControlBuild.FileRef.measure(requestPath),
                temporary.resolve("receipt.json").toString(), limits(), CompiledOriginalCapture.Mode.EXECUTE);
        var result = CompiledOriginalCapture.execute(spec);
        assertEquals(CompiledOriginalCapture.Status.RED, result.status()); assertFalse(result.childStarted());
        assertEquals("xar.compiled-original-capture-actual/v6", result.schema()); assertNull(result.invocationEvidence());
        assertTrue(result.error().contains("capture.json")); assertFalse(Files.exists(Path.of(request.outputPath())));
        assertEquals(result, ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(spec.receiptPath())), CompiledOriginalCapture.Receipt.class));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.acceptedReceipt(ControlBuild.FileRef.measure(Path.of(spec.receiptPath())),
                CompiledOriginalCapture.Mode.EXECUTE));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.execute(spec));
    }

    @Test void passAndUnknownCannotBeManufacturedFromAnAckOrUnstartedCommand() {
        var request = ref(temporary.resolve("request.json"));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCapture.Receipt(CompiledOriginalCapture.RECEIPT_SCHEMA,
                "unit-machine", Instant.now().toString(), CompiledOriginalCapture.Mode.EXECUTE, CompiledOriginalCapture.Status.PASS,
                CompiledOriginalCapture.Scope.ORIGINAL_SOURCE_EXPORT_ONLY, request, limits(), false, null, request, true, null, null, null, null, List.of(), List.of(), null, null));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCapture.Receipt(CompiledOriginalCapture.RECEIPT_SCHEMA,
                "unit-machine", Instant.now().toString(), CompiledOriginalCapture.Mode.EXECUTE, CompiledOriginalCapture.Status.UNKNOWN,
                CompiledOriginalCapture.Scope.ORIGINAL_SOURCE_EXPORT_ONLY, request, limits(), false, null, null, false, null, null, null, null, List.of(), List.of(), "unavailable", null));
    }

    @Test void currentReceiptRequiresExplicitNullableEvidenceAndHistoricalMetadataCannotQualify() throws Exception {
        var request = request(WindowsJobProcess.currentMachineId());
        Path input = temporary.resolve("receipt-input.json"); Files.write(input, ControlBuild.strictMapper().writeValueAsBytes(request));
        Path destination = temporary.resolve("receipt.json");
        var actual = CompiledOriginalCapture.execute(new CompiledOriginalCapture.RunSpec(ControlBuild.FileRef.measure(input),
                destination.toString(), limits(), CompiledOriginalCapture.Mode.QUALIFY_ONLY));
        assertFalse(actual.childStarted()); assertNull(actual.invocationEvidence());
        var mapper = ControlBuild.strictMapper(); ObjectNode wire = mapper.valueToTree(actual);
        wire.remove("invocation_evidence");
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(wire), CompiledOriginalCapture.Receipt.class));
        wire.put("schema", CompiledOriginalCapture.HISTORICAL_RECEIPT_SCHEMA_V3);
        Path historical = temporary.resolve("historical-v3.json"); Files.write(historical, mapper.writeValueAsBytes(wire));
        var retained = ControlBuild.FileRef.measure(historical);
        var metadata = CompiledOriginalCapture.readHistoricalV3Metadata(retained);
        assertEquals(actual.error(), metadata.error()); assertEquals(actual.requestRef(), metadata.requestRef());
        assertEquals(actual.status(), metadata.status()); assertFalse(metadata.childStarted());
        assertThrows(IOException.class, () -> CompiledOriginalCapture.acceptedReceipt(retained, CompiledOriginalCapture.Mode.QUALIFY_ONLY));
        var v4 = (ObjectNode) mapper.valueToTree(actual); v4.put("schema", CompiledOriginalCapture.HISTORICAL_RECEIPT_SCHEMA_V4);
        Path historicalV4 = temporary.resolve("historical-v4.json"); Files.write(historicalV4, mapper.writeValueAsBytes(v4));
        var v4Ref = ControlBuild.FileRef.measure(historicalV4);
        assertEquals(actual.requestRef(), CompiledOriginalCapture.readHistoricalV4Metadata(v4Ref).requestRef());
        assertThrows(IOException.class, () -> CompiledOriginalCapture.acceptedReceipt(v4Ref, CompiledOriginalCapture.Mode.QUALIFY_ONLY));
        var v5=(ObjectNode)mapper.valueToTree(actual);v5.put("schema",CompiledOriginalCapture.HISTORICAL_RECEIPT_SCHEMA_V5);
        Path historicalV5=temporary.resolve("historical-v5.json");Files.write(historicalV5,mapper.writeValueAsBytes(v5));
        var v5Ref=ControlBuild.FileRef.measure(historicalV5);
        assertNull(CompiledOriginalCapture.readHistoricalV5Metadata(v5Ref).invocationEvidence());
        assertThrows(IOException.class,()->CompiledOriginalCapture.acceptedReceipt(v5Ref,CompiledOriginalCapture.Mode.QUALIFY_ONLY));
        wire.put("invocation_evidence", "invented");
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(wire), CompiledOriginalCapture.HistoricalReceiptV3.class));
    }

    @Test void originalArgvProducerPreservesUnicodePinsAndExactArgumentOrder() throws Exception {
        Path request = temporary.resolve("请求-Ω-😀.json"), proof = temporary.resolve("来源-ß-𐐀.json");
        Files.writeString(request, "actual request bytes"); Files.writeString(proof, "actual proof bytes");
        Path owned = temporary.resolve("owned-ascii"); Files.createDirectory(owned);
        var javaExecutable = ControlBuild.FileRef.measure(Path.of(System.getProperty("java.home")).resolve("bin/java.exe"));
        var requestRef = ControlBuild.FileRef.measure(request); var proofRef = ControlBuild.FileRef.measure(proof);
        var command = CompiledOriginalCapture.childCommand(javaExecutable, List.of("runtime-first", "资源-second"), owned, requestRef, proofRef);
        assertEquals(List.of(javaExecutable.path(), "-Xms16m", "-Xmx96m", "-Djava.io.tmpdir=" + owned, "-Djna.tmpdir=" + owned,
                "-cp", "runtime-first" + java.io.File.pathSeparator + "资源-second", OriginalCaptureInvoker.class.getName(),
                requestRef.path(), Long.toString(requestRef.bytes()), requestRef.sha256(),
                proofRef.path(), Long.toString(proofRef.bytes()), proofRef.sha256()), command);
        assertThrows(UnsupportedOperationException.class, () -> command.add("changed"));
    }

    @Test void actualUnicodeEnvelopeLaunchAndNativeTerminalUseOneRetainedInvocation() throws Exception {
        Path root = temporary.resolve("unicode-launch"), tmp = root.resolve("tmp"); Files.createDirectories(tmp);
        Path output = root.resolve("output.json");
        Path targetOrigin = Path.of(UnicodeInvocationChild.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        Path carrierOrigin = Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        var targetPin = CiBootstrap.JavaUtf8Invocation.captureClasspath(targetOrigin);
        var carrierPin = CiBootstrap.JavaUtf8Invocation.captureClasspath(carrierOrigin);
        var target = new CiBootstrap.JavaUtf8Invocation.ClassTarget(UnicodeInvocationChild.class.getName(), targetPin, List.of(targetPin));
        var directory = CiBootstrap.JavaUtf8Invocation.captureOutputRoot(root);
        var words = List.of(output.toString(), "罗贝尔 Ω ß 𐐀 😀", "", "quotes\" slash\\ newline\n");
        var logical = new CiBootstrap.JavaUtf8Invocation.Request(target,
                List.of(new CiBootstrap.JavaUtf8Invocation.Property("xar.capture.unicode.fixture", "配置-😀")), words, directory);
        var publication = CiBootstrap.JavaUtf8Invocation.publish(logical, directory, "actual-java.bin",
                pending -> CompiledCaptureProcess.requireAdditionalBytes(root, 8L << 20, pending));
        var carrier = new CiBootstrap.JavaUtf8Invocation.ClassCarrier(List.of(carrierPin));
        var options = new ArrayList<String>(List.of("-Xms16m", "-Xmx96m")); options.addAll(CompiledOriginalCapture.childTemporaryArguments(tmp));
        var launch = CiBootstrap.JavaUtf8Invocation.launch(publication, carrier, options);
        assertEquals(logical, CiBootstrap.JavaUtf8Invocation.inspect(launch.physicalArguments(), carrier, options));
        assertEquals(logical, CiBootstrap.JavaUtf8Invocation.read(publication));
        var command = new ArrayList<String>(); command.add(Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toString());
        command.addAll(launch.physicalArguments());
        var plan = new CompiledCaptureProcess.Plan(command, root.toString(), tmp.toString(), root.toString(),
                root.resolve("out.log").toString(), root.resolve("err.log").toString(), output.toString(), 65536, 8L << 20,
                30, Instant.now().plusSeconds(60).toString(), 256L << 20, List.of());
        var state = new CompiledCaptureProcess.StartState();
        var result = CompiledCaptureProcess.runJava(plan, launch, carrier, options, JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES, state);
        assertTrue(result.passed(), Files.readString(Path.of(plan.stderrPath()))); assertTrue(state.started());
        var evidence = state.actualEvidence(); assertEquals(result.identity(), evidence.actualProcess());
        assertSame(launch, state.actualLaunch());
        assertNull(state.preparationFailure());assertNull(state.custodyFailure());assertSame(result,state.actualTerminal());
        assertEquals(result,state.actualEvidence().nativeSources().terminal());
        assertEquals(evidence.nativeSources(),JavaUtf8NativeCustody.decodeEvidence(JavaUtf8NativeCustody.encodeEvidence(evidence.nativeSources())));
        assertEquals(launch.physicalArguments(), evidence.physicalArguments());
        CompiledCaptureProcess.requireJavaInvocation(evidence, carrier, options, logical);
        CompiledCaptureProcess.requireProcess(evidence, result);
        var preparation = CiBootstrap.JavaUtf8Invocation.inspectPreparation(CiBootstrap.JavaUtf8Invocation.captureFile(
                CiBootstrap.JavaUtf8Invocation.preparationPath(logical)), publication);
        assertEquals("CLASS", preparation.mode()); assertEquals(UnicodeInvocationChild.class.getName(), preparation.mainClass());
        assertEquals(targetOrigin.toString(), preparation.actualCodeSource());
        assertEquals(SharedSourceFiles.observe(CiBootstrap.JavaUtf8Invocation.preparationPath(logical)), evidence.preparation());
        var mapper = ControlBuild.strictMapper();
        assertEquals(evidence, mapper.readValue(mapper.writeValueAsBytes(evidence), CompiledCaptureProcess.InvocationEvidence.class));
        var actual = Files.readAllLines(output, StandardCharsets.UTF_8);
        assertEquals(List.of("配置-😀", words.get(1), words.get(2), words.get(3).replace("\n", "\\n")), actual);
        var foreign = new CompiledCaptureProcess.InvocationEvidence(evidence.physicalArguments(),
                new WindowsJobProcess.ProcessIdentity(result.identity().pid() + 1, result.identity().creationFiletimeDecimal(), result.identity().executable()), evidence.preparation(),evidence.nativeSources());
        assertThrows(IOException.class, () -> CompiledCaptureProcess.requireProcess(foreign, result));
        var changedPhysical = new ArrayList<String>(evidence.physicalArguments()); changedPhysical.set(0, "-Xms32m");
        var changedEvidence = new CompiledCaptureProcess.InvocationEvidence(changedPhysical, evidence.actualProcess(), evidence.preparation(),evidence.nativeSources());
        assertThrows(IOException.class, () -> CompiledCaptureProcess.requireJavaInvocation(changedEvidence, carrier, options, logical));
        var changed = new CiBootstrap.JavaUtf8Invocation.Request(target, logical.properties(), List.of("different"), directory);
        assertThrows(IOException.class, () -> CompiledCaptureProcess.requireJavaInvocation(evidence, carrier, options, changed));
        var strict = (ObjectNode) mapper.valueToTree(evidence); strict.remove("actual_process");
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(strict), CompiledCaptureProcess.InvocationEvidence.class));
        var missingPreparation = (ObjectNode) mapper.valueToTree(evidence); missingPreparation.remove("preparation");
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(missingPreparation), CompiledCaptureProcess.InvocationEvidence.class));
        var withoutPreparation = new CompiledCaptureProcess.InvocationEvidence(evidence.physicalArguments(), evidence.actualProcess(), null,evidence.nativeSources());
        assertThrows(IOException.class, () -> CompiledCaptureProcess.requireJavaInvocation(withoutPreparation, carrier, options, logical));
        var missingNative=(ObjectNode)mapper.valueToTree(evidence);missingNative.remove("native_sources");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(missingNative),CompiledCaptureProcess.InvocationEvidence.class));
        var noNative=new CompiledCaptureProcess.InvocationEvidence(evidence.physicalArguments(),evidence.actualProcess(),evidence.preparation(),null);
        assertThrows(IOException.class,()->CompiledCaptureProcess.requireJavaInvocation(noNative,carrier,options,logical));
        assertThrows(IOException.class, () -> CompiledCaptureProcess.runJava(plan, launch, carrier, options, JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES, state));
        Path preparationPath = Path.of(evidence.preparation().source().path()); byte[] preparedBytes = Files.readAllBytes(preparationPath);
        Files.move(preparationPath, preparationPath.resolveSibling("old-preparation-retained.bin"));
        Files.write(preparationPath, preparedBytes);
        assertThrows(IOException.class, () -> CompiledCaptureProcess.requireJavaInvocation(evidence, carrier, options, logical));
        Files.write(Path.of(publication.envelope().path()), new byte[] {0}, java.nio.file.StandardOpenOption.APPEND);
        assertThrows(IOException.class, () -> CompiledCaptureProcess.requireJavaInvocation(evidence, carrier, options, logical));
    }

    @Test void envelopeQuotaRefusesBeforeCreateAndStartupUnicodeOptionsRemainExplicitFailure() throws Exception {
        Path root = temporary.resolve("envelope-budget"); Files.createDirectory(root);
        Files.write(root.resolve("existing"), new byte[64]);
        assertThrows(IOException.class, () -> CompiledCaptureProcess.requireAdditionalBytes(root, 64, 1));
        var origin = CiBootstrap.JavaUtf8Invocation.captureClasspath(Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI()));
        var dir = CiBootstrap.JavaUtf8Invocation.captureOutputRoot(root);
        var logical = new CiBootstrap.JavaUtf8Invocation.Request(new CiBootstrap.JavaUtf8Invocation.ClassTarget(
                CiBootstrap.class.getName(), origin, List.of(origin)), List.of(), List.of("Ω"), dir);
        assertThrows(IOException.class, () -> CiBootstrap.JavaUtf8Invocation.publish(logical, dir, "refused.bin",
                pending -> CompiledCaptureProcess.requireAdditionalBytes(root, 64, pending)));
        assertFalse(Files.exists(root.resolve("refused.bin")));
        var publication = CiBootstrap.JavaUtf8Invocation.publish(logical, dir, "allowed.bin",
                pending -> CompiledCaptureProcess.requireAdditionalBytes(root, 8L << 20, pending));
        var carrier = new CiBootstrap.JavaUtf8Invocation.ClassCarrier(List.of(origin));
        assertThrows(IOException.class, () -> CiBootstrap.JavaUtf8Invocation.launch(publication, carrier, List.of("-Djava.io.tmpdir=临时")));
        Path preparation = CiBootstrap.JavaUtf8Invocation.preparationPath(logical);
        var invocation = new CompiledOriginalCapture.JavaInvocation(logical, carrier, List.of());
        CompiledOriginalCapture.requireInvocationOutput(invocation, root.resolve("original-output.json"));
        for (Path collision : List.of(preparation, preparation.resolve("child"), preparation.getParent()))
            assertThrows(IOException.class, () -> CompiledOriginalCapture.requireInvocationOutput(invocation, collision));
        Files.write(preparation, new byte[] {1});
        assertThrows(IOException.class, () -> CiBootstrap.JavaUtf8Invocation.publish(logical, dir, "occupied-preparation.bin",
                pending -> CompiledCaptureProcess.requireAdditionalBytes(root, 8L << 20, pending)));
        assertFalse(Files.exists(root.resolve("occupied-preparation.bin")));
        assertNull(new CompiledCaptureProcess.StartState().actualEvidence());
    }

    @Test void childRemovingItsActualPreparationRetainsNativeTerminalButCannotQualify() throws Exception {
        Path root = temporary.resolve("missing-preparation"), tmp = root.resolve("tmp"); Files.createDirectories(tmp);
        Path origin = Path.of(RemovePreparationChild.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        Path carrierOrigin = Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        var targetPin = CiBootstrap.JavaUtf8Invocation.captureClasspath(origin);
        var dir = CiBootstrap.JavaUtf8Invocation.captureOutputRoot(root);
        var logical = new CiBootstrap.JavaUtf8Invocation.Request(new CiBootstrap.JavaUtf8Invocation.ClassTarget(
                RemovePreparationChild.class.getName(), targetPin, List.of(targetPin)), List.of(),
                List.of(CiBootstrap.JavaUtf8Invocation.preparationPath(dir).toString()), dir);
        var carrier = new CiBootstrap.JavaUtf8Invocation.ClassCarrier(List.of(CiBootstrap.JavaUtf8Invocation.captureClasspath(carrierOrigin)));
        var publication = CiBootstrap.JavaUtf8Invocation.publish(logical, dir, "missing-proof.bin",
                pending -> CompiledCaptureProcess.requireAdditionalBytes(root, 8L << 20, pending));
        var options = new ArrayList<String>(List.of("-Xms16m", "-Xmx96m")); options.addAll(CompiledOriginalCapture.childTemporaryArguments(tmp));
        var launch = CiBootstrap.JavaUtf8Invocation.launch(publication, carrier, options);
        var command = new ArrayList<String>(); command.add(Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toString());
        command.addAll(launch.physicalArguments());
        var plan = new CompiledCaptureProcess.Plan(command, root.toString(), tmp.toString(), root.toString(),
                root.resolve("out.log").toString(), root.resolve("err.log").toString(), root.resolve("unused").toString(),
                65536, 8L << 20, 30, Instant.now().plusSeconds(60).toString(), 256L << 20, List.of());
        var state = new CompiledCaptureProcess.StartState();
        var terminal = CompiledCaptureProcess.runJava(plan, launch, carrier, options, JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES, state);
        assertTrue(terminal.passed(), Files.readString(Path.of(plan.stderrPath())));
        assertEquals(0, terminal.accounting().activeProcesses()); assertSame(launch, state.actualLaunch());
        assertEquals(terminal.identity(), state.actualEvidence().actualProcess()); assertNull(state.actualEvidence().preparation());
        assertSame(terminal,state.actualTerminal());assertNull(state.custodyFailure());assertNotNull(state.actualEvidence().nativeSources());
        assertTrue(state.preparationFailure() != null && !state.preparationFailure().isBlank());
        CompiledCaptureProcess.requireProcess(state.actualEvidence(), terminal);
        assertThrows(IOException.class, () -> CompiledCaptureProcess.requireJavaInvocation(state.actualEvidence(), carrier, options, logical));
    }

    @Test void insufficientRealReceiptAllowanceRefusesBeforeAnyNativeChildOrLogs()throws Exception {
        Path root=temporary.resolve("pre-native-evidence-cap"),tmp=root.resolve("tmp");Files.createDirectories(tmp);
        Path origin=Path.of(UnicodeInvocationChild.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        Path carrierRoot=Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        var target=CiBootstrap.JavaUtf8Invocation.captureClasspath(origin);
        var directory=CiBootstrap.JavaUtf8Invocation.captureOutputRoot(root);
        var logical=new CiBootstrap.JavaUtf8Invocation.Request(new CiBootstrap.JavaUtf8Invocation.ClassTarget(
                UnicodeInvocationChild.class.getName(),target,List.of(target)),List.of(),List.of(root.resolve("output.txt").toString()),directory);
        var publication=CiBootstrap.JavaUtf8Invocation.publish(logical,directory,"limited-envelope.bin",
                pending->CompiledCaptureProcess.requireAdditionalBytes(root,8L<<20,pending));
        var envelope=SharedSourceFiles.observe(Path.of(publication.envelope().path()));
        var carrier=new CiBootstrap.JavaUtf8Invocation.ClassCarrier(List.of(CiBootstrap.JavaUtf8Invocation.captureClasspath(carrierRoot)));
        var options=new ArrayList<String>(List.of("-Xms16m","-Xmx96m"));options.addAll(CompiledOriginalCapture.childTemporaryArguments(tmp));
        var launch=CiBootstrap.JavaUtf8Invocation.launch(publication,carrier,options);
        var command=new ArrayList<String>();command.add(Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toString());command.addAll(launch.physicalArguments());
        var plan=new CompiledCaptureProcess.Plan(command,root.toString(),tmp.toString(),root.toString(),root.resolve("out.log").toString(),
                root.resolve("err.log").toString(),root.resolve("output.txt").toString(),65536,8L<<20,30,Instant.now().plusSeconds(60).toString(),256L<<20,List.of());
        var state=new CompiledCaptureProcess.StartState();
        var failure=assertThrows(IOException.class,()->CompiledCaptureProcess.runJava(plan,launch,carrier,options,1,state));
        assertTrue(failure.getMessage().contains("original receipt allowance"),failure.toString());
        assertFalse(state.started());assertNull(state.actualTerminal());assertNull(state.actualEvidence());
        for(Path absent:List.of(Path.of(plan.stdoutPath()),Path.of(plan.stderrPath()),Path.of(plan.outputPath()),CiBootstrap.JavaUtf8Invocation.preparationPath(logical)))
            assertFalse(Files.exists(absent),absent.toString());
        SharedSourceFiles.assertUnchanged(envelope);
    }

    @Test void actualChildCannotRewriteTheEnvelopeHeldByItsOwnNativeCustody()throws Exception {
        var fixture=runCustodyFixture("held-envelope",RewriteHeldEnvelopeChild.class);
        assertTrue(fixture.terminal().passed(),Files.readString(Path.of(fixture.plan().stderrPath())));
        assertEquals("WRITE_DENIED",Files.readString(Path.of(fixture.plan().outputPath())));
        SharedSourceFiles.assertUnchanged(fixture.envelope());
        assertNull(fixture.state().custodyFailure());assertSame(fixture.terminal(),fixture.state().actualTerminal());
        CompiledCaptureProcess.requireJavaInvocation(fixture.state().actualEvidence(),fixture.carrier(),fixture.options(),fixture.launch().logicalRequest());
    }
    @Test void nativeCustodyNeverReplacesAnActualNonzeroChildTerminal()throws Exception {
        var fixture=runCustodyFixture("actual-fail42",Fail42CustodyChild.class);
        assertFalse(fixture.terminal().passed());assertEquals(42,fixture.terminal().exitCode());
        assertEquals(0,fixture.terminal().accounting().activeProcesses());
        assertSame(fixture.terminal(),fixture.state().actualTerminal());assertNull(fixture.state().custodyFailure());
        assertEquals(fixture.terminal(),fixture.state().actualEvidence().nativeSources().terminal());
        CompiledCaptureProcess.requireProcess(fixture.state().actualEvidence(),fixture.terminal());
        // Source continuity remains separate from original exit/limits and cannot turn this terminal into PASS.
        CompiledCaptureProcess.requireJavaInvocation(fixture.state().actualEvidence(),fixture.carrier(),fixture.options(),fixture.launch().logicalRequest());
    }
    private record CustodyFixture(WindowsJobProcess.CommandResult terminal,CompiledCaptureProcess.StartState state,
            CiBootstrap.JavaUtf8Invocation.Launch launch,CiBootstrap.JavaUtf8Invocation.ClassCarrier carrier,
            List<String> options,CompiledCaptureProcess.Plan plan,SharedSourceFiles.Witness envelope){ }
    private CustodyFixture runCustodyFixture(String name,Class<?> actualMain)throws Exception {
        Path root=temporary.resolve(name),tmp=root.resolve("tmp");Files.createDirectories(tmp);
        Path envelope=root.resolve("held-invocation.bin"),output=root.resolve("output.txt");
        Path targetRoot=Path.of(actualMain.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        Path carrierRoot=Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        var target=CiBootstrap.JavaUtf8Invocation.captureClasspath(targetRoot);
        var directory=CiBootstrap.JavaUtf8Invocation.captureOutputRoot(root);
        var request=new CiBootstrap.JavaUtf8Invocation.Request(new CiBootstrap.JavaUtf8Invocation.ClassTarget(
                actualMain.getName(),target,List.of(target)),List.of(),List.of(envelope.toString(),output.toString()),directory);
        var publication=CiBootstrap.JavaUtf8Invocation.publish(request,directory,envelope.getFileName().toString(),
                pending->CompiledCaptureProcess.requireAdditionalBytes(root,8L<<20,pending));
        var original=SharedSourceFiles.observe(envelope);
        var carrier=new CiBootstrap.JavaUtf8Invocation.ClassCarrier(List.of(CiBootstrap.JavaUtf8Invocation.captureClasspath(carrierRoot)));
        var options=new ArrayList<String>(List.of("-Xms16m","-Xmx96m"));options.addAll(CompiledOriginalCapture.childTemporaryArguments(tmp));
        var launch=CiBootstrap.JavaUtf8Invocation.launch(publication,carrier,options);
        var command=new ArrayList<String>();command.add(Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toString());command.addAll(launch.physicalArguments());
        var plan=new CompiledCaptureProcess.Plan(command,root.toString(),tmp.toString(),root.toString(),root.resolve("out.log").toString(),
                root.resolve("err.log").toString(),output.toString(),65536,8L<<20,30,Instant.now().plusSeconds(60).toString(),256L<<20,List.of());
        var state=new CompiledCaptureProcess.StartState();var terminal=CompiledCaptureProcess.runJava(plan,launch,carrier,options,JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES,state);
        return new CustodyFixture(terminal,state,launch,carrier,List.copyOf(options),plan,original);
    }
    public static final class RewriteHeldEnvelopeChild {
        private RewriteHeldEnvelopeChild(){ }
        public static void main(String[] args)throws IOException {
            String actual="WRITE_SUCCEEDED";
            try{Files.write(Path.of(args[0]),new byte[]{0},java.nio.file.StandardOpenOption.TRUNCATE_EXISTING);}
            catch(IOException denied){actual="WRITE_DENIED";}
            Files.writeString(Path.of(args[1]),actual,java.nio.file.StandardOpenOption.CREATE_NEW);
        }
    }
    public static final class Fail42CustodyChild {
        private Fail42CustodyChild(){ }
        public static void main(String[] args){System.exit(42);}
    }

    public static final class RemovePreparationChild {
        private RemovePreparationChild() { }
        public static void main(String[] args) throws IOException { Files.delete(Path.of(args[0])); }
    }

    public static final class UnicodeInvocationChild {
        private UnicodeInvocationChild() { }
        public static void main(String[] args) throws Exception {
            var lines = new ArrayList<String>(); lines.add(System.getProperty("xar.capture.unicode.fixture"));
            for (int index = 1; index < args.length; index++) lines.add(args[index].replace("\n", "\\n"));
            Files.write(Path.of(args[0]), lines, StandardCharsets.UTF_8, java.nio.file.StandardOpenOption.CREATE_NEW);
        }
    }

    @Test void finiteCanonicalModuleSelectionsRejectDuplicatesAliasesAndNonCaptureSources() {
        var source = ref(temporary.resolve("CaptureFixture.java")); var pom = ref(temporary.resolve("module/pom.xml"));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Selection("fixture.CaptureFixture", source,
                List.of(pom, pom), List.of()));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Selection("fixture.Main",
                ref(temporary.resolve("Main.java")), List.of(pom), List.of()));
        assertThrows(IllegalArgumentException.class, () -> CompiledOriginalCaptureProfile.canonical(temporary.resolve("a/../b").toString()));
    }

    @Test void sharedNativeEngineConsumesActualExitAndJobZero() throws Exception {
        Path root = temporary.resolve("engine"), tmp = root.resolve("tmp"); Files.createDirectories(tmp);
        Path java = Path.of(System.getProperty("java.home")).resolve("bin/java.exe");
        var state = new CompiledCaptureProcess.StartState();
        var plan = new CompiledCaptureProcess.Plan(List.of(java.toString(), "-Xms8m", "-Xmx16m", "-XX:+UseSerialGC", "-version"),
                root.toString(), tmp.toString(), root.toString(), root.resolve("stdout.log").toString(),
                root.resolve("stderr.log").toString(), root.resolve("not-produced.json").toString(), 1024, 1 << 20,
                15, Instant.now().plusSeconds(30).toString(), 128L << 20, List.of());
        var result = CompiledCaptureProcess.run(plan, state);
        assertTrue(state.started()); assertTrue(result.passed()); assertEquals(0, result.accounting().activeProcesses());
    }

    private record Fixture(Path snapshot, Path root, ControlBuild.FileRef source,
            List<ControlBuild.FileRef> inputs, ControlBuild.TestCompilationManifest manifest,
            CompiledOriginalCaptureProfile.Selection selection) { }

    /** Real javac bytes exercise only the inventory sub-boundary, never a fabricated accepted Maven/build receipt. */
    private Fixture fixture() throws Exception {
        Path snapshot = temporary.resolve("snapshot"), module = snapshot.resolve("module");
        Path source = module.resolve("src/test/java/fixture/CaptureFixture.java"), root = module.resolve("test-classes");
        Files.createDirectories(source.getParent()); Files.createDirectories(root);
        Files.writeString(source, "package fixture; public final class CaptureFixture {"
                + "public static String source(){ return \"ORIGINAL_SOURCE\\n\"; }"
                + "public static void main(String[] a)throws Exception{ if(a[0].equals(\"directory\")){"
                + "var scratch=java.nio.file.Path.of(a[1]).toRealPath();var input=java.nio.file.Path.of(a[2]).toRealPath();var out=java.nio.file.Path.of(a[3]);"
                + "java.nio.file.Files.createDirectory(out);java.nio.file.Files.copy(input.resolve(\"input.txt\"),out.resolve(\"result.txt\"));"
                + "java.nio.file.Files.writeString(scratch.resolve(\"side.txt\"),\"owned output\");Thread.sleep(1000);"
                + "}else java.nio.file.Files.writeString(java.nio.file.Path.of(a[0]),\"ORIGINAL_MAIN\\n\"); }"
                + "public static final class Nested{} }");
        var compiler = ToolProvider.getSystemJavaCompiler(); var errors = new ByteArrayOutputStream();
        assertEquals(0, compiler.run(null, errors, errors, "--release", "21", "-Xlint:all", "-Werror", "-d", root.toString(), source.toString()),
                errors.toString(StandardCharsets.UTF_8));
        Path pom = module.resolve("pom.xml"); Files.writeString(pom, "<project/>");
        Path resource = module.resolve("src/test/resources/data.txt"); Files.createDirectories(resource.getParent());
        Files.writeString(resource, "resource"); Files.copy(resource, root.resolve("data.txt"));
        Path inputs = module.resolve("inputs.lst"), created = module.resolve("created.lst");
        Files.writeString(inputs, source.toString()); Files.writeString(created, "fixture/CaptureFixture.class\nfixture/CaptureFixture$Nested.class\n");
        var classes = new ArrayList<ControlBuild.FileRef>();
        try (var walk = Files.walk(root)) {
            for (Path file : walk.filter(path -> path.toString().endsWith(".class")).sorted().toList()) classes.add(ControlBuild.FileRef.measure(file));
        }
        var sourceRef = ControlBuild.FileRef.measure(source); var pomRef = ControlBuild.FileRef.measure(pom);
        var manifest = new ControlBuild.TestCompilationManifest(ControlBuild.TEST_COMPILATION_SCHEMA, "unit-machine",
                Instant.now().toString(), ControlBuild.CaptureTestState.NOT_RUN,
                List.of(new ControlBuild.ModuleTestCompilation(pomRef, root.toString(), ControlBuild.FileRef.measure(inputs), ControlBuild.FileRef.measure(created))),
                List.of(new ControlBuild.NotRunTestCompilation(sourceRef, classes, ControlBuild.CaptureTestState.NOT_RUN)));
        return new Fixture(snapshot, root, sourceRef, List.of(pomRef, sourceRef, ControlBuild.FileRef.measure(resource)), manifest,
                new CompiledOriginalCaptureProfile.Selection("fixture.CaptureFixture", sourceRef, List.of(pomRef), List.of()));
    }
    private CompiledOriginalCaptureProfile.Inventory inventory(Fixture fixture) throws IOException {
        return CompiledOriginalCaptureProfile.inventory(fixture.snapshot(), fixture.inputs(), fixture.manifest(), fixture.selection());
    }
    private CompiledOriginalCapture.Request request(String machine) {
        var profile = new CompiledOriginalCaptureProfile.Profile(ref(temporary.resolve("capture.json")), ref(temporary.resolve("manifest.json")),
                ref(temporary.resolve("caller.json")), ref(temporary.resolve("producer.json")),
                new CompiledOriginalCaptureProfile.Selection("fixture.CaptureFixture", ref(temporary.resolve("CaptureFixture.java")),
                        List.of(ref(temporary.resolve("module/pom.xml"))), List.of()),
                CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, null, List.of(), List.of(), List.of(), null);
        return new CompiledOriginalCapture.Request(CompiledOriginalCapture.REQUEST_SCHEMA, "original-fixture", machine, temporary.toString(),
                profile, List.of(ref(temporary.resolve("CaptureFixture.java"))), List.of(ref(temporary.resolve("CaptureFixture.class"))),
                temporary.resolve("original.source.txt").toString(), CompiledOriginalCapture.OutputKind.FILE, 65536, 1 << 20, List.of());
    }
    private CompiledGoldenCapture.Limits limits() {
        return new CompiledGoldenCapture.Limits(temporary.toString(), temporary.toString(), Instant.now().plusSeconds(60).toString(), 60, 128L << 20);
    }
    private static ControlBuild.FileRef ref(Path path) { return new ControlBuild.FileRef(path.toString(), 1, "0".repeat(64)); }

    @Test void originalInnerJvmCarriesOwnedTemporaryPropertiesThroughActualNativeIdentity() throws Exception {
        Path owned = temporary.resolve("owned temporary directory"); Files.createDirectory(owned);
        var arguments = new ArrayList<String>(List.of(Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toString(), "-Xms8m", "-Xmx32m", "-XX:+UseSerialGC"));
        arguments.addAll(CompiledOriginalCapture.childTemporaryArguments(owned));
        arguments.addAll(List.of("-cp", System.getProperty("java.class.path"), TemporaryIdentityChild.class.getName(), owned.toString()));
        var state = new CompiledCaptureProcess.StartState();
        Path stdout = temporary.resolve("native-identity.stdout"), stderr = temporary.resolve("native-identity.stderr");
        var plan = new CompiledCaptureProcess.Plan(arguments, temporary.toString(), owned.toString(), temporary.toString(),
                stdout.toString(), stderr.toString(), temporary.resolve("unused-artifact").toString(), 1024, 1 << 20,
                15, Instant.now().plusSeconds(30).toString(), 128L << 20, List.of());
        var result = CompiledCaptureProcess.run(plan, state);
        assertTrue(state.started()); assertTrue(result.passed(), Files.readString(stderr));
        assertEquals(0, result.accounting().activeProcesses());
        assertTrue(Files.readString(stdout).contains(WindowsJobProcess.currentMachineId()));
    }
    private CompiledOriginalCaptureProfile.Profile directoryProfile(Path owned, Path input, Path output) throws IOException {
        var old = request("unit-machine").profile();
        return new CompiledOriginalCaptureProfile.Profile(old.captureReceiptRef(), old.testCompilationRef(), old.callerToolsReceiptRef(), old.producerToolsReceiptRef(),
                old.selection(), CompiledOriginalCaptureProfile.InvocationKind.JAVA_MAIN, null, List.of(
                    new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.LITERAL, "directory", null),
                    new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.EXISTING_OWNED_DIRECTORY, owned.toString(), null),
                    new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY, input.toString(), null),
                    new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.OUTPUT, output.toString(), null)), List.of(
                    new CompiledOriginalCaptureProfile.DirectoryArgument(CompiledOriginalCaptureProfile.ArgumentKind.EXISTING_OWNED_DIRECTORY, owned.toString(), CompiledOriginalCaptureProfile.DirectoryPreparation.CREATE_EMPTY, null),
                    new CompiledOriginalCaptureProfile.DirectoryArgument(CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY, input.toString(), CompiledOriginalCaptureProfile.DirectoryPreparation.EXISTING,
                        CompiledOriginalCaptureProfile.DirectoryManifest.measure(input, 65536))), List.of(), null);
    }
    private CompiledOriginalCapture.Request directoryRequest(CompiledOriginalCaptureProfile.Profile profile, Path output) {
        var old = request("unit-machine");
        return new CompiledOriginalCapture.Request(CompiledOriginalCapture.REQUEST_SCHEMA, "directory-fixture", old.machineId(), old.cwd(), profile,
                old.sourceRefs(), old.inputRefs(), output.toString(), CompiledOriginalCapture.OutputKind.DIRECTORY, 4L << 20, 8L << 20, List.of());
    }
    @Test void javaMainAndDirectoryInventoriesHaveOneStrictVersionedWireContract() throws Exception {
        Path input = temporary.resolve("input"); Files.createDirectory(input); Files.writeString(input.resolve("input.txt"), "original");
        var request = directoryRequest(directoryProfile(temporary.resolve("owned"), input, temporary.resolve("output")), temporary.resolve("output"));
        var mapper = ControlBuild.strictMapper(); byte[] raw = mapper.writeValueAsBytes(request);
        assertEquals(request, CompiledOriginalCapture.parseRequest(raw));
        var missing = (ObjectNode) mapper.valueToTree(request); missing.remove("output_kind");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(missing)));
        var old = (ObjectNode) mapper.valueToTree(request); old.put("schema", "xar.compiled-original-capture-request/v1");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(old)));
        var bad = (ObjectNode) mapper.valueToTree(request); ((ObjectNode) bad.path("profile")).remove("directories");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(bad)));
        var identity = (ObjectNode) mapper.valueToTree(request);
        ((ObjectNode) identity.path("profile").path("directories").get(1).path("input_manifest").path("identity")).put("file_id_decimal", true);
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(identity)));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.DirectoryArgument(CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY,
                input.toString(), CompiledOriginalCaptureProfile.DirectoryPreparation.CREATE_EMPTY, request.profile().directories().getLast().inputManifest()));
        assertThrows(IllegalArgumentException.class, () -> new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.INPUT_DIRECTORY, input.toString(), ref(input)));
    }
    @Test void actualDirectoryPreparationOriginalJavaMainAndOutputConsumerCloseTheLoop() throws Exception {
        Fixture fixture = fixture(); Path input = temporary.resolve("input"); Files.createDirectory(input); Files.writeString(input.resolve("input.txt"), "original bytes");
        Path owned = temporary.resolve("owned"), output = temporary.resolve("output"); var request = directoryRequest(directoryProfile(owned, input, output), output);
        var initial = new ArrayList<ControlBuild.FileRef>(); CompiledOriginalCapture.prepareDirectories(request, temporary, initial);
        assertEquals(1, initial.size()); assertTrue(Files.isDirectory(owned));
        try (var loader = new URLClassLoader(new java.net.URL[] {fixture.root().toUri().toURL()}, getClass().getClassLoader())) {
            OriginalCaptureInvoker.invoke(Class.forName("fixture.CaptureFixture", false, loader), fixture.root().toString(),
                    request.profile().invocation(), request.profile().arguments().stream().map(CompiledOriginalCaptureProfile.Argument::value).toArray(String[]::new), output);
        }
        var manifest = CompiledOriginalCapture.writeDirectoryManifest(temporary.resolve("directory.json"), output, request.maxOutputBytes());
        CompiledOriginalCapture.requireOutput(request, null, manifest);
        Path metadata = temporary.resolve("cli-directory.json");
        String[] arguments = {"directory-manifest", output.toString(), metadata.toString(), "65536", temporary.toString()};
        CompiledOriginalCapture.main(arguments);
        assertTrue(CompiledOriginalCapture.readDirectoryManifest(manifest).sameInventory(CompiledOriginalCapture.readDirectoryManifest(ControlBuild.FileRef.measure(metadata))));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.main(arguments));
        CompiledOriginalCapture.readDirectoryManifest(initial.getFirst()).verifyRetained();
        assertEquals("original bytes", Files.readString(output.resolve("result.txt")));
        Files.createDirectory(output.resolve("extra-empty-directory"));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.requireOutput(request, null, manifest));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.prepareDirectories(request, temporary, new ArrayList<>()));
    }
    @Test void immutableDirectoryAndOwnedRetentionRejectChangesAndNativeReplacement() throws Exception {
        Path input = temporary.resolve("input"); Files.createDirectory(input); Files.createDirectory(input.resolve("empty")); Files.writeString(input.resolve("input.txt"), "same bytes");
        var initial = CompiledOriginalCaptureProfile.DirectoryManifest.measure(input, 65536); initial.verify();
        Files.writeString(input.resolve("new.txt"), "new owned output"); initial.verifyRetained(); assertThrows(IOException.class, initial::verify);
        Files.move(input.resolve("input.txt"), input.resolve("previous.txt")); Files.writeString(input.resolve("input.txt"), "same bytes");
        assertThrows(IOException.class, initial::verifyRetained);
        Path outside = temporary.resolveSibling("outside-owned"); var output = temporary.resolve("output");
        var request = directoryRequest(directoryProfile(outside, input, output), output);
        assertThrows(IOException.class, () -> CompiledOriginalCapture.prepareDirectories(request, temporary, new ArrayList<>()));
        assertFalse(Files.exists(outside));
    }
    @Test void actualManagedDirectoryOutputOverflowKeepsFailureAndJobZero() throws Exception {
        Fixture fixture = fixture(); Path owned = temporary.resolve("owned"), input = temporary.resolve("input"), output = temporary.resolve("output");
        Files.createDirectory(owned); Files.createDirectory(input); Files.writeString(input.resolve("input.txt"), "larger than one byte");
        var command = new ArrayList<String>(List.of(Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toString(), "-Xms8m", "-Xmx32m", "-XX:+UseSerialGC"));
        command.addAll(CompiledOriginalCapture.childTemporaryArguments(owned)); command.addAll(List.of("-cp", fixture.root().toString(), "fixture.CaptureFixture", "directory", owned.toString(), input.toString(), output.toString()));
        var state = new CompiledCaptureProcess.StartState();
        var plan = new CompiledCaptureProcess.Plan(command, temporary.toString(), owned.toString(), temporary.toString(), temporary.resolve("out.log").toString(), temporary.resolve("err.log").toString(),
                output.toString(), 1, 1 << 20, 15, Instant.now().plusSeconds(30).toString(), 128L << 20, List.of());
        var result = CompiledCaptureProcess.run(plan, state);
        assertTrue(state.started()); assertFalse(result.passed()); assertEquals(0, result.accounting().activeProcesses()); assertTrue(result.stopReason() != null);
        assertTrue(Files.isRegularFile(output.resolve("result.txt")));
    }
    public static final class TemporaryIdentityChild {
        private TemporaryIdentityChild() { }
        public static void main(String[] args) throws Exception {
            Path expected = Path.of(args[0]).toRealPath();
            for (String key : List.of("java.io.tmpdir", "jna.tmpdir"))
                if (!Path.of(System.getProperty(key)).toRealPath().equals(expected)) throw new IllegalStateException("Wrong owned temporary property");
            System.out.println(WindowsJobProcess.currentMachineId());
        }
    }
}
