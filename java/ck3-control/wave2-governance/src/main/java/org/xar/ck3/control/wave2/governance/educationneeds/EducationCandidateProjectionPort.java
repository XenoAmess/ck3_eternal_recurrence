package org.xar.ck3.control.wave2.governance.educationneeds;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.*;

/** Projects the observed native final pair; Ready and CanSend remain independent facts. */
public final class EducationCandidateProjectionPort implements ProjectionPort<EducationCandidateProjectionPort.Input, EducationCandidateProjectionPort.Result> {
    public static final String SCHEMA = "xar.education-candidate-projection-input/v1";
    public record Input(NeedsRowProjection needs, OrdinaryContext context) {
        public Input { Objects.requireNonNull(needs); Objects.requireNonNull(context); }
    }
    public record Result(RequestCandidate candidate, WireValue originalRoles) {
        public Result { Objects.requireNonNull(candidate); Objects.requireNonNull(originalRoles); }
    }
    @Override public ProjectionOperation operation() { return ProjectionOperation.EDUCATION_CANDIDATE; }
    @Override public int inputMaximumBytes() { return 8_388_608; }
    @Override public int outputMaximumBytes() { return 8_388_608; }
    @Override public Input decode(byte[] rawPayload) {
        JsonNode root = StrictJson.object(EducationNeedsCodec.parse(rawPayload), Set.of("schema", "needs", "context"));
        StrictJson.require(SCHEMA.equals(EducationNeedsCodec.text(EducationNeedsCodec.field(root, "schema"))), "education candidate schema");
        return new Input(EducationNeedsComposer.needsRowProjection(EducationNeedsCodec.encode(EducationNeedsCodec.field(root, "needs"))),
                EducationNeedsCodec.ordinary(EducationNeedsCodec.encode(EducationNeedsCodec.field(root, "context"))));
    }
    @Override public Result project(Input input) {
        return new Result(EducationNeedsComposer.deriveCandidate(input.needs(), input.context()), input.context().rolesWire());
    }
    @Override public byte[] encode(Result result) {
        return EducationNeedsCodec.encode(EducationNeedsComposer.candidate(result.candidate(), result.originalRoles()));
    }
}
