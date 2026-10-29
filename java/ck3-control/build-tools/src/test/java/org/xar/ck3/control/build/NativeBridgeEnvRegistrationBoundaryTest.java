package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Request/codec regression only. No accepted ENV, native process or helper runtime is fabricated. */
final class NativeBridgeEnvRegistrationBoundaryTest {
    @TempDir Path temporary;

    @Test void currentEnvContractDoesNotRequireAnUnrelatedPythonInstallation() throws IOException {
        assertEquals("xar.native-bridge-build-request/v2", NativeBridgeBuild.REQUEST_SCHEMA);
        var request = request(NativeBridgeBuild.Stage.ENV, null);
        assertNull(request.defender());
        assertNull(request.environmentActual());
        assertNull(request.buildActual());
        assertFalse(Files.exists(temporary.resolve("python-base")));
        assertFalse(Files.exists(temporary.resolve("venv")));
    }

    @Test void buildDefersRegistrationWhileRetainingItsCausalEnvReference() throws IOException {
        var request = request(NativeBridgeBuild.Stage.BUILD, null);
        assertNull(request.defender());
        assertEquals(pin("env-reference.json", "unqualified codec input"), request.environmentActual());
        assertNull(request.buildActual());
    }

    @Test void registrationStillRequiresAnExplicitHelperRuntime() throws IOException {
        assertThrows(IllegalArgumentException.class, () -> request(NativeBridgeBuild.Stage.REGISTER, null));
        var runtime = helperCodecFixture();
        var request = request(NativeBridgeBuild.Stage.REGISTER, runtime);
        assertEquals(runtime, request.defender());
        var encoded = pin("register-request.json", RootNativePlanJson.mapper().writeValueAsString(request));
        assertThrows(IOException.class, () -> NativeBridgeBuild.readAccepted(encoded, NativeBridgeBuild.Stage.REGISTER));
    }

    @Test void currentEnvAndBuildRejectUnrelatedRegistrationPayloads() throws IOException {
        var runtime = helperCodecFixture();
        assertThrows(IllegalArgumentException.class, () -> request(NativeBridgeBuild.Stage.ENV, runtime));
        assertThrows(IllegalArgumentException.class, () -> request(NativeBridgeBuild.Stage.BUILD, runtime));
    }

    @Test void actualRequestWriterReaderKeepsTheExplicitNullBranch() throws IOException {
        var request = request(NativeBridgeBuild.Stage.ENV, null);
        var mapper = RootNativePlanJson.mapper();
        String encoded = mapper.writeValueAsString(request);
        var tree = mapper.readTree(encoded);
        assertTrue(tree.has("defender"));
        assertTrue(tree.get("defender").isNull());
        var original = pin("env-request.json", encoded);
        assertEquals(request, NativeBridgeBuild.readRequest(original));
        assertThrows(IOException.class, () -> NativeBridgeBuild.readAccepted(original, NativeBridgeBuild.Stage.ENV));
    }

    @Test void missingNullableCreatorOrWrongBranchTypeIsStillRejected() throws IOException {
        var request = request(NativeBridgeBuild.Stage.ENV, null);
        var mapper = RootNativePlanJson.mapper();
        ObjectNode tree = mapper.valueToTree(request);
        ObjectNode missing = tree.deepCopy();
        missing.remove("defender");
        var absent = pin("missing-defender.json", mapper.writeValueAsString(missing));
        assertThrows(IOException.class, () -> NativeBridgeBuild.readRequest(absent));
        ObjectNode wrong = tree.deepCopy();
        wrong.put("defender", true);
        var invalid = pin("wrong-defender.json", mapper.writeValueAsString(wrong));
        assertThrows(IOException.class, () -> NativeBridgeBuild.readRequest(invalid));
    }

    @Test void theRealSameBuildPredicateAcceptsTheV2StageChain() throws IOException {
        var env = request(NativeBridgeBuild.Stage.ENV, null);
        var build = request(NativeBridgeBuild.Stage.BUILD, null);
        var registration = request(NativeBridgeBuild.Stage.REGISTER, helperCodecFixture());
        assertTrue(NativeBridgeBuild.sameBuild(env, build));
        assertTrue(NativeBridgeBuild.sameBuild(registration, env));
        assertTrue(NativeBridgeBuild.sameBuild(registration, build));
        var originalHelper = org.junit.jupiter.api.Assertions.assertInstanceOf(
                NativeBridgeDefender.HelperRuntime.class, registration.defender());
        var otherHelper = new NativeBridgeDefender.HelperRuntime(temporary.resolve("different-register-base"),
                temporary.resolve("different-register-venv"), originalHelper.python(), originalHelper.helper(),
                originalHelper.completePythonFiles(), originalHelper.completeHelperSources());
        assertFalse(NativeBridgeBuild.sameBuild(registration, request(NativeBridgeBuild.Stage.REGISTER, otherHelper)));
        var different = new NativeBridgeBuild.Request(build.schema(), build.machineId(), build.stage(),
                build.canonicalRepository(), build.sourceRoot(), build.completeSources(), build.buildRoot(),
                build.scratchRoot(), build.qualifiedToolsBuild(), build.tools(), build.definitions(), 1,
                build.environmentActual(), build.buildActual(), null);
        assertFalse(NativeBridgeBuild.sameBuild(env, different));
    }

    @Test void historicalV1KeepsItsExactHelperAndCannotMixWithV2() throws IOException {
        var runtime = helperCodecFixture();
        var legacy = request(NativeBridgeBuild.LEGACY_REQUEST_SCHEMA, NativeBridgeBuild.Stage.ENV, runtime);
        var oldBuild = request(NativeBridgeBuild.LEGACY_REQUEST_SCHEMA, NativeBridgeBuild.Stage.BUILD, runtime);
        var encoded = pin("historical-v1.json", RootNativePlanJson.mapper().writeValueAsString(legacy));
        assertEquals(legacy, NativeBridgeBuild.readRequest(encoded));
        assertTrue(NativeBridgeBuild.sameBuild(legacy, oldBuild));
        assertFalse(NativeBridgeBuild.sameBuild(legacy, request(NativeBridgeBuild.Stage.ENV, null)));
        var otherRuntime = new NativeBridgeDefender.HelperRuntime(temporary.resolve("another-base"),
                temporary.resolve("another-venv"), runtime.python(), runtime.helper(),
                runtime.completePythonFiles(), runtime.completeHelperSources());
        var other = request(NativeBridgeBuild.LEGACY_REQUEST_SCHEMA, NativeBridgeBuild.Stage.BUILD, otherRuntime);
        assertFalse(NativeBridgeBuild.sameBuild(legacy, other));
    }

    @Test void historicalProtocolIsRejectedBeforeARequestWriteOrLiveRootLock() throws IOException {
        var legacy = request(NativeBridgeBuild.LEGACY_REQUEST_SCHEMA, NativeBridgeBuild.Stage.ENV, helperCodecFixture());
        var expected = assertThrows(IOException.class, () -> NativeBridgeBuild.requireCurrentRequest(legacy));
        var oldPin = pin("legacy-for-live-rejection.json", RootNativePlanJson.mapper().writeValueAsString(legacy));
        Path output = temporary.resolve("must-not-be-created.json");
        var writer = assertThrows(IOException.class, () -> NativeBridgeBuild.writeRequest(legacy, temporary, output));
        assertEquals(expected.getMessage(), writer.getMessage());
        assertFalse(Files.exists(output));
        var direct = assertThrows(IOException.class, () -> NativeBridgeBuild.execute(oldPin, null));
        assertEquals(expected.getMessage(), direct.getMessage());
        var limits = new NativeBridgeRootGate.Limits("/root", pin("capacity-not-consumed.json", "{}"),
                Instant.now().plusSeconds(30), 64L << 20, 32L << 20, 20);
        var live = assertThrows(IOException.class, () -> NativeBridgeRootGate.open(oldPin, limits));
        assertEquals(expected.getMessage(), live.getMessage());
        assertFalse(Files.exists(legacy.scratchRoot().resolve("ROOT-NATIVE-BUILD.lock")));
        assertFalse(Files.exists(legacy.stageRoot()));
    }


    @Test void explicitBoundRequestRoundTripsAndNeverSynthesizesItsRequiredBinding() throws IOException {
        var request = boundRequest(NativeBridgeBuild.Stage.ENV, pin("binding.json", "unqualified codec fixture"));
        var mapper = RootNativePlanJson.mapper();
        assertEquals(request, NativeBridgeBuild.readRequest(pin("bound-env.json", mapper.writeValueAsString(request))));
        for (String name : List.of("absent", "null", "boolean")) {
            ObjectNode tree = mapper.valueToTree(request);
            if (name.equals("absent")) tree.remove("compile_source_binding_ref");
            else if (name.equals("null")) tree.putNull("compile_source_binding_ref");
            else tree.put("compile_source_binding_ref", true);
            var ref = pin("bound-" + name + ".json", mapper.writeValueAsString(tree));
            assertThrows(IOException.class, () -> NativeBridgeBuild.readRequest(ref));
        }
        ObjectNode unknown = mapper.valueToTree(request); unknown.put("schema", "xar.native-bridge-build-request/v5");
        assertThrows(IOException.class, () -> NativeBridgeBuild.readRequest(pin("unknown-bound.json", mapper.writeValueAsString(unknown))));
    }

    @Test void oldTagCompatibilityAddsOnlyTheNewAbsentFieldAndRejectsAnAcquiredBinding() throws IOException {
        var request = request(NativeBridgeBuild.Stage.ENV, null);
        var mapper = RootNativePlanJson.mapper(); ObjectNode old = mapper.valueToTree(request);
        old.remove("compile_source_binding_ref");
        assertEquals(request, NativeBridgeBuild.readRequest(pin("old-without-binding.json", mapper.writeValueAsString(old))));
        ObjectNode acquired = mapper.valueToTree(request);
        acquired.set("compile_source_binding_ref", mapper.valueToTree(pin("foreign-binding.json", "{}")));
        assertThrows(IOException.class, () -> NativeBridgeBuild.readRequest(pin("old-acquired-binding.json", mapper.writeValueAsString(acquired))));
        old.remove("defender");
        assertThrows(IOException.class, () -> NativeBridgeBuild.readRequest(pin("old-missing-real-field.json", mapper.writeValueAsString(old))));
    }

    @Test void boundSameBuildRequiresTheSameExplicitBindingAcrossAllStages() throws IOException {
        var binding = pin("same-binding.json", "unqualified codec fixture");
        var env = boundRequest(NativeBridgeBuild.Stage.ENV, binding);
        var build = boundRequest(NativeBridgeBuild.Stage.BUILD, binding);
        var registration = boundRequest(NativeBridgeBuild.Stage.REGISTER, binding);
        assertTrue(NativeBridgeBuild.sameBuild(env, build));
        assertTrue(NativeBridgeBuild.sameBuild(env, registration));
        assertTrue(NativeBridgeBuild.sameBuild(build, registration));
        assertFalse(NativeBridgeBuild.sameBuild(env, boundRequest(NativeBridgeBuild.Stage.BUILD, pin("other-binding.json", "{}"))));
        assertFalse(NativeBridgeBuild.sameBuild(env, request(NativeBridgeBuild.Stage.ENV, null)));
    }

    @Test void boundShapeAndDirectRuntimeDoNotQualifyAnInventedSourceBinding() throws IOException {
        var request = boundRequest(NativeBridgeBuild.Stage.ENV, pin("unqualified-binding.json", "{}"));
        NativeBridgeBuild.requireCurrentRequest(request);
        assertThrows(IOException.class, () -> NativeBridgeBuild.validateSources(request));
        Path output = temporary.resolve("unqualified-bound-output.json");
        assertThrows(IOException.class, () -> NativeBridgeBuild.writeRequest(request, temporary, output));
        assertFalse(Files.exists(output));
        var base = request(NativeBridgeBuild.Stage.ENV, null);
        assertThrows(NullPointerException.class, () -> new NativeBridgeBuild.Request(NativeBridgeBuild.BOUND_REQUEST_SCHEMA,
                base.machineId(), base.stage(), base.canonicalRepository(), base.sourceRoot(), base.completeSources(),
                base.buildRoot(), base.scratchRoot(), base.qualifiedToolsBuild(), base.tools(), base.definitions(), base.parallelJobs(),
                null, null, (NativeBridgeDefender.Runtime) null, null));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.Request(NativeBridgeBuild.BOUND_REQUEST_SCHEMA,
                base.machineId(), NativeBridgeBuild.Stage.REGISTER, base.canonicalRepository(), base.sourceRoot(), base.completeSources(),
                base.buildRoot(), base.scratchRoot(), base.qualifiedToolsBuild(), base.tools(), base.definitions(), base.parallelJobs(),
                pin("env-reference.json", "unqualified codec input"), pin("build-reference.json", "unqualified codec input"),
                helperCodecFixture(), request.compileSourceBindingRef()));
    }

    @Test void directBaseProductionArgvMatchesTheObservedIsolatedHelperRoute() throws IOException {
        var request = boundRequest(NativeBridgeBuild.Stage.REGISTER, pin("argv-binding.json", "{}"));
        var manifest = new ControlBuild.FileRef(request.stageRoot().resolve("manifest.json").toString(), 2, "0".repeat(64));
        var command = NativeBridgeDefender.command(request, manifest, request.stageRoot().resolve("helper-receipt.json"));
        assertEquals(request.defender().python().path(), command.getFirst());
        assertEquals(List.of("-E", "-s", "-B", "-X", "utf8"), command.subList(1, 6));
        assertEquals(request.defender().helper().path(), command.get(6));
        var old = request(NativeBridgeBuild.Stage.REGISTER, helperCodecFixture());
        var oldManifest = new ControlBuild.FileRef(old.stageRoot().resolve("manifest.json").toString(), 2, "0".repeat(64));
        assertEquals("-B", NativeBridgeDefender.command(old, oldManifest, old.stageRoot().resolve("helper-receipt.json")).get(1));
    }


    @Test void nativeProducerMainDispatchesTheTypedOriginalStageBeforeAnyRootClaim() throws Exception {
        var base = boundRequest(NativeBridgeBuild.Stage.ENV, pin("cli-bound-source.json", "{}"));
        var request = new NativeBridgeBuild.Request(base.schema(), WindowsJobProcess.currentMachineId(), base.stage(),
                base.canonicalRepository(), base.sourceRoot(), base.completeSources(), base.buildRoot(), base.scratchRoot(),
                base.qualifiedToolsBuild(), base.tools(), base.definitions(), base.parallelJobs(), null, null,
                (NativeBridgeDefender.Runtime)null, base.compileSourceBindingRef());
        var mapper = RootNativePlanJson.mapper();
        var requestPin = pin("native-main-request.json", mapper.writeValueAsString(request));
        var limits = new NativeBridgeRootGate.Limits("/root/native_execution", pin("native-main-capacity.json", "{}"),
                Instant.now().plusSeconds(60), 64L << 20, 32L << 20, 20);
        var spec = new NativeProjectExeUac.CurrentNativeStageSpec("xar.native-bridge-stage-command/v1",
                request.machineId(), request.stage(), pin("unqualified-retained-source.json", "{}"), requestPin, limits);
        var specPin = pin("native-main-stage-spec.json", mapper.writeValueAsString(spec));
        var direct = assertThrows(IOException.class, () -> NativeBridgeBuild.executeStage(spec));
        var cli = assertThrows(IOException.class, () -> NativeBridgeBuild.main(new String[]{"execute", specPin.path(),
                Long.toString(specPin.bytes()), specPin.sha256()}));
        assertEquals(direct.getMessage(), cli.getMessage());
        assertFalse(Files.exists(request.stageRoot()));
        assertFalse(Files.exists(request.scratchRoot().resolve("ROOT-NATIVE-BUILD.lock")));
        assertThrows(IOException.class, () -> NativeBridgeBuild.main(new String[]{"arbitrary-command", specPin.path(),
                Long.toString(specPin.bytes()), specPin.sha256()}));
    }

    @Test void causalPublicWriterKeepsExplicitBuildRegisterBranchesAndCannotInventAnEnvActual() throws Exception {
        var metadata = pin("no-env-actual.json", "{}");
        var input = new NativeBridgeBuild.CausalInput("xar.native-bridge-causal-request-input/v2",
                WindowsJobProcess.currentMachineId(), NativeBridgeBuild.Stage.BUILD, metadata, metadata, null, null,
                temporary, temporary.resolve("unproduced-causal-request.json"));
        var mapper = RootNativePlanJson.mapper();
        var inputPin = pin("current-causal-input.json", mapper.writeValueAsString(input));
        assertThrows(IOException.class, () -> NativeBridgeBuild.main(new String[]{"write-request", inputPin.path(),
                Long.toString(inputPin.bytes()), inputPin.sha256()}));
        assertFalse(Files.exists(input.requestOutput()));
        ObjectNode missing = mapper.valueToTree(input); missing.remove("runtime_inventory_ref");
        assertThrows(IOException.class, () -> mapper.treeToValue(missing, NativeBridgeBuild.CausalInput.class));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.CausalInput(input.schema(), input.machineId(),
                NativeBridgeBuild.Stage.REGISTER, metadata, metadata, null, null, temporary, input.requestOutput()));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.CausalInput("xar.native-bridge-causal-request-input/v1",
                input.machineId(), input.stage(), metadata, metadata, null, null, temporary, input.requestOutput()));
    }

    private NativeBridgeBuild.Request boundRequest(NativeBridgeBuild.Stage stage, ControlBuild.FileRef binding) throws IOException {
        var base = request(stage == NativeBridgeBuild.Stage.REGISTER ? NativeBridgeBuild.Stage.BUILD : stage, null);
        NativeBridgeDefender.Runtime runtime = null;
        if (stage == NativeBridgeBuild.Stage.REGISTER) {
            Path pythonBase = temporary.resolve("bound-python-base");
            Files.createDirectories(pythonBase);
            Path python = pythonBase.resolve("python.exe"); Files.writeString(python, "unqualified codec input");
            runtime = new NativeBridgeDefender.ManifestRuntime(NativeBridgeDefender.ManifestRuntime.DIRECT_SCHEMA,
                    pythonBase, temporary.resolve("bound-venv"), ControlBuild.FileRef.measure(python),
                    pin("bound-helper.py", "unqualified codec input"), pin("bound-runtime-inventory.json", "{}"));
        }
        return new NativeBridgeBuild.Request(NativeBridgeBuild.BOUND_REQUEST_SCHEMA, base.machineId(), stage,
                base.canonicalRepository(), base.sourceRoot(), base.completeSources(), base.buildRoot(), base.scratchRoot(),
                base.qualifiedToolsBuild(), base.tools(), base.definitions(), base.parallelJobs(),
                stage == NativeBridgeBuild.Stage.ENV ? null : pin("env-reference.json", "unqualified codec input"),
                stage == NativeBridgeBuild.Stage.REGISTER ? pin("build-reference.json", "unqualified codec input") : null,
                runtime, binding);
    }

    private NativeBridgeBuild.Request request(NativeBridgeBuild.Stage stage,
            NativeBridgeDefender.HelperRuntime runtime) throws IOException {
        return request(NativeBridgeBuild.REQUEST_SCHEMA, stage, runtime);
    }

    private NativeBridgeBuild.Request request(String schema, NativeBridgeBuild.Stage stage,
            NativeBridgeDefender.HelperRuntime runtime) throws IOException {
        Path source = temporary.resolve("source");
        Files.createDirectories(source);
        if (!Files.exists(source.resolve("CMakeLists.txt"))) {
            Files.writeString(source.resolve("CMakeLists.txt"), "option(XAR_CK3_FIXTURE \"fixture\" OFF)\n");
        }
        var tools = new ArrayList<ControlBuild.FileRef>();
        for (String name : List.of("cmd.exe", "vcvars64.bat", "java.exe", "cmake.exe", "ninja.exe", "cl.exe", "link.exe")) {
            tools.add(pin(name, "codec input only"));
        }
        ControlBuild.FileRef env = stage == NativeBridgeBuild.Stage.ENV ? null
                : pin("env-reference.json", "unqualified codec input");
        ControlBuild.FileRef build = stage == NativeBridgeBuild.Stage.REGISTER
                ? pin("build-reference.json", "unqualified codec input") : null;
        return new NativeBridgeBuild.Request(schema, "software-fixture", stage,
                temporary, source, NativeBridgeBuild.inventory(source), temporary.resolve("build"),
                temporary.resolve("scratch"), pin("tools-receipt.json", "unqualified codec input"),
                new NativeBridgeBuild.Toolchain(tools.get(0), tools.get(1), tools.get(2), tools.get(3),
                        tools.get(4), tools.get(5), tools.get(6)),
                List.of(new NativeBridgeBuild.Definition("XAR_CK3_FIXTURE", NativeBridgeBuild.SwitchValue.OFF)),
                4, env, build, runtime);
    }

    private NativeBridgeDefender.HelperRuntime helperCodecFixture() throws IOException {
        var python = pin("python.exe", "unqualified codec input");
        var helper = pin("helper.py", "unqualified codec input");
        return new NativeBridgeDefender.HelperRuntime(temporary.resolve("python-base"), temporary.resolve("venv"),
                python, helper, List.of(python), List.of(helper));
    }

    private ControlBuild.FileRef pin(String name, String text) throws IOException {
        Path file = temporary.resolve(name);
        if (!Files.exists(file)) Files.writeString(file, text);
        return ControlBuild.FileRef.measure(file);
    }
}
