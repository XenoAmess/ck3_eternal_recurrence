package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
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

    private static String fail(NativeFreshSnapshotPort.Unavailable original) {
        var failure = assertThrowsExactly(IOException.class,
                () -> DriverBootstrap.requireIndependentFullRead(original, RECOVERY));
        assertNull(failure.getCause());
        return failure.getMessage();
    }

    /** Source56 Recovery04 archived ACK payloads. Framing is mechanical and supplies no live custody. */
    private static NativeActionPort.AckReceived originalAck(String filename, String sha256) throws Exception {
        byte[] payload;
        try (var input = DriverBootstrapIndependentFullReadTest.class.getResourceAsStream(
                "/source56-independent-recovery/" + filename)) {
            assertNotNull(input);
            payload = input.readAllBytes();
        }
        assertEquals(sha256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(payload)));
        byte[] packet = ByteBuffer.allocate(payload.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(payload.length).put(payload).array();
        var original = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(packet));
        assertFalse(original.nativeOk());
        return new NativeActionPort.AckReceived(original.requestId(), original.nativeOk(),
                Optional.empty(), new RawJson(payload), packet);
    }
}
