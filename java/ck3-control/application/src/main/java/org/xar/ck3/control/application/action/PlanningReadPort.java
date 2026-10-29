package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.util.Optional;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

public interface PlanningReadPort {
    /** Observation of one actual failed READ, inside its original writer callback; never a new read permission. */
    @FunctionalInterface interface FailureEvidenceObserver {
        void failed(Session same, ReadContract<?> identical, PlanningReadRequest actual,
                PlanningReadResult.Unavailable<?> exact,
                Optional<PlanningReadCoordinator.FailedReadAttempt> attempted,
                ActionPorts.OutcomeArchive originals) throws IOException;
    }
    default <T> PlanningReadResult<T> readWithFailureEvidence(ReadContract<T> contract,
            PlanningReadRequest request, FailureEvidenceObserver observer) {
        throw new IllegalStateException("original failed-read evidence observation is not installed");
    }
    default <T> PlanningReadResult<T> readWithFailureEvidence(Session borrowed, ReadContract<T> contract,
            PlanningReadRequest request, FailureEvidenceObserver observer) {
        throw new IllegalStateException("same-writer failed-read evidence observation is not installed");
    }

    default <T> PlanningReadResult<T> read(Session borrowed, ReadContract<T> contract, PlanningReadRequest request) {
        throw new IllegalStateException("same-writer planning read is not installed");
    }
    <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request);

    /** Optional capability. No caller-created request/UNKNOWN can mint an original-read ticket. */
    default <T> PlanningReadAttempt<T> readOriginal(ReadContract<T> contract, PlanningReadRequest request) {
        throw new IllegalStateException("original planning-read custody is not installed");
    }
    default <T> PlanningReadAttempt<T> readOriginal(Session borrowed, ReadContract<T> contract, PlanningReadRequest request) {
        throw new IllegalStateException("same-writer original planning-read custody is not installed");
    }
    default Optional<NativeActionPort.AckReceived> pollOriginal(PlanningReadCoordinator.OriginalRead<?> original) throws IOException {
        throw new IOException("original planning-read outcome polling is not installed");
    }
    default Optional<NativeActionPort.AckReceived> pollOriginal(Session borrowed, PlanningReadCoordinator.OriginalRead<?> original) throws IOException {
        throw new IOException("same-writer original planning-read outcome polling is not installed");
    }
    default <T> PlanningReadResult<T> adoptOriginal(PlanningReadCoordinator.OriginalRead<T> original,
            NativeActionPort.AckReceived actual, PlanningReadRequest currentRequest, Obj currentSemantic) throws IOException {
        throw new IOException("original planning-read adoption is not installed");
    }
    default <T> PlanningReadResult<T> adoptOriginal(Session borrowed, PlanningReadCoordinator.OriginalRead<T> original,
            NativeActionPort.AckReceived actual, PlanningReadRequest currentRequest, Obj currentSemantic) throws IOException {
        throw new IOException("same-writer original planning-read adoption is not installed");
    }
}
