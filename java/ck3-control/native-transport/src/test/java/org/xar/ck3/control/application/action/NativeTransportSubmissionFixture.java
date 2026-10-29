package org.xar.ck3.control.application.action;

import java.time.Instant;

/** Controlled transport regression issuer only. Never selected into a production module. */
public final class NativeTransportSubmissionFixture {
    private NativeTransportSubmissionFixture() { }
    public static SubmissionPermit issue(ActionCommand command, GuardEvidence guard, NativeRequest request, String requestId) {
        return new SubmissionPermit(command, "a".repeat(64), 1, requestId, Instant.now(), guard, request);
    }
}
