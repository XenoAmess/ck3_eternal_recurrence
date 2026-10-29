package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesDefinitions;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesExecutor;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.LoadedFeaturesData;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesContract.*;

/** Public orchestration over the one installed native rules producer, original read/action journals and replay material. */
public final class FrontendRulesService {
    public record MissingPermission(OperationKey operation,String capability,boolean operationPresent,boolean capabilityPresent) {
        public MissingPermission { Objects.requireNonNull(operation);StrictJson.text(capability);StrictJson.require(!operationPresent||!capabilityPresent,"missing permission must name an actual absent original admission"); }
    }
    public static final class Unavailable extends IOException {
        @java.io.Serial private static final long serialVersionUID = 1L;
        private final Method method;
        private final org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Build build;
        private final transient List<MissingPermission> missing;
        private Unavailable(Method method,org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Build build,List<MissingPermission> missing) {
            super("actual "+build.version()+" frontend method "+method.publicName()+" unavailable: "+missing);this.method=method;this.build=build;this.missing=List.copyOf(missing);
        }
        public Method method() { return method; }
        public org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Build build() { return build; }
        public List<MissingPermission> missing() { return missing; }
    }
    @FunctionalInterface public interface StartPort {
        StartMaterial startSelected(FrontendRulesExecutor.Context actual,String characterNameKey)throws IOException,InterruptedException;
    }
    /** Supplied only inside Root's real menu lease; a detached invocation is not a permission. */
    public record Invocation(FrontendRulesExecutor executor,ActionCoordinatorPort actions,
            FrontendRulesExecutor.Context initial,StartPort start,Clock clock) {
        public Invocation { Objects.requireNonNull(executor);Objects.requireNonNull(actions);Objects.requireNonNull(initial);Objects.requireNonNull(start);Objects.requireNonNull(clock);StrictJson.require(initial.deadline().isAfter(clock.instant()),"frontend public observation deadline expired"); }
    }
    private final FrontendRulesDefinitions definitions;
    private final ActionPorts.OutcomeArchive archive;
    public FrontendRulesService(FrontendRulesDefinitions sameDefinitions,ActionPorts.OutcomeArchive sameArchive) {
        definitions=Objects.requireNonNull(sameDefinitions);archive=Objects.requireNonNull(sameArchive);
    }
    public FrontendRulesDefinitions definitions() { return definitions; }
    /** Fresh ordinary startup uses the same primitive producers as the public menu tools. */
    public FrontendRulesExecutor.CandidateRead prepareFreshRobert(Invocation actual)throws IOException,InterruptedException {
        Objects.requireNonNull(actual);var call=new Call(actual);
        var route=call.known(actual.executor().queryRoute(call.context("fresh-route")));
        if(route.value().route()==org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Route.MAIN_MENU) {
            transition(Method.NEW_GAME,call);
            route=call.known(actual.executor().queryRoute(call.context("fresh-bookmarks")));
        }
        StrictJson.require(route.value().route()==org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Route.BOOKMARKS,
                "fresh Robert preparation requires the independently observed Bookmarks route");
        select1066Bookmark(call);
        return select1066(call,"bookmark_rags_to_riches_duke_robert").actual();
    }
    /** Actual advertised/executable menu DATA is checked before orchestration; each original guard still revalidates. */
    public void requireAvailable(Request request,org.xar.ck3.control.application.effects.FrontendAuthority.LeaseSnapshot actual)throws Unavailable {
        Objects.requireNonNull(request);Objects.requireNonNull(actual);
        List<FrontendRulesRequests.Primitive> required=switch(request.method()) {
            case PREPARE_RULER->List.of(FrontendRulesRequests.Primitive.ROUTE,FrontendRulesRequests.Primitive.TREE,FrontendRulesRequests.Primitive.PICK_ANY,FrontendRulesRequests.Primitive.SELECT_RANDOM);
            case NEW_GAME->List.of(FrontendRulesRequests.Primitive.ROUTE,FrontendRulesRequests.Primitive.NEW_GAME);
            case PICK_ANY->List.of(FrontendRulesRequests.Primitive.ROUTE,FrontendRulesRequests.Primitive.PICK_ANY);
            case RULER_DESIGNER->List.of(FrontendRulesRequests.Primitive.ROUTE,FrontendRulesRequests.Primitive.TREE,FrontendRulesRequests.Primitive.RULER_DESIGNER);
            case START_1066->List.of(FrontendRulesRequests.Primitive.ROUTE,FrontendRulesRequests.Primitive.BOOKMARK_MODEL,FrontendRulesRequests.Primitive.START_BOOKMARK);
            default->List.of();
        };
        var missing=required.stream().filter(value->!actual.executableOperations().contains(value.operation())||!actual.bridgeCapabilities().contains(value.capability())).map(value->new MissingPermission(value.operation(),value.capability(),actual.executableOperations().contains(value.operation()),actual.bridgeCapabilities().contains(value.capability()))).toList();
        if(!missing.isEmpty())throw new Unavailable(request.method(),definitions.exactBuild(),missing);
    }
    public Response execute(Request request,Invocation actual)throws IOException,InterruptedException {
        Objects.requireNonNull(request);Objects.requireNonNull(actual);var execution=new Call(actual);
        if(request instanceof Features)throw new IllegalArgumentException("loaded features require the distinct actual paused gameplay read scope");
        Response result=switch(request.method()) {
            case APPLIED_RULES->new ReadResponse(request.method(),new Selections(execution.known(actual.executor().queryAppliedRules(execution.context("applied"))),true));
            case SELECTIONS->new ReadResponse(request.method(),new Selections(execution.known(actual.executor().querySelections(execution.context("selections"))),false));
            case WINDOW->new ReadResponse(request.method(),new Window(execution.known(actual.executor().queryWindow(execution.context("window")))));
            case ROUTE->new ReadResponse(request.method(),new RouteRead(execution.known(actual.executor().queryRoute(execution.context("route")))));
            case TREE->new ReadResponse(request.method(),new Tree(execution.known(actual.executor().inspectTree(execution.context("tree")))));
            case SELECT_RULE->selection((Select)request,execution);
            case APPLY_HIDE,HIDE->closure(request.method(),execution);
            case OPEN_RULES->open(execution);
            case NEW_GAME,PICK_ANY,RULER_DESIGNER->transition(request.method(),execution);
            case PREPARE_RULER->prepare(execution);
            case START_1066->start((Start)request,execution);
            default->throw new IllegalArgumentException("unregistered original frontend method");
        };
        // The same encoder is used before return and by every public consumer; malformed original evidence fails here.
        FrontendRulesCodec.encode(result);return result;
    }
    public ReadResponse loadedFeatures(Features request,PlanningReadResult<LoadedFeaturesData.Observation> actual)throws IOException {
        var known=known(actual);NativeRecordedEvidenceVerifier.requireRead(known.receipt(),archive);
        var result=new ReadResponse(Method.LOADED_FEATURES,new FeaturesRead(known,request.expectedRevision()));FrontendRulesCodec.encode(result);return result;
    }
    private Selected selection(Select request,Call call)throws IOException,InterruptedException {
        var nativeRequest=new FrontendRulesRequests.SelectRule(request.ruleKey(),request.expectedCurrentSettingKey(),request.desiredSettingKey());
        ActionReceipt action=call.settle(call.invocation.executor().selectRule(call.context("select-rule"),nativeRequest).receipt());
        var arguments=arguments(action);var before=load(definitions.selections(),ref(arguments,"selections"));var window=load(definitions.window(),ref(arguments,"window"));var after=after(action,definitions.selections());call.advance(after.receipt());
        return new Selected(action,request,new Selections(before,false),new Window(window),ack(action),new Selections(after,false));
    }
    private Closed closure(Method method,Call call)throws IOException,InterruptedException {
        ActionReceipt action=call.settle((method==Method.APPLY_HIDE?call.invocation.executor().applyAndHideRules(call.context("apply-hide")):call.invocation.executor().hideRules(call.context("hide"))).receipt());
        var before=load(definitions.selections(),ref(arguments(action),"selections"));var after=after(action,definitions.window());call.advance(after.receipt());
        return new Closed(action,method==Method.APPLY_HIDE,new Selections(before,false),ack(action),new Window(after));
    }
    private Opened open(Call call)throws IOException,InterruptedException {
        var execution=call.invocation.executor().openRules(call.context("open-rules"));
        if(execution instanceof FrontendRulesExecutor.AlreadyObserved observed) {
            var receipt=observed.receipt();NativeRecordedEvidenceVerifier.requireRead(receipt,archive);var known=new PlanningReadResult.Known<>(definitions.selections().decode(receipt),receipt,archive.preserveRead(receipt));call.advance(receipt);return new Opened(Optional.empty(),new Selections(known,false));
        }
        ActionReceipt action=call.settle(((FrontendRulesExecutor.Submitted)execution).receipt());var after=after(action,definitions.selections());call.advance(after.receipt());return new Opened(Optional.of(action),new Selections(after,false));
    }
    private Transition transition(Method method,Call call)throws IOException,InterruptedException {
        var context=call.context(method.name().toLowerCase(java.util.Locale.ROOT));
        var submitted=switch(method) { case NEW_GAME->call.invocation.executor().newGame(context);case PICK_ANY->call.invocation.executor().pickAnyCharacter(context);case RULER_DESIGNER->call.invocation.executor().rulerDesigner(context);default->throw new IllegalArgumentException("ordinary transition absent"); };
        ActionReceipt action=call.settle(submitted.receipt());ObjectNode arguments=arguments(action);var before=load(definitions.route(),ref(arguments,"before"));Optional<Tree> tree=arguments.get("tree").isNull()?Optional.empty():Optional.of(new Tree(load(definitions.tree(),ref(arguments,"tree"))));var after=after(action,definitions.route());call.advance(after.receipt());
        return new Transition(method,action,new RouteRead(before),tree,ack(action),new RouteRead(after));
    }
    private Prepared prepare(Call call)throws IOException,InterruptedException {
        return FrontendCustomRulerPreparation.prepare(new FrontendCustomRulerPreparation.Port() {
            @Override public Transition pickAny()throws IOException,InterruptedException { return transition(Method.PICK_ANY,call); }
            @Override public Tree randomTarget()throws IOException,InterruptedException {
                return new Tree(call.known(call.invocation.executor().inspectTree(call.context("random-target"))));
            }
            @Override public FrontendCustomRulerPreparation.DrawOutcome drawOnce(int attempt)throws IOException,InterruptedException {
                StrictJson.require(attempt>=1&&attempt<=FrontendCustomRulerPreparation.MAX_DRAWS,"bounded original draw index required");
                Duration timeout=FrontendCustomRulerPreparation.DESIGNER_OBSERVATION_TIMEOUT;
                ActionReceipt submitted=call.invocation.executor().selectRandomPlayable(call.context("random-playable-"+attempt,timeout)).receipt();
                ActionReceipt observed=call.observe(submitted,timeout);
                if(!(observed.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.FrontendApplied))
                    return new FrontendCustomRulerPreparation.Unresolved(observed,"original random playable action remains "+observed.outcome()+"; no independent designer confirmation, never redraw");
                var tree=after(observed,definitions.tree());call.advance(tree.receipt());
                // The current native producer proves designer-ready only. A negative tree cannot manufacture SelectedIneligible.
                return new FrontendCustomRulerPreparation.DesignerReady(observed,ack(observed),new Tree(tree));
            }
        });
    }
    private Started start(Start request,Call call)throws IOException,InterruptedException {
        var before=call.known(call.invocation.executor().queryRoute(call.context("start-before")));StrictJson.require(before.value().route()==org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Route.BOOKMARKS,"ordinary 1066 Start requires Bookmarks");
        var selected=select1066(call,request.characterNameKey());
        StartMaterial material=call.invocation.start().startSelected(call.context("start-1066"),request.characterNameKey());return new Started(request,new RouteRead(before),selected.acknowledgement(),selected.actual().candidate(),ack(material.action()),material);
    }
    private record SelectedCandidate(FrontendRulesExecutor.CandidateRead actual,Optional<RawJson> acknowledgement) {
        private SelectedCandidate { Objects.requireNonNull(actual);Objects.requireNonNull(acknowledgement); }
    }
    private void select1066Bookmark(Call call)throws IOException,InterruptedException {
        var execution=call.invocation.executor().selectSupported1066Bookmark(call.context("select-bookmark-1066"));
        if(execution instanceof FrontendRulesExecutor.Submitted submitted) {
            var action=call.settle(submitted.receipt());var selected=after(action,definitions.bookmark());call.advance(selected.receipt());
        } else {var receipt=((FrontendRulesExecutor.AlreadyObserved)execution).receipt();NativeRecordedEvidenceVerifier.requireRead(receipt,archive);call.advance(receipt);}
        var model=call.known(call.invocation.executor().queryBookmarkModel(call.context("selected-bookmark-1066")));
        model.value().requireSupported1066Bookmark();
    }
    private SelectedCandidate select1066(Call call,String characterNameKey)throws IOException,InterruptedException {
        var execution=call.invocation.executor().selectSupported1066Character(call.context("select-1066"),characterNameKey);Optional<RawJson> selectionAck=Optional.empty();
        if(execution instanceof FrontendRulesExecutor.Submitted submitted) {var action=call.settle(submitted.receipt());var selected=after(action,definitions.bookmark());call.advance(selected.receipt());selectionAck=Optional.of(ack(action));}
        else {var receipt=((FrontendRulesExecutor.AlreadyObserved)execution).receipt();NativeRecordedEvidenceVerifier.requireRead(receipt,archive);call.advance(receipt);}
        var candidate=call.invocation.executor().querySelected1066Candidate(call.context("selected-1066"),characterNameKey);NativeRecordedEvidenceVerifier.requireRead(candidate.receipt(),archive);call.advance(candidate.receipt());
        return new SelectedCandidate(candidate,selectionAck);
    }
    private <T>PlanningReadResult.Known<T> after(ActionReceipt action,ReadContract<T> contract)throws IOException {
        confirmed(action);var settled=(ActionState.Settled)action.state();var observation=((ActionState.FrontendApplied)settled.settlement()).observation();
        StrictJson.require(observation.supportingEvidence().size()==1,"frontend action lacks its original independent-read basis");
        ObjectNode basis=FrontendRulesCodec.object(archive.loadMaterial(observation.supportingEvidence().getFirst()));StrictJson.object(basis,Set.of("schema","command_body_sha256","request_id","after_read","compatible_material"));
        StrictJson.require("xar.java.frontend-rules-original-basis/v1".equals(StrictJson.text(basis.get("schema")))&&action.bodySha256().equals(StrictJson.text(basis.get("command_body_sha256")))&&settled.attempt().requestId().equals(StrictJson.text(basis.get("request_id"))),"frontend action proof crossed its canonical request/body");
        var result=load(contract,ref(basis,"after_read"));StrictJson.require(result.receipt().requestId().equals(observation.readRequestId())&&result.receipt().after().binding().origin().requireFrontend().equals(observation.after()),"frontend independent read differs from actual settlement");
        // Read the preserved compatible material as well; a missing original is never replaced with a synthesized success.
        var compatible=FrontendRulesCodec.object(archive.loadMaterial(ref(basis,"compatible_material")));StrictJson.trueValue(compatible.get("postcondition_verified"));return result;
    }
    private <T>PlanningReadResult.Known<T> load(ReadContract<T> contract,ExactRef reference) {
        PlanningReadReceipt receipt=archive.loadRead(reference);NativeRecordedEvidenceVerifier.requireRead(receipt,archive);StrictJson.require(receipt.contractId().equals(contract.contractId())&&receipt.request().operation().equals(contract.operation()),"public adapter original read uses another installed contract");
        return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,reference);
    }
    private static RawJson ack(ActionReceipt action)throws IOException { return action.ack().orElseThrow(()->new IOException("native action ACK unavailable; original outcome remains unknown")).originalResultToken().orElseThrow(()->new IOException("original native action token unavailable")); }
    private static ObjectNode arguments(ActionReceipt action) { return FrontendRulesCodec.object(new RawJson(OpportunityJson.encode(action.command().arguments()))); }
    private static ExactRef ref(ObjectNode row,String field) { return ExactRef.fromJson(row.get(field)); }
    private static <T>PlanningReadResult.Known<T> known(PlanningReadResult<T> result)throws IOException {
        if(result instanceof PlanningReadResult.Known<T> actual)return actual;throw new IOException("actual native public frontend read unavailable: "+((PlanningReadResult.Unavailable<T>)result).reason());
    }
    private final class Call {
        private final Invocation invocation;private FrontendIdentity identity;private int step;
        Call(Invocation invocation) { this.invocation=invocation;identity=invocation.initial().identity(); }
        FrontendRulesExecutor.Context context(String phase) { return new FrontendRulesExecutor.Context(invocation.initial().actionId()+"-"+(++step)+"-"+phase,identity,invocation.initial().source(),invocation.initial().deadline()); }
        FrontendRulesExecutor.Context context(String phase,Duration maximum) {
            var limited=invocation.clock().instant().plus(maximum);var deadline=limited.isBefore(invocation.initial().deadline())?limited:invocation.initial().deadline();
            return new FrontendRulesExecutor.Context(invocation.initial().actionId()+"-"+(++step)+"-"+phase,identity,invocation.initial().source(),deadline);
        }
        void advance(PlanningReadReceipt receipt) { identity=receipt.after().binding().origin().requireFrontend(); }
        <T>PlanningReadResult.Known<T> known(PlanningReadResult<T> value)throws IOException {var result=FrontendRulesService.known(value);NativeRecordedEvidenceVerifier.requireRead(result.receipt(),archive);advance(result.receipt());return result;}
        ActionReceipt settle(ActionReceipt original)throws IOException,InterruptedException {
            ActionReceipt current=observe(original,Duration.ofSeconds(10));
            if(!(current.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.FrontendApplied))throw new IOException("original frontend action "+original.command().actionId()+" remains "+current.outcome()+"; retain actual receipt and reconcile, never resubmit");
            return current;
        }
        ActionReceipt observe(ActionReceipt original,Duration timeout)throws IOException,InterruptedException {
            ActionReceipt current=original;long maximum=System.nanoTime()+timeout.toNanos();
            while(!(current.state() instanceof ActionState.Settled)&&System.nanoTime()<maximum&&invocation.initial().deadline().isAfter(invocation.clock().instant())) {
                if(current.settled())break;Thread.sleep(50);current=invocation.actions().reconcile(original.command().actionId());
                StrictJson.require(current.command().equals(original.command()),"reconcile changed the immutable submitted frontend command");
            }
            if(current.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.FrontendApplied applied)identity=applied.observation().after();
            return current;
        }
    }
}
