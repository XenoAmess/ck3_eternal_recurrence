package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.service.mcp.NormalExitPublicCodec;

/** Native owned-memory software producer/serializer samples, never Game, pipe, mailbox or OS-exit evidence. */
final class NormalExitClaimCompatibilityTest {
    private static final Binding B = new Binding(BigInteger.valueOf(72), BigInteger.valueOf(9301),
            BigInteger.valueOf(43), BigInteger.valueOf(8), new BigInteger("133000000000000043"), "b".repeat(64));
    private static final Dispatch NONE = new Dispatch(false, false, false, false, false);

    @Test void actualNativeSoftwareProducerUnknownPacketsKeepClaimAndCannotCompleteThePhase() throws Exception {
        var stream = getClass().getResourceAsStream("/normal-exit/native-software-autosave-unknown.jsonl");
        assertNotNull(stream, "retained actual Native software producer/serializer samples are required");
        int count = 0;
        try (var lines = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            for (String line; (line = lines.readLine()) != null;) {
                if (line.isBlank()) continue;
                var frame = assertInstanceOf(NativeWire.CommandResult.class,
                        NativeWire.decode(NativeWire.packet(line.getBytes(StandardCharsets.UTF_8))));
                assertTrue(frame.nativeOk(), "outer ACK is separate from semantic UNKNOWN");
                var ack = decodeObservation(StrictJson.parse(frame.result().token().orElseThrow().value()),
                        B, Action.DISABLE_EXIT_AUTOSAVE);
                assertEquals(Status.DISPATCH_UNKNOWN_CLAIMED, ack.status());
                assertFalse(ack.proof().frame());
                var autosave = ack.exitAutosave().orElseThrow();
                assertTrue(autosave.disableClaimed());
                assertTrue(autosave.invoked());
                assertFalse(ack.autosaveVerified());
                assertFalse(ack.orderlyExitVerified());
                assertEquals(ack, decodeObservation(observationJson(ack), B, Action.DISABLE_EXIT_AUTOSAVE));
                assertTrue(RootNormalExitRuntime.phaseOutcome(Action.DISABLE_EXIT_AUTOSAVE, ack, readyQuery()).isEmpty());
                var memory = StrictJson.object().put("schema", "ck3-normal-exit-request-result-v1")
                        .put("action", "disable_exit_autosave").put("status", "dispatch_unknown_claimed")
                        .put("public_revision", B.nativeRevision()).put("process_creation_filetime_100ns", B.creationFiletime())
                        .put("source_inventory_sha256", B.sourceInventorySha256()).put("claim_consumed", true)
                        .put("retry_authorized", false).put("autosave_verified", false).put("orderly_exit_verified", false)
                        .put("process_exit_observed", false).put("typed_normal_exit_observed", false)
                        .put("request_id", frame.requestId()).put("claim_path", "D:/software-fixture/retained-original")
                        .put("uses_desktop_input", false).put("uses_ocr", false).put("native_submission_count", 1);
                memory.set("native_observation", observationJson(ack));
                var publicValue = NormalExitPublicCodec.fromMemory(new RawJson(StrictJson.canonical(memory)));
                var roundTrip = NormalExitPublicCodec.decode(NormalExitPublicCodec.encode(publicValue), Optional.of(B.creationFiletime()));
                var retained = StrictJson.parse(roundTrip.memory().bytes());
                assertTrue(retained.get("claim_consumed").booleanValue());
                assertFalse(retained.get("retry_authorized").booleanValue());
                assertEquals("dispatch_unknown_claimed", retained.get("status").textValue());
                count++;
            }
        }
        assertEquals(3, count);
    }

    @Test void claimedUnknownWithResidualModalProofCannotConfirmPreparation() {
        for (Action action : List.of(Action.PREPARE_CONFIRMATION, Action.CONTINUE_PREPARATION)) {
            var dispatches = action == Action.PREPARE_CONFIRMATION
                    ? List.of(new Dispatch(true, true, true, true, true), NONE, NONE)
                    : List.of(NONE, new Dispatch(true, true, true, true, true), NONE);
            var good = new Observation(B, action, Status.CONFIRMATION_OBSERVED, BigInteger.ONE,
                    new Proof(true, true, true, true, true, true, true), true, true, false, false,
                    "a".repeat(64), "controlled protocol DATA", readyQuery().targets(), dispatches,
                    List.of(true, true, false), Optional.empty());
            assertTrue(RootNormalExitRuntime.phaseOutcome(action, good, readyQuery()).isPresent());
            var unknown = observationJson(good);
            unknown.put("status", "dispatch_unknown_claimed");
            var completeLegacyUnknown = decodeObservation(unknown, B, action);
            assertTrue(RootNormalExitRuntime.phaseOutcome(action, completeLegacyUnknown, readyQuery()).isPresent(),
                    "retain existing complete-proof original plus independent observed context behavior");
            unknown.put("status", "dispatch_unknown_claimed").put("frame_verified", false).put("exit_context_signature", "");
            var decoded = decodeObservation(unknown, B, action);
            assertTrue(RootNormalExitRuntime.phaseOutcome(action, decoded, readyQuery()).isEmpty());
        }
    }

    @Test void conclusiveStatusStillRequiresCompleteProofAndQueryHistoricalClaimGrantsNoMutation() {
        var query = readyQuery();
        assertTrue(query.exitAutosave().orElseThrow().disableClaimed());
        assertFalse(query.exitAutosave().orElseThrow().invoked());
        assertFalse(query.continuePreparationReady());
        var invalid = observationJson(query);
        invalid.put("frame_verified", false);
        assertThrows(IllegalArgumentException.class, () -> decodeObservation(invalid, B, Action.QUERY_CONTEXT));
        var disabled = observationJson(query);
        disabled.put("action", "disable_exit_autosave").put("status", "autosave_disabled")
                .put("context_signature_verified", true).put("frame_verified", false);
        ((ObjectNode) disabled.get("exit_autosave")).put("dispatch_invoked", true).put("postcondition_observed", true);
        assertThrows(IllegalArgumentException.class, () -> decodeObservation(disabled, B, Action.DISABLE_EXIT_AUTOSAVE));
    }

    @Test void completeProofUnknownStillNeedsItsOriginalSignatureAndPositiveEpochToConfirmPhase() {
        var query = readyQuery();
        for (Action action : List.of(Action.PREPARE_CONFIRMATION, Action.CONTINUE_PREPARATION)) {
            var dispatches = action == Action.PREPARE_CONFIRMATION
                    ? List.of(new Dispatch(true, true, true, true, true), NONE, NONE)
                    : List.of(NONE, new Dispatch(true, true, true, true, true), NONE);
            var original = new Observation(B, action, Status.DISPATCH_UNKNOWN_CLAIMED, BigInteger.ONE,
                    query.proof(), true, true, false, false, "a".repeat(64), "controlled protocol DATA",
                    query.targets(), dispatches, List.of(true, true, false), Optional.empty());
            var noSignature = observationJson(original);
            noSignature.put("exit_context_signature", "");
            assertTrue(RootNormalExitRuntime.phaseOutcome(action, decodeObservation(noSignature, B, action), query).isEmpty());
            var noEpoch = observationJson(original);
            noEpoch.put("pump_epoch", 0);
            assertTrue(RootNormalExitRuntime.phaseOutcome(action, decodeObservation(noEpoch, B, action), query).isEmpty());
        }
    }

    private static Observation readyQuery() {
        var target = new Target(true, true, true, true, true, true, true, true, BigInteger.ONE);
        return new Observation(B, Action.QUERY_CONTEXT, Status.CONTEXT_OBSERVED, BigInteger.ONE,
                new Proof(true, true, true, true, true, true, true), false, true, false, false,
                "a".repeat(64), "controlled independent protocol DATA only", List.of(target, target, target),
                List.of(NONE, NONE, NONE), List.of(true, true, false),
                Optional.of(new Autosave(true, true, true, false, true, false, false)));
    }
}
