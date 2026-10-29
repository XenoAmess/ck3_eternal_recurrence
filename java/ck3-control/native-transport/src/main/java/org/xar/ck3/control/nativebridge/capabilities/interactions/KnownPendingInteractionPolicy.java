package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.application.planning.military.WarCorePlanner;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence;
import org.xar.ck3.control.application.planning.warexit.WarExitInboundProvider;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Ordinary full production collector and coordinator proposal, hosted by the one native transport. */
public final class KnownPendingInteractionPolicy {
    public static final String CANDIDATE="prepared_pending_interaction_candidate";
    @FunctionalInterface public interface ContextPort { Context current(PlanningRequest request); }
    public record ReadPublication(OpportunityJson.Obj result,Optional<OpportunityJson.Obj> snapshot) {
        public ReadPublication { Objects.requireNonNull(result);Objects.requireNonNull(snapshot); }
    }
    @FunctionalInterface public interface ReadCatalog {
        Optional<ReadRoute<?>> exact(OperationKey operation);
    }
    @FunctionalInterface public interface ReadArguments { OpportunityJson.Obj prepare(PlanningRequest request); }
    @FunctionalInterface public interface Publication<T> { ReadPublication publish(PlanningReadResult.Known<T> original); }
    public record Collected(ReadPublication publication,ExactRef originalReceipt) {
        public Collected { Objects.requireNonNull(publication);Objects.requireNonNull(originalReceipt); }
    }
    /** Captures the existing registered typed contract; a publication view never registers a duplicate operation. */
    public record ReadRoute<T>(ReadContract<T> original,ReadArguments arguments,Publication<T> publication) {
        public ReadRoute { Objects.requireNonNull(original);Objects.requireNonNull(arguments);Objects.requireNonNull(publication); }
        public OperationKey operation() { return original.operation(); }
        public Optional<Collected> collect(PlanningReadPort actualReads,PlanningRequest current) {
            return collect(actualReads,current,org.xar.ck3.control.application.planning.events.EventIncidentCapturePort.unavailable());
        }
        public Optional<Collected> collect(PlanningReadPort actualReads,PlanningRequest current,
                org.xar.ck3.control.application.planning.events.EventIncidentCapturePort incidents) {
            PlanningReadResult<T> result=incidents.read(actualReads,original,new PlanningReadRequest(current.before(),current.source(),current.sessionId(),
                    original.operation(),Objects.requireNonNull(arguments.prepare(current)),current.deadline()),current);
            if(!(result instanceof PlanningReadResult.Known<T> known))return Optional.empty();
            InteractionReadPublications.sameRequest(known.receipt(),current);
            return Optional.of(new Collected(Objects.requireNonNull(publication.publish(known)),known.originalReceipt()));
        }
    }
    public static ReadRoute<org.xar.ck3.control.application.action.RawJson> prisonerRead(
            ReadContract<org.xar.ck3.control.application.action.RawJson> actualCanonicalContractZero) {
        need(actualCanonicalContractZero.operation().value().equals("query-player-prisoner-collection-private-v1"),
                "canonical complete prisoner collection zero required");
        return new ReadRoute<>(actualCanonicalContractZero,request->org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries.arguments(
                new org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent.Unconditional(),java.util.OptionalLong.empty()),
                known->new ReadPublication(InteractionReadPublications.publish(known.receipt()),Optional.empty()));
    }
    private final ExactRef implementationSource;
    private final ContextPort contexts;
    private final PlanningReadPort reads;
    private org.xar.ck3.control.application.planning.events.EventIncidentCapturePort incidentCapture;
    public synchronized void bindIncidentCapture(org.xar.ck3.control.application.planning.events.EventIncidentCapturePort actual) {
        Objects.requireNonNull(actual);need(incidentCapture==null||incidentCapture==actual,"ordinary pending incident source binds once");incidentCapture=actual;
    }
    private synchronized org.xar.ck3.control.application.planning.events.EventIncidentCapturePort incidents() {
        return incidentCapture==null?org.xar.ck3.control.application.planning.events.EventIncidentCapturePort.unavailable():incidentCapture;
    }
    private final ReadContract<PendingContext> pendingContract;
    private final ReadCatalog supplemental;
    private final Optional<KnownPendingInteractionContinuation> continuation;
    public KnownPendingInteractionPolicy(ExactRef implementationSource,ContextPort actualContexts,
            PlanningReadPort actualReads,ReadContract<PendingContext> actualPendingContract,ReadCatalog supplemental) {
        this(implementationSource,actualContexts,actualReads,actualPendingContract,supplemental,Optional.empty());
    }
    public KnownPendingInteractionPolicy(ExactRef implementationSource,ContextPort actualContexts,
            PlanningReadPort actualReads,ReadContract<PendingContext> actualPendingContract,ReadCatalog supplemental,
            KnownPendingInteractionContinuation.Core actualSameCore) {
        this(implementationSource,actualContexts,actualReads,actualPendingContract,supplemental,
                Optional.of(new KnownPendingInteractionContinuation(actualSameCore)));
    }
    private KnownPendingInteractionPolicy(ExactRef implementationSource,ContextPort actualContexts,
            PlanningReadPort actualReads,ReadContract<PendingContext> actualPendingContract,ReadCatalog supplemental,
            Optional<KnownPendingInteractionContinuation> continuation) {
        this.implementationSource=Objects.requireNonNull(implementationSource);
        need(implementationSource.bytes()>0,"actual Java policy source required");
        contexts=Objects.requireNonNull(actualContexts);reads=Objects.requireNonNull(actualReads);
        pendingContract=Objects.requireNonNull(actualPendingContract);
        need(pendingContract.operation().value().equals(PendingContextCodec.STEP)
                &&pendingContract.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                "actual canonical registered pending context contract required");
        this.supplemental=Objects.requireNonNull(supplemental);
        this.continuation=Objects.requireNonNull(continuation);
    }
    public ExactRef implementationSource() { return implementationSource; }

    /**
     * Source 9238..9365 prepares an active-war candidate only. It performs no native read
     * and returns no pending command before battle/latched-assault lifecycle guards.
     */
    public WarCorePlanner.Leaf leaf(ExactRef source) {
        need(implementationSource.equals(source),"leaf source differs from the actual policy");
        return new WarCorePlanner.Leaf(WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_PRELUDE,source,
                (request,current)-> {
                    if(deferred(request))return new MilitaryPlanningDecision.Keep(InteractionArguments.app(F.objectNode()));
                    Context held=context(request); PendingSummary pending=held.controls().pending();
                    if(pending==null)return new MilitaryPlanningDecision.Keep(InteractionArguments.app(F.objectNode()));
                    if(pending.autoAcceptNotification() || !request.observations().warInProgress())
                        return new MilitaryPlanningDecision.ApplicationDecision(evaluateCore(request,current));
                    ObjectNode candidate=F.objectNode().put("schema","xar.known-pending-prepared-candidate/v1")
                            .put("snapshot_id",request.before().frame().snapshotId())
                            .put("revision",request.before().frame().revision()).put("native_revision",held.revision())
                            .put("date_raw",held.date()).put("pending_interaction_id",pending.instance().value())
                            .put("sender_character_id",pending.sender().value())
                            .put("auto_accept_notification",pending.autoAcceptNotification()).put("interaction_submission",false);
                    KnownPendingInteractionEvidence.pending(request,held).ifPresent(value->
                            candidate.set("original_context_wrapper",InteractionArguments.parseApp(value.originalWrapper())));
                    ObjectNode annotation=F.objectNode();annotation.set(CANDIDATE,candidate);
                    return new MilitaryPlanningDecision.Keep(InteractionArguments.app(annotation));
                });
    }

    /** Two exact original call sites; the Root installs the summary/assault guard between them. */
    public List<WarCorePlanner.Leaf> leaves(ExactRef source) {
        WarCorePlanner.Leaf prepare=leaf(source);
        WarCorePlanner.Leaf consume=new WarCorePlanner.Leaf(WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_CONSUMPTION,source,
                (request,current)->deferred(request)||context(request).controls().pending()==null
                        ?new MilitaryPlanningDecision.Keep(InteractionArguments.app(F.objectNode()))
                        :new MilitaryPlanningDecision.ApplicationDecision(consumeCore(request,current)));
        return List.of(prepare,consume);
    }

    /** Install only at strategy.py:9855, AFTER the genuine battle and latched-assault guards. */
    public OrdinaryPolicy.Decision consumeCore(PlanningRequest request,OrdinaryPolicy.Draft current) {
        Context held=context(request);
        if(held.controls().pending()==null)return new OrdinaryPolicy.NotApplicable("the actual current pending queue is empty");
        if(request.observations().warInProgress()) {
            JsonNode candidate=InteractionArguments.parseApp(current.detail()).get(CANDIDATE);
            if(candidate==null||!candidate.isObject()
                    ||!KnownPendingInteractionEvidence.equalText(candidate.get("snapshot_id"),request.before().frame().snapshotId())
                    ||!KnownPendingInteractionEvidence.equalInt(candidate.get("revision"),request.before().frame().revision())
                    ||!KnownPendingInteractionEvidence.equalInt(candidate.get("native_revision"),held.revision())
                    ||!KnownPendingInteractionEvidence.equalInt(candidate.get("date_raw"),held.date())
                    ||!KnownPendingInteractionEvidence.equalInt(candidate.get("pending_interaction_id"),
                        java.math.BigInteger.valueOf(held.controls().pending().instance().value())))
                return incomplete("pending reply candidate has not passed the actual same-frame war prelude");
        }
        return evaluateCore(request,current);
    }

    /** Peace calls this directly; active war calls consumeCore at the original later return. */
    public OrdinaryPolicy.Decision evaluateCore(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        if(deferred(request))return new OrdinaryPolicy.NotApplicable("the exact blocked marriage is deferred within this same-core call");
        PlanningRequest current=request; Set<String> attempted=new HashSet<>();
        for(int count=0;count<4;count++) {
            Context held=context(current); PendingSummary pending=held.controls().pending();
            if(pending==null)return new OrdinaryPolicy.NotApplicable("the actual pending queue is empty");
            Set<String> steps=current.observations().actionSteps().stream().map(OperationKey::value).collect(java.util.stream.Collectors.toUnmodifiableSet());
            if(pending.autoAcceptNotification()) {
                List<String> gaps=steps.contains(Action.ACKNOWLEDGE.step())?List.of():List.of("acknowledge_command_unavailable");
                Plan plan=new Plan(Classification.ORDINARY,"acknowledge-notification-v1",
                        gaps.isEmpty()?Optional.of(Action.ACKNOWLEDGE):Optional.empty(),Optional.empty(),Optional.empty(),gaps,
                        Optional.empty(),Optional.empty(),Optional.empty(),
                        KnownPendingInteractionEvidence.warSignature(WarExitEvidence.snapshot(current)),false);
                return propose(current,held,plan,Optional.empty(),previous);
            }
            Optional<KnownPendingInteractionEvidence.Current> captured=KnownPendingInteractionEvidence.pending(current,held);
            if(captured.isEmpty()) {
                if(!steps.contains(PendingContextCodec.STEP)||!attempted.add(PendingContextCodec.STEP))
                    return blockedMissingContext(current,held,previous);
                ObjectNode args=InteractionArguments.body(held).put("pending_id",pending.instance().value());
                PlanningReadResult<PendingContext> read=incidents().read(reads,pendingContract,new PlanningReadRequest(current.before(),current.source(),
                        current.sessionId(),pendingContract.operation(),InteractionArguments.app(args),current.deadline()),current);
                if(!(read instanceof PlanningReadResult.Known<PendingContext> known))
                    return blockedMissingContext(current,held,previous);
                InteractionReadPublications.sameRequest(known.receipt(),current);
                current=append(current,InteractionReadPublications.pending(known),Optional.empty(),known.originalReceipt());
                continue;
            }
            PendingContext context=captured.orElseThrow().value();
            ObjectNode snapshot=WarExitEvidence.snapshot(current);
            Optional<WarExitInboundProvider.Result> inbound=context.status()==PendingContext.Status.AVAILABLE&&context.terms().war().available()
                    ?Optional.of(WarExitInboundProvider.project(current,context.terms().war().value().warId())):Optional.empty();
            Long prisoner=context.status()==PendingContext.Status.AVAILABLE
                    ?context.terms().ransom().filter(PendingContext.Ransom::available).map(PendingContext.Ransom::prisoner).map(Integer::longValue).orElse(null):null;
            var collection=prisoner==null?Optional.<org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.Observation>empty()
                    :KnownPendingInteractionEvidence.prisoners(current,held,prisoner);
            Plan plan=KnownPendingInteractionRules.evaluate(new Input(context,held,WarExitEvidence.wars(snapshot),
                    KnownPendingInteractionEvidence.warSignature(snapshot),collection,inbound,steps));
            String required=plan.requiredStep().filter(value->value.startsWith("query-war-termination-options-")).orElse(
                    plan.requiredTool().filter("ck3_query_player_prisoner_collection_private_v1"::equals)
                            .map(value->"query-player-prisoner-collection-private-v1").orElse(null));
            if(required!=null&&attempted.add(required)) {
                OperationKey operation=new OperationKey(required);
                Optional<ReadRoute<?>> route=supplemental.exact(operation);
                if(route.isPresent()) {
                    need(route.orElseThrow().operation().equals(operation),"supplemental query route changed its exact operation");
                    Optional<Collected> result=route.orElseThrow().collect(reads,current,incidents());
                    if(result.isPresent()) {
                        Collected known=result.orElseThrow();
                        current=append(current,known.publication().result(),known.publication().snapshot(),known.originalReceipt());continue;
                    }
                }
            }
            return propose(current,held,plan,Optional.of(captured.orElseThrow().originalWrapper()),previous);
        }
        return new OrdinaryPolicy.Wait("bounded exact pending read collection completed without an executable reply");
    }

    private Context context(PlanningRequest request) {
        Context held=Objects.requireNonNull(contexts.current(request));
        need(held.before().equals(request.before())&&held.source().equals(request.source())
                &&held.sessionId().equals(request.sessionId())&&held.deadline().equals(request.deadline()),
                "actual interaction context crossed the current planning frame/source/session");
        ObjectNode snapshot=WarExitEvidence.snapshot(request); JsonNode pending=snapshot.get("pending_character_interaction");
        need(held.controls().paused()==request.observations().paused(),"held paused state differs from current snapshot");
        need(held.controls().mapReady()==request.observations().mapReady(),"held map readiness differs from current snapshot");
        if(pending==null||pending.isNull())need(held.controls().pending()==null,"held pending differs from empty snapshot queue");
        else {
            need(held.controls().pending()!=null,"snapshot pending lacks held exact native control");
            eq(pending,"instance_id",java.math.BigInteger.valueOf(held.controls().pending().instance().value()));
            eq(pending,"sender_character_id",java.math.BigInteger.valueOf(held.controls().pending().sender().value()));
            need(bool(pending,"auto_accept_notification")==held.controls().pending().autoAcceptNotification(),"pending notification channel drift");
        }
        JsonNode diagnostics=snapshot.get("diagnostics");
        need(diagnostics!=null&&diagnostics.isObject(),"actual native diagnostics required");
        eq(diagnostics,"connection_generation",held.connectionGeneration());
        eq(diagnostics,"bridge_pid",java.math.BigInteger.valueOf(request.before().game().pid()));
        return held;
    }

    private OrdinaryPolicy.Decision propose(PlanningRequest request,Context held,Plan plan,
            Optional<OpportunityJson.Obj> original,OrdinaryPolicy.Draft previous) {
        OpportunityJson.Obj retained=KnownPendingInteractionPlans.encode(request,held,plan,original);
        if(plan.selected().isEmpty()) {
            OrdinaryPolicy.Draft diagnosis=new OrdinaryPolicy.Draft("one-life-turn-v1",plan.phase(),
                "known pending interaction submitted no reply: "+String.join(", ",plan.blockedReasons()),OrdinaryPolicy.Kind.ORDINARY,
                Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),retained);
            return continuation.map(value->value.choose(request,diagnosis,previous)).orElseGet(()->
                    new OrdinaryPolicy.Replace(diagnosis,"preserve exact known-policy diagnosis for the later continuation"));
        }
        Action selected=plan.selected().orElseThrow(); OperationKey operation=new OperationKey(selected.step());
        ObjectNode args=InteractionArguments.body(held).put("mutation_kind","PENDING_REPLY")
                .put("pending_id",held.controls().pending().instance().value())
                .put("accept",selected==Action.ACCEPT).put("acknowledge",selected==Action.ACKNOWLEDGE);
        args.set("known_pending_plan",InteractionArguments.parseApp(retained));
        Set<java.math.BigInteger> characters=new HashSet<>();
        characters.add(held.actor());characters.add(java.math.BigInteger.valueOf(held.controls().pending().sender().value()));
        plan.prisonerId().ifPresent(id->characters.add(java.math.BigInteger.valueOf(id)));
        Claims claims=new Claims(Set.of(),Set.of(),characters,Set.of("pending-interaction:"+held.controls().pending().instance().value()));
        String identity=request.before().toString()+"|"+request.source().sourceRef().sha256()+"|"+selected.step()+"|"+held.controls().pending().instance().value();
        ActionCommand command=new ActionCommand("pending:"+sha(identity),request.before(),request.source(),request.sessionId(),operation,
                InteractionArguments.app(args),KnownPendingInteractionPostcondition.expected(request,plan),claims,request.deadline());
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("one-life-turn-v1",plan.phase(),
                "execute the exact same-frame known pending reply; require independent lifecycle and material observations",
                OrdinaryPolicy.Kind.FOREGROUND,Optional.of(command),OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.empty(),retained),
                "the native typed policy selected one legal executable reply");
    }
    private boolean deferred(PlanningRequest request) { return continuation.map(value->value.defers(request)).orElse(false); }
    private OrdinaryPolicy.Decision blockedMissingContext(PlanningRequest request,Context held,OrdinaryPolicy.Draft previous) {
        ObjectNode detail=F.objectNode().put("policy","one-life-turn-v1")
                .put("phase","pending_character_interaction_evidence_required").putNull("selected_step")
                .put("required_step",PendingContextCodec.STEP).put("reason","no same-frame strict pending context is available")
                .put("known_policy_handled",true);
        detail.set("pending_character_interaction",WarExitEvidence.snapshot(request).get("pending_character_interaction").deepCopy());
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("one-life-turn-v1","pending_character_interaction_evidence_required",
                "observe exact full native pending context before any reply",OrdinaryPolicy.Kind.FOREGROUND,Optional.empty(),
                OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),InteractionArguments.app(detail)),"missing current typed evidence authorizes no reply");
    }
    private static PlanningRequest append(PlanningRequest current,OpportunityJson.Obj result,Optional<OpportunityJson.Obj> projection,ExactRef original) {
        PlanningObservation base=current.observations(); OpportunityJson.Obj snapshot=projection.orElse(base.snapshot());
        for(String key:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id","paused","map_ready",
                "active_event","pending_character_interaction","active_wars","played_character"))
            need(Objects.equals(base.snapshot().get(key),snapshot.get(key)),"readonly publication changed live binding "+key);
        ObjectNode wrapper=InteractionArguments.parseApp(result);
        need(KnownPendingInteractionEvidence.same(wrapper,current),"supplemental read publication lacks actual public/native query binding");
        ObjectNode row=F.objectNode().put("command",text(wrapper,"step")).put("ok",true);
        row.set("result",wrapper);InteractionArguments.ref(row.putObject("native_read_original_receipt"),original);
        List<OpportunityJson.Obj> history=new ArrayList<>(base.history());history.add(InteractionArguments.app(row));
        return new PlanningRequest(current.before(),current.source(),current.sessionId(),current.deadline(),
                new PlanningObservation(snapshot,history,base.actionSteps(),base.bridgeCapabilities(),base.battleSpeedReadiness(),
                        base.actionFacts(),base.campaignGoal(),base.crossRunPlan(),base.initialLifestyleFocusRequired()));
    }
    private static String sha(String value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8))); }
        catch(NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static OrdinaryPolicy.Stop incomplete(String reason) {
        return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,reason);
    }
}

