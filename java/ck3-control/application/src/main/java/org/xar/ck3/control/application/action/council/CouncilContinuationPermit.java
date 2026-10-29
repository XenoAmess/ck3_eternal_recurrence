package org.xar.ck3.control.application.action.council;

import java.time.Clock;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** Only the coordinator package mints a live permit after an actual original-writer ISSUED commit. */
public final class CouncilContinuationPermit {
    private final Request request;
    private final NativeRequest prepared;
    private final Runnable verifyIssued;
    private final Clock clock;
    private final Thread owner = Thread.currentThread();
    private final AtomicBoolean consumed = new AtomicBoolean();
    private boolean open = true;
    CouncilContinuationPermit(Request request, NativeRequest prepared, Runnable verifyIssued, Clock clock) {
        this.request = Objects.requireNonNull(request); this.prepared = Objects.requireNonNull(prepared);
        this.verifyIssued = Objects.requireNonNull(verifyIssued); this.clock = Objects.requireNonNull(clock);
    }
    public String originalActionId() { return request.scope().parentActionId(); }
    public String originalBodySha256() { return request.scope().parentBodySha256(); }
    public String originalAttemptRequestId() { return request.scope().originalAttemptRequestId(); }
    public String requestId() { return request.requestId(); }
    public String sessionId() { return request.guard().sessionId(); }
    public Stage stage() { return request.stage(); }
    public GuardEvidence guard() { return request.guard(); }
    public NativeRequest preparedRequest() { return prepared; }
    public boolean consumed() { return consumed.get(); }
    public void consumeOnce() {
        StrictJson.require(open && owner == Thread.currentThread() && clock.instant().isBefore(request.deadline())
                && !clock.instant().isAfter(guard().validUntil()), "continuation permit is closed, stale or on another thread");
        verifyIssued.run(); StrictJson.require(consumed.compareAndSet(false, true), "original continuation permit was already consumed");
    }
    void close() { open = false; }
}
