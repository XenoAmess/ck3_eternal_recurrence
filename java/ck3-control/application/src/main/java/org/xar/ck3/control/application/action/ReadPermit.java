package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** One registered read on the original guarded connection; never an action submit capability. */
public final class ReadPermit {
    private final ReadContract<?> contract;
    private final PlanningReadRequest request;
    private final NativeRequest preparedRequest;
    private final PlanningReadGuard readGuard;
    private final String requestId;
    private final AtomicBoolean consumed = new AtomicBoolean();
    ReadPermit(ReadContract<?> contract, PlanningReadRequest request, NativeRequest preparedRequest, PlanningReadGuard readGuard, String requestId) {
        this.contract = contract; this.request = request; this.preparedRequest = preparedRequest; this.readGuard = readGuard; this.requestId = requestId;
    }
    public ReadContract<?> contract() { return contract; }
    public NativeRequest preparedRequest() { return preparedRequest; }
    public CommandOrigin origin() { return request.origin(); }
    public BigInteger expectedRevision() { return origin().expectedRevision(); }
    public ObservationIdentity before() { return origin().requireGameplay(); }
    public String sessionId() { return request.sessionId(); }
    public String requestId() { return requestId; }
    public GuardEvidence guard() { return readGuard.binding(); }
    public PlanningReadGuard readGuard() { return readGuard; }
    public boolean consumed() { return consumed.get(); }
    public void consumeOnce() { if (!consumed.compareAndSet(false, true)) throw new IllegalStateException("read permit consumed; allocate a fresh request ID, never resend"); }
}
