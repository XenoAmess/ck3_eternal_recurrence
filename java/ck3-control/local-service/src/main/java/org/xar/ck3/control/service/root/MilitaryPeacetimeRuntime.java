package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsBoundary;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly;
import org.xar.ck3.control.wave3.planning.m5peacetimeassembly.M5FamilyCandidatePool;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScope;
import org.xar.ck3.control.wave3.planning.peacetimescope.PeacetimeScopeCodec;

/** One real M5 aggregate of the already installed construction, finance and family producers.
 * No query, command preparer, ledger writer or family planner is duplicated here. */
public final class MilitaryPeacetimeRuntime implements M5PeacetimePolicy.SourceCollector {
    private final RootRuntimeContext context;
    private final ConstructionRuntimeInstaller construction;
    private final FamilyRuntimeInstaller family;
    private final M5PeacetimePolicy.Consumers consumers;
    private final M5PeacetimePolicy.Options options;
    private Pending pending;
    private record Pending(PlanningRequest request,Session writer,String head,M5PeacetimePolicy.Prior aggregate,
            ConstructionPeacetimeSources.Prior construction) { }
    public MilitaryPeacetimeRuntime(RootRuntimeContext current,ConstructionRuntimeInstaller sameConstruction,
            FamilyRuntimeInstaller sameFamily,OrdinaryPolicy actualGift,M5PeacetimePolicy.Options options) {
        context=Objects.requireNonNull(current);construction=Objects.requireNonNull(sameConstruction);family=Objects.requireNonNull(sameFamily);
        this.options=Objects.requireNonNull(options);
        List<OrdinaryPolicy> tracked=construction.install().policies().stream().filter(p->p.stage()==PlanningStage.CONSTRUCTION).toList();
        StrictJson.require(tracked.size()==1,"M5 requires the sole installed tracked construction policy");
        consumers=new M5PeacetimePolicy.Consumers(tracked.getFirst(),Objects.requireNonNull(actualGift),family.ordinary());
    }
    public M5PeacetimePolicy policy(ExactRef source,MilitaryPlanningDecision.ApplicationAdapter originalReads) {
        return new M5PeacetimePolicy(source,options,this,consumers,originalReads);
    }
    public void requireContext(RootRuntimeContext actual){StrictJson.require(context==actual,"M5 aggregate belongs to another physical Root runtime");}
    @Override public synchronized M5PeacetimePolicy.Prior prior(PlanningRequest request,OrdinaryPolicy.Draft original) {
        Objects.requireNonNull(original);
        try{return context.withSession(same->{
            context.requireCurrent(request.deadline());context.writer().requireSession(same);
            var build=construction.m5Prior(same,request);
            var ledgers=ledgers(same,request,build.ledger().original());
            var actual=new M5PeacetimePolicy.Prior(ledgers,build.release());
            pending=new Pending(request,same,same.head().digest(),actual,build);return actual;
        });}catch(IOException unavailable){throw new UncheckedIOException("actual M5 prior sources unavailable",unavailable);}
    }
    @Override public synchronized M5PeacetimePolicy.Capture capture(PlanningRequest request,OrdinaryPolicy.Draft original,M5PeacetimePolicy.Prior before) {
        Pending held=pending;pending=null;
        StrictJson.require(held!=null&&held.request()==request&&held.aggregate()==before,"M5 capture requires its exact actual prior producer invocation");
        try{return context.withSession(same->{
            context.requireCurrent(request.deadline());context.writer().requireSession(same);
            StrictJson.require(same==held.writer()&&same.head().digest().equals(held.head()),"M5 aggregate changed original writer or canonical head");
            var build=construction.m5Capture(same,request,held.construction());
            var faction=faction(same,request);
            var relationship=relationship(request,original);
            var after=ledgers(same,request,build.after().original());
            Obj ending=context.collector().currentPlanning(same,request,request.deadline(),(exact,current)->current.frame().semantic());
            var scope=new PeacetimeScopeCodec.Request(PeacetimeScopeCodec.project(request.observations().snapshot()),request.before().frame().revision(),
                    new PeacetimeScope.Observed(PeacetimeScopeCodec.project(ending)));
            StrictJson.require(same.head().digest().equals(held.head()),"M5 native collection changed its original canonical body head");
            var actual=new PeacetimeAssembly.Inputs(scope,request.observations().snapshot(),original.detail(),before.ledgers(),after,before.constructionRelease(),
                    build.construction(),faction,relationship);
            // Compose now, while these exact original bodies and current writer are still held.
            PeacetimeAssembly.compose(actual);
            return new M5PeacetimePolicy.Capture(actual,build.cash(),Optional.empty());
        });}catch(IOException unavailable){throw new UncheckedIOException("actual M5 proposal sources unavailable: " + unavailable.getMessage(),unavailable);}
    }
    private PeacetimeAssembly.Ledgers ledgers(Session same,PlanningRequest request,Obj actualConstruction) {
        var state=context.finance().collector().state(same,request);
        if(!(state instanceof FinanceStatePort.Known known))throw new IllegalStateException("actual M5 finance bodies unavailable: "+state);
        var gift=known.snapshot().ledger(FinanceStatePort.Domain.FACTION_GIFT).orElseThrow(()->new IllegalStateException("actual M5 faction body missing"));
        var documents=family.documents(request);
        if(!(documents instanceof FamilyPorts.KnownDocuments present))throw new IllegalStateException("actual M5 family bodies unavailable: "+documents);
        var familyBodies=present.documents();
        StrictJson.require(known.snapshot().head().canonicalHead().equals(familyBodies.canonicalHead()),"M5 family and finance original bodies crossed their actual writer head");
        return new PeacetimeAssembly.Ledgers(actualConstruction,gift.original(),familyBodies.family(),familyBodies.childDefault());
    }
    private PeacetimeAssembly.Faction faction(Session same,PlanningRequest request) {
        return captureFaction(request,options.giftEnabled(),query->packet(same,query,request).result());
    }

    /** The same typed read boundary is used by the original Session-bound capture and software regressions.
     * It returns original result objects; it grants neither Native nor action authority. */
    @FunctionalInterface interface FactionQueries { Obj read(FinanceReadContracts.Query query); }

    static PeacetimeAssembly.Faction captureFaction(PlanningRequest request,boolean giftEnabled,FactionQueries queries) {
        Objects.requireNonNull(request);Objects.requireNonNull(queries);
        if(!giftEnabled)return new PeacetimeAssembly.Faction(PeacetimeAssembly.FactionStatus.CONSUMER_DISABLED,
                OrdinaryFinanceCollector.obj("status",new Text("consumer_disabled")));
        Obj result=queries.read(FinanceReadContracts.Query.ROOT);
        Obj actual=OpportunityJson.object(result.get("campaign_root_context"),"actual M5 campaign root");
        if(new Text("unavailable").equals(actual.get("status")))return new PeacetimeAssembly.Faction(PeacetimeAssembly.FactionStatus.SAME_FRAME_ROOT_UNAVAILABLE,
                OrdinaryFinanceCollector.obj("status",new Text("same_frame_root_unavailable"),"actual_root",actual));
        var identity=request.before().frame().identity();
        var root=FactionCandidateCodec.decodeRootProjection(OpportunityJson.encode(actual));
        var current=new FactionCandidatePolicy.Frame(identity.nativeRevision(),identity.dateRaw(),identity.player());
        var view=FactionCandidatePolicy.latestSameFrameRoot(new FactionCandidatePolicy.RootSearch(Optional.of(current),
                List.of(new FactionCandidatePolicy.RootHistory(new Text("available").equals(result.get("status")),root))));
        if(view.status()==FactionCandidatePolicy.RootStatus.KNOWN_EMPTY)
            return new PeacetimeAssembly.Faction(PeacetimeAssembly.FactionStatus.KNOWN_EMPTY,
                    OrdinaryFinanceCollector.obj("status",new Text("known_empty"),"reason",new Text("same_frame_public_targeting_count_zero"),
                            "public_capability_advertised",new Bool(false),"gift_submission_enabled",new Bool(false)));
        StrictJson.require(view.status()==FactionCandidatePolicy.RootStatus.TARGETING_PRESENT,
                "M5 peacetime source lacks a complete same-frame feudal faction root: "+view.status().wire());
        Obj candidate=queries.read(FinanceReadContracts.Query.FACTION_GIFT);
        var observed=FactionCandidateCodec.evaluatePrivateCandidate(OpportunityJson.encode(request.observations().snapshot()),
                root,OpportunityJson.encode(candidate),BigInteger.valueOf(10000000));
        Obj encoded=DriverJson.object(FactionCandidateCodec.encodeCandidateResult(observed),RawJson.MAXIMUM_BYTES);
        if(new Text("selected").equals(encoded.get("status"))) {
            Obj enriched=encoded.with("stock_threat_response",stockThreat(request,encoded,queries).toJson());
            return new PeacetimeAssembly.Faction(PeacetimeAssembly.FactionStatus.SELECTED,enriched);
        }
        if(new Text("no_legal_candidate").equals(encoded.get("status"))&&encoded.get("observation") instanceof Obj)
            return new PeacetimeAssembly.Faction(PeacetimeAssembly.FactionStatus.NO_LEGAL_CANDIDATE,encoded);
        // The original Rejected NO_DIRECT_LANDED_MEMBER variant lacks an observation. Do not invent one or relabel it as empty.
        throw new IllegalStateException("actual M5 faction producer has no complete assembly variant: "+encoded);
    }

    private sealed interface StockThreat permits ObservedThreat,MissingThreat { Obj toJson(); }
    /** A validated non-dangerous row remains an observation; it is not a missing-input default. */
    private record ObservedThreat(FactionAlertModel.Available frame,FactionAlertModel.TargetingFaction row,
            Obj nativeRow,BigInteger recipient,boolean historyReused) implements StockThreat {
        @Override public Obj toJson() {
            return OrdinaryFinanceCollector.obj("status",new Text("observed"),"observer_step",new Text(FactionAlertModel.STEP),
                    "same_frame_history_reused",new Bool(historyReused),"source_faction_id",n(row.factionId()),
                    "recipient_character_id",new IntegerValue(recipient),"snapshot_revision",new IntegerValue(frame.snapshotRevision()),
                    "date_raw",n(frame.dateRaw()),"player_character_id",n(frame.playerCharacterId()),
                    "dangerous_response_ready",new Bool(row.dangerous()&&!row.factionAtWar()),"native_row",nativeRow,
                    "exact_ultimatum_timing_ready",new Bool(false),"faction_departure_or_threat_resolution",new Text("not_inferred"));
        }
    }
    private record MissingThreat(String reason,Optional<String> observerError) implements StockThreat {
        private MissingThreat { StrictJson.text(reason);Objects.requireNonNull(observerError); }
        @Override public Obj toJson() {
            Obj value=OrdinaryFinanceCollector.obj("status",new Text("unavailable"),"dangerous_response_ready",new Bool(false),
                    "exact_ultimatum_timing_ready",new Bool(false),"reason",new Text(reason));
            return observerError.map(error->value.with("observer_error",new Text(error))).orElse(value);
        }
    }
    private static StockThreat stockThreat(PlanningRequest request,Obj candidate,FactionQueries queries) {
        Obj observed=null;boolean reused=false;
        var history=OrdinaryHistory.collect(request.observations().history()).rows();
        for(int index=history.size()-1;index>=0;index--) {
            Obj row=history.get(index);
            if(!OrdinaryHistory.successful(row)||!OrdinaryHistory.effectiveCommand(row).filter(FactionAlertModel.STEP::equals).isPresent())continue;
            var result=OrdinaryHistory.effectiveCommandResult(row);
            if(result.isPresent()&&result.orElseThrow().get("player_faction_alerts") instanceof Obj alert&&sameFactionFrame(request,alert)) {
                observed=result.orElseThrow();reused=true;break;
            }
        }
        try {
            if(observed==null)observed=queries.read(FinanceReadContracts.Query.FACTION_ALERTS);
            var identity=request.before().frame().identity();
            var expected=new FactionAlertModel.ExpectedFrame(identity.dateRaw().intValueExact(),identity.nativeRevision(),
                    Optional.of(FactionAlertModel.Build.CK3_12004));
            var projection=reused?FactionAlertsBoundary.normalizeExistingDriverResult(OpportunityJson.encode(observed),expected,
                    OpportunityJson.encode(request.observations().snapshot().get("active_wars"))):
                    FactionAlertsBoundary.normalizeCurrentNativeResult(OpportunityJson.encode(observed),expected,
                            OpportunityJson.encode(request.observations().snapshot().get("active_wars"))).projection();
            if(!(projection.frame() instanceof FactionAlertModel.Available available))
                return new MissingThreat("same_frame_stock_threat_not_observed",Optional.empty());
            StrictJson.require(available.playerCharacterId()==identity.player().intValueExact(),"M5 faction alert actor drift");
            if(!available.readiness().targetingRowsReady()||!available.readiness().stockDangerousReady()||!available.readiness().sameFrameReady())
                return new MissingThreat("same_frame_stock_threat_not_observed",Optional.empty());
            Obj choice=OpportunityJson.object(candidate.get("choice"),"selected M5 gift choice");
            BigInteger factionId=OpportunityJson.integer(choice.get("source_faction_id"),"selected faction");
            BigInteger recipient=OpportunityJson.integer(choice.get("recipient_character_id"),"selected recipient");
            var matches=available.targetingFactions().stream().filter(row->BigInteger.valueOf(row.factionId()).equals(factionId)).toList();
            if(matches.size()!=1)return new MissingThreat("selected_faction_not_in_current_alert",Optional.empty());
            var selected=matches.getFirst();
            if(selected.targetCharacterId()!=available.playerCharacterId()
                    ||selected.leaderCharacterId().filter(id->BigInteger.valueOf(id).equals(recipient)).isEmpty()
                    &&!selected.characterMemberIds().contains(recipient.intValueExact()))
                return new MissingThreat("selected_recipient_not_in_current_faction",Optional.empty());
            Obj normalized=DriverJson.object(projection.normalizedAlertJson(),RawJson.MAXIMUM_BYTES);
            Obj nativeRow=OpportunityJson.array(normalized.get("targeting_factions"),"observed targeting factions").stream()
                    .map(value->OpportunityJson.object(value,"observed native faction"))
                    .filter(row->new IntegerValue(factionId).equals(row.get("faction_id"))).findFirst().orElseThrow();
            return new ObservedThreat(available,selected,nativeRow,recipient,reused);
        }catch(PreSubmissionRevisionMismatchException changed){throw changed;}
        catch(IllegalArgumentException|IllegalStateException|UncheckedIOException|ArithmeticException unavailable) {
            return new MissingThreat("existing_alert_read_unavailable",Optional.of(unavailable.getMessage()==null
                    ?unavailable.getClass().getSimpleName():unavailable.getMessage()));
        }
    }
    private static boolean sameFactionFrame(PlanningRequest request,Obj alert) {
        var identity=request.before().frame().identity();
        return new IntegerValue(identity.nativeRevision()).equals(alert.get("snapshot_revision"))
                &&new IntegerValue(identity.dateRaw()).equals(alert.get("date_raw"))
                &&new IntegerValue(identity.player()).equals(alert.get("player_character_id"));
    }
    private static IntegerValue n(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private FinanceReadContracts.Packet packet(Session same,FinanceReadContracts.Query query,PlanningRequest request) {
        var observed=context.finance().collector().query(same,query,request);
        if(!(observed instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> known))throw new IllegalStateException("actual M5 native source unavailable: "+query);
        var packet=known.value();var original=packet.receipt().request();
        StrictJson.require(original.before().equals(request.before())&&original.source().equals(request.source())&&original.sessionId().equals(request.sessionId())
                &&original.operation().equals(query.operation()),"M5 actual original read crossed its complete request binding");
        return packet;
    }
    private PeacetimeAssembly.Family relationship(PlanningRequest request,OrdinaryPolicy.Draft original) {
        if(!options.familyEnabled())return new PeacetimeAssembly.Family("consumer_disabled",Optional.empty(),List.of());
        var decision=consumers.family().evaluate(request,original);
        OrdinaryPolicy.Draft result=decision instanceof OrdinaryPolicy.Replace replace?replace.draft():decision instanceof OrdinaryPolicy.Annotate annotate?annotate.retained():null;
        if(result==null) {
            if(decision instanceof OrdinaryPolicy.Keep||decision instanceof OrdinaryPolicy.NotApplicable)
                return new PeacetimeAssembly.Family("actual_consumer_retained_baseline",Optional.empty(),List.of());
            org.xar.ck3.control.application.planning.family.FamilyOrdinaryPolicy.propagateSourceContractFailure(decision);
            throw new IllegalStateException("actual M5 family source requires its independent continuation: "+decision);
        }
        if(new Text(M5PeacetimePolicy.FAMILY).equals(result.detail().get("selected_step")))return M5FamilyCandidatePool.collect(result.detail()).family();
        String status=result.detail().get("family_marriage_status") instanceof Text actual?actual.value():"no_approved_proposal";
        return new PeacetimeAssembly.Family(status,Optional.empty(),List.of());
    }
}
