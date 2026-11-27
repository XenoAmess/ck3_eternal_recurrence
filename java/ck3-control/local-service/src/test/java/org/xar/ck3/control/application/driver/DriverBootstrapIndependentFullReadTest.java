package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;

class DriverBootstrapIndependentFullReadTest {
    private static final String RECOVERY = "settled continuation independent native full-state read unavailable";
    private static final String ACK_REASON = "original fresh READ received negative Native ACK";

    @Test
    void source56Native131FailuresKeepTheOriginalReadStage() throws Exception {
        var submit = originalAck("full12-submit-rejected.json",
                "120111a27d227281e97edaaccda982e4d0d934f103f6cc22ebcaf7a9e7d2e4e2");
        var unavailable = originalAck("full14-raw-read-unavailable.json",
                "ad5f76b3e17e706e8c14d96bef961997277269db7f0f5f8bfc4a67589f9f7146");

        var submitFailure = fail(new NativeFreshSnapshotPort.Unavailable(submit, ACK_REASON));
        var rawFailure = fail(new NativeFreshSnapshotPort.Unavailable(unavailable, ACK_REASON));
        assertEquals(RECOVERY + "; kind=ACK/native_ok=false; request_id=" + submit.requestId()
                + "; reason=" + ACK_REASON + "; native_error=fresh_full_state_read_failed; native_stage=submit_rejected",
                submitFailure);
        assertEquals(RECOVERY + "; kind=ACK/native_ok=false; request_id=" + unavailable.requestId()
                + "; reason=" + ACK_REASON + "; native_error=fresh_full_state_read_failed; native_stage=raw_read_unavailable",
                rawFailure);
    }

    @Test
    void completedSoftwareCallbackExplainsTheOriginalRawReadFailure() throws Exception {
        var body = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                .put("request_id", "fresh-software-event").put("ok", false).put("error", "fresh_full_state_read_failed");
        var diagnostic = body.putObject("fresh_full_state_diagnostic")
                .put("schema", "xar.native.fresh-full-state-diagnostic/v1").put("stage", "raw_read_unavailable")
                .put("fresh_available", false).put("query_sequence", "701");
        var callback = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, StrictJson.parse(
                fixture("software-event-callback-cause.json",
                        "22c6f5da0fd8e6c598086914e368983b223e8a723da443fe284b298944f4f420"), 4096));
        diagnostic.set("callback_cause81", callback);
        var prefix = RECOVERY + "; kind=ACK/native_ok=false; request_id=fresh-software-event; reason=" + ACK_REASON
                + "; native_error=fresh_full_state_read_failed; native_stage=raw_read_unavailable";

        assertEquals(prefix + "; native_full_stage=event; native_full_reason=current111_ordinary_event_gui_scene_unavailable",
                fail(new NativeFreshSnapshotPort.Unavailable(negativeAck(ContinuityJson.canonical(body)), ACK_REASON)));
        callback.put("ticket_sequence", "702");
        assertEquals(prefix, fail(new NativeFreshSnapshotPort.Unavailable(negativeAck(ContinuityJson.canonical(body)), ACK_REASON)));
    }

    @Test
    void transportAndBeforeDispatchFailuresNeverAcquireASyntheticNativeStage() {
        var beforeWrite = new NativeActionPort.RejectedBeforeDispatch("fresh-before-write",
                new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,
                        0, "actual source unavailable before write", Optional.empty()));
        var unknown = new NativeActionPort.Unknown("fresh-budget", "frame read budget",
                new byte[0], Optional.empty(), Optional.of(new NativeActionPort.FailureCause(
                        NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED, NativeActionPort.FailureStage.RESPONSE_WAIT,
                        Optional.empty(), Optional.empty(), Optional.empty())));
        assertEquals(RECOVERY + "; kind=REJECTED_BEFORE_DISPATCH; request_id=fresh-before-write"
                + "; reason=actual source unavailable before write",
                fail(new NativeFreshSnapshotPort.Unavailable(beforeWrite, beforeWrite.proof().reason())));
        assertEquals(RECOVERY + "; kind=UNKNOWN; request_id=fresh-budget; reason=frame read budget"
                + "; transport_failure=FRAME_BUDGET_EXHAUSTED/RESPONSE_WAIT",
                fail(new NativeFreshSnapshotPort.Unavailable(unknown, unknown.reason())));
    }

    @Test
    void anUnboundPacketCannotSupplyTheNativeStage() throws Exception {
        var original = originalAck("full14-raw-read-unavailable.json",
                "ad5f76b3e17e706e8c14d96bef961997277269db7f0f5f8bfc4a67589f9f7146");
        var unbound = new NativeActionPort.AckReceived("another-read", false, original.originalResultToken(),
                original.originalFrame(), original.originalPacket());
        assertEquals(RECOVERY + "; kind=ACK/native_ok=false; request_id=another-read; reason=" + ACK_REASON,
                fail(new NativeFreshSnapshotPort.Unavailable(unbound, ACK_REASON)));
    }

    @Test
    void committedSeedReadsValidPinnedJsonWithAnotherJvmMemberOrder() throws IOException {
        var game = new GameGeneration(61127, new PythonOnlyUInt64(BigInteger.valueOf(134401544348311914L)));
        var owner = new SessionIdentity("software-writer", game, "successor");
        var full = new ExactRef(Path.of("driver.json").toAbsolutePath().toString(), 2, "a".repeat(64));
        var history = new ExactRef(Path.of("history.json").toAbsolutePath().toString(), 2, "b".repeat(64));
        var expected = new DriverSnapshotFacts.RestoreSeedSupplement("committed-restore", full, 3, 1, owner,
                history, DriverJson.object(new byte[]{'{', '}'}, 2), Optional.empty());
        var object = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, StrictJson.parse(expected.encode(), 4096));
        var schema = object.remove("schema");
        object.set("schema", schema);
        byte[] pinned = org.xar.ck3.control.contracts.FullJsonTree.encode(object, 4096);
        assertFalse(java.util.Arrays.equals(pinned, expected.encode()));
        var pin = new WriterContracts.Pin(new ExactRef(Path.of("seed.json").toAbsolutePath().toString(), pinned.length,
                DriverJson.sha256(pinned)), new WriterContracts.FileIdentity("1", "2", "1", "2026-11-27T00:00:00Z", pinned.length));

        var state = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", owner.machineId())
                .put("sequence", 0).put("window_id", 1).put("status", "running").put("target_days", 365)
                .put("start_date_raw", 1008).put("target_date_raw", 9768).put("last_settled_date_raw", 1008).put("last_settled_cycles", 0);
        state.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD, history.toJson());
        var before = ContinuityState.fromJson(state, owner.machineId());
        var details = StrictJson.object().put("evidence_id", expected.requestId()).put("source", "java_saved_checkpoint_restore_v1");
        details.set(DriverSnapshotFacts.RestoreSeedSupplement.DETAIL_FIELD, pin.toJson());
        details.set("driver_after_game", game.toJson());
        details.set("restored_full_driver", full.toJson());
        details.putObject("driver_snapshot").put("expected_version", 2).put("expected_epoch", 1).put("next_epoch", 1)
                .put("before_sha256", "c".repeat(64)).put("after_sha256", full.sha256());
        var request = new WriterContracts.Request(SavedAttachmentAuthority.KIND, ContinuityJson.canonical(details), List.of());
        state.put("sequence", 1).put("last_event_identity", request.identity()).set("game_binding", game.toJson());
        var after = ContinuityState.fromJson(state, owner.machineId());
        var edge = new WriterContracts.HistoricalTransition(1, request.kind(), request.details(), request.identity(), before, after, pin);
        var head = new WriterContracts.Head(after, List.of(), List.of(), List.of(), false);
        var same = (ContinuityStorePort.Session) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{ContinuityStorePort.Session.class}, (ignored, method, arguments) -> {
                    if (method.getName().equals("head")) return head;
                    if (method.getName().equals("readPinned")) {
                        assertEquals(pin, arguments[0]);
                        return pinned.clone();
                    }
                    throw new UnsupportedOperationException(method.getName());
                });
        assertEquals(expected, DriverBootstrap.readCommittedImportedSeed(same, edge, owner));
    }

    private static String fail(NativeFreshSnapshotPort.Unavailable original) {
        var failure = assertThrowsExactly(IOException.class,
                () -> DriverBootstrap.requireIndependentFullRead(original, RECOVERY));
        assertNull(failure.getCause());
        return failure.getMessage();
    }

    /** Source56 Recovery04 archived ACK payloads. Framing is mechanical and supplies no live custody. */
    private static NativeActionPort.AckReceived originalAck(String filename, String sha256) throws Exception {
        return negativeAck(fixture(filename, sha256));
    }

    private static byte[] fixture(String filename, String sha256) throws Exception {
        byte[] payload;
        try (var input = DriverBootstrapIndependentFullReadTest.class.getResourceAsStream(
                "/source56-independent-recovery/" + filename)) {
            assertNotNull(input);
            payload = input.readAllBytes();
        }
        assertEquals(sha256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(payload)));
        return payload;
    }

    private static NativeActionPort.AckReceived negativeAck(byte[] payload) throws IOException {
        byte[] packet = ByteBuffer.allocate(payload.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(payload.length).put(payload).array();
        var original = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(packet));
        assertFalse(original.nativeOk());
        return new NativeActionPort.AckReceived(original.requestId(), original.nativeOk(),
                Optional.empty(), new RawJson(payload), packet);
    }
}
