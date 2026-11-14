package org.xar.ck3.control.application.action;

import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.application.advance.PreparedCleanupEvidence;
import org.xar.ck3.control.contracts.StrictJson;

/** Source-owned one-shot pair of fixed read-only observations after durable
 * preparation. It carries no world-write capability and cannot be substituted
 * for PreparedCleanupPermit or a legacy SubmissionPermit. SDK still requires
 * its real Root qualification to prove the identical active source/write scope. */
public final class PreparedCleanupObservationPermit {
    private final CompositeActionPort.PreparedCleanupSource issuer;
    private final CompositeContinuationToken token;
    private final PreparedCleanupEvidence.Prepared preparation;
    private final long sequence;
    private final Clock clock;
    private final AtomicBoolean consumed=new AtomicBoolean();
    PreparedCleanupObservationPermit(CompositeActionPort.PreparedCleanupSource actualRegisteredSource,
            CompositeContinuationToken actualToken,PreparedCleanupEvidence.Prepared preparation,
            long actualPreparedSequence,Clock actualClock) {
        issuer=Objects.requireNonNull(actualRegisteredSource);token=Objects.requireNonNull(actualToken);
        this.preparation=Objects.requireNonNull(preparation);sequence=actualPreparedSequence;clock=Objects.requireNonNull(actualClock);
        StrictJson.require(sequence>0,"read-only late observer requires the actual durable prepared child sequence");
    }
    public boolean issuedBy(CompositeActionPort.PreparedCleanupSource actual){return issuer==actual;}
    public CompositeContinuationToken sourceToken(){return token;}
    public PreparedCleanupEvidence.Prepared preparation(){return preparation;}
    public long preparationSequence(){return sequence;}
    public Instant deadline(){return preparation.deadline();}
    public boolean consumed(){return consumed.get();}
    public void consumeOnce(){
        StrictJson.require(clock.instant().isBefore(deadline())&&consumed.compareAndSet(false,true),
                "prepared cleanup read-only observation already consumed or outside its new own deadline");
    }
}
