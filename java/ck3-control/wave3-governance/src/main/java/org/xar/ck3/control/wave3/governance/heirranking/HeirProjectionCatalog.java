package org.xar.ck3.control.wave3.governance.heirranking;

import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave3.governance.heirdiagnostic.HeirCandidateDiagnosticConsumerPort;
import org.xar.ck3.control.wave3.governance.heirintake.HeirCandidateIntakeConsumerPort;

/** The existing unique codecs enter the resident host through their validated immutable request types. */
public final class HeirProjectionCatalog implements ProjectionPortCatalog {
    public HeirProjectionCatalog() { }

    @Override public List<RegisteredProjection> registrations() {
        return List.of(
                RegisteredProjection.of(new DomainPort<>(ProjectionOperation.GOVERNANCE_HEIR_INTAKE,
                        HeirCandidateIntakeConsumerPort::decode, HeirCandidateIntakeConsumerPort::evaluate,
                        HeirCandidateIntakeConsumerPort.Evaluation::result)),
                RegisteredProjection.of(new DomainPort<>(ProjectionOperation.GOVERNANCE_HEIR_RANK,
                        HeirCandidateRankingConsumerPort::decode, HeirCandidateRankingConsumerPort::evaluate,
                        HeirCandidateRankingConsumerPort.Evaluation::choices)),
                RegisteredProjection.of(new DomainPort<>(ProjectionOperation.GOVERNANCE_HEIR_DIAGNOSTIC,
                        HeirCandidateDiagnosticConsumerPort::decode, HeirCandidateDiagnosticConsumerPort::evaluate,
                        HeirCandidateDiagnosticConsumerPort.Evaluation::diagnostic)));
    }

    private record DomainPort<I, O>(ProjectionOperation operation, Function<byte[], I> inputDecoder,
            Function<I, O> projector, Function<O, byte[]> encoder) implements ProjectionPort<I, O> {
        private DomainPort {
            Objects.requireNonNull(operation); Objects.requireNonNull(inputDecoder);
            Objects.requireNonNull(projector); Objects.requireNonNull(encoder);
        }
        @Override public I decode(byte[] rawPayload) {
            // Only the unique consumed-field decoder's established contract exception is a public refusal.
            // Project/encode are outside this catch: indexing, serializer and policy bugs remain HTTP 500.
            try { return inputDecoder.apply(rawPayload); }
            catch (ContractViolationException rejectedInput) {
                throw new ProjectionDomainRejection(rejectedInput.getMessage());
            }
        }
        @Override public O project(I input) { return projector.apply(input); }
        @Override public byte[] encode(O result) { return encoder.apply(result); }
        @Override public int inputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
        @Override public int outputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
    }
}
