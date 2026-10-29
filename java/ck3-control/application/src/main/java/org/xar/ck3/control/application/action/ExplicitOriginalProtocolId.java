package org.xar.ck3.control.application.action;

import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original caller ID from a closed migrated tool contract. Construction does not grant nonce or submit permission. */
public record ExplicitOriginalProtocolId(Contract contract, String value, ExactRef producerSource) implements ProtocolRequestIdentity {
    public enum Contract {
        PUBLIC_COUNCIL_ASSIGNMENT("xar.java.public-council-assignment/v1", new OperationKey("private-assign-councillor-v1"));
        private final String schema; private final OperationKey operation;
        Contract(String schema, OperationKey operation) { this.schema = schema; this.operation = operation; }
        public String schema() { return schema; }
        public OperationKey operation() { return operation; }
    }
    public ExplicitOriginalProtocolId {
        Objects.requireNonNull(contract); Objects.requireNonNull(producerSource);
        StrictJson.require(value != null && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"), "original Council protocol ID token required");
        StrictJson.require(producerSource.bytes() > 0 && Path.of(producerSource.path()).isAbsolute(), "actual source-bound caller contract file required");
    }
}
