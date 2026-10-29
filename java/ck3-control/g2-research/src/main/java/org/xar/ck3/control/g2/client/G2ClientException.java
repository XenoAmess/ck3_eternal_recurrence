package org.xar.ck3.control.g2.client;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.g2.common.G2HttpError;

/** A local transport outcome; it never changes the common domain response schema. */
public final class G2ClientException extends RuntimeException {
    @java.io.Serial private static final long serialVersionUID = 1L;
    public enum Reason {
        LOCAL_REQUEST_INVALID, LOCAL_DEADLINE_EXPIRED, HTTP_REJECTED, TRANSPORT_UNKNOWN,
        RESPONSE_UNVERIFIED, RESPONSE_LIMIT_EXCEEDED
    }

    private final Reason reason;
    private final transient G2CallEvidence evidence;
    private final transient G2HttpError httpError;
    private final byte[] responseBytes;

    public G2ClientException(Reason reason, String message, G2CallEvidence evidence,
            G2HttpError httpError, byte[] responseBytes, Throwable cause) {
        super(message, cause);
        this.reason = Objects.requireNonNull(reason, "reason");
        this.evidence = Objects.requireNonNull(evidence, "evidence");
        this.httpError = httpError;
        this.responseBytes = Objects.requireNonNull(responseBytes, "responseBytes").clone();
        if ((reason == Reason.HTTP_REJECTED) != (httpError != null)) {
            throw new IllegalArgumentException("only a verified HTTP refusal carries the common typed error");
        }
        if (httpError != null && (!evidence.actualHttpInvoked() || !evidence.responseComplete()
                || evidence.httpStatus().orElse(-1) != httpError.code().httpStatus())) {
            throw new IllegalArgumentException("verified common refusal requires matching complete actual HTTP status");
        }
        boolean local = reason == Reason.LOCAL_REQUEST_INVALID || reason == Reason.LOCAL_DEADLINE_EXPIRED;
        if (local == evidence.actualHttpInvoked()) {
            throw new IllegalArgumentException("local request failure and attempted HTTP failure must remain distinct");
        }
    }

    public Reason reason() { return reason; }
    public G2CallEvidence evidence() { return evidence; }
    public Optional<G2HttpError> httpError() { return Optional.ofNullable(httpError); }
    public byte[] responseBytes() { return responseBytes.clone(); }
}
