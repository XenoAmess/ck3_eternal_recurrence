package org.xar.ck3.control.application.lifecycle;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Canonical historical publication DATA for an independently verified, actually admitted episode.
 * This reader never returns Base, an admission token, current readiness or Native permission.
 */
public final class LifecycleHistoricalPublication {
    private final ContinuityStorePort writer;
    private final ActionSnapshotReader snapshots;
    private final LifecycleComposites lifecycle;
    public LifecycleHistoricalPublication(ContinuityStorePort exactWriter,ActionSnapshotReader actualSnapshots,
            LifecycleComposites registeredLifecycle) {
        writer=Objects.requireNonNull(exactWriter);snapshots=Objects.requireNonNull(actualSnapshots);
        lifecycle=Objects.requireNonNull(registeredLifecycle);
    }
    public Recorded read(ContinuityStorePort.Session same,String canonicalParentActionId)throws IOException {
        writer.requireSession(same);StrictJson.text(canonicalParentActionId);
        try{return snapshots.withFrozen(same,lease->{
            try {
                var head=same.head();StrictJson.require(lease.snapshot().headSha256().equals(head.digest()),"historical lifecycle requires the actual current canonical action snapshot");
                var parent=lease.find(canonicalParentActionId).orElseThrow(()->new IOException("actual canonical lifecycle parent is absent"));
                StrictJson.require(parent.state() instanceof ActionState.CompositeSettled settled
                        &&settled.settlement() instanceof ActionState.LifecycleApplied,"historical publication requires its actual canonical LifecycleApplied parent");
                var applied=(ActionState.LifecycleApplied)((ActionState.CompositeSettled)parent.state()).settlement();
                var proof=(LifecycleTransitionProof.Recorded)LifecycleProofCodec.decodeRecorded(applied.proof().encode());
                lifecycle.verifyRecorded(parent.command(),proof,head);
                StrictJson.require(proof.kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,"historical current-episode reconstruction requires an actual Continue publication");
                var registry=LifecycleJson.object(head.state().toJson().get(LifecycleContinuityAuthority.STATE_FIELD));
                var details=LifecycleJson.object(LifecycleJson.object(registry.get("transitions")).get(canonicalParentActionId));
                StrictJson.require(LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED.name().equals(LifecycleJson.text(details.get("phase"))),
                        "only the explicitly finalized pending publication is supported by this historical reader");
                var request=new WriterContracts.Request(LifecycleChild.KIND,LifecycleJson.bytes(details),proof.originalEvidence());
                StrictJson.require(request.identity().equals(proof.eventIdentity),"actual historical publication identity differs");
                WriterContracts.HistoricalTransition actual=null;
                for(var pin:proof.documents) {
                    if(!head.documents().contains(pin)||!Path.of(pin.reference().path()).getFileName().toString().matches("[0-9]{8}\\.json"))continue;
                    var candidate=same.readHistoricalTransition(pin);
                    if(candidate.eventIdentity().equals(proof.eventIdentity)){actual=candidate;break;}
                }
                if(actual==null)throw new IOException("original canonical lifecycle event FileID is absent");
                StrictJson.require(actual.kind().equals(LifecycleChild.KIND)
                        &&LifecycleJson.same(LifecycleJson.parse(actual.details(),ContinuityJson.DOCUMENT_MAX_BYTES),details),"actual historical lifecycle details differ");
                var delta=LifecycleJson.object(details.get("delta"));var adopted=ExactRef.fromJson(delta.get("adopted_driver_ref"));
                var driverPin=proof.documents.stream().filter(pin->pin.reference().equals(adopted)).findFirst()
                        .orElseThrow(()->new IOException("historical adopted full Driver original pin is absent"));
                StrictJson.require(adopted.bytes()>0&&adopted.bytes()<=DriverCheckpointStore.MAX_DRIVER_BYTES,"bounded historical full Driver role required");
                var driver=DriverStateSnapshot.decodeComplete(same.readPinned(driverPin,Math.toIntExact(adopted.bytes())));same.verifyPin(driverPin);
                var reduced=LifecycleContinuityAuthority.project(actual.before(),request,driver).toJson();
                reduced.put("sequence",actual.sequence());reduced.put("last_event_identity",actual.eventIdentity());
                StrictJson.require(ContinuityJson.same(reduced,actual.after().toJson()),"sole lifecycle reducer does not reproduce the original canonical publication");
                var predecessor=ExactRef.fromJson(delta.get("causal_original_driver_ref"));
                StrictJson.require(predecessor.equals(parent.command().lifecycleBefore().evidence().originalDriver()),"historical publication changed the actual old parent causal Driver role");
                var publication=new LifecyclePublication.RecordedEvent(request,actual.before(),actual.after(),actual.eventPin(),proof.documents);
                lease.assertCurrent();StrictJson.require(head.digest().equals(same.head().digest()),"historical publication reader changed the actual canonical head");
                return new Recorded(this,parent,proof,publication,predecessor,adopted);
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        });}catch(UncheckedIOException failure){throw failure.getCause();}
    }
    public static final class Recorded {
        private final LifecycleHistoricalPublication issuer;
        private final ActionReceipt parent;
        private final LifecycleTransitionProof.Recorded proof;
        private final LifecyclePublication.RecordedEvent publication;
        private final ExactRef predecessor,adopted;
        private Recorded(LifecycleHistoricalPublication issuer,ActionReceipt parent,LifecycleTransitionProof.Recorded proof,
                LifecyclePublication.RecordedEvent publication,ExactRef predecessor,ExactRef adopted) {
            this.issuer=issuer;this.parent=parent;this.proof=proof;this.publication=publication;this.predecessor=predecessor;this.adopted=adopted;
        }
        public ActionReceipt parent(){return parent;}
        public LifecycleTransitionProof.Recorded proof(){return proof;}
        public LifecyclePublication.RecordedEvent publication(){return publication;}
        public ExactRef predecessorDriverReference(){return predecessor;}
        public ExactRef adoptedDriverReference(){return adopted;}
        /** Reopens the same historical originals at this head; it does not qualify the current Driver. */
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            var current=issuer.read(same,parent.command().actionId());
            StrictJson.require(current.parent.version()==parent.version()&&current.parent.sequence()==parent.sequence()
                    &&current.parent.bodySha256().equals(parent.bodySha256())
                    &&Arrays.equals(ActionCodec.encodeCommand(current.parent.command()),ActionCodec.encodeCommand(parent.command()))
                    &&Arrays.equals(current.proof.encode(),proof.encode())
                    &&current.predecessor.equals(predecessor)&&current.adopted.equals(adopted),"historical lifecycle originals changed");
        }
    }
}
