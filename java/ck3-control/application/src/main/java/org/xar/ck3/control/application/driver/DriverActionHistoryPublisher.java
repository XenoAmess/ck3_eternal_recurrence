package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One actual archived-material -> full Driver/coverage publication. Implementation provenance is DATA; it never submits or observes Native. */
public final class DriverActionHistoryPublisher implements WriterContracts.TransitionAuthority {
    /** Root must install the actual domain material product. Missing products are not empty legacy rows. */
    public interface MaterialSource {
        void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive);
        /** Implementation provenance metadata only; these references are not Native or action evidence. */
        List<ExactRef> sources();
        /** Exact source-owned rejected/never-dispatched operator policy; no generic no-recorder fallback. */
        default void requireOperatorWithoutRebind(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            throw new IOException("actual source-owned operator non-rebind verifier is not installed");
        }
        /** Exact source-owned composite no-gameplay contract; this has no Advance recorder material. */
        default void requireNoGameplayWrite(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            throw new IOException("actual source-owned no-gameplay-write verifier is not installed");
        }
        DriverActionHistoryCodec.OriginalMaterial capture(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals) throws IOException;
        void requireOriginal(Session same,ActionReceipt actual,DriverActionHistoryCodec.OriginalMaterial captured,
                ActionPorts.OutcomeArchive originals) throws IOException;
    }
    public sealed interface Disposition permits Unchanged,Published { }
    public enum Reason { UNRESOLVED, NON_GAMEPLAY, OUTSIDE_ACTIVE_EPISODE, ALREADY_COVERED, OPERATOR_CANONICAL_RECEIPT_VERIFIED, OPERATOR_NO_REBIND_RECEIPT_VERIFIED, NO_GAMEPLAY_WRITE_RECEIPT_VERIFIED }
    public record Unchanged(Reason reason) implements Disposition {public Unchanged {Objects.requireNonNull(reason);}}
    public record Published(DriverSnapshotFacts.Stamp before,DriverSnapshotFacts.Stamp after,ExactRef fullDriver,
            ExactRef originalSource,Optional<ExactRef> legacyRow) implements Disposition {
        public Published {Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(fullDriver);Objects.requireNonNull(originalSource);Objects.requireNonNull(legacyRow);}
    }
    /** Only this publisher's same-session actual material capture creates a publication. */
    static final class Publication {
        private final DriverActionHistoryPublisher owner;private final Session session;private final DriverSnapshotFacts.Known before;
        private final ActionReceipt action;private final ExactRef record;private final DriverActionHistoryCodec.OriginalMaterial material;
        private final DriverStateSnapshot.Complete replacement;private final DriverSnapshotFacts.ActionRow coverage;
        private final DriverSnapshotFacts.Stamp after;
        private final ExactRef source,fullDriver;private final Optional<ExactRef> row;private final String head;
        private final DriverActionHistoryState.Publication data;private final WriterContracts.Request request;
        private WriterContracts.Prepared prepared;private WriterContracts.Receipt receipt;private boolean commitStarted;
        private Optional<ExactRef> recoveredEvent=Optional.empty();private String committedHead;
        private Publication(DriverActionHistoryPublisher owner,Session session,DriverSnapshotFacts.Known before,ActionReceipt action,
                ExactRef record,DriverActionHistoryCodec.OriginalMaterial material,DriverStateSnapshot.Complete replacement,
                DriverSnapshotFacts.ActionRow coverage,DriverSnapshotFacts.Stamp after,ExactRef source,ExactRef fullDriver,Optional<ExactRef> row,String head,
                DriverActionHistoryState.Publication data,WriterContracts.Request request) {
            this.owner=owner;this.session=session;this.before=before;this.action=action;this.record=record;this.material=material;
            this.replacement=replacement;this.coverage=coverage;this.after=after;this.source=source;this.fullDriver=fullDriver;this.row=row;this.head=head;
            this.data=data;this.request=request;
        }
        DriverSnapshotFacts.Known before(){return before;}
        DriverStateSnapshot.Complete replacement(){return replacement;}
        DriverSnapshotFacts.ActionRow coverage(){return coverage;}
        DriverSnapshotFacts.Stamp after(){return after;}
        void requireCurrent(Session same,DriverStateAssembler expected,DriverSnapshotFacts.Known current,ActionSnapshotReader.Lease actions) throws IOException {
            StrictJson.require(owner.pending==this&&same==session&&expected==owner.authority&&current==before,
                    "original action publication escaped its private producer or exact current Driver");
            owner.materials.requireOwner(owner.authority,owner.journal,owner.archive);
            ActionPorts.OutcomeArchive originals=owner.archive.withSession(same);
            StrictJson.require(committedHead!=null&&same.head().digest().equals(committedHead)&&actions.find(action.command().actionId()).filter(action::equals).isPresent(),
                    "original action publication lost its actual canonical action/head");
            if(recoveredEvent.isPresent())StrictJson.require(DriverActionHistoryState.findCommittedCoverage(same,action,originals).orElseThrow().canonicalEvent().equals(recoveredEvent.orElseThrow()),"recovered ACTION publication lost its original canonical event");
            else same.requireCommitted(prepared,receipt);
            StrictJson.require(ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),action,originals).equals(record),
                    "original action publication changed its actual canonical record membership");
            owner.materials.requireOriginal(same,action,material,originals);
            DriverActionHistoryState.requireOriginal(same,data,action,originals);
            StrictJson.require(Arrays.equals(originals.loadFullMaterial(fullDriver).bytes(),replacement.encode()),"archived complete replacement Driver differs");
            actions.assertCurrent();
        }
    }
    private final DriverStateAssembler authority;private final ActionJournal journal;private final ActionPorts.OutcomeArchive archive;
    private final MaterialSource materials;private final List<ExactRef> sources,materialSources;private volatile Publication pending;
    public DriverActionHistoryPublisher(DriverStateAssembler actualAuthority,ActionJournal actualJournal,ActionPorts.OutcomeArchive actualArchive,
            MaterialSource actualMaterials,List<ExactRef> actualPublisherSources) {
        authority=Objects.requireNonNull(actualAuthority);journal=Objects.requireNonNull(actualJournal);archive=Objects.requireNonNull(actualArchive);
        materials=Objects.requireNonNull(actualMaterials);sources=List.copyOf(actualPublisherSources);
        StrictJson.require(!sources.isEmpty()&&sources.size()<=64&&new java.util.HashSet<>(sources).size()==sources.size(),"actual finite publisher sources required");
        materials.requireOwner(authority,journal,archive);materialSources=List.copyOf(materials.sources());
        StrictJson.require(!materialSources.isEmpty()&&materialSources.size()<=1024&&new java.util.HashSet<>(materialSources).size()==materialSources.size(),"stable finite actual installed material source closure required");
    }
    public void requireOwner(DriverStateAssembler expected,ActionJournal actualJournal,ActionPorts.OutcomeArchive originals) {
        StrictJson.require(authority==expected&&journal==actualJournal&&archive==originals,"action history publisher crossed actual Driver/journal/archive ownership");
        materials.requireOwner(authority,journal,archive);
    }
    /** Pending includes a durable or unknown commit whose sole Driver CAS has not completed. Host transfer must refuse it. */
    public boolean hasPending(Session same) throws IOException {Objects.requireNonNull(same).head();return pending!=null;}
    /** Used by the same central primitive/child callback and outer parent/reconciliation tail; repeats are data-only and idempotent. */
    public Disposition completed(Session same,ActionReceipt actual) {
        Objects.requireNonNull(same);Objects.requireNonNull(actual);
        try {return journal.locked(same,locked->{try{return publish(same,actual,locked);}catch(IOException failure){throw new UncheckedIOException(failure);}});}
        catch(UncheckedIOException failure){throw failure;}
    }
    private Disposition publish(Session same,ActionReceipt actual,ActionJournal.LockedJournal locked) throws IOException {
        if(!actual.settled())return new Unchanged(Reason.UNRESOLVED);
        if(actual.command().expectation() instanceof CommandExpectation.OperatorRebind) {
            StrictJson.require(pending==null&&locked.find(actual.command().actionId()).filter(actual::equals).isPresent(),
                    "operator verification requires its actual canonical action and no pending ordinary history publication");
            var originals=archive.withSession(same);
            if(actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.OperatorRebound) {
                DriverActionHistoryCodec.verifyOperator(same,actual,originals);
                return new Unchanged(Reason.OPERATOR_CANONICAL_RECEIPT_VERIFIED);
            }
            String head=same.head().digest();
            StrictJson.require(originals.loadReceipt(originals.receiptReferenceOf(actual)).equals(actual),"operator non-rebind receipt lost its exact prepared/outbound custody");
            var record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,originals);
            StrictJson.require(originals.loadRecord(record).receipt().equals(actual),"operator non-rebind is not its actual canonical record");
            materials.requireOwner(authority,journal,archive);materials.requireOperatorWithoutRebind(same,actual,originals);
            StrictJson.require(same.head().digest().equals(head),"operator non-rebind verification changed the writer head");
            return new Unchanged(Reason.OPERATOR_NO_REBIND_RECEIPT_VERIFIED);
        }
        if(!(actual.command().origin() instanceof CommandOrigin.Gameplay))return new Unchanged(Reason.NON_GAMEPLAY);
        authority.requireOutsideObservationScope(same);
        Publication retained=pending;
        if(retained!=null)StrictJson.require(retained.action.equals(actual),"an original ACTION publication must be resolved before another action or owner transfer");
        StrictJson.require(locked.find(actual.command().actionId()).filter(actual::equals).isPresent(),"actual durable completed action required");
        if(actual.state() instanceof ActionState.CompositeSettled settled
                &&settled.settlement() instanceof ActionState.CompositeNoGameplayWrite terminal) {
            StrictJson.require(retained==null,"no-gameplay-write verification cannot replace a pending ACTION publication");
            terminal.observation().validate(actual.command(),settled.execution());
            ActionEffects.validateComposite(actual.command(),settled.execution(),terminal);
            ActionEffects.validateCompositeChildren(settled.execution(),terminal,List.of());
            StrictJson.require(actual.outcome()==ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT
                    &&!actual.visibleGameplay()&&!actual.eligibleAdvance()&&actual.applied().isEmpty(),
                    "no-gameplay-write receipt cannot claim an applied or Advance effect");
            var originals=archive.withSession(same);
            materials.requireOwner(authority,journal,archive);materials.requireNoGameplayWrite(same,actual,originals);
            return new Unchanged(Reason.NO_GAMEPLAY_WRITE_RECEIPT_VERIFIED);
        }
        DriverSnapshotFacts.Known before=authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual complete Driver predecessor unavailable");return (DriverSnapshotFacts.Known)frozen.state();
        });
        if(!actual.command().before().game().equals(before.stamp().game())
                ||!actual.command().before().frame().episodeRunId().equals(before.driver().session().episodeRunId()))return new Unchanged(Reason.OUTSIDE_ACTIVE_EPISODE);
        StrictJson.require(actual.command().before().frame().identity().player().equals(before.driver().session().actorId()),"actual history crossed its episode actor");
        var covered=before.actionRows().stream().filter(row->row.actionId().equals(actual.command().actionId())).toList();
        if(!covered.isEmpty()) {
            var existing=covered.getFirst();
            StrictJson.require(covered.size()==1&&existing.bodySha256().equals(actual.bodySha256())
                    &&existing.durableSequence()<=actual.sequence(),"existing action history coverage differs from the actual completed action");
            if(existing.coverageSource() instanceof DriverSnapshotFacts.CanonicalOnly)
                StrictJson.require(existing.durableSequence()==actual.sequence(),"canonical-only ACTION coverage requires its exact settled sequence");
            else {
                var legacy=DriverJson.object(before.driver().commandHistory().get(Math.toIntExact(existing.historyIndex()-1)).originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
                if(legacy.members().containsKey(DriverActionHistoryCodec.SOURCE_FIELD))
                    StrictJson.require(existing.durableSequence()==actual.sequence(),"new ACTION source coverage requires its exact settled sequence");
                // SAVE publishes its real row during AckReceived; its later canonical settled receipt has a later sequence.
            }
            if(retained!=null) {DriverActionHistoryState.findCommittedCoverage(same,actual,archive.withSession(same)).orElseThrow();pending=null;}
            return new Unchanged(Reason.ALREADY_COVERED);
        }
        if(retained!=null&&retained.session==same)return commitAndPublish(same,retained);
        String head=same.head().digest();ActionPorts.OutcomeArchive originals=archive.withSession(same);
        var committed=DriverActionHistoryState.findCommittedCoverage(same,actual,originals);
        if(committed.isPresent())return recover(same,actual,before,committed.orElseThrow(),originals);
        StrictJson.require(retained==null||!retained.commitStarted,"original ACTION commit outcome is unknown; no second commit or replacement publication");
        ExactRef record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,originals);
        materials.requireOwner(authority,journal,archive);DriverActionHistoryCodec.OriginalMaterial material=Objects.requireNonNull(materials.capture(same,actual,originals),"actual material product cannot return null");
        materials.requireOriginal(same,actual,material,originals);
        var original=DriverActionHistoryCodec.source(actual,record,originals.receiptReferenceOf(actual),material);
        DriverActionHistoryCodec.requireSource(actual,original,originals);
        RawJson sourceBody=DriverActionHistoryCodec.encode(original);ExactRef source=originals.preserveMaterial(sourceBody);
        StrictJson.require(originals.loadMaterial(source).equals(sourceBody),"actual action source archive readback changed");
        DriverStateSnapshot.Complete replacement=before.driver();DriverSnapshotFacts.ActionRow coverage;Optional<ExactRef> row=Optional.empty();
        if(material instanceof DriverActionHistoryCodec.Legacy||material instanceof DriverActionHistoryCodec.GiftLegacyPair) {
            long index=Math.addExact(before.driver().commandHistory().size(),1L);
            var value=DriverActionHistoryCodec.legacyRow(index,actual,original,originals);
            RawJson body=new RawJson(DriverJson.encode(value));ExactRef rowRef=originals.preserveMaterial(body);
            DriverActionHistoryCodec.verifyLegacy(actual,DriverJson.object(originals.loadMaterial(rowRef).bytes(),DriverJson.MAX_NATIVE_BYTES),originals);
            var history=new ArrayList<>(before.driver().commandHistory());var actualRows=DriverActionHistoryCodec.legacyRows(index,actual,original,originals);
            for(int offset=0;offset<actualRows.size();offset++)history.add(new DriverStateSnapshot.HistoryEntry(Math.addExact(index,offset),
                    new DriverStateSnapshot.Value(DriverJson.encode(actualRows.get(offset)))));
            var old=before.driver();replacement=new DriverStateSnapshot.Complete(old.session(),history,old.lastCheckpoint(),old.rollbackWarFailure(),old.managedRestoreTransaction(),
                    old.successionExpectation(),old.successionLifecycle(),old.campaignGoal(),old.rollbackWarFailures());
            coverage=new DriverSnapshotFacts.ActionRow(actual.command().actionId(),actual.bodySha256(),actual.sequence(),index,rowRef);row=Optional.of(rowRef);
        } else {
            DriverActionHistoryCodec.verifyCanonicalOnly(actual,source,originals);
            coverage=new DriverSnapshotFacts.ActionRow(actual.command().actionId(),actual.bodySha256(),actual.sequence(),new DriverSnapshotFacts.CanonicalOnly(source));
        }
        ExactRef full=originals.preserveMaterial(RawJson.fullMaterial(replacement.encode()));
        StrictJson.require(Arrays.equals(originals.loadFullMaterial(full).bytes(),replacement.encode()),"actual full Driver archive readback differs");
        StrictJson.require(same.head().digest().equals(head),"archival action material capture changed the canonical writer");
        var stamp=new DriverSnapshotFacts.Stamp(Math.addExact(before.stamp().driverVersion(),1),before.stamp().episodeEpoch(),before.stamp().game(),
                before.stamp().episodeRunId(),DriverJson.sha256(replacement.encode()));
        ExactRef beforeDriver=originals.materialReferenceOf(RawJson.fullMaterial(before.driver().encode()));
        var data=new DriverActionHistoryState.Publication("driver-action:"+UUID.randomUUID(),actual.command(),actual.bodySha256(),actual.sequence(),head,
                before.stamp().driverVersion(),stamp.driverVersion(),stamp.episodeEpoch(),beforeDriver,full,source,row);
        var archivedEvidence=new ArrayList<>(List.of(beforeDriver,full,source,record,originals.receiptReferenceOf(actual)));row.ifPresent(archivedEvidence::add);
        var evidence=publicationEvidence(archivedEvidence,material);
        var publication=new Publication(this,same,before,actual,record,material,replacement,coverage,stamp,source,full,row,head,data,data.request(evidence));
        pending=publication;return commitAndPublish(same,publication);
    }
    private Disposition commitAndPublish(Session same,Publication publication) throws IOException {
        if(publication.recoveredEvent.isEmpty()) {
            if(publication.prepared==null)publication.prepared=same.preview(publication.request);
            if(publication.receipt==null) {
                if(publication.commitStarted)publication.receipt=same.queryCommitted(publication.prepared).orElseThrow(()->new IOException("original ACTION publication commit outcome unknown; no second commit"));
                else {publication.commitStarted=true;publication.receipt=same.commit(publication.prepared);}
            }
            same.requireCommitted(publication.prepared,publication.receipt);
        }
        publication.committedHead=same.head().digest();authority.publishActionHistory(same,publication);
        pending=null;return new Published(publication.before.stamp(),publication.after,publication.fullDriver,publication.source,publication.row);
    }
    private Disposition recover(Session same,ActionReceipt actual,DriverSnapshotFacts.Known before,DriverActionHistoryState.CommittedCoverage committed,
            ActionPorts.OutcomeArchive originals) throws IOException {
        var data=committed.publication();StrictJson.require(before.stamp().driverVersion()==data.beforeVersion()
                &&before.stamp().episodeEpoch()==data.episodeEpoch()&&Arrays.equals(before.driver().encode(),originals.loadFullMaterial(data.beforeDriver()).bytes()),
                "committed ACTION publication cannot be replayed onto a different current full Driver predecessor");
        var original=DriverActionHistoryCodec.decode(originals.loadMaterial(data.originalSource()));
        materials.requireOriginal(same,actual,original.material(),originals);
        var replacement=DriverStateSnapshot.decodeComplete(originals.loadFullMaterial(data.afterDriver()).bytes());DriverSnapshotFacts.ActionRow coverage;
        if(data.legacyRow().isPresent()) {
            var row=DriverJson.object(originals.loadMaterial(data.legacyRow().orElseThrow()).bytes(),DriverJson.MAX_NATIVE_BYTES);
            long index=org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(row.get("index"),"index").longValueExact();
            coverage=new DriverSnapshotFacts.ActionRow(actual.command().actionId(),actual.bodySha256(),actual.sequence(),index,data.legacyRow().orElseThrow());
        } else coverage=new DriverSnapshotFacts.ActionRow(actual.command().actionId(),actual.bodySha256(),actual.sequence(),new DriverSnapshotFacts.CanonicalOnly(data.originalSource()));
        var after=new DriverSnapshotFacts.Stamp(data.afterVersion(),data.episodeEpoch(),before.stamp().game(),before.stamp().episodeRunId(),DriverJson.sha256(replacement.encode()));
        var publication=new Publication(this,same,before,actual,original.record(),original.material(),replacement,coverage,after,data.originalSource(),data.afterDriver(),data.legacyRow(),
                data.predecessor(),data,data.request(List.of(data.originalSource(),data.beforeDriver(),data.afterDriver())));
        publication.recoveredEvent=Optional.of(committed.canonicalEvent());pending=publication;return commitAndPublish(same,publication);
    }
    @Override public String revalidate(ContinuityState before,WriterContracts.Request request) throws IOException {
        throw new IOException("ACTION history requires the actual original writer Head and private archived material publication");
    }
    @Override public String revalidate(WriterContracts.Head head,WriterContracts.Request request) throws IOException {
        Publication publication=actual(request);Session same=publication.session;
        StrictJson.require(head.digest().equals(publication.head)&&same.head().digest().equals(publication.head),"ACTION publication actual writer predecessor changed");
        authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==publication.before,"ACTION history lost its exact complete Driver predecessor");
            StrictJson.require(frozen.actions().actions().stream().anyMatch(publication.action::equals),"ACTION publication lost actual durable receipt");
            materials.requireOwner(authority,journal,archive);materials.requireOriginal(same,publication.action,publication.material,archive.withSession(same));
            DriverActionHistoryState.requireOriginal(same,publication.data,publication.action,archive.withSession(same));return null;
        });
        for(ExactRef ref:request.evidence()){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
        var guard=StrictJson.object();guard.put("head",head.digest());guard.put("request",request.identity());guard.put("full_driver",publication.before.stamp().driverSha256());return ContinuityJson.digest(guard);
    }
    @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request request) {
        actual(request);return DriverActionHistoryState.reduce(before,request);
    }
    private Publication actual(WriterContracts.Request request) {
        Publication publication=pending;StrictJson.require(publication!=null&&request.kind().equals(WriterContracts.DRIVER_ACTION_HISTORY_KIND)
                &&publication.request.identity().equals(request.identity())&&Arrays.equals(publication.request.details(),request.details())
                &&publication.request.evidence().equals(request.evidence()),"no actual private archived-material ACTION publication matches this request");return publication;
    }
    /** Real publication evidence only. An implementation reference is retained only when it has an explicit business role too. */
    static List<ExactRef> publicationEvidence(List<ExactRef> archivedBusinessEvidence,DriverActionHistoryCodec.OriginalMaterial material) {
        Objects.requireNonNull(archivedBusinessEvidence);Objects.requireNonNull(material);
        var evidence=new java.util.LinkedHashSet<ExactRef>(archivedBusinessEvidence);
        material.evidence().forEach(value->evidence.add(value.reference()));
        return List.copyOf(evidence);
    }
}
