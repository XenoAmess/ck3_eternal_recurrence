package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.service.OrdinarySessionResource;

/**
 * One actual Main lifetime: its original ordinary batch, real paired SAVE, then public RESTORE.
 * The request step timeout applies to standalone reads and RESTORE; batch limits remain those
 * supplied by the original startup request.
 */
public final class RootFiniteFirstLiveWork implements RootStartupInputsProducer.Work {
    public static final int MAXIMUM_REPORT_BYTES=1<<20;
    public enum Outcome { NOT_RUN, COMPLETED, BATCH_STOPPED, INSUFFICIENT_SAVE, RESTORE_UNKNOWN, RESTORE_REJECTED, FAILED }
    public record FrontierFacts(SessionIdentity owner,long savedDateRaw,long sequence,String digest) {
        public FrontierFacts { Objects.requireNonNull(owner);Objects.requireNonNull(digest); }
    }
    public record SavedFacts(CheckpointPair pair,ExactRef material,ExactRef fullDriver,long sequence,String headDigest) {
        public SavedFacts { Objects.requireNonNull(pair);Objects.requireNonNull(material);Objects.requireNonNull(fullDriver);Objects.requireNonNull(headDigest); }
    }
    public record RestoredFacts(SessionIdentity owner,ObservationIdentity snapshot,ExactRef fullDriver,
            List<ExactRef> originalSources,long newSavedDayCredit,long newCycleCredit) {
        public RestoredFacts { Objects.requireNonNull(owner);Objects.requireNonNull(snapshot);Objects.requireNonNull(fullDriver);originalSources=List.copyOf(originalSources); }
    }
    /** Immutable outcome DATA; it contains no Root, Host, private binding or current permission. */
    public record Report(String requestId,String machineId,Outcome outcome,String detail,
            Optional<FrontierFacts> before,Optional<FrontierFacts> after,long forwardSavedDays,
            Optional<BatchReport> batch,Optional<SavedFacts> saved,Optional<ExactRef> canonicalSaveReceipt,
            Optional<RestoredFacts> restored) {
        public Report {
            Objects.requireNonNull(requestId);Objects.requireNonNull(machineId);Objects.requireNonNull(outcome);Objects.requireNonNull(detail);
            Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(batch);Objects.requireNonNull(saved);
            Objects.requireNonNull(canonicalSaveReceipt);Objects.requireNonNull(restored);
        }
        public int exitCode(){return outcome==Outcome.COMPLETED?0:outcome==Outcome.NOT_RUN?3:20+outcome.ordinal();}
        public byte[] toJson(){
            var row=StrictJson.object();row.put("schema","xar.java-finite-first-live-result/v1");
            row.put("request_id",requestId);row.put("machine_id",machineId);row.put("outcome",outcome.name());row.put("detail",detail);
            row.put("exit_code",exitCode());row.put("forward_saved_days",forwardSavedDays);
            before.ifPresentOrElse(value->row.set("before",frontierJson(value)),()->row.putNull("before"));
            after.ifPresentOrElse(value->row.set("after",frontierJson(value)),()->row.putNull("after"));
            batch.ifPresentOrElse(value->row.set("batch",OrdinarySessionResource.report(value)),()->row.putNull("batch"));
            saved.ifPresentOrElse(value->{var data=row.putObject("saved");data.set("pair",StrictJson.parse(CheckpointPairCodec.encode(value.pair())));
                data.set("material",value.material().toJson());data.set("full_driver",value.fullDriver().toJson());
                data.put("sequence",value.sequence());data.put("head_digest",value.headDigest());},()->row.putNull("saved"));
            canonicalSaveReceipt.ifPresentOrElse(value->row.set("canonical_save_receipt",value.toJson()),()->row.putNull("canonical_save_receipt"));
            restored.ifPresentOrElse(value->{var data=row.putObject("restored");data.set("owner",OrdinaryCycleTransitions.sessionToJson(value.owner()));
                data.set("snapshot",org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(value.snapshot()));
                data.set("full_driver",value.fullDriver().toJson());var refs=data.putArray("original_sources");value.originalSources().forEach(ref->refs.add(ref.toJson()));
                data.put("new_saved_day_credit",value.newSavedDayCredit());data.put("new_cycle_credit",value.newCycleCredit());},()->row.putNull("restored"));
            return StrictJson.canonical(row,MAXIMUM_REPORT_BYTES);
        }
        private static com.fasterxml.jackson.databind.node.ObjectNode frontierJson(FrontierFacts value){
            var row=StrictJson.object();row.set("owner",OrdinaryCycleTransitions.sessionToJson(value.owner()));
            row.put("saved_date_raw",value.savedDateRaw());row.put("sequence",value.sequence());row.put("head_digest",value.digest());return row;
        }
    }
    /** Typed stdout DATA for the existing launcher consumer; this creates no live Report or authority. */
    public record DecodedReport(String requestId,String machineId,Outcome outcome,int exitCode,long forwardSavedDays,
            Optional<CheckpointPair> pair,Optional<SessionIdentity> restoredOwner) {
        public DecodedReport { Objects.requireNonNull(requestId);Objects.requireNonNull(machineId);Objects.requireNonNull(outcome);Objects.requireNonNull(pair);Objects.requireNonNull(restoredOwner); }
    }
    public static DecodedReport decodeReport(byte[] original){
        var row=StrictJson.object(StrictJson.parse(Objects.requireNonNull(original),MAXIMUM_REPORT_BYTES),Set.of(
                "schema","request_id","machine_id","outcome","detail","exit_code","forward_saved_days",
                "before","after","batch","saved","canonical_save_receipt","restored"));
        StrictJson.require("xar.java-finite-first-live-result/v1".equals(StrictJson.text(row.get("schema"))),"finite first-live result schema required");
        Outcome outcome=Outcome.valueOf(StrictJson.text(row.get("outcome")));
        int exit=(int)StrictJson.integer(row.get("exit_code"),0,255);
        int expected=outcome==Outcome.COMPLETED?0:outcome==Outcome.NOT_RUN?3:20+outcome.ordinal();
        StrictJson.require(exit==expected,"finite first-live result exit differs from its typed outcome");
        long days=StrictJson.integer(row.get("forward_saved_days"),-StrictJson.MAX_SAFE_INTEGER,StrictJson.MAX_SAFE_INTEGER);
        Optional<CheckpointPair> pair=row.get("saved").isNull()?Optional.empty():Optional.of(
                CheckpointPairCodec.decode(StrictJson.canonical(row.get("saved").get("pair"))));
        Optional<SessionIdentity> owner=row.get("restored").isNull()?Optional.empty():Optional.of(
                OrdinaryCycleTransitions.sessionFromJson(row.get("restored").get("owner")));
        return new DecodedReport(StrictJson.text(row.get("request_id")),StrictJson.text(row.get("machine_id")),outcome,exit,days,pair,owner);
    }
    /** Private construction retains only verified immutable saved DATA, never its material issuer. */
    public static final class SavedBoundary {
        private final SavedFacts facts;
        private final DriverStateSnapshot.Complete driver;
        private SavedBoundary(SavedFacts facts,DriverStateSnapshot.Complete driver){this.facts=facts;this.driver=driver;}
        public SavedFacts facts(){return facts;}
        public CheckpointPair pair(){return facts.pair();}
        public ExactRef materialReference(){return facts.material();}
        public ExactRef driverReference(){return facts.fullDriver();}
    }
    /** Shared real software/Root edge; only current ordinary material supplies its actual cycle proof. */
    public static SavedBoundary requireSavedBoundary(ContinuityStorePort.Session same,SessionIdentity owner,
            CheckpointPair pair,SavedCheckpointMaterialStore materials,ContinuityBatchJournal journal)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(owner);Objects.requireNonNull(pair);
        var material=Objects.requireNonNull(materials).currentPhysical(same,pair);
        materials.requireOwn(material);material.requirePhysical(same);
        if(!(material instanceof SavedAttachmentSourceStore.SavedMaterial ordinary))
            throw new IOException("finite first-live requires the ordinary batch SAVE material");
        var frontier=Objects.requireNonNull(journal).currentSavedFrontier(same,owner,ordinary.proof());
        if(frontier.checkpointRequired()||frontier.pair().isEmpty()||!frontier.pair().orElseThrow().equals(pair))
            throw new IOException("ordinary batch still requires a checkpoint or has another saved frontier");
        if(!ordinary.session().equals(owner)||!ordinary.pair().equals(pair))
            throw new IOException("ordinary saved material belongs to another owner or pair");
        var head=same.head();
        return new SavedBoundary(new SavedFacts(pair,ordinary.reference(),pair.driver().reference(),head.state().sequence(),head.digest()),ordinary.savedDriver());
    }
    private final RootFiniteFirstLiveRequest request;
    private boolean consumed;
    private Optional<FrontierFacts> before=Optional.empty(),after=Optional.empty();
    private Optional<BatchReport> batch=Optional.empty();
    private Optional<SavedFacts> saved=Optional.empty();
    private Optional<ExactRef> canonical=Optional.empty();
    private Optional<RestoredFacts> restored=Optional.empty();
    private long forwardSavedDays;
    private Report result;
    public RootFiniteFirstLiveWork(RootFiniteFirstLiveRequest request){
        this.request=Objects.requireNonNull(request);result=report(Outcome.NOT_RUN,"actual Main has not supplied its admitted lifetime");
    }
    public synchronized Report result(){return result;}
    private Report report(Outcome outcome,String detail){
        return new Report(request.requestId(),request.machineId(),outcome,detail,before,after,forwardSavedDays,batch,saved,canonical,restored);
    }
    private Instant deadline(RootStartupInputsProducer.Actual actual)throws IOException {
        Instant now=actual.clock().instant(),until=now.plus(request.stepTimeout());
        if(request.reviewAt().isBefore(until))until=request.reviewAt();
        if(actual.deadline().isBefore(until))until=actual.deadline();
        if(!now.isBefore(until))throw new IOException("finite first-live step deadline expired");
        return until;
    }
    private static FrontierFacts frontier(RootApplicationSession root,Instant deadline)throws IOException,InterruptedException {
        return root.withPublicStandaloneRead(deadline,same->{var head=same.head();
            return new FrontierFacts(root.identity(),head.state().settledDateRaw(),head.state().sequence(),head.digest());});
    }
    @Override public synchronized void consume(RootStartupInputsProducer.Actual actual)throws Exception {
        Objects.requireNonNull(actual);
        if(consumed)throw new IllegalStateException("finite first-live Work consumes exactly one admitted Main lifetime");
        consumed=true;
        try {consumeActual(actual);}
        catch(Exception failure){result=report(Outcome.FAILED,failure.toString());throw failure;}
    }
    private void consumeActual(RootStartupInputsProducer.Actual actual)throws Exception {
        var original=actual.original();var core=actual.core();
        if(!original.identity().machineId().equals(request.machineId()))throw new IOException("first-live request machine differs from actual Root");
        before=Optional.of(frontier(original,deadline(actual)));
        var execution=original.batch(actual.nextBatch());batch=Optional.of(execution);
        if(execution.terminal()!=BatchReport.Terminal.TURN_BOUND){
            result=report(Outcome.BATCH_STOPPED,"actual ordinary batch terminal: "+execution.terminal()+": "+execution.detail());return;
        }
        after=Optional.of(frontier(original,deadline(actual)));
        forwardSavedDays=Math.subtractExact(after.orElseThrow().savedDateRaw(),before.orElseThrow().savedDateRaw())/24;
        if(forwardSavedDays<request.minimumForwardSavedDays()||execution.committedSavedDays()==0
                ||execution.dirtySinceSave()||execution.lastSavedPair().isEmpty()){
            result=report(Outcome.INSUFFICIENT_SAVE,"actual batch has no requested forward clean paired SAVE");return;
        }
        var pair=execution.lastSavedPair().orElseThrow();
        SavedBoundary boundary=original.withPublicStandaloneRead(deadline(actual),same->{
            var value=requireSavedBoundary(same,original.identity(),pair,original.savedMaterials(),original.batchJournal());
            var retained=core.actions().withFrozen(same,held->{
                var found=held.find(pair.saveActionId());held.assertCurrent();return found;
            });
            var receipt=retained.orElseThrow(()->new IOException("canonical ordinary SAVE receipt is absent"));
            if(receipt.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)throw new IOException("ordinary SAVE is not canonically applied and confirmed");
            var archive=core.archive().withSession(same);var ref=archive.receiptReferenceOf(receipt);
            if(!archive.loadReceipt(ref).equals(receipt))throw new IOException("canonical ordinary SAVE archive changed");
            canonical=Optional.of(ref);return value;
        });
        saved=Optional.of(boundary.facts());
        var requestBody=new RootCheckpointPublicCalls.Request(new RootCheckpointPublicCalls.MissingRevision());
        var restoredCall=core.restoreCheckpointPublic(requestBody,deadline(actual));
        if(restoredCall.actual() instanceof RestoreCheckpointService.Unknown unknown){
            result=report(Outcome.RESTORE_UNKNOWN,unknown.reason());return;
        }
        if(restoredCall.actual() instanceof RestoreCheckpointService.Rejected rejected){
            result=report(Outcome.RESTORE_REJECTED,rejected.reason());return;
        }
        if(!(restoredCall.actual() instanceof RestoreCheckpointService.Restored completed))
            throw new IOException("public restoration returned no supported result branch");
        var replacement=restoredCall.published().orElseThrow(()->new IOException("RESTORE has no published replacement"));
        var installed=actual.catalogFor(replacement);var context=installed.context();var binding=completed.binding();
        if(replacement==original||!original.isRetired()||replacement.isRetired()
                ||replacement.identity().game().equals(original.identity().game())
                ||core.sessionAccess().current()!=replacement||replacement.hostForPublication()!=actual.host()
                ||context.core()!=core||context.writer()!=core.writer()||context.archive()!=core.archive()
                ||context.actions()!=replacement||context.adopted()!=replacement.driver()
                ||!binding.session().equals(replacement.identity())||!binding.pair().equals(pair))
            throw new IOException("RESTORE did not retain its actual new Game, Core, Host, writer, catalog and pair");
        var material=binding.savedMaterial();
        if(material.kind()!=SavedCheckpointMaterial.Kind.ORDINARY||!material.session().equals(original.identity())
                ||!material.reference().equals(boundary.materialReference())
                ||!Arrays.equals(material.savedDriver().encode(),boundary.driver.encode()))
            throw new IOException("RESTORE did not consume the actual ordinary saved material and full Driver");
        long cycleCredit=context.withSession(same->{
            var origin=context.requireRestoredOrigin(same);origin.requireOriginal(same);
            if(origin!=binding.requireReboundOrigin(same)||!origin.evidence().savedOwner().equals(original.identity())
                    ||!origin.evidence().restoredOwner().equals(replacement.identity())||!origin.evidence().pair().equals(pair)
                    ||origin.newSavedDayCredit()!=0||origin.newCycleCredit()!=0||binding.newSavedDayCredit()!=0)
                throw new IOException("actual restored origin is not the same zero-credit ordinary pair");
            material.requireRetained(same);return origin.newCycleCredit();
        });
        var observed=snapshot(replacement,deadline(actual));
        if(!observed.game().equals(replacement.identity().game())
                ||!observed.frame().identity().dateRaw().equals(pair.frame().frame().identity().dateRaw())
                ||!observed.frame().identity().player().equals(pair.frame().frame().identity().player()))
            throw new IOException("replacement native snapshot differs from the actual saved date or actor");
        restored=Optional.of(new RestoredFacts(replacement.identity(),observed,binding.semantic().originalDriver(),
                binding.semantic().references(),binding.newSavedDayCredit(),cycleCredit));
        result=report(Outcome.COMPLETED,"actual ordinary batch advanced and saved; public RESTORE published its real replacement");
    }
    private static ObservationIdentity snapshot(RootApplicationSession root,Instant deadline)throws IOException,InterruptedException {
        return root.withPublicSnapshot(deadline,new RootApplicationSession.SnapshotWork<ObservationIdentity>() {
            @Override public ObservationIdentity ordinary(DriverObservationAssembler.Complete frame,DriverSnapshotFacts.Known known,
                    ContinuityStorePort.Session same){return frame.identity();}
            @Override public ObservationIdentity terminal(DriverObservationAssembler.FullSnapshot frame,LifecycleIdentity identity,
                    DriverSnapshotFacts.Known known,ContinuityStorePort.Session same)throws IOException {
                throw new IOException("restored replacement has a terminal native snapshot");
            }
        });
    }
}
