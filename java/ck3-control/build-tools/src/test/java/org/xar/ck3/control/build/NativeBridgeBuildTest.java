package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Software protocol rejection only; no native process, accepted build or launch is fabricated. */
final class NativeBridgeBuildTest {
    @TempDir Path temporary;
    private ControlBuild.FileRef pin(String name, String body) throws IOException {
        Path path = temporary.resolve(name); Files.writeString(path, body); return ControlBuild.FileRef.measure(path);
    }
    private NativeBridgeBuild.Request request(NativeBridgeBuild.Stage stage,
            ControlBuild.FileRef environment, ControlBuild.FileRef build) throws IOException {
        Path source = temporary.resolve("source"); Files.createDirectories(source);
        if (!Files.exists(source.resolve("CMakeLists.txt"))) Files.writeString(source.resolve("CMakeLists.txt"), "option(XAR_CK3_EXAMPLE \"fixture\" OFF)\n");
        var toolPins = new ArrayList<ControlBuild.FileRef>();
        for (String name : List.of("cmd.exe", "vcvars64.bat", "java.exe", "cmake.exe", "ninja.exe", "cl.exe", "link.exe")) {
            Path file = temporary.resolve(name); if (!Files.exists(file)) Files.writeString(file, name); toolPins.add(ControlBuild.FileRef.measure(file));
        }
        Path helper = temporary.resolve("helper.py"), python = temporary.resolve("python.exe");
        if (!Files.exists(helper)) Files.writeString(helper, "helper fixture"); if (!Files.exists(python)) Files.writeString(python, "python fixture");
        var helperRuntime = new NativeBridgeDefender.HelperRuntime(temporary.resolve("python-base"), temporary.resolve("venv"),
                ControlBuild.FileRef.measure(python), ControlBuild.FileRef.measure(helper), List.of(ControlBuild.FileRef.measure(python)), List.of(ControlBuild.FileRef.measure(helper)));
        Path metadata = temporary.resolve("tools.json"); if (!Files.exists(metadata)) Files.writeString(metadata, "{}");
        return new NativeBridgeBuild.Request(NativeBridgeBuild.REQUEST_SCHEMA, "software-machine", stage, temporary, source,
                NativeBridgeBuild.inventory(source), temporary.resolve("build"), temporary.resolve("scratch"), ControlBuild.FileRef.measure(metadata),
                new NativeBridgeBuild.Toolchain(toolPins.get(0), toolPins.get(1), toolPins.get(2), toolPins.get(3), toolPins.get(4), toolPins.get(5), toolPins.get(6)),
                List.of(new NativeBridgeBuild.Definition("XAR_CK3_EXAMPLE", NativeBridgeBuild.SwitchValue.ON)), 2, environment, build, stage == NativeBridgeBuild.Stage.REGISTER ? helperRuntime : null);
    }
    @Test void buildCommandHasOnlyTheRealDllAndInjectorTargets() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null);
        assertEquals(List.of("xar_ck3_bridge", "xar_ck3_bridge_injector"), NativeBridgeBuild.TARGETS);
        var command = NativeBridgeBuild.buildCommand(request);
        assertEquals(List.of("--target", "xar_ck3_bridge", "xar_ck3_bridge_injector"), command.subList(command.size() - 3, command.size()));
        assertFalse(command.stream().anyMatch(word -> word.contains("kinship") || word.contains("combat_roles")));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.Definition("CMAKE_PROJECT_INCLUDE", NativeBridgeBuild.SwitchValue.ON));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.Definition("XAR_CK3_EXAMPLE;EXECUTE", NativeBridgeBuild.SwitchValue.ON));
    }
    @Test void onlySourceDeclaredBooleanOptionsAndCompleteSourceTreeAreAccepted() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null); NativeBridgeBuild.validateSources(request);
        Files.writeString(request.sourceRoot().resolve("unlisted-resource.txt"), "new native input");
        assertThrows(IOException.class, () -> NativeBridgeBuild.validateSources(request));
    }
    @Test void causalStageFieldsAndOldFixtureProtocolCannotGrantBridgeQualification() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> request(NativeBridgeBuild.Stage.BUILD, null, null));
        var old = pin("research-actual.json", "{\"schema\":\"xar.shared-native-stage-actual/v2\",\"status\":\"PASS\",\"stage_id\":\"two-target-build\"}");
        assertThrows(IOException.class, () -> NativeBridgeBuild.readAccepted(old, NativeBridgeBuild.Stage.BUILD));
    }
    @Test void strictRequestRoundTripRejectsBooleanOrFractionalSequenceAndMissingFields() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null); var mapper = ControlBuild.strictMapper();
        assertEquals(request, mapper.readValue(mapper.writeValueAsBytes(request), NativeBridgeBuild.Request.class));
        for (String invalid : List.of("true", "2.0", "\"2\"")) {
            var tree = mapper.valueToTree(request); ((com.fasterxml.jackson.databind.node.ObjectNode) tree).set("parallel_jobs", mapper.readTree(invalid));
            assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(tree), NativeBridgeBuild.Request.class));
        }
        var missing = mapper.valueToTree(request); ((com.fasterxml.jackson.databind.node.ObjectNode) missing).remove("complete_sources");
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(missing), NativeBridgeBuild.Request.class));
    }
    @Test void unknownCommandOwnerAndNonzeroJobCannotPassCommandAdmission() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null); var actualPin = pin("request-pin.json", "{}");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, actualPin, actualPin,
                Instant.now().plusSeconds(20), 64L << 20, 4096, 10);
        var command = new NativeBridgeBuild.Command(NativeBridgeBuild.CommandKind.ENV_CAPTURE, List.of(request.tools().cmd().path()),
                request.stageRoot().toString(), null, null, null, null);
        var actual = new NativeBridgeBuild.Actual(NativeBridgeBuild.ACTUAL_SCHEMA, "software-machine", NativeBridgeBuild.Stage.ENV, NativeBridgeBuild.Status.UNKNOWN,
                Instant.now().toString(), Instant.now().toString(), actualPin, grant, List.of(command), List.of(), List.of(), List.of(),
                null, null, null, List.of(), List.of(), List.of(), false, "child terminal unavailable");
        assertThrows(IOException.class, () -> NativeBridgeBuild.validateCommands(request, actual));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.Actual(NativeBridgeBuild.ACTUAL_SCHEMA, "software-machine", NativeBridgeBuild.Stage.ENV,
                NativeBridgeBuild.Status.PASS, Instant.now().toString(), Instant.now().toString(), actualPin, grant, List.of(), List.of(), List.of(), List.of(),
                null, null, null, List.of(), List.of(), List.of(), true, null));
    }

    @Test void rootLimitsRejectUnscopedOwnerAndMissingTerminalReserve() throws Exception {
        var metadata = pin("capacity-shape.json", "{}");
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeRootGate.Limits("owner", metadata,
                Instant.now().plusSeconds(30), 64L << 20, 32L << 20, 20));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeRootGate.Limits("/root", metadata,
                Instant.now().plusSeconds(30), 64L << 20, 4096, 20));
    }

    @Test void actualRootGateRejectsMalformedCapacityBeforeCreatingLockOrStage() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null);
        var requestPin = pin("root-negative-request.json", ControlBuild.strictMapper().writeValueAsString(request));
        var capacity = pin("root-malformed-capacity.json", "{}");
        var limits = new NativeBridgeRootGate.Limits("/root", capacity, Instant.now().plusSeconds(30),
                64L << 20, 32L << 20, 20);
        assertThrows(IOException.class, () -> NativeBridgeRootGate.open(requestPin, limits));
        assertFalse(Files.exists(request.scratchRoot().resolve("ROOT-NATIVE-BUILD.lock")));
        assertFalse(Files.exists(request.stageRoot()));
    }

    @Test void historicalGrantCannotBorrowAnotherOwnersPinnedCapacity() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null);
        var requestPin = pin("historical-negative-request.json", ControlBuild.strictMapper().writeValueAsString(request));
        var policy = pin("historical-policy-shape.json", "{}");
        Instant opened = Instant.now().minusSeconds(10), until = Instant.now().plusSeconds(60), at = Instant.now();
        var release = new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1", request.machineId(),
                opened.toString(), until.toString(), "RELEASED", "/root/other_owner", policy,
                List.of(request.buildRoot().toString(), request.scratchRoot().toString()), request.scratchRoot().toString(),
                java.util.Map.of("artifacts", 64L << 20),
                java.util.Map.of(request.buildRoot().getRoot().toString(), new CiBootstrap.VolumeBudget(1000, 900, 100, 0, 1, 1, 1, 1000, 102)),
                java.util.Map.of(), 128L << 20, 32L << 20);
        var capacity = pin("historical-capacity.json", ControlBuild.strictMapper().writeValueAsString(release));
        var grant = new NativeBridgeBuild.Grant(request.machineId(), "/root", request.stage(), requestPin, capacity,
                until.minusSeconds(1), 64L << 20, 32L << 20, 20);
        IOException rejected = assertThrows(IOException.class,
                () -> NativeBridgeRootGate.verifyHistorical(request, grant, at, at));
        assertTrue(rejected.getMessage().contains("owner/machine/stage/window/memory/allocation"));
        assertFalse(Files.exists(request.stageRoot()));
    }

    @Test void missingOwnerAndLegacyActualCannotEnterTheNewStrictProtocol() throws Exception {
        var ref = pin("negative-grant-ref.json", "{}");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, ref, ref,
                Instant.now().plusSeconds(30), 64L << 20, 32L << 20, 20);
        var mapper = ControlBuild.strictMapper();
        var intent = NativeBridgeBuild.writeNew(temporary.resolve("owner-negative-intent.json"), grant);
        var missing = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(intent.path())));
        missing.remove("owner_task");
        var missingPin = pin("owner-missing-intent.json", mapper.writeValueAsString(missing));
        assertThrows(IOException.class, () -> NativeBridgeBuild.readGrantEnvelope(missingPin));
        var old = pin("old-native-v1-actual.json", "{\"schema\":\"xar.native-bridge-build-actual/v1\",\"status\":\"PASS\"}");
        assertThrows(IOException.class, () -> NativeBridgeBuild.readAccepted(old, NativeBridgeBuild.Stage.ENV));
    }

    @Test void productionIntentWriterAndReaderRoundTripExactUtcNanoseconds() throws Exception {
        // This is the actual execute -> INTENT writer and readAccepted -> INTENT reader.
        // The grant is codec input only; no Root gate, stage or successful native evidence is fabricated.
        var ref = pin("intent-codec-input.json", "{}");
        Instant deadline = Instant.parse("2030-01-02T03:04:05.123456789Z");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, ref, ref,
                deadline, 64L << 20, 32L << 20, 20);
        Path output = temporary.resolve("codec-INTENT.json");
        var written = NativeBridgeBuild.writeNew(output, grant);
        var tree = ControlBuild.strictMapper().readTree(Files.readAllBytes(output));
        assertTrue(tree.get("deadline").isTextual()); assertEquals(deadline.toString(), tree.get("deadline").textValue());
        assertEquals(grant, NativeBridgeBuild.readGrantEnvelope(written));
        assertEquals(written, ControlBuild.FileRef.measure(output));
        assertThrows(IOException.class, () -> NativeBridgeBuild.writeNew(output, grant));
        assertEquals(written, ControlBuild.FileRef.measure(output));
    }

    @Test void productionActualWriterAndReaderRoundTripNestedDeadlineWithoutGrantingAcceptance() throws Exception {
        var ref = pin("actual-codec-input.json", "{}");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, ref, ref,
                Instant.parse("2030-01-02T03:04:05.000000007Z"), 64L << 20, 32L << 20, 20);
        var red = new NativeBridgeBuild.Actual(NativeBridgeBuild.ACTUAL_SCHEMA, "software-machine", NativeBridgeBuild.Stage.ENV,
                NativeBridgeBuild.Status.RED, "2026-10-23T00:00:00Z", "2026-10-23T00:00:01Z", ref, grant,
                List.of(), List.of(), List.of(), List.of(), null, null, null, List.of(), List.of(), List.of(), false,
                "Codec boundary only: no native command or successful stage exists");
        var written = NativeBridgeBuild.writeNew(temporary.resolve("codec-ACTUAL.json"), red);
        assertEquals(red, NativeBridgeBuild.readActualEnvelope(written));
        var tree = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(written.path())));
        assertTrue(tree.path("grant").get("deadline").isTextual());
        assertEquals(grant.deadline().toString(), tree.path("grant").get("deadline").textValue());
        assertThrows(IOException.class, () -> NativeBridgeBuild.readAccepted(written, NativeBridgeBuild.Stage.ENV));
    }

    @Test void productionGrantReaderRejectsWrongTemporalTypesOffsetsAndInvalidDates() throws Exception {
        var ref = pin("temporal-negative-input.json", "{}");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, ref, ref,
                Instant.parse("2030-01-02T03:04:05Z"), 64L << 20, 32L << 20, 20);
        var original = NativeBridgeBuild.writeNew(temporary.resolve("temporal-original.json"), grant);
        var mapper = ControlBuild.strictMapper();
        var tree = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(original.path())));
        int index = 0;
        for (String invalid : List.of("true", "1", "1.5", "null", "\"2030-01-02T03:04:05+00:00\"",
                "\"2030-02-30T03:04:05Z\"", "\"123456789\"")) {
            var changed = tree.deepCopy(); changed.set("deadline", mapper.readTree(invalid));
            var malformed = pin("temporal-invalid-" + index++ + ".json", mapper.writeValueAsString(changed));
            assertThrows(IOException.class, () -> NativeBridgeBuild.readGrantEnvelope(malformed));
        }
        assertEquals(grant, NativeBridgeBuild.readGrantEnvelope(original));
    }
}
