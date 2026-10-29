package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.family.FamilyRootCurrentFrame;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRootBinding;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Context;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Family and first-heir adapters borrow Finance's identical campaign-root contract and its raw receipt. */
public final class RootFamilyCampaignRead implements FamilyPorts.ProjectedSource {
    private static final Obj EMPTY=new Obj(Map.of());
    private static final Obj ROOT_ARGUMENTS=FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY);
    private static final List<String> MIRRORS=List.of("schema_version","date_raw","local_player_id","player_character_id","player_character_alive",
            "player_monthly_gold_income","player_health","player_domain_size","player_domain_limit","player_targeting_faction_count","council","primary_title",
            "primary_title_succession_character_ids","held_title_partition","capital_province_id","immediate_liege_character_id","top_liege_character_id","independent",
            "direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids","related_character_contexts","government","selected_game_rule_tokens",
            "native_selected_game_rule_token_count","readiness","unavailable_reason","provenance");
    private final RootRuntimeContext context;
    private record HistoricalTarget(GuardEvidence guard,Complete frame) { }
    @FunctionalInterface public interface OriginalWork<T> {T run() throws IOException;}
    private final ThreadLocal<HistoricalTarget> historical=new ThreadLocal<>();
    private final FamilyRootBinding.Originals originals=new FamilyRootBinding.Originals() {
        @Override public PlanningReadResult.Known<Obj> read(ExactRef ref){return original(ref);}
        @Override public FamilyRootBinding.Basis bind(ExactRef ref,Context target){return RootFamilyCampaignRead.this.bind(original(ref),target);}
    };
    public FamilyRootBinding.Originals originals(){return originals;}
    /** Reopens an actual leaf guard and full original frame, without minting current readiness. */
    public <T> T withHistoricalTarget(Session same,GuardEvidence guard,Complete frame,OriginalWork<T> work)throws IOException {
        context.writer().requireSession(same);var archive=context.archive().withSession(same);
        RootGuardEvidence.requireHistory(guard,archive,same);
        var reopened=RootGuardEvidence.loadFrame(guard,archive,context.frameLoader());
        StrictJson.require(reopened.equals(frame)&&guard.observed().equals(frame.identity()),"historical ROOT target lacks its exact original guard/full frame");
        var previous=historical.get();historical.set(new HistoricalTarget(guard,frame));
        try{return work.run();}finally{if(previous==null)historical.remove();else historical.set(previous);}
    }
    public <T> T replayAt(PlanningReadReceipt leaf,OriginalWork<T> work) {
        try {
            var same=context.borrowedSession();var archive=context.archive().withSession(same);
            NativeRecordedEvidenceVerifier.requireRead(leaf,archive);var guard=leaf.before().binding();
            var frame=RootGuardEvidence.loadFrame(guard,archive,context.frameLoader());
            return withHistoricalTarget(same,guard,frame,work);
        } catch(IOException failure){throw new UncheckedIOException("actual leaf ROOT replay target unavailable",failure);}
    }
    /** Before INTENT exists the genuine retained leaf supplies the target guard. */
    public GuardEvidence freshTarget(Session same,ActionCommand command,Complete frame,List<ExactRef> retained)throws IOException {
        var archive=context.archive().withSession(same);
        for(var ref:retained) {
            var read=archive.loadRead(ref);NativeRecordedEvidenceVerifier.requireRead(read,archive);
            if(!read.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID)&&read.request().before().equals(command.before())
                    &&read.request().source().equals(command.source())&&read.request().sessionId().equals(command.sessionId())) {
                StrictJson.require(archive.readReferenceOf(read).equals(ref),"fresh target receipt source differs");
                var guard=read.before().binding();RootGuardEvidence.requireHistory(guard,archive,same);
                StrictJson.require(RootGuardEvidence.loadFrame(guard,archive,context.frameLoader()).equals(frame),"fresh leaf does not retain the actual full command frame");
                return guard;
            }
        }
        throw new IOException("fresh ROOT replay has no actual non-ROOT target guard");
    }
    public void requireFreshOriginal(Session same,PlanningReadReceipt root,ActionCommand command,Complete target,List<ExactRef> retained)throws IOException {
        requireOriginal(root);StrictJson.require(target.identity().equals(command.before())&&target.source().equals(command.source())
                &&target.sessionId().equals(command.sessionId()),"fresh ROOT target differs from actual command");
        var guard=freshTarget(same,command,target,retained);
        withHistoricalTarget(same,guard,target,()->{qualify(same,root,target.identity(),command.deadline());return null;});
    }
    public FamilyRootBinding.Basis bind(PlanningReadResult.Known<Obj> root,Context target) {
        try {
            var same=context.borrowedSession();
            if(root.receipt().request().before().equals(target.before()))return FamilyRootBinding.fromOriginal(root,target);
            var origin=historical.get()==null?FamilyRootBinding.QualifiedOrigin.CURRENT_CANONICAL_READ:FamilyRootBinding.QualifiedOrigin.HISTORICAL_CANONICAL_READ;
            return FamilyRootBinding.fromQualifiedOriginal(root,target,new FamilyRootBinding.ReadLineageAdmission(){
                @Override public FamilyRootBinding.QualifiedOrigin origin(){return origin;}
                @Override public void verifyOriginal(PlanningReadResult.Known<Obj> original,Context actual) {
                    try {
                        StrictJson.require(original.originalReceipt().equals(root.originalReceipt())&&original.receipt().equals(root.receipt())
                                &&actual.equals(target),"ROOT lineage callback changed its original or target");
                        qualify(same,original.receipt(),actual.before(),actual.deadline());
                    } catch(IOException failure){throw new UncheckedIOException(failure);}
                }
            });
        } catch(IOException failure){throw new UncheckedIOException("actual family ROOT lineage unavailable",failure);}
    }
    void requireCurrentOriginal(Session same,PlanningReadReceipt original,PlanningReadRequest target)throws IOException {
        StrictJson.require(original.request().source().equals(target.source())&&original.request().sessionId().equals(target.sessionId()),"current ROOT source/session changed");
        qualify(same,original,target.before(),target.deadline());
    }
    private void qualify(Session same,PlanningReadReceipt original,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity target,java.time.Instant deadline)throws IOException {
        requireOriginal(original);context.writer().requireSession(same);var archive=context.archive().withSession(same);
        NativeRecordedEvidenceVerifier.requireRead(original,archive);var ref=archive.readReferenceOf(original);
        if(original.request().before().equals(target))return;
        var actual=historical.get();
        if(actual!=null) {
            StrictJson.require(actual.frame().identity().equals(target),"historical ROOT scope selected another actual target");
            var proof=context.readHistoryPublisher().requireHistoricalReadOnlyExtension(same,original,actual.guard(),actual.frame()).requireHistorical(same);
            StrictJson.require(proof.originalRead().equals(original)&&proof.originalReceipt().equals(ref)&&proof.targetObserved().equals(actual.frame()),"historical ROOT proof changed original endpoints");
        } else {
            var contract=context.finance().definitions().contract(FinanceReadContracts.Query.ROOT);
            var request=new PlanningReadRequest(target,original.request().source(),original.request().sessionId(),FinanceReadContracts.Query.ROOT.operation(),ROOT_ARGUMENTS,deadline);
            var witness=context.readHistoryPublisher().canonicalReadWitness(same,contract,request).orElseThrow(()->new IOException("ROOT has no actual current canonical READ witness"));
            var known=witness.requireCurrent(same,contract,request);
            StrictJson.require(known.originalReceipt().equals(ref)&&known.receipt().equals(original),"current canonical ROOT witness selected another original");
        }
    }
    private Obj currentView(Session same,Obj raw,PlanningReadReceipt receipt,ExactRef ref,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity target,java.time.Instant deadline)throws IOException {
        qualify(same,receipt,target,deadline);
        if(receipt.request().before().equals(target))return raw;
        StrictJson.require(context.archive().withSession(same).readReferenceOf(receipt).equals(ref),"ROOT current DATA changed original receipt reference");
        return raw.with(FamilyRootCurrentFrame.FIELD,FamilyRootCurrentFrame.observed(ref,receipt.request().before(),target).toJson());
    }

    public RootFamilyCampaignRead(RootRuntimeContext context) {this.context=Objects.requireNonNull(context);}
    public void requireContext(RootRuntimeContext actual) {StrictJson.require(context==actual,"shared campaign ROOT belongs to another physical Game context");}
    /** Call once before the leaf read; the leaf stores this original receipt reference in its canonical arguments. */
    public PlanningReadResult<Obj> current(Session same,PlanningReadRequest leaf) {
        try {
            context.requireCurrent(leaf.deadline());context.writer().requireSession(same);
            StrictJson.require(same==context.borrowedSession() && leaf.source().equals(context.source())
                    && leaf.sessionId().equals(context.game().sessionId()),"shared campaign root escaped the current physical Game/writer");
            var definitions=context.finance().definitions();var contract=definitions.contract(FinanceReadContracts.Query.ROOT);
            var request=publicRootRequest(leaf);
            var actual=context.finance().readPort().read(same,contract,request);context.writer().requireSession(same);
            if(actual instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known) {
                StrictJson.require(known.value().receipt().equals(known.receipt()),"campaign Packet lost its original receipt");
                return new PlanningReadResult.Known<>(currentView(same,project(known.value().result(),known.receipt()),known.receipt(),known.originalReceipt(),request.before(),request.deadline()),known.receipt(),known.originalReceipt());
            }
            var unavailable=(PlanningReadResult.Unavailable<FinanceReadContracts.Packet>)actual;
            return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
        } catch(IOException failure) {throw new UncheckedIOException("actual shared campaign root unavailable",failure);}
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest request,Obj familyArguments) {
        StrictJson.require(familyArguments.members().keySet().equals(java.util.Set.of("expected_revision"))
                && new IntegerValue(request.before().frame().revision()).equals(familyArguments.get("expected_revision")),"family root expected public revision differs");
        try {
            var same=context.borrowedSession();
            return new FamilyPorts.ProjectedRead(ROOT_ARGUMENTS,current(same,new PlanningReadRequest(request.before(),request.source(),request.sessionId(),
                    FinanceReadContracts.Query.ROOT.operation(),ROOT_ARGUMENTS,request.deadline())));
        } catch(IOException failure) {throw new UncheckedIOException(failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original) {
        var actual=context.finance().definitions().decodeOriginal(FinanceReadContracts.Query.ROOT,original,EMPTY);
        Obj raw=project(actual.result(),original);var target=historical.get();
        if(target==null)return raw;
        try {var same=context.borrowedSession();return currentView(same,raw,original,context.archive().withSession(same).readReferenceOf(original),target.frame().identity(),original.request().deadline());}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    /** Reopens this exact immutable ROOT receipt; leaf decoders must never execute a replacement root query. */
    public PlanningReadResult.Known<Obj> original(org.xar.ck3.control.contracts.ExactRef reference) {
        try {
            var same=context.borrowedSession();context.writer().requireSession(same);var archive=context.archive().withSession(same);
            var receipt=archive.loadRead(reference);StrictJson.require(archive.readReferenceOf(receipt).equals(reference),"family root archive identity differs");
            var packet=context.finance().definitions().decodeOriginal(FinanceReadContracts.Query.ROOT,receipt,EMPTY);
            NativeRecordedEvidenceVerifier.requireRead(receipt,archive);
            return new PlanningReadResult.Known<>(project(packet.result(),receipt),receipt,reference);
        } catch(IOException failure) {throw new UncheckedIOException(failure);}
    }
    /** Same outer DTO mirrors as the original public producer; absent baseline fields remain absent. */
    public static Obj project(Obj normalizedEnvelope,PlanningReadReceipt original) {
        requireOriginal(original);
        Obj root=OpportunityJson.object(normalizedEnvelope.get("campaign_root_context"),"normalized shared root");
        Obj cache=org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.campaignRootFromOriginal(original);
        StrictJson.require(root.equals(cache.get("campaign_root_context")) && Objects.equals(normalizedEnvelope.get("query_sequence"),cache.get("query_sequence")),"family root differs from the one original cache producer");
        Obj result=normalizedEnvelope;for(String key:MIRRORS)if(root.members().containsKey(key))result=result.with(key,root.get(key));
        if(cache.members().containsKey("player_heir_fixed_dynasty_projection_v1"))result=result.with("player_heir_fixed_dynasty_projection_v1",cache.get("player_heir_fixed_dynasty_projection_v1"));
        Obj readiness=OpportunityJson.object(root.get("readiness"),"actual root readiness");
        var frame=original.request().before().frame();
        return result.with("campaign_root_context_ready",new Bool(OpportunityJson.bool(readiness.get("ready"),"root ready")))
                .with("queried_snapshot_id",new Text(frame.snapshotId())).with("queried_revision",new IntegerValue(frame.revision()))
                .with("queried_native_revision",new IntegerValue(frame.identity().nativeRevision()));
    }
    static PlanningReadRequest publicRootRequest(PlanningReadRequest leaf) {
        Objects.requireNonNull(leaf);return new PlanningReadRequest(leaf.before(),leaf.source(),leaf.sessionId(),FinanceReadContracts.Query.ROOT.operation(),ROOT_ARGUMENTS,leaf.deadline());
    }
    static void requireOriginal(PlanningReadReceipt receipt) {
        var request=receipt.request();StrictJson.require(request.operation().equals(FinanceReadContracts.Query.ROOT.operation())
                && receipt.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID)
                && FinanceReadContracts.rootCapture(request.arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY && receipt.original().nativeOk(),"actual canonical campaign root read required");
        for(var guard:List.of(receipt.before(),receipt.after()))StrictJson.require(guard.paused() && guard.mapReady() && guard.playerAlive()
                && guard.binding().operation().equals(request.operation()) && guard.binding().source().equals(request.source())
                && guard.binding().sessionId().equals(request.sessionId()) && guard.binding().observed().equals(request.before()),"campaign root lost original source/frame/session guards");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()),"campaign root crossed the held connection or full binding");
    }
}
