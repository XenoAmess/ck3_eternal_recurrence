package org.xar.ck3.control.application.action;

import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.application.advance.PreparedCleanupEvidence;
import org.xar.ck3.control.contracts.StrictJson;

/** Separate one-world-write capability. Neither a DATA record nor a package name
 * grants Root authority: the SDK additionally requires its installed Root's
 * PreparedQualification to verify this identical source, held writer/head,
 * canonical A terminal, prepared nonce/body and current late physical originals. */
public final class PreparedCleanupPermit {
    private final CompositeActionPort.PreparedCleanupSource issuer;
    private final CompositeContinuationToken sourceToken;
    private final PreparedCleanupEvidence.Prepared preparation;
    private final PreparedCleanupEvidence.LateBinding binding;
    private final long preparationSequence;
    private final Clock clock;
    private final AtomicBoolean consumed=new AtomicBoolean();

    PreparedCleanupPermit(CompositeActionPort.PreparedCleanupSource actualRegisteredSource,
            CompositeContinuationToken actualSourceToken,PreparedCleanupEvidence.Prepared preparation,
            PreparedCleanupEvidence.LateBinding binding,long actualPreparationSequence,Clock actualClock) {
        issuer=Objects.requireNonNull(actualRegisteredSource);sourceToken=Objects.requireNonNull(actualSourceToken);
        this.preparation=Objects.requireNonNull(preparation);this.binding=Objects.requireNonNull(binding);
        preparationSequence=actualPreparationSequence;clock=Objects.requireNonNull(actualClock);
        StrictJson.require(actualPreparationSequence>0&&binding.prepared().equals(preparation),"permit changed its actual durable preparation or late binding");
        requireFresh();
    }
    public boolean issuedBy(CompositeActionPort.PreparedCleanupSource actualRegisteredSource){return issuer==actualRegisteredSource;}
    public CompositeContinuationToken sourceToken(){return sourceToken;}
    public PreparedCleanupEvidence.Prepared preparation(){return preparation;}
    public PreparedCleanupEvidence.LateBinding binding(){return binding;}
    public ActionCommand command(){return preparation.command();}
    public String bodySha256(){return ActionCodec.bodySha256(command());}
    public String requestId(){return preparation.nativeRequestId();}
    public String nonce(){return preparation.preparationNonce();}
    public NativeRequest preparedRequest(){return preparation.nativePrepared();}
    public long preparationSequence(){return preparationSequence;}
    public java.math.BigInteger actualExpectedRevision(){return binding.writeFrame().nativeRevision();}
    public Instant writeDeadline(){return binding.writeDeadline();}
    public boolean consumed(){return consumed.get();}
    public void requireFresh(){
        Instant now=clock.instant();
        StrictJson.require(!now.isBefore(binding.boundAt())&&now.isBefore(binding.writeDeadline())
                &&now.isBefore(preparation.deadline()),"prepared cleanup late physical write window expired or regressed");
    }
    /** All slow source callbacks must already have ended. This performs no archive, writer, READ or callback. */
    public void consumeOnce(){
        requireFresh();
        StrictJson.require(consumed.compareAndSet(false,true),"prepared cleanup permit was already consumed; same-ID collection only");
        requireFresh();
    }
}
