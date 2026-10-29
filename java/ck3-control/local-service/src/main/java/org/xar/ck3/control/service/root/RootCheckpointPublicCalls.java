package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Public data contract around the actual unique Root SAVE / restored-publication calls. */
public final class RootCheckpointPublicCalls {
    private RootCheckpointPublicCalls(){ }
    public sealed interface RevisionField permits MissingRevision,NullRevision,ExactRevision {
        Optional<BigInteger> expected();
    }
    public record MissingRevision() implements RevisionField {
        @Override public Optional<BigInteger> expected(){return Optional.empty();}
    }
    public record NullRevision() implements RevisionField {
        @Override public Optional<BigInteger> expected(){return Optional.empty();}
    }
    public record ExactRevision(BigInteger value) implements RevisionField {
        public ExactRevision {
            Objects.requireNonNull(value);StrictJson.require(value.signum()>=0&&value.compareTo(StrictJson.UINT64_MAX)<=0,"exact public uint64 revision required");
        }
        @Override public Optional<BigInteger> expected(){return Optional.of(value);}
    }
    public record Request(RevisionField expectedRevision) {
        public Request {Objects.requireNonNull(expectedRevision);}
        /** Missing and null both bind the current actual frame; their JSON field branches remain distinct. */
        public Optional<BigInteger> effectiveExpectedRevision(){return expectedRevision.expected();}
    }
    /** The complete saved Driver and receipt reference are captured in the original actual writer scope. */
    public record SaveCall(CheckpointResult actual,Optional<DriverStateSnapshot.Complete> savedDriver,
            Optional<ExactRef> canonicalReceipt) {
        public SaveCall {
            Objects.requireNonNull(actual);savedDriver=Objects.requireNonNull(savedDriver);canonicalReceipt=Objects.requireNonNull(canonicalReceipt);
            Optional<ActionReceipt> action=action(actual);
            StrictJson.require(action.isPresent()==canonicalReceipt.isPresent(),"actual SAVE receipt must retain its canonical archive reference");
            canonicalReceipt.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty canonical SAVE receipt source"));
            if(actual instanceof CheckpointResult.Confirmed confirmed){
                var driver=savedDriver.orElseThrow(()->new IllegalArgumentException("confirmed SAVE requires its actual complete saved Driver"));
                byte[] bytes=driver.encode();
                StrictJson.require(bytes.length==confirmed.pair().driver().reference().bytes()
                        &&ActionCodec.sha256(bytes).equals(confirmed.pair().driver().reference().sha256()),"public SAVE Driver differs from its actual physical pair");
                StrictJson.require(driver.lastCheckpoint() instanceof DriverStateSnapshot.Value,"actual saved Driver must contain its original checkpoint object");
            }else StrictJson.require(savedDriver.isEmpty(),"unconfirmed SAVE cannot acquire a complete saved Driver result");
        }
    }
    /** A private restore binding alone is not public success: the same actual new Root must be host-published. */
    public record RestoreCall(RestoreCheckpointService.Result actual,CheckpointRequest.Readiness starting,
            Optional<RootApplicationSession> published) {
        public RestoreCall {
            Objects.requireNonNull(actual);Objects.requireNonNull(starting);published=Objects.requireNonNull(published);
            if(actual instanceof RestoreCheckpointService.Restored restored){
                var root=published.orElseThrow(()->new IllegalArgumentException("actual restore needs its published Root owner"));
                StrictJson.require(root.identity().equals(restored.binding().session())&&!root.isRetired()&&root.hasInstalledHost()
                        &&starting.observed().game().equals(restored.lifecycleAck().previous()),"restore result is not the actual published replacement Root");
            }else StrictJson.require(published.isEmpty(),"unconfirmed restore cannot name a published Root successor");
        }
    }
    public static Optional<ActionReceipt> action(CheckpointResult actual){
        Objects.requireNonNull(actual);
        if(actual instanceof CheckpointResult.Confirmed value)return Optional.of(value.action());
        if(actual instanceof CheckpointResult.Rejected value)return Optional.of(value.action());
        return ((CheckpointResult.Unknown)actual).action();
    }
}
