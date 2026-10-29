package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit public SAVE uses the ordinary source-bound journal/store, never a second SAVE implementation. */
public final class PublicCheckpointMaterialCapture {
    public static final class Pending {
        private final PublicCheckpointMaterialCapture issuer;
        private final SessionIdentity owner;
        private final CheckpointRequest request;
        private final CompletedCycleProof proof;
        private CheckpointResult.Confirmed confirmed;
        private boolean boundaryAttempted;
        private Captured captured;
        private Pending(PublicCheckpointMaterialCapture issuer,SessionIdentity owner,CheckpointRequest request,CompletedCycleProof proof){
            this.issuer=issuer;this.owner=owner;this.request=request;this.proof=proof;
        }
        /** Retained original result only; this DATA accessor cannot mint material qualification. */
        public Optional<CheckpointResult.Confirmed> confirmedResult(){return Optional.ofNullable(confirmed);}
        public boolean materialConfirmed(){return captured!=null;}
    }
    public static final class Captured {
        private final PublicCheckpointMaterialCapture issuer;
        private final SavedCheckpointMaterial material;
        private final JournalCommit journalCommit;
        private final ActionCommand originalCommand;
        private final ActionReceipt originalReceipt;
        private Captured(PublicCheckpointMaterialCapture issuer,SavedCheckpointMaterial material,JournalCommit journalCommit,ActionReceipt originalReceipt){
            this.issuer=issuer;this.material=material;this.journalCommit=journalCommit;
            this.originalReceipt=Objects.requireNonNull(originalReceipt);this.originalCommand=originalReceipt.command();
        }
        public CheckpointPair pair(){return material.pair();}
        public SavedCheckpointMaterial material(){return material;}
        public JournalCommit journalCommit(){return journalCommit;}
        /** Exact prepared original only; DATA does not grant Controller adoption. */
        public ActionCommand originalCommand(){return originalCommand;}
        /** Original canonical SAVE fact for truthful late-adoption reporting; DATA grants no admission. */
        public ActionReceipt originalReceipt(){return originalReceipt;}
        /** Revalidate this private capture against the actual current saved frontier; performs no write or SAVE. */
        public JournalCommit requireAdoption(ContinuityStorePort.Session same,SessionIdentity owner,
                ContinuityBatchJournal identicalJournal)throws IOException{
            return issuer.requireAdoption(same,this,owner,identicalJournal);
        }
        public void requirePhysical(ContinuityStorePort.Session same)throws IOException{
            issuer.store.requireSession(same);issuer.materials.requireOwn(material);material.requirePhysical(same);
        }
    }
    private record CanonicalPair(CheckpointPair pair,long sequence){}
    private final ContinuityStorePort store;
    private final ContinuityBatchJournal journal;
    private final SavedCheckpointMaterialStore materials;
    private final ActionSnapshotReader actions;
    private Pending latest;
    private Captured latestCaptured;
    public PublicCheckpointMaterialCapture(ContinuityStorePort actualWriter,ContinuityBatchJournal actualJournal,
            SavedCheckpointMaterialStore actualMaterials,ActionSnapshotReader actualActions){
        store=Objects.requireNonNull(actualWriter);journal=Objects.requireNonNull(actualJournal);
        materials=Objects.requireNonNull(actualMaterials);actions=Objects.requireNonNull(actualActions);
        journal.requireStore(store);
    }
    /** Called after genuine readiness/READ-flush and preparation, before the only SAVE submission. */
    public synchronized Pending begin(ContinuityStorePort.Session same,SessionIdentity owner,SemanticEvidence preSave,
            CheckpointRequest prepared)throws IOException{
        store.requireSession(same);journal.requireStore(store);
        Objects.requireNonNull(owner);Objects.requireNonNull(preSave);Objects.requireNonNull(prepared);
        var command=prepared.saveCommand();
        requireOwner(owner,command);
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                &&command.operation().equals(new OperationKey("save-checkpoint"))
                &&preSave.frame().equals(command.before()),"public SAVE must retain its actual pre-SAVE semantic frame and prepared command");
        if(latest!=null&&latest.captured==null){
            if(latest.confirmed!=null)throw new IOException("original confirmed public SAVE material remains unresolved; never replace or re-SAVE it");
            String expectedHead=same.head().digest();
            boolean unresolved=actions.withFrozen(same,lease->{
                requireHead(lease,expectedHead);var old=lease.find(latest.request.saveCommand().actionId());lease.assertCurrent();
                return old.isPresent()&&!old.orElseThrow().settled();
            });
            if(unresolved)throw new IOException("original public SAVE remains unresolved; query that exact attempt only");
        }
        var proof=journal.cycleProof(same,owner,preSave)
                .orElseThrow(()->new IOException("actual completed-cycle frontier is unavailable; zero SAVE dispatch"));
        StrictJson.require(proof.semantic().equals(preSave)&&proof.frame().equals(command.before()),
                "public SAVE cycle proof differs from actual pre-SAVE evidence");
        latest=new Pending(this,owner,prepared,proof);return latest;
    }
    /** One original SAVE -> one existing SAVE_CONFIRMED boundary -> private original material. */
    public synchronized Captured confirm(ContinuityStorePort.Session same,Pending original,CheckpointResult.Confirmed saved)throws IOException{
        store.requireSession(same);requirePending(original);Objects.requireNonNull(saved);
        var request=original.request;var command=request.saveCommand();var pair=saved.pair();
        StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(saved.action().command()))
                &&saved.action().outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                &&pair.saveActionId().equals(command.actionId())&&pair.lineageId().equals(request.lineageId())
                &&pair.frame().equals(saved.poststate())&&pair.nativeAckRef().equals(saved.ackEvidence())
                &&Path.of(pair.save().reference().path()).normalize().equals(request.expectedSavePath().normalize()),
                "public material confirmation changed the original SAVE command, pair, path or ACK");
        canonical(same,pair,Optional.of(saved.action()));
        if(original.confirmed!=null)StrictJson.require(original.confirmed.pair().equals(saved.pair())
                &&original.confirmed.action().equals(saved.action())&&original.confirmed.ackEvidence().equals(saved.ackEvidence())
                &&original.confirmed.poststate().equals(saved.poststate())&&original.confirmed.advancedDays().equals(saved.advancedDays()),
                "same original SAVE changed its canonical result");
        if(original.captured!=null){original.captured.requirePhysical(same);return original.captured;}
        if(original.confirmed==null)original.confirmed=saved;
        if(original.boundaryAttempted)throw new IOException("original SAVE boundary outcome is unresolved; inspect its original evidence, never commit or SAVE again");
        original.boundaryAttempted=true;
        var committed=journal.commit(same,new JournalInput(original.owner,"public-save-"+ActionCodec.bodySha256(command),
                JournalKind.SAVE_CONFIRMED,Optional.of(pair.frame()),Optional.of(pair),Optional.of(original.proof),
                List.of(pair.save().reference(),pair.driver().reference(),pair.nativeAckRef())));
        var material=materials.currentPhysical(same,pair);materials.requireOwn(material);material.requirePhysical(same);
        StrictJson.require(material.kind()==SavedCheckpointMaterial.Kind.ORDINARY
                &&material.session().equals(original.owner)
                &&material.sourceSemantic().equals(original.proof.semantic()),
                "public SAVE must consume the ordinary store's actual pre-SAVE source material");
        original.captured=new Captured(this,material,committed,saved.action());latestCaptured=original.captured;return original.captured;
    }
    /** Choose by actual canonical SAVE order, then verify only that source. No stale-pair fallback. */
    public synchronized SavedCheckpointMaterial currentPhysical(ContinuityStorePort.Session same,
            Optional<CheckpointPair> actualControllerPair)throws IOException{
        store.requireSession(same);Objects.requireNonNull(actualControllerPair);
        if(latest!=null&&latest.confirmed!=null&&latest.captured==null)
            throw new IOException("newest confirmed public SAVE has no qualified material; refusing an older Controller checkpoint");
        Optional<CanonicalPair> controller=actualControllerPair.isPresent()
                ?Optional.of(canonical(same,actualControllerPair.orElseThrow(),Optional.empty())):Optional.empty();
        Optional<CanonicalPair> publicSave=latestCaptured==null?Optional.empty()
                :Optional.of(canonical(same,latestCaptured.pair(),Optional.empty()));
        CanonicalPair selected;
        if(controller.isEmpty())selected=publicSave.orElseThrow(()->new IOException("no actual Controller or qualified public SAVE checkpoint"));
        else if(publicSave.isEmpty())selected=controller.orElseThrow();
        else{
            var a=controller.orElseThrow();var b=publicSave.orElseThrow();
            StrictJson.require(a.sequence()!=b.sequence()||a.pair().equals(b.pair()),
                    "same canonical SAVE cannot name different physical pairs");
            selected=a.sequence()>=b.sequence()?a:b;
        }
        var material=materials.currentPhysical(same,selected.pair());materials.requireOwn(material);material.requirePhysical(same);
        if(latestCaptured!=null&&selected.pair().equals(latestCaptured.pair()))
            StrictJson.require(material.witness().equals(latestCaptured.material().witness()),"public SAVE original material identity changed");
        return material;
    }
    private synchronized JournalCommit requireAdoption(ContinuityStorePort.Session same,Captured captured,
            SessionIdentity owner,ContinuityBatchJournal identicalJournal)throws IOException{
        store.requireSession(same);journal.requireStore(store);Objects.requireNonNull(owner);
        StrictJson.require(identicalJournal==journal&&captured!=null&&captured.issuer==this
                &&captured==latestCaptured&&latest!=null&&latest.captured==captured,
                "checkpoint adoption requires this actual journal and latest private capture");
        requireOwner(owner,captured.originalCommand);
        StrictJson.require(owner.equals(latest.owner)&&owner.equals(captured.material.session())
                &&Arrays.equals(ActionCodec.encodeCommand(captured.originalCommand),ActionCodec.encodeCommand(latest.request.saveCommand())),
                "checkpoint adoption crossed its actual original owner or complete command");
        captured.requirePhysical(same);
        if(!(captured.material instanceof SavedAttachmentSourceStore.SavedMaterial ordinary))
            throw new IllegalArgumentException("public checkpoint adoption requires the genuine ordinary saved material");
        var current=same.head().state();var whole=current.toJson();var original=ordinary.originalHead().toJson();
        StrictJson.require(Objects.equals(whole.get(WriterContracts.ORDINARY_CYCLE_FIELD),original.get(WriterContracts.ORDINARY_CYCLE_FIELD)),
                "ordinary cycle changed after this SAVE; retained capture cannot clear later unsaved work");
        var saved=StrictJson.object(whole.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),java.util.Set.of("pair","state"));
        StrictJson.require(CheckpointPairCodec.decode(ContinuityJson.canonical(saved.get("pair"))).equals(captured.pair())
                &&ContinuityJson.digest(saved.get("state")).equals(ordinary.proof().cycleStateDigest()),
                "current saved pair or exact saved cycle branch differs from this capture");
        long elapsed=current.settledDateRaw()-current.origin().startDateRaw();
        StrictJson.require((current.status()==ContinuityState.Status.RUNNING||current.status()==ContinuityState.Status.COMPLETE)
                &&current.origin().equals(ordinary.originalHead().origin())
                &&current.settledCycles()==ordinary.proof().completedCycles()
                &&current.settledDateRaw()==captured.pair().frame().frame().identity().dateRaw().longValueExact()
                &&elapsed>=0&&elapsed%24==0&&elapsed/24==captured.journalCommit.committedSavedDays(),
                "current saved frontier differs from the original real SAVE journal commit");
        String expectedHead=same.head().digest();
        actions.withFrozen(same,lease->{
            requireHead(lease,expectedHead);
            var actual=lease.find(captured.originalCommand.actionId())
                    .orElseThrow(()->new IllegalArgumentException("original canonical SAVE receipt is absent"));
            StrictJson.require(latest.confirmed!=null&&actual.equals(captured.originalReceipt)&&actual.equals(latest.confirmed.action())
                    &&Arrays.equals(ActionCodec.encodeCommand(actual.command()),ActionCodec.encodeCommand(captured.originalCommand))
                    &&actual.settled()&&actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    &&actual.ack().filter(ack->ack.nativeOk()&&ack.outbound().isPresent()).isPresent(),
                    "checkpoint adoption requires the actual complete canonical SAVE and positive original ACK");
            for(var row:lease.snapshot().actions()){
                var command=row.command();
                boolean sameOwner=command.origin().machineId().equals(owner.machineId())
                        &&command.origin().game().equals(owner.game())&&command.sessionId().equals(owner.sessionId());
                if(sameOwner&&!command.actionId().equals(actual.command().actionId())){
                    StrictJson.require(row.settled(),"another original action remains unresolved; SAVE adoption cannot clear it");
                    StrictJson.require(!(command.origin() instanceof CommandOrigin.Gameplay)||row.sequence()<actual.sequence(),
                            "a later gameplay action exists; SAVE adoption cannot clear its unsaved work");
                }
            }
            lease.assertCurrent();return null;
        });
        return captured.journalCommit;
    }
    private CanonicalPair canonical(ContinuityStorePort.Session same,CheckpointPair pair,Optional<ActionReceipt> expected)throws IOException{
        String expectedHead=same.head().digest();
        return actions.withFrozen(same,lease->{
            requireHead(lease,expectedHead);
            var receipt=lease.find(pair.saveActionId()).orElseThrow(()->new IllegalArgumentException("actual canonical SAVE receipt is absent"));
            StrictJson.require(receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    &&receipt.command().origin() instanceof CommandOrigin.Gameplay
                    &&receipt.command().operation().equals(new OperationKey("save-checkpoint"))
                    &&receipt.ack().filter(ack->ack.nativeOk()&&ack.outbound().isPresent()).isPresent()
                    &&expected.map(receipt::equals).orElse(true),"checkpoint selection requires the exact applied canonical SAVE receipt and ACK");
            lease.assertCurrent();return new CanonicalPair(pair,receipt.sequence());
        });
    }
    private static void requireHead(ActionSnapshotReader.Lease lease,String expectedHead){
        StrictJson.require(lease.snapshot().headSha256().equals(expectedHead),"public checkpoint reader crossed the original writer");
    }
    private void requirePending(Pending pending){
        StrictJson.require(pending!=null&&pending.issuer==this&&latest==pending,"public SAVE capture belongs to another issuer or original attempt");
    }
    private static void requireOwner(SessionIdentity owner,ActionCommand command){
        StrictJson.require(owner.machineId().equals(command.before().machineId())&&owner.game().equals(command.before().game())
                &&owner.sessionId().equals(command.sessionId()),"public SAVE capture crossed its actual owned session");
    }
}
