package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Producer/reader rejection tests. No ReferenceActual or accepted build is fabricated. */
final class CompiledReferenceMainTest {
    @TempDir Path temporary;

    private ControlBuild.FileRef input(String name, String body) throws IOException {
        Path path = temporary.resolve(name); Files.writeString(path, body);
        return ControlBuild.FileRef.measure(path);
    }
    private CompiledOriginalCaptureProfile.Profile profile(CompiledOriginalCaptureProfile.InvocationKind kind,
            ControlBuild.FileRef reference) throws IOException {
        var metadata = input("metadata-" + kind + ".json", "{}");
        var source = input("CaptureInput-" + kind + ".java", "final class CaptureInput {}");
        var pom = input("pom-" + kind + ".xml", "<project/>");
        var selection = new CompiledOriginalCaptureProfile.Selection("fixture.CaptureInput", source, List.of(pom), List.of());
        boolean main = kind == CompiledOriginalCaptureProfile.InvocationKind.MAIN
                || kind == CompiledOriginalCaptureProfile.InvocationKind.REFERENCE_MAIN;
        var interpreter = main ? ControlBuild.FileRef.measure(Path.of(System.getProperty("java.home"), "bin/java.exe")) : null;
        var arguments = main ? List.of(
                new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.REPOSITORY, temporary.toString(), null),
                new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.INTERPRETER, interpreter.path(), null),
                new CompiledOriginalCaptureProfile.Argument(CompiledOriginalCaptureProfile.ArgumentKind.OUTPUT, temporary.resolve("result.txt").toString(), null))
                : List.<CompiledOriginalCaptureProfile.Argument>of();
        return new CompiledOriginalCaptureProfile.Profile(metadata, metadata, metadata, metadata, selection, kind,
                interpreter, arguments, List.of(), List.of(), reference);
    }
    private CompiledOriginalCapture.Request request(CompiledOriginalCaptureProfile.Profile profile, String machine) {
        return new CompiledOriginalCapture.Request(CompiledOriginalCapture.REQUEST_SCHEMA, "reference-contract", machine,
                temporary.toString(), profile, List.of(profile.selection().compiledSourceRef()), List.of(profile.captureReceiptRef()),
                temporary.resolve("result.txt").toString(), CompiledOriginalCapture.OutputKind.FILE, 65536, 1 << 20, List.of());
    }

    private CompiledOriginalCaptureProfile.ReferenceAuditInputs auditInputs() throws IOException {
        var originals = new java.util.ArrayList<ControlBuild.FileRef>();
        for (int index = 0; index < 8; index++) originals.add(input("original-" + index + ".txt", "original " + index));
        return new CompiledOriginalCaptureProfile.ReferenceAuditInputs(input("original-audit.json", "original audit"),
                input("separation-audit.json", "separation audit"), originals, input("selected-client.txt", "selected client"));
    }

    @Test void referenceAuditInputsMustRemainInEveryDeclaredReaderClosure() throws Exception {
        // These local input pins test only the metadata boundary, never ReferenceActual/build qualification.
        var audit = auditInputs();
        var complete = audit.checkedRefs();
        assertEquals(11, complete.size());
        assertTrue(complete.containsAll(audit.originalSources()));
        assertTrue(complete.containsAll(List.of(audit.originalAuditRef(), audit.separationAuditRef(), audit.selectedClientRef())));
        CompiledOriginalCaptureProfile.requireReferenceInputClosure(complete, complete);
        var missing = new java.util.ArrayList<>(complete); missing.remove(audit.separationAuditRef());
        assertThrows(IOException.class, () -> CompiledOriginalCaptureProfile.requireReferenceInputClosure(missing, complete));
        missing.add(input("substituted-audit.json", "another audit"));
        assertThrows(IOException.class, () -> CompiledOriginalCaptureProfile.requireReferenceInputClosure(missing, complete));
    }

    @Test void changedConstructionAuditCannotProduceAReferenceInputBinding() throws Exception {
        var audit = auditInputs(); audit.checkedRefs();
        Files.writeString(Path.of(audit.separationAuditRef().path()), "changed audit");
        assertThrows(IOException.class, audit::checkedRefs);
    }

    @Test void referenceKindRequiresItsOwnPinAndOtherKindsRejectIt() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> profile(CompiledOriginalCaptureProfile.InvocationKind.REFERENCE_MAIN, null));
        var malformed = input("not-reference.json", "{}");
        for (var kind : List.of(CompiledOriginalCaptureProfile.InvocationKind.MAIN,
                CompiledOriginalCaptureProfile.InvocationKind.JAVA_MAIN, CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT))
            assertThrows(IllegalArgumentException.class, () -> profile(kind, malformed));
    }

    @Test void v3ProducerAndStrictReaderRoundTripWithoutGrantingQualification() throws Exception {
        var value = request(profile(CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, null), "unit-machine");
        Path output = temporary.resolve("request.json");
        var pin = CompiledOriginalCapture.writeRequest(value, temporary, output);
        assertEquals(value, CompiledOriginalCapture.parseRequest(Files.readAllBytes(output)));
        assertEquals(pin, ControlBuild.FileRef.measure(output));
        assertThrows(IOException.class, () -> CompiledOriginalCapture.writeRequest(value, temporary, output));
        assertEquals(pin, ControlBuild.FileRef.measure(output));
    }

    @Test void previousSchemaMissingReferenceFieldAndWrongTypesAreRejected() throws Exception {
        var malformed = input("not-reference.json", "{}");
        var value = request(profile(CompiledOriginalCaptureProfile.InvocationKind.REFERENCE_MAIN, malformed), "unit-machine");
        var mapper = ControlBuild.strictMapper();
        assertEquals(value, CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(value)));
        ObjectNode old = mapper.valueToTree(value); old.put("schema", "xar.compiled-original-capture-request/v2");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(old)));
        ObjectNode missing = mapper.valueToTree(value); ((ObjectNode) missing.get("profile")).remove("reference_actual_ref");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(missing)));
        ObjectNode wrong = mapper.valueToTree(value);
        ((ObjectNode) wrong.get("profile").get("reference_actual_ref")).put("bytes", true);
        assertThrows(IOException.class, () -> CompiledOriginalCapture.parseRequest(mapper.writeValueAsBytes(wrong)));
    }

    @Test void ordinaryMainCannotUseAnExternalInterpreter() throws Exception {
        var value = request(profile(CompiledOriginalCaptureProfile.InvocationKind.MAIN, null), "unit-machine");
        assertThrows(IOException.class, () -> CompiledOriginalCaptureProfile.requireInterpreter(temporary, value.profile().interpreterRef()));
        Path output = temporary.resolve("request.json");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.writeRequest(value, temporary, output));
        assertFalse(Files.exists(output));
    }

    @Test void actualMalformedReferenceReaderRejectsBeforeCreatingARequest() throws Exception {
        var malformed = input("not-reference.json", "{}");
        var value = request(profile(CompiledOriginalCaptureProfile.InvocationKind.REFERENCE_MAIN, malformed), "unit-machine");
        assertThrows(IOException.class, () -> CompiledOriginalCaptureProfile.readReferenceBinding(malformed));
        Path output = temporary.resolve("request.json");
        assertThrows(IOException.class, () -> CompiledOriginalCapture.writeRequest(value, temporary, output));
        assertFalse(Files.exists(output));
    }

    @Test void pinnedReferenceDriftAndEscapedProducerDestinationAreRejected() throws Exception {
        var malformed = input("not-reference.json", "{}");
        Files.writeString(Path.of(malformed.path()), "changed source");
        assertThrows(IOException.class, () -> CompiledOriginalCaptureProfile.readReferenceBinding(malformed));
        var value = request(profile(CompiledOriginalCaptureProfile.InvocationKind.SOURCE_EXPORT, null), "unit-machine");
        Path owned = temporary.resolve("owned"); Files.createDirectory(owned);
        assertThrows(IOException.class, () -> CompiledOriginalCapture.writeRequest(value, owned, temporary.resolve("outside.json")));
    }

    @Test void genuineExecuteRejectsMalformedReferenceAndAcceptedReaderCannotBlessRed() throws Exception {
        var malformed = input("not-reference.json", "{}");
        var value = request(profile(CompiledOriginalCaptureProfile.InvocationKind.REFERENCE_MAIN, malformed), WindowsJobProcess.currentMachineId());
        Path requestPath = temporary.resolve("negative-request.json");
        Files.write(requestPath, ControlBuild.strictMapper().writeValueAsBytes(value));
        Path root = temporary;
        var limits = new CompiledGoldenCapture.Limits(root.toString(), temporary.toString(), Instant.now().plusSeconds(45).toString(), 30, 128L << 20);
        Path actualPath = root.resolve("actual.json");
        var actual = CompiledOriginalCapture.execute(new CompiledOriginalCapture.RunSpec(ControlBuild.FileRef.measure(requestPath),
                actualPath.toString(), limits, CompiledOriginalCapture.Mode.EXECUTE));
        assertEquals(CompiledOriginalCapture.Status.RED, actual.status()); assertFalse(actual.childStarted());
        assertNull(actual.commandResult()); assertNull(actual.proofRef());
        assertEquals(CompiledOriginalCapture.RECEIPT_SCHEMA, actual.schema());
        assertNull(actual.invocationEvidence());
        assertThrows(IOException.class, () -> CompiledOriginalCapture.acceptedReceipt(ControlBuild.FileRef.measure(actualPath), CompiledOriginalCapture.Mode.EXECUTE));
        for(String historicalSchema:List.of("xar.compiled-original-capture-actual/v2","xar.compiled-original-capture-actual/v3",
                "xar.compiled-original-capture-actual/v4","xar.compiled-original-capture-actual/v5")) {
            ObjectNode old = ControlBuild.strictMapper().valueToTree(actual);
            old.put("schema", historicalSchema);
            if (!historicalSchema.endsWith("v4") && !historicalSchema.endsWith("v5")) old.remove("invocation_evidence");
            String version = historicalSchema.substring(historicalSchema.lastIndexOf('/') + 1);
            Path oldPath = temporary.resolve("old-receipt-" + version + "-no-preparation.json");
            Files.write(oldPath, ControlBuild.strictMapper().writeValueAsBytes(old));
            if (historicalSchema.endsWith("v4")) {
                var historical = CompiledOriginalCapture.readHistoricalV4Metadata(ControlBuild.FileRef.measure(oldPath));
                assertEquals(historicalSchema, historical.schema());
                assertFalse(historical.childStarted()); assertNull(historical.invocationEvidence());
            }
            if (historicalSchema.endsWith("v5")) {
                var historical = CompiledOriginalCapture.readHistoricalV5Metadata(ControlBuild.FileRef.measure(oldPath));
                assertEquals(historicalSchema, historical.schema());
                assertFalse(historical.childStarted()); assertNull(historical.invocationEvidence());
            }
            assertThrows(IOException.class, () -> CompiledOriginalCapture.acceptedReceipt(ControlBuild.FileRef.measure(oldPath), CompiledOriginalCapture.Mode.EXECUTE));
        }
    }
}
