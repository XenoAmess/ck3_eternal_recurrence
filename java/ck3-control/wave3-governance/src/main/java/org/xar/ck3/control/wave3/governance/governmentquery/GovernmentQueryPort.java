package org.xar.ck3.control.wave3.governance.governmentquery;

import java.math.BigInteger;
import java.util.Objects;

/** Value-only request/receipt admission for the existing single native reader. */
public final class GovernmentQueryPort {
    public static final String STEP = "query-government-runtime-adapter-v1";
    private GovernmentQueryPort() { }

    public enum Rejection {
        QUERY_DISABLED, INVALID_EXPECTED_REVISION, LIVING_PAUSED_FRAME_REQUIRED,
        COMMAND_RESULT_UNAVAILABLE, ENVELOPE_MALFORMED, SOURCE_UNAVAILABLE, CROSSED_PAUSED_FRAME
    }

    public static final class QueryRejectedException extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        private final Rejection rejection;
        QueryRejectedException(Rejection rejection, String message) { super(message); this.rejection = rejection; }
        public Rejection rejection() { return rejection; }
    }

    public record NativeRequest(String requestId, BigInteger expectedNativeRevision) {
        public NativeRequest {
            Objects.requireNonNull(requestId); Objects.requireNonNull(expectedNativeRevision);
            if (requestId.isEmpty() || requestId.length() > 128 || expectedNativeRevision.signum() <= 0) {
                throw new IllegalArgumentException("bounded request identity and positive native revision required");
            }
        }
    }

    record SourceFrame(BigInteger publicRevision, BigInteger nativeRevision, BigInteger dateRaw,
            boolean paused, boolean mapReady, boolean actorObject, boolean actorAlive, String snapshotId) { }

    static NativeRequest prepare(boolean enabled, BigInteger expectedRevision, String requestId, SourceFrame before) {
        require(enabled, Rejection.QUERY_DISABLED, "private government runtime adapter query is disabled");
        require(expectedRevision != null && expectedRevision.signum() > 0, Rejection.INVALID_EXPECTED_REVISION,
                "expected_revision must be positive");
        require(Objects.equals(before.publicRevision(), expectedRevision) && before.paused() && before.mapReady()
                && before.actorObject() && before.actorAlive() && before.nativeRevision() != null && before.nativeRevision().signum() > 0,
                Rejection.LIVING_PAUSED_FRAME_REQUIRED, "government runtime adapter requires a living paused player");
        return new NativeRequest(requestId, before.nativeRevision());
    }

    static void require(boolean condition, Rejection rejection, String reason) {
        if (!condition) { throw new QueryRejectedException(rejection, reason); }
    }
}
