package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** In-memory one-write capability, issued only by the common durable SUBMITTING transition. Never serializable. */
public final class SubmissionPermit {
    private final ActionCommand command;
    private final String bodySha256;
    private final long sequence;
    private final String requestId;
    private final Instant submittedAt;
    private final GuardEvidence guard;
    private final NativeRequest preparedRequest;
    private Runnable beforeFirstWrite=()->{};
    private final AtomicBoolean consumed = new AtomicBoolean();
    SubmissionPermit(ActionCommand command, String bodySha256, long sequence, String requestId,
            Instant submittedAt, GuardEvidence guard, NativeRequest preparedRequest) {
        this.command = Objects.requireNonNull(command); this.bodySha256 = bodySha256; this.sequence = sequence;
        this.requestId = requestId; this.submittedAt = submittedAt; this.guard = Objects.requireNonNull(guard);
        this.preparedRequest = Objects.requireNonNull(preparedRequest);
    }
    /** Package-private owner observer, bound before this original permit reaches Native. */
    void beforeFirstWrite(Runnable actual) {
        if(consumed.get())throw new IllegalStateException("cannot bind after original submission");
        beforeFirstWrite=Objects.requireNonNull(actual);
    }
    public void consumeOnce() {
        if (!consumed.compareAndSet(false, true)) throw new IllegalStateException("submission permit already consumed; never replay");
        beforeFirstWrite.run();
    }
    public boolean consumed() { return consumed.get(); }
    public String actionId() { return command.actionId(); }
    public String bodySha256() { return bodySha256; }
    public CommandOrigin origin() { return command.origin(); }
    public BigInteger expectedRevision() { return origin().expectedRevision(); }
    public ObservationIdentity before() { return origin().requireGameplay(); }
    public String sessionId() { return command.sessionId(); }
    public long sequence() { return sequence; }
    public String requestId() { return requestId; }
    public Instant submittedAt() { return submittedAt; }
    public GuardEvidence guard() { return guard; }
    public NativeRequest preparedRequest() { return preparedRequest; }
}
