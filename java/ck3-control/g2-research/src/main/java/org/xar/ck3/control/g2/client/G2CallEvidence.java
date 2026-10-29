package org.xar.ck3.control.g2.client;

import java.net.URI;
import java.time.Instant;
import java.util.Objects;
import java.util.OptionalInt;

/** Actual byte measurements, with a bounded prefix separate from full-body status. */
public record G2CallEvidence(
        URI endpoint, String requestId, Instant startedAtUtc, Instant completedAtUtc,
        long elapsedNanos, long requestBytes, String requestSha256,
        long observedResponseBytes, int retainedResponseBytes, String retainedResponseSha256,
        OptionalInt httpStatus, boolean responseComplete, boolean actualHttpInvoked) {
    public G2CallEvidence {
        Objects.requireNonNull(endpoint, "endpoint");
        Objects.requireNonNull(requestId, "requestId");
        Objects.requireNonNull(startedAtUtc, "startedAtUtc");
        Objects.requireNonNull(completedAtUtc, "completedAtUtc");
        Objects.requireNonNull(requestSha256, "requestSha256");
        Objects.requireNonNull(retainedResponseSha256, "retainedResponseSha256");
        Objects.requireNonNull(httpStatus, "httpStatus");
        if (elapsedNanos < 0 || requestBytes < 0 || observedResponseBytes < 0
                || retainedResponseBytes < 0 || retainedResponseBytes > observedResponseBytes
                || responseComplete && (retainedResponseBytes != observedResponseBytes || httpStatus.isEmpty())
                || !actualHttpInvoked && (httpStatus.isPresent() || responseComplete || observedResponseBytes != 0)
                || httpStatus.isPresent() && (httpStatus.getAsInt() < 100 || httpStatus.getAsInt() > 599)
                || !requestSha256.matches("[0-9a-f]{64}")
                || !retainedResponseSha256.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("invalid measured evaluation-call evidence");
        }
    }
}
