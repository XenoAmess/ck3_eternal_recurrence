package org.xar.ck3.control.contracts.projection;

import java.util.Objects;
import java.util.Locale;

public record ProjectionError(Code code, String message) {
    public enum Code {
        INVALID_ENVELOPE, UNSUPPORTED_VERSION, UNSUPPORTED_OPERATION, OPERATION_UNAVAILABLE,
        PAYLOAD_TOO_LARGE, INVALID_PAYLOAD, DOMAIN_REJECTED, PROJECTION_FAILED, INVALID_RESULT;

        public String wire() { return name().toLowerCase(Locale.ROOT).replace('_', '-'); }

        public static Code fromWire(String wire) {
            for (Code code : values()) {
                if (code.wire().equals(wire)) { return code; }
            }
            throw ProjectionJson.invalid("unknown projection error code");
        }
    }
    public ProjectionError {
        Objects.requireNonNull(code); Objects.requireNonNull(message);
        if (message.isEmpty() || message.length() > 512) {
            throw new IllegalArgumentException("bounded projection error message required");
        }
        for (int i = 0; i < message.length(); i++) {
            char c = message.charAt(i);
            if (Character.isHighSurrogate(c)) {
                if (i + 1 >= message.length() || !Character.isLowSurrogate(message.charAt(++i))) {
                    throw new IllegalArgumentException("invalid error Unicode");
                }
            } else if (Character.isLowSurrogate(c)) { throw new IllegalArgumentException("invalid error Unicode"); }
        }
    }
}
