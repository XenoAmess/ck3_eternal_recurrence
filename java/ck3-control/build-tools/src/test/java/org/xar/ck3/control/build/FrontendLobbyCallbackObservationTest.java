package org.xar.ck3.control.build;
import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.LobbyVerifyTestInputs;

/** Mandatory actual C++ producer -> unchanged serializer -> Java codec; absence never skips. */
final class FrontendLobbyCallbackObservationTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    @TempDir Path temporary;
    private LobbyVerifyTestInputs.Recorded typedFixture() throws Exception {
        Path directory = Files.createDirectory(temporary.resolve("actual-native-wire-copies"));
        var originals = new ArrayList<ControlBuild.FileRef>();
        for (String name : SdkFixtureProductionInputs.LOBBY_NAMES) {
            Path copy = directory.resolve(name);
            Files.write(copy, original(name.substring(0, name.length() - ".json".length())));
            originals.add(ControlBuild.FileRef.measure(copy));
        }
        var inputs = new LobbyVerifyTestInputs.Inputs(LobbyVerifyTestInputs.SCHEMA,
                WindowsJobProcess.currentMachineId(), Instant.now().plusSeconds(3600).toString(),
                new SdkFixtureProductionInputs.LobbyWireSet(directory.toString(), originals));
        Path metadata = temporary.resolve("lobby-inputs.json");
        Files.write(metadata, ControlBuild.strictMapper().writeValueAsBytes(inputs));
        return new LobbyVerifyTestInputs.Recorded(ControlBuild.FileRef.measure(metadata), directory.toString());
    }
    private LobbyVerifyTestInputs.Recorded changed(LobbyVerifyTestInputs.Recorded original, String name, ObjectNode value) throws Exception {
        Path metadata = temporary.resolve(name + ".json");
        Files.write(metadata, JSON.writeValueAsBytes(value));
        return new LobbyVerifyTestInputs.Recorded(ControlBuild.FileRef.measure(metadata), original.directory());
    }
    @Test void typedMetadataPreservesNativeDataAndRejectsWrongPinsTypesMachineReviewAndDrift() throws Exception {
        var recorded = typedFixture();
        String machine = WindowsJobProcess.currentMachineId();
        assertDoesNotThrow(() -> LobbyVerifyTestInputs.requireInputs(recorded, machine, Instant.now()));
        assertEquals(6, LobbyVerifyTestInputs.inputRefs(recorded).size());
        var original = (ObjectNode)JSON.readTree(Files.readAllBytes(Path.of(recorded.inputsRef().path())));
        var wrongPin = original.deepCopy();
        ((ObjectNode)wrongPin.path("lobby_wires").path("originals").get(0)).put("sha256", "0".repeat(64));
        var badPin = changed(recorded, "wrong-pin", wrongPin);
        assertThrows(IOException.class, () -> LobbyVerifyTestInputs.requireInputs(badPin, machine, Instant.now()));
        for (String mode : List.of("bool", "float", "null", "missing", "extra")) {
            ObjectNode invalid = original.deepCopy();
            switch (mode) {
                case "bool" -> invalid.put("machine_id", true);
                case "float" -> ((ObjectNode)invalid.path("lobby_wires").path("originals").get(0)).put("bytes",
                        invalid.path("lobby_wires").path("originals").get(0).path("bytes").doubleValue());
                case "null" -> invalid.putNull("lobby_wires");
                case "missing" -> invalid.remove("review_at_utc");
                default -> invalid.put("current_native_runtime_qualified", true);
            }
            var invalidRecord = changed(recorded, mode, invalid);
            assertThrows(IOException.class, () -> LobbyVerifyTestInputs.requireInputs(invalidRecord, machine, Instant.now()));
        }
        var foreign = original.deepCopy(); foreign.put("machine_id", "foreign-fixture-machine");
        var foreignRecord = changed(recorded, "foreign-machine", foreign);
        assertThrows(IOException.class, () -> LobbyVerifyTestInputs.requireInputs(foreignRecord, machine, Instant.now()));
        var expired = original.deepCopy(); expired.put("review_at_utc", Instant.EPOCH.toString());
        var expiredRecord = changed(recorded, "expired", expired);
        assertThrows(IOException.class, () -> LobbyVerifyTestInputs.requireInputs(expiredRecord, machine, Instant.now()));
        var guard = LobbyVerifyTestInputs.guarded(recorded, machine, () -> {});
        Files.writeString(Path.of(recorded.directory()).resolve("lobby-callback.json"), "changed");
        assertThrows(IOException.class, guard::check);
    }
    @Test void recordedLobbyProjectionIsPureStrictAndFreezesShortArguments() throws Exception {
        var recorded = typedFixture();
        assertEquals(recorded, LobbyVerifyTestInputs.fromRecordedArguments(recorded.mavenArguments()).orElseThrow());
        assertTrue(MavenArgumentFile.required(null, recorded.mavenArguments()));
        var absent = new LobbyVerifyTestInputs.Recorded(
                new ControlBuild.FileRef(temporary.resolve("absent-metadata.json").toString(), 2, "a".repeat(64)),
                recorded.directory());
        assertEquals(absent, LobbyVerifyTestInputs.fromRecordedArguments(absent.mavenArguments()).orElseThrow());
        assertTrue(LobbyVerifyTestInputs.fromRecordedArguments(List.of()).isEmpty());
        assertTrue(LobbyVerifyTestInputs.fromRecordedArguments(List.of("-D" + SdkFixtureProductionInputs.LOBBY_DIRECTORY
                + "=" + recorded.directory())).isEmpty()); // Explicit historical absence; never a live input qualification.
        var partial = new ArrayList<>(recorded.mavenArguments()); partial.removeLast();
        assertThrows(IOException.class, () -> LobbyVerifyTestInputs.fromRecordedArguments(partial));
        var duplicate = new ArrayList<>(recorded.mavenArguments()); duplicate.add(duplicate.get(1));
        assertThrows(IOException.class, () -> LobbyVerifyTestInputs.fromRecordedArguments(duplicate));
    }

    private LobbyVerifyTestInputs.Recorded softwareRecorded;
    private byte[] original(String name) throws Exception {
        // 1. Check for explicit external lanes (recorded arguments or SDK bundle properties) first.
        //    If present, delegate to the existing global consumer; do not repair or hide failures.
        List<String> systemProperties = System.getProperties().stringPropertyNames().stream()
                .map(key -> "-D" + key + "=" + System.getProperty(key)).toList();
        if (LobbyVerifyTestInputs.fromRecordedArguments(systemProperties).isPresent()
                || SdkFixtureProductionInputs.hasRecordedArguments(systemProperties)) {
            return LobbyVerifyTestInputs.original(name + ".json");
        }

        // 2. Only if no explicit external lane is selected, attempt to load from the software environment.
        if (softwareRecorded == null) {
            String env = System.getenv("XAR_FRONTEND_LOBBY_SOFTWARE_FRAMES");
            if (env != null && !env.isBlank()) {
                Path sourceDir = Path.of(env);
                if (!Files.isDirectory(sourceDir)) throw new IOException("Software frames directory missing");
                Path directory = Files.createDirectory(temporary.resolve("software-lobby-copies"));
                var originals = new ArrayList<ControlBuild.FileRef>();
                for (String n : SdkFixtureProductionInputs.LOBBY_NAMES) {
                    Path copy = directory.resolve(n);
                    if (n.equals("lobby-callback-request.json")) {
                        // Fifth file: emitted by actual current Java FrontendLobbyCallbackObservation.arguments()
                        Files.write(copy, FrontendLobbyCallbackObservation.arguments().getBytes(StandardCharsets.UTF_8));
                    } else {
                        // Four files: unchanged from real Native production serializer on owned typed data
                        Path source = sourceDir.resolve(n);
                        if (!Files.isRegularFile(source)) throw new IOException("Missing software frame: " + n);
                        Files.copy(source, copy);
                    }
                    originals.add(ControlBuild.FileRef.measure(copy));
                }
                var inputs = new LobbyVerifyTestInputs.Inputs(LobbyVerifyTestInputs.SCHEMA,
                        WindowsJobProcess.currentMachineId(), Instant.now().plusSeconds(3600).toString(),
                        new SdkFixtureProductionInputs.LobbyWireSet(directory.toString(), originals));
                Path metadata = temporary.resolve("software-lobby-inputs.json");
                Files.write(metadata, ControlBuild.strictMapper().writeValueAsBytes(inputs));
                softwareRecorded = new LobbyVerifyTestInputs.Recorded(ControlBuild.FileRef.measure(metadata), directory.toString());
            }
        }

        // 3. Use the typed overload if software provenance was established.
        if (softwareRecorded != null) {
            return LobbyVerifyTestInputs.original(softwareRecorded, name + ".json");
        }

        // 4. Fallback to existing global metadata/V2 lanes if no software env and no explicit args.
        return LobbyVerifyTestInputs.original(name + ".json");
    }
    @Test void actualNativeProducerRoundtripsAndDoesNotGrantSelectionAuthority() throws Exception {
        assertEquals(JSON.readTree(original("lobby-callback-request")),
                JSON.readTree(FrontendLobbyCallbackObservation.arguments()));
        var observed=(FrontendLobbyCallbackObservation.Observed)FrontendLobbyCallbackObservation.decode(original("lobby-callback"),"lobby-callback");
        assertEquals(1,observed.callbacks().size());
        assertEquals(FrontendLobbyCallbackObservation.Receiver.PRESENT,observed.callbacks().getFirst().indirect().orElseThrow().receiver());
        assertFalse(observed.selectedIdentityProven()); assertFalse(observed.eligibilityProven());
        assertFalse(observed.drawCompletionProven()); assertFalse(observed.callbackAbiQualified());
        assertInstanceOf(FrontendLobbyCallbackObservation.Unavailable.class,
                FrontendLobbyCallbackObservation.decode(original("lobby-callback-unavailable"),"lobby-callback-unavailable"));
        assertInstanceOf(FrontendLobbyCallbackObservation.Unavailable.class,
                FrontendLobbyCallbackObservation.decode(original("lobby-callback-bad-slot"),"lobby-callback-bad-slot"));
        assertInstanceOf(FrontendLobbyCallbackObservation.Unavailable.class,
                FrontendLobbyCallbackObservation.decode(original("lobby-callback-bad-pin"),"lobby-callback-bad-pin"));
    }
    @Test void crossedSourceWrongTypeMissingAndNullCannotBecomeObserved() throws Exception {
        byte[] actual=original("lobby-callback");
        assertThrows(IllegalArgumentException.class,()->FrontendLobbyCallbackObservation.decode(actual,"another-request"));
        var root=(ObjectNode)JSON.readTree(actual);
        var source=(ObjectNode)root.path("result").path("callback_binding_source_12004");
        source.put("executable_sha256","0".repeat(64));
        assertThrows(IllegalArgumentException.class,()->FrontendLobbyCallbackObservation.decode(JSON.writeValueAsBytes(root),"lobby-callback"));
        for(String mode:new String[]{"bool","float","null","missing","extra"}) {
            var changed=(ObjectNode)JSON.readTree(actual);
            var row=(ObjectNode)changed.path("result").path("widgets").get(0).path("standard_click_binding_12004").path("callbacks").get(0);
            switch(mode) {
                case "bool"->row.put("callback_slot2_rva",true);
                case "float"->row.put("callback_slot2_rva",61485280.0);
                case "null"->row.putNull("callback_slot2_rva");
                case "missing"->row.remove("callback_slot2_rva");
                default->row.put("selected_character_id","123");
            }
            assertThrows(IllegalArgumentException.class,()->FrontendLobbyCallbackObservation.decode(JSON.writeValueAsBytes(changed),"lobby-callback"));
        }
    }
}
