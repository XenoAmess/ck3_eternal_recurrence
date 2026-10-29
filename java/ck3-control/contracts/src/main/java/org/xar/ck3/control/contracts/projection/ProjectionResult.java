package org.xar.ck3.control.contracts.projection;

import java.util.Objects;
import java.util.Optional;

public sealed interface ProjectionResult permits ProjectionResult.Succeeded, ProjectionResult.Rejected {
    String SCHEMA = "xar.projection-result/v1";
    record Succeeded(ProjectionCall.Identity identity, ProjectionJson result) implements ProjectionResult {
        public Succeeded { Objects.requireNonNull(identity); Objects.requireNonNull(result); }
    }
    record Rejected(Optional<ProjectionCall.Identity> identity, ProjectionError error) implements ProjectionResult {
        public Rejected {
            Objects.requireNonNull(identity); Objects.requireNonNull(error);
            if (identity.isEmpty()) {
                switch (error.code()) {
                    case INVALID_ENVELOPE, UNSUPPORTED_VERSION, UNSUPPORTED_OPERATION -> { }
                    default -> throw new IllegalArgumentException("projection business and execution rejections require request identity");
                }
            }
        }
    }
}
