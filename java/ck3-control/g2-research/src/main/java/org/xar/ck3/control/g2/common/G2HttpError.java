package org.xar.ck3.control.g2.common;

import java.util.Objects;

public record G2HttpError(String schema, Code code, String message) {
    public static final String SCHEMA = "xar.g2-research-http-error/v1";
    public enum Code {
        MALFORMED_REQUEST(400), PAYLOAD_TOO_LARGE(413), DOMAIN_REJECTED(422), SOURCE_MISMATCH(409),
        ENGINE_UNAVAILABLE(503), INTERNAL_FAILURE(500), INVALID_RESULT(500);
        private final int status;
        Code(int status) { this.status = status; }
        public int httpStatus() { return status; }
    }
    public G2HttpError {
        if (!SCHEMA.equals(schema)) throw new IllegalArgumentException("exact G2 error schema required");
        Objects.requireNonNull(code);
        if (message == null || message.isBlank() || message.length() > 512) throw new IllegalArgumentException("bounded G2 error message required");
        G2Request.requireUnicode(message);
    }
}
