package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.application.planning.prisoners.PrisonerOrdinaryPolicy12004;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;

/** Ordinary root observation only. The actual natural producer still captures the original estate before resume. */
public final class RootSuccessionPlanningPolicies {
    private static final OperationKey RELEASE=PrisonerOrdinaryPolicy12004.RELEASE;
    private static final String DEFERRED="succession_deferred_root_required";
    private static final String OBSERVATION="succession_preflight_observation";
    @FunctionalInterface interface CurrentScope {void require(PlanningRequest request)throws IOException;}
    @FunctionalInterface interface ReleaseEligibility {boolean ready(PlanningRequest request);}
    @FunctionalInterface interface RootReader {
        RootRead read(PlanningRequest request)throws IOException;
        default Optional<Observed> retained(PlanningRequest request)throws IOException{return Optional.empty();}
    }
    sealed interface RootRead permits Observed,Unavailable,AwaitingPublication { }
    record Unavailable(String reason) implements RootRead {Unavailable{StrictJson.text(reason);}}
    record AwaitingPublication(String reason) implements RootRead {AwaitingPublication{StrictJson.text(reason);}}
    /** This is source-bound observed DATA, never a persisted expectation, lifecycle or action admission. */
    static final class Observed implements RootRead {
        final ObservationIdentity frame;final G2Source source;final String session;
        final ExactRef originalRead;final byte[] estate;
        Observed(PlanningRequest request,ExactRef originalRead,SuccessionNativeEstate12004.FrozenEstate projection) {
            var binding=Objects.requireNonNull(projection).expectation().binding();var actual=request.before().frame();
            StrictJson.require(binding.frame().snapshotId().equals(actual.snapshotId())&&binding.frame().revision().equals(actual.revision())
                    &&binding.frame().nativeRevision().equals(actual.identity().nativeRevision())&&binding.frame().dateRaw()==actual.identity().dateRaw().intValueExact()
                    &&binding.episodeRunId().equals(actual.episodeRunId())&&binding.episodeCharacterId()==actual.identity().player().intValueExact(),
                    "observed estate data differs from its actual source frame/episode/actor");
            frame=request.before();source=request.source();session=request.sessionId();this.originalRead=Objects.requireNonNull(originalRead);estate=projection.wire();
        }
        boolean sameNative(PlanningRequest current) {
            var before=frame.frame();var after=current.before().frame();
            return source.equals(current.source())&&session.equals(current.sessionId())&&frame.machineId().equals(current.before().machineId())
                    &&frame.game().equals(current.before().game())&&frame.observationVersion()==current.before().observationVersion()
                    &&before.episodeRunId().equals(after.episodeRunId())&&before.snapshotId().equals(after.snapshotId())
                    &&before.identity().equals(after.identity());
        }
        OpportunityJson.Obj detail() {
            return new OpportunityJson.Obj(Map.of("schema",new OpportunityJson.Text("xar.java.succession-preflight-root-observation/v1"),
                    "original_read",OpportunityJson.parse(StrictJson.canonical(originalRead.toJson())),
                    "estate",OpportunityJson.parse(estate),"persisted_expectation",new OpportunityJson.Bool(false),
                    "natural_succession_authority",new OpportunityJson.Bool(false),"business_submission",new OpportunityJson.Bool(false)));
        }
    }
    private final ExactRef implementation;
    private final CurrentScope current;
    private final ReleaseEligibility release;
    private final RootReader roots;
    private final ThreadLocal<PlanningRequest> deferredPlan=new ThreadLocal<>();
    private final List<OrdinaryPolicy> policies;

    /** The original Root and its original lifecycle/finance/prisoner products are required together. */
    public static RootSuccessionPlanningPolicies install(ExactRef implementation,RootRuntimeContext context,
            RootLifecycleRuntimeFactory.Installed lifecycle,PrisonersRuntimeInstaller prisoners)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(lifecycle);Objects.requireNonNull(prisoners);lifecycle.requireContext(context);
        var contract=context.finance().definitions().contract(FinanceReadContracts.Query.ROOT);
        return new RootSuccessionPlanningPolicies(implementation,request->{
            lifecycle.requireContext(context);context.requireCurrent(request.deadline());context.writer().requireSession(context.borrowedSession());
            StrictJson.require(request.source().equals(context.source())&&request.before().game().equals(context.game().generation())
                    &&request.sessionId().equals(context.game().sessionId())&&context.readCatalog().containsIdentity(contract),
                    "succession preflight must retain the same actual Root/Game/source and installed root contract");
        },prisoners::retainedReleaseReady,new ActualRoots(context,contract));
    }
    /** Every reuse requires the actual publisher's private current witness and the original typed ROOT decoder. */
    private static final class ActualRoots implements RootReader {
        private final RootRuntimeContext context;private final ReadContract<FinanceReadContracts.Packet> contract;
        ActualRoots(RootRuntimeContext context,ReadContract<FinanceReadContracts.Packet> contract){this.context=context;this.contract=contract;}
        @Override public Optional<Observed> retained(PlanningRequest request)throws IOException {
            var same=context.borrowedSession();
            return context.collector().currentPlanning(same,request,request.deadline(),(exact,lease)->{
                StrictJson.require(exact==request&&lease.frame().semantic().equals(request.observations().snapshot()),"retained root requires the actual complete current planning frame");
                var archive=context.archive().withSession(same);
                var current=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),contract.operation(),
                        FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),request.deadline());
                var found=context.readHistoryPublisher().canonicalReadWitness(same,contract,current);
                if(found.isEmpty())return Optional.empty();
                var witness=found.orElseThrow();var canonical=witness.requireCurrent(same,contract,current);
                var replayed=witness.originalContract().replay(canonical.receipt());
                StrictJson.require(replayed.receipt().equals(canonical.receipt())&&replayed.result().equals(canonical.value().result())
                        &&replayed.originalResult().equals(canonical.value().originalResult()),"original installed ROOT decoder changed its complete canonical packet");
                if(!new OpportunityJson.Text("available").equals(replayed.result().get("status")))return Optional.empty();
                NativeRecordedEvidenceVerifier.requireRead(canonical.receipt(),archive);
                var estate=SuccessionNativeEstate12004.freeze(DriverJson.encode(replayed.originalResult()),DriverJson.encode(lease.frame().semantic()));
                return Optional.of(new Observed(request,canonical.originalReceipt(),estate));
            });
        }
        @Override public RootRead read(PlanningRequest request)throws IOException {
            var same=context.borrowedSession();
            return context.collector().currentPlanning(same,request,request.deadline(),(exact,lease)->{
                StrictJson.require(exact==request&&lease.frame().semantic().equals(request.observations().snapshot()),"succession root observation crossed its actual complete planning frame");
                var result=context.finance().collector().query(same,FinanceReadContracts.Query.ROOT,request);
                if(!(result instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> known))return new Unavailable("actual current campaign root unavailable");
                var packet=known.value();
                if(!new OpportunityJson.Text("available").equals(packet.result().get("status")))return new Unavailable("accepted campaign root is explicitly unavailable");
                observe(request,packet.receipt(),packet.originalResult(),lease.frame().semantic(),context.archive().withSession(same));
                if(!context.readHistoryPublisher().hasPending(same))return new Unavailable("actual PUBLIC_QUERY ROOT read is not retained by the sole history producer; no publication or action credit");
                return new AwaitingPublication("actual original root read requires Root READ-first publication and a fresh complete ordinary plan");
            });
        }
    }
    /** Package-local controlled source edge for the complete scheduler regression; there is no public permissive default. */
    RootSuccessionPlanningPolicies(ExactRef implementation,CurrentScope current,ReleaseEligibility release,RootReader roots) {
        this.implementation=Objects.requireNonNull(implementation);this.current=Objects.requireNonNull(current);
        this.release=Objects.requireNonNull(release);this.roots=Objects.requireNonNull(roots);
        StrictJson.require(implementation.bytes()>0,"actual selected succession policy implementation source required");
        policies=List.of(new Policy(PlanningStage.SUCCESSION_PREFLIGHT),new Policy(PlanningStage.DEFERRED_SUCCESSION_ROOT));
    }
    public List<OrdinaryPolicy> policies(){return policies;}

    /** Validates actual packet/receipt custody and reuses the sole strict M3 native estate producer. */
    static Observed observe(PlanningRequest request,PlanningReadReceipt receipt,OpportunityJson.Obj originalResult,
            OpportunityJson.Obj actualSemantic,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(request);Objects.requireNonNull(receipt);Objects.requireNonNull(archive);
        StrictJson.require(receipt.request().before().equals(request.before())&&receipt.request().source().equals(request.source())
                &&receipt.request().sessionId().equals(request.sessionId())&&receipt.request().arguments().equals(FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY))
                &&receipt.request().operation().value().equals("query-campaign-root-context-v1")
                &&receipt.request().deadline().equals(request.deadline())&&actualSemantic.equals(request.observations().snapshot()),
                "preflight root receipt crossed original current frame/source/session/arguments/deadline");
        NativeRecordedEvidenceVerifier.requireRead(receipt,archive);ExactRef original=archive.readReferenceOf(receipt);
        StrictJson.require(archive.loadRead(original).equals(receipt)
                &&DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES).equals(originalResult),
                "preflight root is not the actual unchanged native result and archived original");
        var estate=SuccessionNativeEstate12004.freeze(DriverJson.encode(originalResult),DriverJson.encode(actualSemantic));
        return new Observed(request,original,estate);
    }
    private final class Policy implements OrdinaryPolicy {
        private final PlanningStage stage;
        Policy(PlanningStage stage){this.stage=stage;}
        @Override public PlanningStage stage(){return stage;}
        @Override public ExactRef implementationSource(){return implementation;}
        @Override public Decision evaluate(PlanningRequest request,Draft previous) {
            try {
                // Lower-priority actual producers may replace Draft.detail in full. The original
                // preflight decision is retained for this exact invocation, never reconstructed from it.
                boolean deferred=deferredPlan.get()==request;
                deferredPlan.remove();
                current.require(request);
                if(stage==PlanningStage.DEFERRED_SUCCESSION_ROOT&&!deferred)return new NotApplicable("no actual initial root observation was deferred");
                var semantic=request.observations().snapshot();var terminal=semantic.get("one_life_terminal_reason");
                if(terminal instanceof OpportunityJson.Text changed&&changed.value().equals("played_character_changed"))
                    return new Stop(PlanningResult.StopReason.NATURAL_SUCCESSION_REQUIRED,"actual changed-player reconciliation belongs to the original lifecycle producer");
                if(terminal!=null&&terminal!=OpportunityJson.Nil.INSTANCE)return new NotApplicable("actual terminal work belongs to the lifecycle owner");
                if(!OpportunityJson.bool(OpportunityJson.object(semantic.get("played_character"),"played_character").get("alive"),"alive"))
                    return new NotApplicable("actual dead-player terminal work belongs to the lifecycle owner");
                if(!request.observations().paused()||!request.observations().mapReady()||request.observations().foregroundPresent())
                    return new NotApplicable("preflight root requires the actual living paused map without foreground work");
                var declaredLifecycle=semantic.get("succession_lifecycle");
                SuccessionLifecycleBinding.Profile profile;
                try {
                    profile=SuccessionLifecycleCodec.decode(DriverJson.encode(OpportunityJson.object(declaredLifecycle,"succession_lifecycle"))).profile();
                    if(!profile.ordinary()&&profile!=SuccessionLifecycleBinding.Profile.ROGUE_ONE_LIFE)
                        return unavailableProfile(declaredLifecycle,"unknown lifecycle profile cannot authorize ordinary estate preflight");
                } catch(IllegalArgumentException|IllegalStateException unavailable) {
                    return unavailableProfile(declaredLifecycle,unavailable.getMessage());
                }
                if(profile==SuccessionLifecycleBinding.Profile.ORDINARY_VANILLA_CONFIGURATION)
                    return new NotApplicable("actual living unchanged vanilla player does not require succession estate preflight");
                if(!profile.ordinary())return new NotApplicable("actual rogue lifecycle retains its own original capture and terminal continuation");
                if(stage==PlanningStage.SUCCESSION_PREFLIGHT) {
                    var existing=roots.retained(request);
                    if(existing.isPresent()) {
                        StrictJson.require(existing.orElseThrow().sameNative(request),"retained root data crossed its actual current source or native subject");
                        return annotate(previous,OBSERVATION,existing.orElseThrow().detail(),"actual canonical ROOT witness and unchanged original native material were reverified; no new estate authority");
                    }
                }
                if(stage==PlanningStage.DEFERRED_SUCCESSION_ROOT&&previous.command().filter(command->command.operation().equals(RELEASE)).isPresent())
                    return annotate(previous,"prisoner_release_initial_expectation_root_deferred",new OpportunityJson.Bool(true),
                            "the actual accepted release retains its initial-root priority");
                if(stage==PlanningStage.SUCCESSION_PREFLIGHT&&!request.observations().initialLifestyleFocusRequired()&&release.ready(request)) {
                    deferredPlan.set(request);
                    return annotate(previous,DEFERRED,new OpportunityJson.Bool(true),"source-bound accepted release may arbitrate before the initial root observation");
                }
                RootRead read=roots.read(request);
                if(read instanceof Unavailable missing)return new Wait(missing.reason());
                if(read instanceof AwaitingPublication pending)return new Refresh(pending.reason());
                Observed observed=(Observed)read;StrictJson.require(observed.sameNative(request),"actual root read changed its native subject or frame");
                if(stage==PlanningStage.DEFERRED_SUCCESSION_ROOT)return new Refresh("another action won release arbitration; the actual root read requires a fresh complete ordinary plan");
                return annotate(previous,OBSERVATION,observed.detail(),"actual root observed; sole READ publication completion must finish before ordinary execution");
            }catch(IOException failure){return new Wait("actual succession root source unavailable: "+bounded(failure.getMessage()));}
            catch(IllegalArgumentException|IllegalStateException rejected){return new Wait("actual succession root source rejected: "+bounded(rejected.getMessage()));}
        }
    }
    private static Defer unavailableProfile(OpportunityJson.Value declared,String reason) {
        String actualReason=bounded(reason);
        return new Defer("actual succession lifecycle profile unavailable; other ordinary policies may continue: "+actualReason,
                new OpportunityJson.Obj(Map.of("succession_lifecycle",declared==null?OpportunityJson.Nil.INSTANCE:declared,
                        "reason",new OpportunityJson.Text(actualReason),"natural_succession_authority",new OpportunityJson.Bool(false),
                        "business_submission",new OpportunityJson.Bool(false))));
    }
    private static Annotate annotate(Draft previous,String field,OpportunityJson.Value value,String reason) {
        return new Annotate(new Draft(previous.policy(),previous.phase(),previous.reason(),previous.kind(),previous.command(),previous.purpose(),
                previous.domain(),previous.detail().with(field,value)),reason);
    }
    private static String bounded(String reason){String value=reason==null?"unknown source failure":reason;return value.substring(0,Math.min(1024,value.length()));}
}
