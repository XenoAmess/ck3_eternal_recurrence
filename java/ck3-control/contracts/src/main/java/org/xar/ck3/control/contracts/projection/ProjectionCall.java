package org.xar.ck3.control.contracts.projection;

import java.util.Objects;

public record ProjectionCall(Identity identity, ProjectionJson payload) {
    public static final String SCHEMA = "xar.projection-call/v1";
    public static final int SCHEMA_VERSION = 1;
    public record Identity(String requestId, ProjectionOperation operation) {
        public Identity {
            Objects.requireNonNull(requestId); Objects.requireNonNull(operation);
            if (!requestId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")) {
                throw ProjectionJson.invalid("bounded projection correlation ID required");
            }
        }
    }
    public ProjectionCall {
        Objects.requireNonNull(identity); Objects.requireNonNull(payload);
        if (!payload.isObject()) { throw ProjectionJson.invalid("projection payload must be an object"); }
    }
}
