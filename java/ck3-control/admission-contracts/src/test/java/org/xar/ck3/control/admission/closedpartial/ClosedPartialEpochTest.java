package org.xar.ck3.control.admission.closedpartial;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryInput;
import org.xar.ck3.control.recovery.ClosedFailureRecoveryReducer;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.recovery.RecoveryPrerequisiteVerifier;
import org.xar.ck3.control.recovery.RecoveryPreview;

/** Original producer receipts, not hand-built GREEN documents. Missing large fixture files fail explicitly. */
class ClosedPartialEpochTest {
    private static byte[] resource(String name) throws IOException {
        try (var stream = ClosedPartialEpochTest.class.getResourceAsStream("/closedpartial/" + name)) {
            assertNotNull(stream, "required source fixture: " + name);
            byte[] raw = stream.readNBytes(65_537); assertTrue(raw.length <= 65_536); return raw;
        }
    }
    private static ObjectNode manifest() throws IOException {
        return (ObjectNode) StrictJson.parse(resource("original-sources.json"));
    }
    private static RecoveryEvidence metadata(JsonNode row) throws IOException {
        return new RecoveryEvidence(ExactRef.fromJson(row.get("ref")), resource(StrictJson.text(row.get("resource"))));
    }
    private static RecoveryEvidence evidence(String path, byte[] raw) {
        return new RecoveryEvidence(new ExactRef(path, raw.length, RecoveryEvidence.sha256(raw)), raw);
    }
    private static ClosedFailureRecoveryInput input() throws IOException {
        JsonNode rows = manifest().get("inputs"); RecoveryEvidence basis = metadata(rows.get("basis"));
        JsonNode value = StrictJson.parse(basis.bytes()), refs = value.get("refs");
        return new ClosedFailureRecoveryInput("xenoamess-full-tower-eb9d2c1186", "2026-10-22T13:36:00Z",
                metadata(rows.get("head")), basis, metadata(rows.get("qualification")), metadata(rows.get("fullRequest")),
                metadata(rows.get("failedFull")), metadata(rows.get("autoRequest")), metadata(rows.get("failedAuto")),
                metadata(rows.get("state")), metadata(rows.get("governance")), metadata(rows.get("next")),
                ExactRef.fromJson(refs.get("driver")), FileStatIdentity.fromJson(value.get("driver_identity"), FileStatIdentity.SCHEMA),
                ExactRef.fromJson(refs.get("save")), FileStatIdentity.fromJson(value.get("save_identity"), FileStatIdentity.SCHEMA));
    }
    private static ClosedPartialRpcEvidence actualRpc(JsonNode row) throws IOException {
        ExactRef ref = ExactRef.fromJson(row.get("ref"));
        Path path = Path.of(ref.path());
        assertTrue(Files.isRegularFile(path), "UNAVAILABLE: actual original RPC environment required: " + path);
        assertEquals(ref.bytes(), Files.size(path), "original RPC size pin");
        try (var stream = Files.newInputStream(path)) {
            return new ClosedPartialRpcEvidence(ref, stream.readNBytes(ClosedPartialRpcEvidence.MAX_BYTES + 1));
        }
    }
    private static ClosedPartialSources sources() throws IOException {
        ObjectNode value = manifest(); JsonNode rows = value.get("sources");
        List<ClosedPartialSources.Task> tasks = new ArrayList<>();
        for (JsonNode task : value.get("tasks")) {
            tasks.add(new ClosedPartialSources.Task(ClosedPartialSources.TaskRole.valueOf(task.get("role").textValue()),
                    metadata(task.get("spec")), metadata(task.get("closed")), metadata(task.get("unregistered"))));
        }
        List<ClosedPartialSources.Cycle> cycles = new ArrayList<>();
        for (JsonNode cycle : value.get("cycles")) {
            cycles.add(new ClosedPartialSources.Cycle(actualRpc(cycle.get("auto")), actualRpc(cycle.get("metrics"))));
        }
        return new ClosedPartialSources(metadata(rows.get("sdk")), metadata(rows.get("game")), metadata(rows.get("supervisor")),
                metadata(rows.get("recording")), metadata(rows.get("capture")), metadata(rows.get("screen")), tasks, cycles);
    }

    @Test void actualN46ProducerToCodecAndRecoveryProviderRetainsUnknown() throws Exception {
        ClosedFailureRecoveryInput input = input(); ClosedPartialSources sources = sources();
        byte[] rawState = input.rawState().bytes();
        ClosedPartialEpochProducer.Produced result = ClosedPartialEpochProducer.compose(input, sources);
        assertEquals(result.epoch(), ClosedPartialEpochCodec.decode(result.epochBytes()));
        assertEquals(11543, result.epoch().fullSequence()); assertEquals(11558, result.epoch().unknownSequence());
        assertEquals(11559, result.epoch().nextSequence()); assertEquals(7, result.epoch().settledCycles());
        assertEquals(5182, result.epoch().savedCycles()); assertFalse(result.ready());
        assertFalse(result.epoch().grantsWriterOrReducerRecovery());
        RecoveryEvidence epoch = evidence("/fixture-only/closed-partial-epoch.json", result.epochBytes());
        RecoveryEvidence prefix = evidence("/fixture-only/closed-partial-prefix.json", result.prefixBytes());
        ClosedPartialAdmissionVerifier provider = new ClosedPartialAdmissionVerifier(sources, epoch, prefix,
                ClosedPartialAdmissionVerifier.unavailableOriginalSdk());
        assertInstanceOf(RecoveryPrerequisiteVerifier.Unavailable.class,
                provider.verify(input, ClosedFailureRecoveryReducer.inputDigest(input)));
        assertInstanceOf(RecoveryPreview.Unavailable.class, ClosedFailureRecoveryReducer.preview(input, provider));
        assertInstanceOf(ClosedPartialColdBasisPreview.Unavailable.class,
                ClosedPartialColdBasisPreview.preview(input, sources, epoch, prefix, input.predecessor(),
                        ClosedPartialAdmissionVerifier.unavailableOriginalSdk()));
        assertArrayEquals(rawState, input.rawState().bytes());
        assertEquals(5190, StrictJson.parse(rawState).get("pending_cycle").get("global_turn").longValue());
        assertTrue(sources.settledCycles().get(6).auto().raw().length > 1_048_576);
    }

    @Test void strictNewSchemaRejectsOldRouteMissingExtraAndWrongIntegerTypes() {
        ExactRef ref = new ExactRef("/fixture-only/receipt.json", 2, RecoveryEvidence.sha256("{}".getBytes(StandardCharsets.UTF_8)));
        ClosedPartialEpochCodec.Epoch epoch = new ClosedPartialEpochCodec.Epoch("fixture-only", "2026-10-22T13:36:00Z",
                "1".repeat(64), 11543, 11558, 11559, 5182, 7, 53279400, ref, ref, ref, ref, ref);
        byte[] raw = ClosedPartialEpochCodec.encode(epoch);
        String original = new String(raw, StandardCharsets.UTF_8);
        String marker = "\"next_sequence\":11559";
        assertTrue(original.contains(marker));
        for (String token : List.of("true", "11559.0", "11559e0", "\"11559\"", "null")) {
            // Keep the original token on the byte boundary: a DecimalNode writer can erase .0.
            String edited = original.replace(marker, "\"next_sequence\":" + token);
            assertNotEquals(original, edited);
            assertTrue(edited.contains("\"next_sequence\":" + token));
            byte[] bytes = edited.getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class, () -> ClosedPartialEpochCodec.decode(bytes));
        }
        ObjectNode missing = (ObjectNode) StrictJson.parse(raw); missing.remove("next_sequence");
        assertThrows(ContractViolationException.class, () -> ClosedPartialEpochCodec.decode(jsonBytes(missing)));
        ObjectNode extra = (ObjectNode) StrictJson.parse(raw); extra.put("alias", "predispatch");
        assertThrows(ContractViolationException.class, () -> ClosedPartialEpochCodec.decode(jsonBytes(extra)));
        for (String schema : List.of("xar.current-saved-readonly-prefix-unknown-epoch/v1", "xar.full-pre-dispatch-failure/v1")) {
            ObjectNode old = (ObjectNode) StrictJson.parse(raw); old.put("schema", schema);
            assertThrows(ContractViolationException.class, () -> ClosedPartialEpochCodec.decode(jsonBytes(old)));
        }
    }

    private static byte[] jsonBytes(JsonNode node) {
        try { return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(node); }
        catch (IOException error) { throw new java.io.UncheckedIOException(error); }
    }

    @Test void missingTaskAndDuplicateRolesAreRejected() throws Exception {
        ClosedPartialSources source = sources();
        assertThrows(ContractViolationException.class, () -> new ClosedPartialSources(source.sdkClosed(), source.gameExit(),
                source.supervisorClosed(), source.recordingClosed(), source.captureClosed(), source.screenReleased(),
                source.tasks().subList(0, 2), source.settledCycles()));
        ClosedPartialSources repeated = new ClosedPartialSources(source.sdkClosed(), source.gameExit(), source.supervisorClosed(),
                source.recordingClosed(), source.captureClosed(), source.screenReleased(),
                List.of(source.tasks().get(0), source.tasks().get(0), source.tasks().get(2)), source.settledCycles());
        assertThrows(ContractViolationException.class, () -> ClosedPartialEpochProducer.compose(input(), repeated));
    }

    @Test void SDKAndScreenAckCannotReplaceActualExitAndTerminal() throws Exception {
        ClosedPartialSources source = sources();
        ObjectNode sdk = (ObjectNode) StrictJson.parse(source.sdkClosed().bytes()); sdk.put("status", "ACK");
        RecoveryEvidence edited = evidence("/fixture-only/sdk-ack.json", jsonBytes(sdk));
        ClosedPartialSources bad = new ClosedPartialSources(edited, source.gameExit(), source.supervisorClosed(), source.recordingClosed(),
                source.captureClosed(), source.screenReleased(), source.tasks(), source.settledCycles());
        assertThrows(ContractViolationException.class, () -> ClosedPartialEpochProducer.compose(input(), bad));
        ObjectNode screen = (ObjectNode) StrictJson.parse(source.screenReleased().bytes());
        ((ObjectNode) screen.get("task")).put("state", "running");
        RecoveryEvidence ack = evidence("/fixture-only/screen-ack.json", jsonBytes(screen));
        ClosedPartialSources badScreen = new ClosedPartialSources(source.sdkClosed(), source.gameExit(), source.supervisorClosed(),
                source.recordingClosed(), source.captureClosed(), ack, source.tasks(), source.settledCycles());
        assertThrows(ContractViolationException.class, () -> ClosedPartialEpochProducer.compose(input(), badScreen));
    }

    @Test void sourceSubstitutionAndUnpublishedEpochAreRejected() throws Exception {
        ClosedFailureRecoveryInput input = input(); ClosedPartialSources source = sources();
        ClosedPartialEpochProducer.Produced produced = ClosedPartialEpochProducer.compose(input, source);
        ObjectNode altered = (ObjectNode) StrictJson.parse(produced.epochBytes()); altered.put("observed_at_utc", "2026-10-22T13:36:01Z");
        ClosedPartialAdmissionVerifier verifier = new ClosedPartialAdmissionVerifier(source,
                evidence("/fixture-only/changed-epoch.json", jsonBytes(altered)),
                evidence("/fixture-only/prefix.json", produced.prefixBytes()), ClosedPartialAdmissionVerifier.unavailableOriginalSdk());
        assertInstanceOf(RecoveryPrerequisiteVerifier.Rejected.class,
                verifier.verify(input, ClosedFailureRecoveryReducer.inputDigest(input)));
        byte[] raw = source.settledCycles().get(0).auto().raw(); raw[0] = '[';
        assertThrows(ContractViolationException.class,
                () -> new ClosedPartialRpcEvidence(source.settledCycles().get(0).auto().reference(), raw));
    }

    /** Synthetic SDK authority is confined to testing the pure projection, never reported as native qualification. */
    private static ClosedPartialAdmissionVerifier.OriginalSdkVerifier fixtureOnlySdk() {
        return (input, digest, epoch, prefix, sources) -> {
            JsonNode basis = StrictJson.parse(input.savedBasis().bytes());
            ExactRef validator = ExactRef.fromJson(basis.get("refs").get("checkpoint_validator"));
            ExactRef synthetic = new ExactRef("/fixture-only/NOT-ACTUAL-SDK-proof.json", 2,
                    RecoveryEvidence.sha256("{}".getBytes(StandardCharsets.UTF_8)));
            return new RecoveryPrerequisiteVerifier.Verified(digest, epoch.reference(), prefix.reference(), synthetic,
                    validator, RecoveryEvidence.sha256(StrictJson.canonical(basis.get("checkpoint"))),
                    input.currentDriver(), input.currentDriverIdentity(), input.currentSave(), input.currentSaveIdentity(),
                    sources.settledCycles().size(), 11558);
        };
    }

    @Test void syntheticSdkPureBasisRequiresExactCommittedReadbackAndRetainsSavedFrontier() throws Exception {
        ClosedFailureRecoveryInput input = input(); ClosedPartialSources sources = sources();
        ClosedPartialEpochProducer.Produced result = ClosedPartialEpochProducer.compose(input, sources);
        RecoveryEvidence epoch = evidence("/fixture-only/epoch.json", result.epochBytes());
        RecoveryEvidence prefix = evidence("/fixture-only/prefix.json", result.prefixBytes());
        ClosedPartialAdmissionVerifier provider = new ClosedPartialAdmissionVerifier(sources, epoch, prefix, fixtureOnlySdk());
        RecoveryPreview.Candidate recovery = assertInstanceOf(RecoveryPreview.Candidate.class,
                ClosedFailureRecoveryReducer.preview(input, provider));
        assertInstanceOf(ClosedPartialColdBasisPreview.Rejected.class,
                ClosedPartialColdBasisPreview.preview(input, sources, epoch, prefix, input.predecessor(), fixtureOnlySdk()));
        RecoveryEvidence readback = evidence("/fixture-only/NOT-ACTUAL-WRITER-committed.json", recovery.committedState());
        java.util.concurrent.atomic.AtomicInteger calls = new java.util.concurrent.atomic.AtomicInteger();
        ClosedPartialAdmissionVerifier.OriginalSdkVerifier counted = (value, digest, closed, settled, actualSources) -> {
            calls.incrementAndGet(); return fixtureOnlySdk().verifyCurrent(value, digest, closed, settled, actualSources);
        };
        ClosedPartialColdBasisPreview.Candidate proposal = assertInstanceOf(ClosedPartialColdBasisPreview.Candidate.class,
                ClosedPartialColdBasisPreview.preview(input, sources, epoch, prefix, readback, counted));
        assertEquals(1, calls.get(), "one current SDK verification per pure proposal; writer boundary revalidates independently");
        assertFalse(proposal.ready()); assertFalse(proposal.grantsColdLaunch());
        JsonNode basis = StrictJson.parse(proposal.proposedBasis()), old = StrictJson.parse(input.savedBasis().bytes());
        for (String field : List.of("frame", "origin", "checkpoint", "completed_cycles", "campaign_goal_anchor")) {
            assertEquals(old.get(field), basis.get(field));
        }
        assertEquals(5182, basis.get("completed_cycles").longValue()); assertEquals(11559, basis.get("next_sequence").longValue());
        assertEquals(readback.reference(), ExactRef.fromJson(basis.get("refs").get("ledger")));
        assertEquals("repair_required", StrictJson.parse(readback.bytes()).get("status").textValue());
        assertEquals(5190, StrictJson.parse(input.rawState().bytes()).get("pending_cycle").get("global_turn").longValue());
        JsonNode qualification = StrictJson.parse(proposal.proposalQualification());
        assertEquals(ClosedPartialColdBasisPreview.QUALIFICATION_SCHEMA, qualification.get("schema").textValue());
        assertEquals(0, qualification.get("new_game_day_credit").longValue());
    }
}
