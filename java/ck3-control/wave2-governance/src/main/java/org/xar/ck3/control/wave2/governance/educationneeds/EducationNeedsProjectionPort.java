package org.xar.ck3.control.wave2.governance.educationneeds;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.*;

/** Host application port over the single original-needs Java implementation. */
public final class EducationNeedsProjectionPort implements ProjectionPort<Request, EducationNeedsProjectionPort.Result> {
    public record Result(List<NeedsRowProjection> rows, WireValue body) {
        public Result { rows = List.copyOf(rows); Objects.requireNonNull(body); }
    }
    @Override public ProjectionOperation operation() { return ProjectionOperation.EDUCATION_NEEDS; }
    @Override public int inputMaximumBytes() { return 8_388_608; }
    @Override public int outputMaximumBytes() { return 8_388_608; }
    @Override public Request decode(byte[] rawPayload) { return EducationNeedsCodec.request(rawPayload); }
    @Override public Result project(Request input) {
        var body = EducationNeedsComposer.emit(input);
        List<NeedsRowProjection> rows = input.decision() == null ? List.of()
                : input.decision().children().stream().map(Child::projection).toList();
        return new Result(rows, EducationNeedsCodec.wire(body));
    }
    @Override public byte[] encode(Result result) { return result.body().bytes(); }
}
