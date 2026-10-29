package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** The actual CLI dispatch keeps source kinds explicit and checks pins before any producer output. */
final class ControlCiSoftwareFixtureInputsCliTest {
    @TempDir Path temporary;

    private String[] command(String flag, ControlBuild.FileRef plan, Path output) {
        return new String[] {flag, plan.path(), Long.toString(plan.bytes()), plan.sha256(),
                "--output-root", output.toString()};
    }

    @Test void actualCliProducesBothExistingTypedHostRequestsFromOriginalFixturePlans() throws Exception {
        for (boolean host : new boolean[] {false, true}) {
            Path source = Files.createDirectory(temporary.resolve(host ? "host-originals" : "golden-originals"));
            var plan = host ? RootSoftwareFixtureInputsProducerTest.hostFixturePlanFixture(source)
                    : RootSoftwareFixtureInputsProducerTest.goldenPlanFixture(source);
            Path output = temporary.resolve(host ? "host-produced" : "golden-produced");
            String flag = host ? "--write-host-software-fixture-inputs" : "--write-software-fixture-inputs";
            PrintStream previous = System.out; ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (PrintStream captured = new PrintStream(bytes, true, StandardCharsets.UTF_8)) {
                System.setOut(captured); ControlCi.main(command(flag, plan, output));
            } finally { System.setOut(previous); }
            String line = bytes.toString(StandardCharsets.UTF_8).strip();
            String prefix = "WROTE_SOFTWARE_FIXTURE_INPUTS ";
            assertEquals(1L, line.lines().count()); assertTrue(line.startsWith(prefix), line);
            var produced = ControlBuild.strictMapper().readValue(line.substring(prefix.length()),
                    RootSoftwareFixtureInputsProducer.Produced.class);
            produced.requestRef().verify(); produced.probePayloadRef().verify(); plan.verify();
            assertEquals(output.resolve("software-fixture-inputs.json"), Path.of(produced.requestRef().path()));
            assertEquals(output.resolve("probe-payload.json"), Path.of(produced.probePayloadRef().path()));
            var request = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(produced.requestRef().path())),
                    RootSoftwareFixtureHandoff.Request.class);
            assertEquals(produced.probePayloadRef(), request.probePayloadRef());
            assertEquals(8, request.originalRequestRefs().size());
            assertTrue(request.originalRequestRefs().contains(request.probeRequestRef()));
            assertTrue(request.originalFixtureRefs().containsAll(request.originalRequestRefs()));
            for (var original : request.originalFixtureRefs()) original.verify();
        }
    }

    @Test void checkoutCliUsesActualProducerAndPersistsTheTypedHostRequest() throws Exception {
        Path source = RootSoftwareFixtureInputsProducerTest.checkoutFixture(temporary.resolve("checkout"));
        Path output = temporary.resolve("checkout-produced");
        String[] command = {"--write-checkout-software-fixture-inputs", "--java-source-root",
                source.toString(), "--output-root", output.toString()};
        var invocation = ControlCi.checkoutSoftwareFixtureInputsInvocation(command);
        assertEquals(source, invocation.javaSourceRoot()); assertEquals(output, invocation.outputRoot());
        PrintStream previous = System.out; ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (PrintStream captured = new PrintStream(bytes, true, StandardCharsets.UTF_8)) {
            System.setOut(captured); ControlCi.main(command);
        } finally { System.setOut(previous); }
        String line = bytes.toString(StandardCharsets.UTF_8).strip(), prefix = "WROTE_SOFTWARE_FIXTURE_INPUTS ";
        assertEquals(1L, line.lines().count()); assertTrue(line.startsWith(prefix), line);
        var produced = ControlBuild.strictMapper().readValue(line.substring(prefix.length()),
                RootSoftwareFixtureInputsProducer.Produced.class);
        var request = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(produced.requestRef().path())),
                RootSoftwareFixtureHandoff.Request.class);
        assertEquals(8, request.originalRequestRefs().size());
        assertEquals(request.originalRequestRefs(), request.originalFixtureRefs());
        assertEquals(request.originalRequestRefs().getFirst(), request.probeRequestRef());
        for (var ref : request.originalFixtureRefs()) ref.verify();
        produced.requestRef().verify(); produced.probePayloadRef().verify();
    }

    @Test void checkoutCliRejectsMalformedPathsAndIncompleteOriginalsBeforePublishing() throws Exception {
        Path source = RootSoftwareFixtureInputsProducerTest.checkoutFixture(temporary.resolve("checkout"));
        Path output = temporary.resolve("checkout-produced");
        String[] command = {"--write-checkout-software-fixture-inputs", "--java-source-root",
                source.toString(), "--output-root", output.toString()};
        for (String[] wrong : new String[][] {new String[0], Arrays.copyOf(command, 4),
                new String[] {command[0], command[1], command[2], command[3], command[4], "extra"}})
            assertThrows(IllegalArgumentException.class, () -> ControlCi.checkoutSoftwareFixtureInputsInvocation(wrong));
        for (int index : new int[] {0, 1, 3}) {
            String[] wrong = command.clone(); wrong[index] = "--wrong";
            assertThrows(IllegalArgumentException.class, () -> ControlCi.checkoutSoftwareFixtureInputsInvocation(wrong));
        }
        for (int index : new int[] {2, 4}) {
            String[] wrong = command.clone(); wrong[index] = "relative-path";
            assertThrows(IllegalArgumentException.class, () -> ControlCi.checkoutSoftwareFixtureInputsInvocation(wrong));
        }
        Files.delete(source.resolve("g2-research/src/test/resources/g2-http/M7.request.json"));
        assertThrows(IOException.class, () -> ControlCi.main(command));
        assertFalse(Files.exists(output));
    }

    @Test void bothOriginalSourceKindsPreserveTheExactPinnedPlanAndOutput() throws Exception {
        Path source = temporary.resolve("original-plan.json");
        Files.writeString(source, "{}");
        var pin = ControlBuild.FileRef.measure(source);
        Path output = temporary.resolve("new-output");
        var golden = ControlCi.softwareFixtureInputsInvocation(command("--write-software-fixture-inputs", pin, output));
        var host = ControlCi.softwareFixtureInputsInvocation(command("--write-host-software-fixture-inputs", pin, output));
        assertEquals(ControlCi.SoftwareFixtureInputKind.PRODUCER_GOLDEN_PLAN, golden.kind());
        assertEquals(ControlCi.SoftwareFixtureInputKind.HOST_FIXTURE_PLAN, host.kind());
        assertEquals(pin, golden.sourcePlanRef()); assertEquals(pin, host.sourcePlanRef());
        assertEquals(output, golden.outputRoot()); assertEquals(output, host.outputRoot());
        assertFalse(Files.exists(output));
        pin.verify();
    }

    @Test void malformedArgumentsAndChangedOriginalRejectBeforeEitherProducerWrites() throws Exception {
        Path source = temporary.resolve("original-plan.json"); Files.writeString(source, "{}");
        var pin = ControlBuild.FileRef.measure(source); Path output = temporary.resolve("new-output");
        String[] original = command("--write-host-software-fixture-inputs", pin, output);
        for (String[] wrong : new String[][] {new String[0], Arrays.copyOf(original, 5),
                new String[] {original[0], original[1], original[2], original[3], original[4], original[5], "extra"}}) {
            assertThrows(IllegalArgumentException.class, () -> ControlCi.softwareFixtureInputsInvocation(wrong));
        }
        for (String invalid : new String[] {"true", "2.0", "0", "02", "-1"}) {
            String[] wrong = original.clone(); wrong[2] = invalid;
            assertThrows(IllegalArgumentException.class, () -> ControlCi.softwareFixtureInputsInvocation(wrong));
        }
        String[] wrongFlag = original.clone(); wrongFlag[0] = "--unknown-source";
        assertThrows(IllegalArgumentException.class, () -> ControlCi.softwareFixtureInputsInvocation(wrongFlag));
        String[] wrongOutput = original.clone(); wrongOutput[5] = "relative-output";
        assertThrows(IllegalArgumentException.class, () -> ControlCi.softwareFixtureInputsInvocation(wrongOutput));
        Files.writeString(source, "[]");
        assertThrows(IOException.class, () -> ControlCi.main(original));
        assertFalse(Files.exists(output));
    }

    @Test void actualMainInvokesTheStrictProducerReaderForBothSourceKinds() throws Exception {
        Path source = temporary.resolve("malformed-original.json"); Files.writeString(source, "{}");
        var pin = ControlBuild.FileRef.measure(source);
        for (String flag : new String[] {"--write-software-fixture-inputs", "--write-host-software-fixture-inputs"}) {
            Path output = temporary.resolve(flag.substring(2));
            assertThrows(IOException.class, () -> ControlCi.main(command(flag, pin, output)));
            assertFalse(Files.exists(output));
            pin.verify();
        }
    }

    private Path checkoutGoldenFixture(Path source) throws IOException {
        RootSoftwareFixtureInputsProducerTest.checkoutFixture(source);
        Path context = Files.createDirectories(source.resolve("local-service/src/test/resources/g2-context"));
        for (String name : new String[] {"context-input.json", "context-result.json", "evaluate-request.json"})
            Files.writeString(context.resolve(name), "{\"fixture\":\"" + name + "\"}");
        Path g2 = source.resolve("g2-research/src/test/resources/g2-http");
        for (var milestone : FreshSdkFixtureStage.GoldenMilestone.values())
            Files.writeString(g2.resolve(milestone.name() + ".expected-result.json"), "{\"fixture\":\"" + milestone.name() + "\"}");
        return source;
    }

    @Test void checkoutGoldenSourcesCliPublishesDataAndFeedsTheExistingHostRequestProducer() throws Exception {
        Path source = checkoutGoldenFixture(temporary.resolve("golden-checkout"));
        Path metadata = temporary.resolve("checkout-golden-sources.json");
        String[] command = {"--write-checkout-producer-golden-sources", "--java-source-root",
                source.toString(), "--output", metadata.toString()};
        var invocation = ControlCi.checkoutProducerGoldenSourcesInvocation(command);
        assertEquals(source, invocation.javaSourceRoot()); assertEquals(metadata, invocation.output());
        PrintStream previous = System.out; ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (PrintStream captured = new PrintStream(bytes, true, StandardCharsets.UTF_8)) {
            System.setOut(captured); ControlCi.main(command);
        } finally { System.setOut(previous); }
        String line = bytes.toString(StandardCharsets.UTF_8).strip(), prefix = "WROTE_CHECKOUT_PRODUCER_GOLDEN_SOURCES ";
        assertEquals(1L, line.lines().count()); assertTrue(line.startsWith(prefix), line);
        var metadataRef = ControlBuild.strictMapper().readValue(line.substring(prefix.length()), ControlBuild.FileRef.class);
        assertEquals(metadata, Path.of(metadataRef.path())); metadataRef.verify();
        var golden = assertInstanceOf(FreshSdkFixtureStage.CheckoutProducerGoldenSources.class,
                FreshSdkFixtureStage.readProducerGoldenSources(metadataRef));
        assertEquals(WindowsJobProcess.currentMachineId(), golden.machineId());
        var originals = FreshSdkFixtureStage.producerGoldenInputs(golden);
        assertEquals(19, originals.size());
        assertFalse(Files.readString(metadata).contains("original_install_map_ref"));
        var produced = RootSoftwareFixtureInputsProducer.produce(metadataRef, temporary.resolve("golden-host-request"));
        var request = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(produced.requestRef().path())),
                RootSoftwareFixtureHandoff.Request.class);
        assertEquals(20, request.originalFixtureRefs().size());
        assertTrue(request.originalFixtureRefs().containsAll(originals));
        assertTrue(request.originalFixtureRefs().contains(metadataRef));
        assertEquals(golden.vectors().stream().map(FreshSdkFixtureStage.ProducerGoldenVector::request).toList(), request.originalRequestRefs());
        assertArrayEquals(RootSoftwareFixtureInputsProducer.payload(request.probeRequestRef(), "G2-M0"),
                Files.readAllBytes(Path.of(produced.probePayloadRef().path())));
    }

    @Test void checkoutGoldenSourcesCliRejectsMalformedOrMissingOriginalsBeforePublication() throws Exception {
        Path source = checkoutGoldenFixture(temporary.resolve("golden-checkout"));
        Path metadata = temporary.resolve("checkout-golden-sources.json");
        String[] command = {"--write-checkout-producer-golden-sources", "--java-source-root",
                source.toString(), "--output", metadata.toString()};
        for (int index : new int[] {0, 1, 3}) {
            String[] wrong = command.clone(); wrong[index] = "--wrong";
            assertThrows(IllegalArgumentException.class, () -> ControlCi.checkoutProducerGoldenSourcesInvocation(wrong));
        }
        for (int index : new int[] {2, 4}) {
            String[] wrong = command.clone(); wrong[index] = "relative";
            assertThrows(IllegalArgumentException.class, () -> ControlCi.checkoutProducerGoldenSourcesInvocation(wrong));
        }
        assertThrows(IllegalArgumentException.class, () -> ControlCi.checkoutProducerGoldenSourcesInvocation(Arrays.copyOf(command, 4)));
        Path result = source.resolve("g2-research/src/test/resources/g2-http/M7.expected-result.json");
        Files.delete(result);
        assertThrows(IOException.class, () -> ControlCi.main(command)); assertFalse(Files.exists(metadata));
        Files.writeString(result, "{}");
        Path request = source.resolve("g2-research/src/test/resources/g2-http/M3.request.json");
        Files.writeString(request, Files.readString(request).replace("G2-M3", "G2-M4"));
        assertThrows(IOException.class, () -> ControlCi.main(command)); assertFalse(Files.exists(metadata));
    }
}
