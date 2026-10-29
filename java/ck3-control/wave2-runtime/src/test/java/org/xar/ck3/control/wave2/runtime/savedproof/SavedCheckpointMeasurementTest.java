package org.xar.ck3.control.wave2.runtime.savedproof;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.channels.FileChannel;
import java.nio.ByteBuffer;
import java.nio.file.StandardOpenOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Synthetic boundary tests. They do not claim an original SDK or current SAVE run. */
final class SavedCheckpointMeasurementTest {
    @TempDir Path temporary;
    private static final String SHA = "a".repeat(64);
    private SavedProofReadTicket ticket() {
        Path root = temporary.toAbsolutePath();
        FileStatIdentity driver = new FileStatIdentity(BigInteger.valueOf(41_000_000), "21110623265666216", "1792668000000000000");
        FileStatIdentity save = new FileStatIdentity(BigInteger.valueOf(8192), "21110623265666217", "1792668000000000001");
        ObjectNode release = StrictJson.object();
        release.put("schema", SavedProofReadTicket.SCHEMA); release.put("machine_id", "synthetic-test-machine");
        release.put("nonce", "0123456789abcdef0123456789abcdef");
        release.put("observed_at_utc", "2026-10-22T14:00:00Z"); release.put("review_at_utc", "2026-10-22T15:00:00Z");
        release.put("driver_path", root.resolve("driver-state.json").toString()); release.set("driver_identity", driver.toJson());
        release.set("save_ref", new ExactRef(root.resolve("save games/xar_checkpoint.ck3").toString(), 8192, SHA).toJson());
        release.set("save_identity", save.toJson()); release.put("sdk_root", root.resolve("src32").toString());
        release.set("sdk_freeze_ref", new ExactRef(root.resolve("freeze.json").toString(), 400_000, SHA).toJson());
        release.set("validator_ref", new ExactRef(root.resolve("src32/xar_autoplayer/cold_checkpoint_validator.py").toString(), 6000, SHA).toJson());
        release.put("pipe_name", "synthetic-pipe"); release.put("python_executable", root.resolve("python.exe").toString());
        release.put("output_root", root.toString()); release.put("max_driver_bytes", 67_108_864);
        release.put("physical_driver_reads", 1); release.put("original_sdk_save_hash_calls", 1);
        release.put("job_memory_limit_bytes", 536_870_912); release.put("timeout_seconds", 120);
        return SavedProofReadTicket.parse(evidence(root.resolve("release.json"), release));
    }
    private static RecoveryEvidence evidence(Path path, ObjectNode row) {
        byte[] raw = StrictJson.canonical(row);
        return new RecoveryEvidence(new ExactRef(path.toString(), raw.length, RecoveryEvidence.sha256(raw)), raw);
    }
    private static Map<String, ExactRef> pins(SavedProofReadTicket ticket) {
        return Map.of("xar_autoplayer/cold_checkpoint_validator.py", ticket.validatorSource(),
            "xar_autoplayer/native_session.py", new ExactRef(ticket.sdkRoot().resolve("xar_autoplayer/native_session.py").toString(), 60_000, SHA),
            "xar_autoplayer/bridge/native_driver.py", new ExactRef(ticket.sdkRoot().resolve("xar_autoplayer/bridge/native_driver.py").toString(), 1_648_649, SHA));
    }
    private static ObjectNode observation(SavedProofReadTicket ticket) {
        ObjectNode row = StrictJson.object();
        row.put("schema", "xar.original-sdk-current-save-transport/v1"); row.put("status", "ORIGINAL_SDK_CALL_COMPLETED");
        row.put("machine_id", ticket.machineId()); row.put("nonce", ticket.nonce()); row.put("observed_at_utc", "2026-10-22T14:01:00Z");
        row.put("worker_source_sha256", FixedSdkTransport.sourceSha256()); row.set("sdk_freeze_ref", ticket.sdkFreeze().toJson());
        row.set("validator_ref", ticket.validatorSource().toJson());
        row.set("driver_ref", new ExactRef(ticket.driverPath().toString(), 41_000_000, SHA).toJson());
        row.set("driver_identity_before", ticket.driverIdentity().toJson()); row.set("driver_identity_after", ticket.driverIdentity().toJson());
        row.set("save_ref", ticket.save().toJson()); row.set("save_identity_before", ticket.saveIdentity().toJson()); row.set("save_identity_after", ticket.saveIdentity().toJson());
        ObjectNode checkpoint = StrictJson.object(); checkpoint.put("name", "xar_checkpoint.ck3"); checkpoint.put("size", 8192);
        checkpoint.put("sha256", SHA); checkpoint.put("date_raw", 53_279_400); checkpoint.put("history_index", 5944);
        checkpoint.put("exact_native_identity", new BigInteger("134371430348828741"));
        row.set("checkpoint", checkpoint);
        ObjectNode anchor = StrictJson.object(); anchor.put("name", "xar_checkpoint.ck3"); anchor.put("load_save_name", "xar_checkpoint");
        anchor.put("path", ticket.save().path()); anchor.put("size", 8192); anchor.put("sha256", SHA);
        anchor.put("saved_date_raw", 53_279_400); anchor.put("history_index", 5944); anchor.putNull("succession_lifecycle"); row.set("anchor", anchor);
        row.put("pipe_name", ticket.pipeName()); ObjectNode counts = StrictJson.object();
        counts.put("driver_physical_body_reads", 1); counts.put("driver_physical_read_bytes", 41_000_000);
        counts.put("original_validator_calls", 1); counts.put("save_sha256_calls", 1); row.set("counts", counts);
        ArrayNode imports = row.putArray("imported_sources");
        pins(ticket).forEach((relative, ref) -> { ObjectNode source = imports.addObject(); source.put("relative", relative); source.put("bytes", ref.bytes()); source.put("sha256", ref.sha256()); });
        row.put("Driver_SAVE_body_rewritten", false); row.put("Game_RPC_calls", 0); return row;
    }
    @Test void exactProducerBoundaryAndUnchangedQualificationRoundTrip() {
        SavedProofReadTicket ticket = ticket(); ObjectNode raw = observation(ticket);
        SavedCheckpointMeasurementCoordinator.Observation measured = SavedCheckpointMeasurementCoordinator.decode(ticket, StrictJson.canonical(raw), pins(ticket));
        JsonNode receipt = StrictJson.parse(SavedCheckpointMeasurementCoordinator.qualification(ticket, measured));
        assertEquals("xar.current-saved-recovery-checkpoint-qualification/v1", receipt.get("schema").textValue());
        assertCanonicalJsonEquals(raw.get("checkpoint"), receipt.get("checkpoint"));
        assertCanonicalJsonEquals(raw.get("anchor"), measured.originalSdkAnchor());
        assertTrue(CachedOriginalSdkVerifier.sameRawNativeCheckpoint(receipt.get("checkpoint"), raw.get("checkpoint")));
        assertFalse(RecoveryEvidence.sha256(StrictJson.canonical(measured.checkpoint()))
            .equals(RecoveryEvidence.sha256(StrictJson.canonical(measured.originalSdkAnchor()))));
        assertEquals(new BigInteger("134371430348828741"), receipt.get("checkpoint").get("exact_native_identity").bigIntegerValue());
        assertEquals(ticket.driverIdentity(), FileStatIdentity.fromJson(receipt.get("driver_identity_after"), FileStatIdentity.SCHEMA));
        assertEquals(1, receipt.get("save_sha256_calls").intValue()); assertFalse(receipt.get("driver_body_rewritten").booleanValue());
    }
    @Test void rejectWrongCounterScalarsMissingFieldsIdentitySourceAndExpiry() {
        SavedProofReadTicket ticket = ticket();
        for (String field : new String[] {"driver_physical_body_reads", "original_validator_calls", "save_sha256_calls"}) {
            ObjectNode row = observation(ticket); ((ObjectNode) row.get("counts")).put(field, true); reject(ticket, row);
            row = observation(ticket); ((ObjectNode) row.get("counts")).put(field, 1.0); reject(ticket, row);
            row = observation(ticket); ((ObjectNode) row.get("counts")).put(field, 2); reject(ticket, row);
        }
        ObjectNode row = observation(ticket); row.remove("anchor"); reject(ticket, row);
        row = observation(ticket); ((ObjectNode) row.get("checkpoint")).remove("size"); reject(ticket, row);
        row = observation(ticket); ((ObjectNode) row.get("driver_identity_after")).put("file_id", "21110623265666218"); reject(ticket, row);
        row = observation(ticket); row.put("worker_source_sha256", "b".repeat(64)); reject(ticket, row);
        row = observation(ticket); row.put("observed_at_utc", ticket.reviewAt().toString()); reject(ticket, row);
        row = observation(ticket); row.put("Game_RPC_calls", false); reject(ticket, row);
        row = observation(ticket); ((ObjectNode) row.get("anchor")).put("history_index", 5944.0); reject(ticket, row);
    }
    private static void reject(SavedProofReadTicket ticket, ObjectNode row) {
        // Jackson's ordinary encoder preserves floating invalid-token cases for the strict parser.
        assertThrows(ContractViolationException.class, () -> SavedCheckpointMeasurementCoordinator.decode(ticket, row.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8), pins(ticket)));
    }
    @Test void ticketRejectsReadCountCoercionAndWrongOriginalValidator() {
        SavedProofReadTicket ticket = ticket(); ObjectNode row = (ObjectNode) StrictJson.parse(ticket.release().bytes());
        row.put("physical_driver_reads", true);
        assertThrows(ContractViolationException.class, () -> SavedProofReadTicket.parse(evidence(temporary.resolve("bad.json"), row)));
        ObjectNode wrong = (ObjectNode) StrictJson.parse(ticket.release().bytes());
        ((ObjectNode) wrong.get("validator_ref")).put("path", temporary.resolve("current-validator.py").toString());
        assertThrows(ContractViolationException.class, () -> SavedProofReadTicket.parse(evidence(temporary.resolve("bad2.json"), wrong)));
    }
    @Test void fixedTransportHasOnlyOriginalCallAndNoActionOrWriterEntry() {
        assertTrue(FixedSdkTransport.PROGRAM.contains("anchor=validator("));
        assertTrue(FixedSdkTransport.PROGRAM.contains("sys.setprofile(profile)"));
        assertFalse(FixedSdkTransport.PROGRAM.contains("WindowLedger"));
        assertFalse(FixedSdkTransport.PROGRAM.contains("write_text("));
        assertEquals(Instant.parse("2026-10-22T15:00:00Z"), ticket().reviewAt());
    }
    @Test void consumedNonceIsCreateOnlyAndSourceLaneNeverReadsPersistence() throws IOException {
        ObjectNode claim = StrictJson.object(); claim.put("schema", "synthetic-consumed-nonce");
        Path destination = temporary.resolve("consumed.json");
        SavedProofFiles.publish(destination, StrictJson.canonical(claim));
        assertThrows(FileAlreadyExistsException.class, () -> SavedProofFiles.publish(destination, StrictJson.canonical(claim)));
        Path driver = temporary.resolve("driver-state.json");
        assertThrows(ContractViolationException.class, () -> SavedProofFiles.read(driver, 2_097_152));
        Path save = temporary.resolve("xar_checkpoint.ck3");
        assertThrows(ContractViolationException.class, () -> SavedProofFiles.read(save, 2_097_152));
        Path source = temporary.resolve("source.py"); Files.writeString(source, "x=1");
        assertThrows(ContractViolationException.class, () -> SavedProofFiles.exact(new ExactRef(source.toString(), 3, SHA), 2_097_152));
    }
    @Test void actualTerminalShapeSurvivesOverCapAndUnavailableLogs() throws IOException {
        SavedProofReadTicket ticket = ticket(); Path stdout = temporary.resolve("oversize.stdout.json");
        try (FileChannel file = FileChannel.open(stdout, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            file.position(65_536); file.write(ByteBuffer.wrap(new byte[] {1})); file.force(true);
        }
        Path absent = temporary.resolve("absent.stderr.txt");
        WindowsJobProcess.CommandResult syntheticTerminal = new WindowsJobProcess.CommandResult(
            new WindowsJobProcess.ProcessIdentity(123, "134371430348828741", ticket.pythonExecutable().toString()),
            124, 1.0, new WindowsJobProcess.Accounting(100_000, 0, ticket.jobMemoryBytes(), WindowsJobProcess.REQUIRED_FLAGS), "synthetic timeout fixture");
        SavedCheckpointMeasurementCoordinator.publishTerminal(ticket,
            new ManagedSdkMeasurementRunner.Outcome(syntheticTerminal, stdout, absent), Instant.parse("2026-10-22T14:01:00Z"));
        JsonNode terminal = StrictJson.parse(Files.readAllBytes(temporary.resolve("sdk-" + ticket.nonce() + ".terminal.json")));
        assertEquals(124, terminal.get("exit_code").intValue()); assertEquals(0, terminal.get("job_active").intValue());
        assertEquals("OVER_CAP_NOT_READ", terminal.get("stdout_log").get("status").textValue());
        assertEquals(65_537, terminal.get("stdout_log").get("bytes").intValue()); assertTrue(terminal.get("stdout_log").get("sha256").isNull());
        assertEquals("UNAVAILABLE_NOT_READ", terminal.get("stderr_log").get("status").textValue());
        assertFalse(terminal.get("passed").booleanValue());
    }
    @Test void actualHistoricalProducerGoldenMapsRawToNormalizedWithoutEquatingDomains() throws IOException {
        byte[] basisBytes = golden("n46-prior-basis.actual.json", "4b53ffa1a422df36cd18d29f47737fed8417a257ff42d2dc4b7093de56d27afa");
        byte[] stateBytes = golden("n46-raw-state.actual.json", "7d62a0c1cf55f29094b8418aa1f716e1b966f03ddc4ab6e826ec415268d1066f");
        JsonNode basis = StrictJson.parse(basisBytes), raw = StrictJson.parse(stateBytes).get("actual_saved_checkpoint");
        JsonNode normalized = basis.get("checkpoint"); ExactRef save = ExactRef.fromJson(basis.get("refs").get("save"));
        assertEquals(raw, SavedCheckpointMeasurementCoordinator.validateCheckpointBinding(save, raw, normalized));
        assertTrue(normalized.has("saved_date_raw")); assertFalse(normalized.has("date_raw"));
        assertTrue(raw.has("date_raw")); assertFalse(raw.has("saved_date_raw")); assertFalse(raw.equals(normalized));
        ObjectNode wrong = (ObjectNode) normalized.deepCopy(); wrong.put("saved_date_raw", true);
        assertThrows(ContractViolationException.class, () -> SavedCheckpointMeasurementCoordinator.validateCheckpointBinding(save, raw, wrong));
    }

    @Test void mixedIntegralNodeImplementationsSurviveRealProducerAndCacheConsumerRoundTrip() {
        SavedProofReadTicket ticket = ticket(); ObjectNode row = observation(ticket);
        ObjectNode checkpoint = (ObjectNode) row.get("checkpoint");
        checkpoint.put("size", 8192L); // LongNode in the caller.
        checkpoint.put("date_raw", BigInteger.valueOf(53_279_400)); // BigIntegerNode.
        checkpoint.put("history_index", 5944); // IntNode.
        ObjectNode anchor = (ObjectNode) StrictJson.parse(StrictJson.canonical(row.get("anchor")));
        assertCanonicalJsonEquals(checkpoint,
            SavedCheckpointMeasurementCoordinator.validateCheckpointBinding(ticket.save(), checkpoint, anchor));

        // The production decoder and producer, then the actual cache consumer's full-content comparator.
        SavedCheckpointMeasurementCoordinator.Observation measured = SavedCheckpointMeasurementCoordinator.decode(
            ticket, row.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8), pins(ticket));
        JsonNode published = StrictJson.parse(SavedCheckpointMeasurementCoordinator.qualification(ticket, measured));
        JsonNode afterPersistence = StrictJson.parse(StrictJson.canonical(published));
        assertTrue(CachedOriginalSdkVerifier.sameRawNativeCheckpoint(afterPersistence.get("checkpoint"), checkpoint));
        assertCanonicalJsonEquals(checkpoint, afterPersistence.get("checkpoint"));
        assertEquals(new BigInteger("134371430348828741"),
            afterPersistence.get("checkpoint").get("exact_native_identity").bigIntegerValue());

        ObjectNode changed = checkpoint.deepCopy(); changed.put("date_raw", 53_279_401);
        assertFalse(CachedOriginalSdkVerifier.sameRawNativeCheckpoint(afterPersistence.get("checkpoint"), changed));
        changed = checkpoint.deepCopy(); changed.put("sha256", "b".repeat(64));
        assertFalse(CachedOriginalSdkVerifier.sameRawNativeCheckpoint(afterPersistence.get("checkpoint"), changed));
        changed = checkpoint.deepCopy(); changed.remove("history_index");
        assertFalse(CachedOriginalSdkVerifier.sameRawNativeCheckpoint(afterPersistence.get("checkpoint"), changed));
        changed = checkpoint.deepCopy(); changed.put("extra_native_field", true);
        assertFalse(CachedOriginalSdkVerifier.sameRawNativeCheckpoint(afterPersistence.get("checkpoint"), changed));
    }

    @Test void rawIntegerTokensRemainStrictBeforeProducerAndConsumerPersistence() {
        SavedProofReadTicket ticket = ticket();
        for (String field : new String[] {"size", "date_raw", "history_index"}) {
            ObjectNode row = observation(ticket);
            ((ObjectNode) row.get("checkpoint")).put(field, true); reject(ticket, row);
            row = observation(ticket);
            ObjectNode checkpoint = (ObjectNode) row.get("checkpoint");
            double sameNumericValue = checkpoint.get(field).doubleValue();
            checkpoint.put(field, sameNumericValue); reject(ticket, row); // Actual raw floating token; never canonicalize first.
            ObjectNode floating = checkpoint;
            assertThrows(ContractViolationException.class,
                () -> CachedOriginalSdkVerifier.sameRawNativeCheckpoint(observation(ticket).get("checkpoint"), floating));
            row = observation(ticket); ((ObjectNode) row.get("checkpoint")).putNull(field); reject(ticket, row);
            row = observation(ticket); ((ObjectNode) row.get("checkpoint")).remove(field); reject(ticket, row);
        }
        ObjectNode row = observation(ticket); ((ObjectNode) row.get("checkpoint")).put("sha256", "b".repeat(64)); reject(ticket, row);
        row = observation(ticket); ((ObjectNode) row.get("checkpoint")).put("sha256", true); reject(ticket, row);
        assertThrows(ContractViolationException.class, () -> CachedOriginalSdkVerifier.sameRawNativeCheckpoint(
            observation(ticket).get("checkpoint"), com.fasterxml.jackson.databind.node.NullNode.instance));
        ObjectNode literalOne = StrictJson.object(); literalOne.put("native_control", 1.0);
        assertThrows(ContractViolationException.class,
            () -> CachedOriginalSdkVerifier.sameRawNativeCheckpoint(StrictJson.object().put("native_control", 1), literalOne));
    }

    private static void assertCanonicalJsonEquals(JsonNode expected, JsonNode actual) {
        // This is the existing exact integer JSON domain, not Jackson's in-memory numeric node class.
        assertArrayEquals(StrictJson.canonical(expected), StrictJson.canonical(actual));
    }

    private static byte[] golden(String name, String expectedSha) throws IOException {
        try (InputStream input = SavedCheckpointMeasurementTest.class.getResourceAsStream("/savedproof/" + name)) {
            if (input == null) { throw new IOException("required original producer golden missing: " + name); }
            byte[] bytes = input.readNBytes(65_537);
            assertEquals(expectedSha, RecoveryEvidence.sha256(bytes), "original whole metadata producer pin");
            return bytes;
        }
    }
}
