package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadCoordinator;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;

/** Native domain preparers receive this exact one-shot link before their observers are installed. */
public final class RootPlanningReads implements PlanningReadPort {
    private final ContinuityWriter writer;
    private volatile PlanningReadCoordinator installed;
    RootPlanningReads(ContinuityWriter writer) { this.writer = Objects.requireNonNull(writer); }
    synchronized void bind(PlanningReadCoordinator actual) {
        if (installed != null) throw new IllegalStateException("Root planning coordinator already installed"); installed = Objects.requireNonNull(actual);
    }
    public boolean isBound() { return installed != null; }
    @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
        // The sole journal inherits an active Driver freeze, or opens its own original writer lease
        // when the ordinary planner calls outside capture. It never creates another writer object.
        return required().read(contract, request);
    }
    @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session borrowed, ReadContract<T> contract, PlanningReadRequest request) {
        try { writer.requireSession(borrowed); return required().read(borrowed, contract, request); }
        catch (IOException failure) { throw new UncheckedIOException("planning read borrowed another writer", failure); }
    }
    @Override public <T> PlanningReadResult<T> readWithFailureEvidence(ReadContract<T> contract,
            PlanningReadRequest request, PlanningReadPort.FailureEvidenceObserver observer) {
        return required().readWithFailureEvidence(contract, request, Objects.requireNonNull(observer));
    }
    @Override public <T> PlanningReadResult<T> readWithFailureEvidence(ContinuityStorePort.Session borrowed,
            ReadContract<T> contract, PlanningReadRequest request, PlanningReadPort.FailureEvidenceObserver observer) {
        try {
            writer.requireSession(borrowed);
            return required().readWithFailureEvidence(borrowed, contract, request, Objects.requireNonNull(observer));
        } catch (IOException failure) {
            throw new UncheckedIOException("failed-read evidence borrowed another writer", failure);
        }
    }
    @Override public <T> org.xar.ck3.control.application.action.PlanningReadAttempt<T> readOriginal(ReadContract<T> contract,PlanningReadRequest request) {
        return required().readOriginal(contract,request);
    }
    @Override public <T> org.xar.ck3.control.application.action.PlanningReadAttempt<T> readOriginal(ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request) {
        try{writer.requireSession(same);return required().readOriginal(same,contract,request);}
        catch(IOException failure){throw new UncheckedIOException("original planning read borrowed another writer",failure);}
    }
    @Override public java.util.Optional<org.xar.ck3.control.application.action.NativeActionPort.AckReceived> pollOriginal(PlanningReadCoordinator.OriginalRead<?> original)throws IOException {
        return required().pollOriginal(original);
    }
    @Override public java.util.Optional<org.xar.ck3.control.application.action.NativeActionPort.AckReceived> pollOriginal(ContinuityStorePort.Session same,PlanningReadCoordinator.OriginalRead<?> original)throws IOException {
        writer.requireSession(same);return required().pollOriginal(same,original);
    }
    @Override public <T> PlanningReadResult<T> adoptOriginal(PlanningReadCoordinator.OriginalRead<T> original,org.xar.ck3.control.application.action.NativeActionPort.AckReceived ack,PlanningReadRequest current,org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic)throws IOException {
        return required().adoptOriginal(original,ack,current,semantic);
    }
    @Override public <T> PlanningReadResult<T> adoptOriginal(ContinuityStorePort.Session same,PlanningReadCoordinator.OriginalRead<T> original,org.xar.ck3.control.application.action.NativeActionPort.AckReceived ack,PlanningReadRequest current,org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic)throws IOException {
        writer.requireSession(same);return required().adoptOriginal(same,original,ack,current,semantic);
    }
    private PlanningReadCoordinator required() {
        PlanningReadCoordinator actual = installed;
        if (actual == null) throw new IllegalStateException("actual Root planning coordinator has not been installed"); return actual;
    }
}
