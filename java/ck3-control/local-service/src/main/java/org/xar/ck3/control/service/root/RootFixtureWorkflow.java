package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.FrontendAuthority;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.readiness.ReadinessArchive;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One installed upfront fixture composite. All Game writes remain canonical children of the same Root coordinator. */
public final class RootFixtureWorkflow implements FixtureCompositeActionPort {
    private final RootRuntimeContext context;
    private final RootFrontendRuntime frontend;
    private final PreparedFixture fixture;
    private final FixtureFrontendEffects effects;
    private final ExactRef implementation;
    private final Map<String,Call> calls=new HashMap<>();
    private final Map<String,ActionCommand> preparedChildren=new HashMap<>();
    private final ThreadLocal<Instant> activeDeadline=new ThreadLocal<>();
    private static final class Call {
        final ActionCommand parent;final RootMenuSession menu;final FixtureFrontendProducer.Claimed claim;
        RootFixtureFrontendPort port;FixtureFrontendProducer producer;FixtureFrontendProducer.Submitted submitted;
        FixtureQualificationTrace trace;FixtureBusinessQualification reducer;ExactRef traceHead;PendingEvent pendingEvent;
        OpportunityJson.Value preservedScenarioEvent;
        Call(ActionCommand parent,RootMenuSession menu,FixtureFrontendProducer.Claimed claim,RootFixtureFrontendPort port,FixtureFrontendProducer producer){
            this.parent=parent;this.menu=menu;this.claim=claim;this.port=port;this.producer=producer;
        }
    }
    private record PendingEvent(SemanticEvidence before,PlanningReadReceipt original,FixtureStartupHandler.Decision decision,String childActionId,String childBodySha256) { }
    private final class Issued implements CompositeContinuationToken {
        final ActionCommand parent;final Instant deadline;final Session same;boolean consumed;
        Issued(ActionCommand parent,Instant deadline,Session same){this.parent=parent;this.deadline=deadline;this.same=same;}
        @Override public ActionCommand originalParent(){return parent;}
        @Override public Instant deadline(){return deadline;}
        @Override public Kind kind(){return Kind.FIXTURE_STARTUP;}
        RootFixtureWorkflow owner(){return RootFixtureWorkflow.this;}
    }
    public RootFixtureWorkflow(RootRuntimeContext context,RootFrontendRuntime sameFrontend,PreparedFixture fixture,
            FixtureFrontendEffects sameEffects,ExactRef actualImplementation)throws IOException {
        this.context=Objects.requireNonNull(context);frontend=Objects.requireNonNull(sameFrontend);this.fixture=Objects.requireNonNull(fixture);
        effects=Objects.requireNonNull(sameEffects);implementation=Objects.requireNonNull(actualImplementation);
        frontend.requireContext(context);StrictJson.require(effects.fixture()==fixture&&implementation.bytes()>0,"fixture workflow must retain identical policy/effects and actual source");
        context.game().launchPlan().sources().requireLoadedClass(getClass());fixture.verifySources();
    }
    @Override public String handlerId(){return "source-bound-frontend-fixture-business-v1";}
    private FixturePlan.Kind kind(){return FixturePlan.Kind.valueOf(fixture.policy().kind().name());}
    @Override public boolean supports(OperationKey operation){return kind().parentOperation().equals(operation);}
    public List<RootExecutableBindings.CompositeBinding> composites(){return List.of(new RootExecutableBindings.CompositeBinding(this,ReadContract.GuardMode.FRONTEND_SESSION,Optional.empty(),implementation,implementation));}
    public List<FrontendRouteAdmission> routeAdmissions(){return List.of(new FrontendRouteAdmission(kind().parentOperation(),Set.of(FrontendRulesData.Route.BOOKMARKS),FrontendRouteAdmission.FrameMode.MENU,implementation));}
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers(){return List.of(new NativeRecordedEvidenceVerifier.Binding(kind().parentOperation(),implementation,(head,actual,archive)->verifyArchived(actual,archive)));}
    /** Original public tool result remains the typed acknowledged/pending receipt, even when the private parent advances further. */
    public FixtureFrontendProducer.Submitted submit(RootMenuSession menu,FrontendAuthority.LeaseSnapshot actual,Instant deadline)throws IOException,InterruptedException {
        context.requireCurrent(deadline);fixture.verifySources();frontend.fixtureCatalog();
        StrictJson.require(context.core().requireFrontendMenu(context)==menu&&menu.coordinator==context.core().requireFrontendMenu(context).coordinator
                &&menu.writer==context.writer()&&actual.source().equals(context.source()),"fixture public producer crossed actual menu/Core/source");
        var port=new RootFixtureFrontendPort(context,frontend,menu,fixture,effects,actual.identity(),deadline);
        var producer=new FixtureFrontendProducer(fixture,port,transition(deadline));String id="public-fixture-"+java.util.UUID.randomUUID();
        var claim=producer.claim(id);var plan=new FixturePlan(kind(),fixture.policySource(),claim.original(),implementation);
        ActionCommand parent=new ActionCommand(id,new CommandOrigin.Frontend(port.identity()),context.source(),context.game().sessionId(),kind().parentOperation(),
                DriverJson.object(StrictJson.canonical(plan.encode(),65536),65536),new CommandExpectation.Frontend(plan.expected(port.identity(),context.source())),emptyClaims(),deadline);
        var call=new Call(parent,menu,claim,port,producer);synchronized(calls){StrictJson.require(calls.putIfAbsent(id,call)==null,"duplicate original fixture parent");}
        ActionReceipt actualParent=menu.execute(parent);
        // Resume only this durable parent. Old UNKNOWN children can collect originals, never submit again.
        while(!actualParent.settled()&&context.clock().instant().isBefore(deadline)) {
            pause(deadline);if(!context.clock().instant().isBefore(deadline))break;actualParent=resume(parent.actionId(),deadline).parent();
        }
        if(call.submitted==null)context.withSession(same->{
            var retained=ContinuityActionJournal.lookup(same.head().state(),parent.actionId(),context.archive().withSession(same)).orElseThrow();
            var cursor=ActionTransitions.composite(retained.state()).orElseThrow();var originalChildren=canonical(same,cursor);
            var start=originalChildren.stream().filter(value->value.command().operation().equals(kind().startOperation())&&value.ack().isPresent()).findFirst();
            if(start.isPresent())call.submitted=reconstruct(parent,originalChildren,start.orElseThrow());return null;
        });
        if(call.submitted==null)throw new IOException("original fixture parent/child remains unresolved; retain canonical ID "+id+"; never repeat public submission");
        return call.submitted;
    }
    @Override public void validate(ActionCommand parent) {
        try{fixture.verifySources();FixturePlan plan=FixturePlan.requireParent(parent);
            StrictJson.require(supports(parent.operation())&&plan.policySource().equals(fixture.policySource())&&plan.producerSource().equals(implementation),"fixture parent changed its installed branch/source");
            var same=context.writer().borrowedSession();requireClaim(parent,plan,context.archive().withSession(same));
            synchronized(calls){StrictJson.require(calls.containsKey(parent.actionId())&&calls.get(parent.actionId()).parent.equals(parent),"fixture parent has no original once-only producer custody");}
        }catch(IOException e){throw new UncheckedIOException(e);}
    }
    @Override public ActionPorts.PostconditionResult run(ActionCommand parent,Children children)throws InterruptedException {
        return execute(parent,children,parent.deadline(),false);
    }
    private ActionPorts.PostconditionResult execute(ActionCommand parent,Children children,Instant deadline,boolean continuation)throws InterruptedException {
        Instant previous=activeDeadline.get();StrictJson.require(previous==null,"fixture workflow cannot nest");activeDeadline.set(deadline);
        try {
            var same=context.writer().borrowedSession();context.writer().requireSession(same);context.requireCurrent(deadline);
            var cursor=ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId());Call call=call(parent);
            List<ActionReceipt> originals=canonical(same,cursor.execution());
            for(var original:originals)if(!original.settled()&&original.command().origin() instanceof CommandOrigin.Frontend)context.core().requireFrontendMenu(context).coordinator.reconcile(same,original.command().actionId());
            originals=canonical(same,ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId()).execution());
            if(originals.stream().anyMatch(value->!value.settled()&&value.command().origin() instanceof CommandOrigin.Frontend))return pending("original fixture frontend child remains UNKNOWN; no following child reserved",parent);
            if(call.submitted==null) {
                Optional<ActionReceipt> start=originals.stream().filter(value->value.command().operation().equals(kind().startOperation())).findFirst();
                if(start.isPresent())call.submitted=reconstruct(parent,originals,start.orElseThrow());
                else {
                    if(continuation) {
                        call.port=new RootFixtureFrontendPort(context,frontend,call.menu,fixture,effects,parent.origin().requireFrontend(),deadline);
                        call.producer=new FixtureFrontendProducer(fixture,call.port,transition(deadline));
                    }
                    final boolean resume=continuation;final List<ActionReceipt> prior=originals;
                    call.submitted=call.port.withChildren(parent,this,children,()->resume?call.producer.continueBeforeStart(call.claim,prior):
                            fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO?call.producer.submitScenario(parent.actionId()):call.producer.submitRobert(parent.actionId()));
                }
            }
            ActionReceipt start=canonical(same,ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId()).execution()).stream()
                    .filter(value->value.command().operation().equals(kind().startOperation())).findFirst().orElseThrow();
            effects.verifyArchivedStart(start,context.archive().withSession(same));
            var retainedEntry=frontend.fixtureEntry(call.menu).resumeFixtureEntry(same,parent);
            if(retainedEntry.isPresent())return new ActionPorts.FixtureBusinessObserved(retainedEntry.orElseThrow());
            var staged=frontend.initialDriver().current(start.command().actionId());
            return RootFixtureQualifiedScope.withFixture(context,call.menu,staged,parent,this,frontend.fixtureCatalog(),deadline,scope->
                    qualify(same,parent,children,start,staged,scope,call.submitted.submission(),deadline));
        }catch(IOException|IllegalArgumentException failure){return pending("actual fixture business continuation unavailable: "+failure.getMessage(),parent);}
        finally{activeDeadline.remove();}
    }
    private ActionPorts.PostconditionResult qualify(Session same,ActionCommand parent,Children children,ActionReceipt start,
            InitialDriverBootstrap.Staged staged,QualifiedFixtureScope scope,FixtureStartSubmission submitted,Instant deadline)throws IOException,InterruptedException {
        var events=frontend.fixtureCatalog().remainingDomains().events();Call call=call(parent);
        if(call.reducer==null)call.reducer=new FixtureBusinessQualification(fixture,submitted);
        if(call.trace==null)call.trace=new FixtureQualificationTrace(context,fixture,submitted);
        var reducer=call.reducer;var trace=call.trace;
        // Existing event UNKNOWN is collected under the actual settled Start's private startup read scope.
        events.withFixtureStartupScope(same,scope,()->{
            var cursor=ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId());
            for(var child:canonical(same,cursor.execution()))if(!child.settled())context.core().requireFrontendMenu(context).coordinator.reconcile(same,child.command().actionId());
            return null;
        });
        if(canonical(same,ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId()).execution()).stream().anyMatch(value->!value.settled()))
            return pending("original startup event remains UNKNOWN after independent read; no following child reserved",parent);
        if(call.pendingEvent!=null) {
            var pending=call.pendingEvent;var child=ContinuityActionJournal.lookup(same.head().state(),pending.childActionId(),context.archive().withSession(same)).orElseThrow();
            StrictJson.require(child.settled()&&child.bodySha256().equals(pending.childBodySha256()),"startup retained original child changed");
            scope.after(same,child.command(),deadline).orElseThrow(()->new IOException("original startup after remains unavailable"));
            trace.event(pending.before(),staged.semantic(),pending.original(),pending.decision(),Optional.of(child),staged.latestFixtureRead());call.pendingEvent=null;call.traceHead=trace.preserve(same,parent);
        }
        FixtureBusinessQualification.Owner previous=null,current=reducer.decision().owner().orElse(null);
        OpportunityJson.Value preserved=call.preservedScenarioEvent;boolean observedScenario=preserved!=null;
        while(context.clock().instant().isBefore(deadline)) {
            staged.pollFixture(start.ack().orElseThrow(),deadline);var snapshot=staged.frame().semantic();var logs=trace.preserveLogs(same,FixtureQualificationLogs.observe(fixture));
            boolean eventAllowed=!observedScenario||fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO;
            previous=current;var admitted=reducer.observeOwner(snapshot,logs,eventAllowed);current=admitted.owner().orElse(null);
            trace.owner(staged.semantic(),staged.sourceQualification(),logs,eventAllowed,staged.latestFixtureRead());
            if(observedScenario)StrictJson.require(preserved.equals(snapshot.get("active_event")),"observed scenario event changed before actual business binding");
            if(admitted.stage()!=FixtureBusinessQualification.Stage.OWNER_QUERY_ADMITTED){pause(deadline);continue;}
            if(snapshot.get("active_event") instanceof OpportunityJson.Obj&&!observedScenario) {
                var before=staged.semantic();var previousOwner=previous;var currentOwner=current;
                final boolean[] observed={false};final OpportunityJson.Value[] preservedEvent={null};
                events.withFixtureStartupScope(same,scope,()->{
                    var observation=events.observeFixtureStartupEvent(same,scope,deadline);
                    StrictJson.require(observation.frame().identity().equals(before.frame()),"startup observation changed two-stable-owner admitted frame");
                    var packet=observation.originalRead().value().result();
                    var typed=OpportunityJson.object(packet.get("current_event_window_context"),"window");
                    FixtureStartupHandler.Decision decision;
                    boolean target=fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO&&new OpportunityJson.Text(FrontendFixturePolicy.STARTUP_EVENT).equals(typed.get("event_definition_key"));
                    if(target)decision=new FixtureStartupHandler.ObserveOnly(implementation);
                    else if(fixture.policy().kind()==FrontendFixturePolicy.Kind.ROBERT&&frontend.startupCase().isPresent()) {
                        var selected=frontend.startupCase().orElseThrow().decide(fixture,snapshot,packet);
                        var old=selected.proof();byte[] raw=FilesForFixture.readExact(old.actualLog(),64*1024*1024);
                        ExactRef retained=context.archive().preserveArtifact(same,raw,64*1024*1024);
                        decision=new FixtureStartupHandler.SelectDisplayedOption(selected.eventInstanceId(),selected.optionNumber(),new FixtureStartupHandler.ScopeEvidence(retained,old.scopes(),false),selected.implementationSource());
                    }else decision=new FixtureStartupHandler.AutomaticSharedPolicy(implementation);
                    var command=events.prepareFixtureStartupDecision(same,scope,observation,decision,children.nextActionId(),deadline);
                    Optional<ActionReceipt> child=Optional.empty();if(command.isPresent()){
                        var exact=command.orElseThrow();remember(exact);
                        call.pendingEvent=new PendingEvent(before,observation.originalRead().receipt(),decision,exact.actionId(),ActionCodec.bodySha256(exact));
                        trace.pendingEvent(before,observation.originalRead().receipt(),decision,exact);call.traceHead=trace.preserve(same,parent);
                        child=Optional.of(children.submit(exact));
                    }
                    scope.after(same,child.map(ActionReceipt::command).orElse(start.command()),deadline).orElseThrow(()->new IOException("independent actual startup after observation unavailable"));
                    var after=staged.semantic();
                    if(target) {
                        new FixtureStartupObservation(events.eventWindowContract()).observe(fixture,submitted,previousOwner,currentOwner,snapshot,observation.originalRead(),staged.frame().semantic(),context.archive().withSession(same));
                        observed[0]=true;preservedEvent[0]=snapshot.get("active_event");
                    }else if(staged.frame().semantic().get("active_event") instanceof OpportunityJson.Obj active) {
                        StrictJson.require(!OpportunityJson.object(snapshot.get("active_event"),"active_event").get("instance_id").equals(active.get("instance_id")),"original startup instance remains; no repeat selection");
                    }
                    trace.event(before,after,observation.originalRead().receipt(),decision,child,staged.latestFixtureRead());call.pendingEvent=null;return null;
                });
                if(observed[0]){observedScenario=true;preserved=preservedEvent[0];call.preservedScenarioEvent=preserved;}
                previous=null;current=null;continue;
            }
            if(fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO&&!observedScenario){pause(deadline);continue;}
            if(snapshot.get("active_event")!=OpportunityJson.Nil.INSTANCE&&!observedScenario){pause(deadline);continue;}
            var frame=staged.frame();ReadContract<?> root=context.finance().definitions().contract(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Query.ROOT);
            var request=new PlanningReadRequest(frame.identity(),context.source(),context.game().sessionId(),root.operation(),
                    org.xar.ck3.control.application.planning.finance.FinanceReadContracts.rootArguments(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS),deadline);
            var actual=scope.read(same,root,request);staged.pollFixture(actual.receipt().original(),deadline);
            if(!actual.receipt().request().before().equals(staged.frame().identity())){previous=null;current=null;continue;}
            var finalSnapshot=staged.frame().semantic();var normalized=FixtureGameplayRoot.publication(actual.receipt(),fixture,finalSnapshot);
            var decision=reducer.observeBusiness(finalSnapshot,normalized,logs,observedScenario);
            trace.business(staged.semantic(),staged.sourceQualification(),logs,observedScenario,actual.receipt(),staged.latestFixtureRead());
            if(!decision.fixtureTargetIdentityProven()){pause(deadline);continue;}
            ExactRef qualification=trace.preserve(same,parent);
            var evidence=new FixtureBusinessEvidence(parent.actionId(),ActionCodec.bodySha256(parent),FixturePlan.requireParent(parent),start,staged.semantic(),actual.receipt(),qualification,List.of(implementation));
            requireFixtureBusiness(parent,ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId()).execution(),evidence);
            var complete=frontend.fixtureEntry(call(parent).menu).finishFixture(same,scope,parent,evidence);
            return new ActionPorts.FixtureBusinessObserved(complete);
        }
        return pending("actual qualified fixture business actor did not stabilize before original deadline; no Start replay",parent);
    }
    private void remember(ActionCommand child){synchronized(preparedChildren){ActionCommand prior=preparedChildren.putIfAbsent(child.actionId(),child);StrictJson.require(prior==null||prior.equals(child),"fixture derived command changed immutable original body");}}
    @Override public void requireFixtureChild(ActionCommand parent,CompositeExecution cursor,ActionCommand child) {
        try {
            var same=context.writer().borrowedSession();var held=ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId());
            StrictJson.require(held.execution().equals(cursor)&&FixturePlan.requireParent(parent).policySource().equals(fixture.policySource())
                    &&child.actionId().equals(ActionIds.child(parent.actionId(),cursor.children().size()+1,child.operation())),"fixture child changed actual Held parent/canonical ordinal");
            var originals=canonical(same,cursor);StrictJson.require(originals.stream().allMatch(ActionReceipt::settled),"UNKNOWN fixture child blocks all new mutation");
            long starts=originals.stream().filter(value->value.command().operation().equals(kind().startOperation())).count();
            if(starts==0) {
                StrictJson.require(child.origin() instanceof CommandOrigin.Frontend&&parent.origin().requireFrontend().sameSession(child.origin().requireFrontend()),"fixture selection crossed original frontend process");
                var allowed=fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO?Set.of(Primitive.SCENARIO_BOOKMARK.operation(),Primitive.SCENARIO_CHARACTER.operation(),Primitive.SCENARIO_START.operation()):Set.of(Primitive.SELECT_1066.operation(),Primitive.START_BOOKMARK.operation());
                StrictJson.require(allowed.contains(child.operation())&&originals.stream().noneMatch(value->value.command().operation().equals(child.operation())),"fixture setter/Start repeated or crossed prepared branch");
                boolean characterDone=originals.stream().anyMatch(value->value.command().operation().equals(fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO?Primitive.SCENARIO_CHARACTER.operation():Primitive.SELECT_1066.operation()));
                boolean bookmarkDone=originals.stream().anyMatch(value->value.command().operation().equals(Primitive.SCENARIO_BOOKMARK.operation()));
                StrictJson.require(!characterDone||child.operation().equals(kind().startOperation()),"fixture setter order cannot move backward after character selection");
                StrictJson.require(!bookmarkDone||!child.operation().equals(Primitive.SCENARIO_BOOKMARK.operation()),"fixture bookmark selection cannot repeat");
                if(!child.operation().equals(Primitive.SELECT_1066.operation()))StrictJson.require(FixturePlan.decode(DriverJson.toNode(child.arguments()).get("fixture_plan")).equals(FixturePlan.requireParent(parent)),"fixture child substituted original policy/claim/producer");
            }else {
                StrictJson.require(starts==1&&child.origin() instanceof CommandOrigin.Gameplay,"only actual startup event child follows unique settled Start");
                synchronized(preparedChildren){StrictJson.require(child.equals(preparedChildren.get(child.actionId())),"startup child was not prepared by identical original Event installer callback");}
            }
        }catch(IOException e){throw new UncheckedIOException(e);}
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand parent,CompositeExecution retained) {
        // Reconciliation has no Children and can never select another event or repeat Start.
        return pending("fixture original parent retained; explicit same-source continuation is required for any following child",parent);
    }
    public CompositeContinuationReport resume(String originalParentId,Instant deadline)throws IOException {
        return context.withSession(same->{
            context.requireCurrent(deadline);fixture.verifySources();var original=ContinuityActionJournal.lookup(same.head().state(),originalParentId,context.archive().withSession(same)).orElseThrow();
            StrictJson.require(original.state() instanceof ActionState.CompositeUnknown&&FixturePlan.isParent(original.command()),"only actual unresolved fixture parent can continue");
            requireClaim(original.command(),FixturePlan.requireParent(original.command()),context.archive().withSession(same));call(original.command());
            return context.core().requireFrontendMenu(context).coordinator.continueOriginalComposite(same,new Issued(original.command(),deadline,same));
        });
    }
    @Override public void requireContinuation(ActionCommand parent,CompositeExecution cursor,CompositeContinuationToken token) {
        try{var same=context.writer().borrowedSession();StrictJson.require(token instanceof RootFixtureWorkflow.Issued,"fixture continuation was not privately issued by installed workflow");
            var issued=(Issued)token;StrictJson.require(issued.owner()==this&&issued.same==same&&!issued.consumed&&issued.parent.equals(parent)
                    &&context.clock().instant().isBefore(issued.deadline),"fixture continuation changed private same-writer owner/parent or expired");
            fixture.verifySources();requireClaim(parent,FixturePlan.requireParent(parent),context.archive().withSession(same));call(parent);
        }catch(IOException e){throw new UncheckedIOException(e);}
    }
    @Override public void requireContinuationChild(ActionCommand parent,CompositeExecution cursor,CompositeContinuationToken token,ActionCommand child){requireContinuation(parent,cursor,token);requireFixtureChild(parent,cursor,child);}
    @Override public ActionPorts.PostconditionResult continueOriginal(ActionCommand parent,CompositeExecution cursor,CompositeContinuationToken token,Children children)throws InterruptedException {
        requireContinuation(parent,cursor,token);try{return execute(parent,children,token.deadline(),true);}finally{((Issued)token).consumed=true;}
    }
    @Override public void requireFixtureBusiness(ActionCommand parent,CompositeExecution cursor,FixtureBusinessEvidence actual) {
        try{var same=context.writer().borrowedSession();ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId());
            actual.validateChildren(cursor,canonical(same,cursor));FixtureQualificationTrace.verify(context,same,fixture,parent,actual);
        }catch(IOException e){throw new UncheckedIOException(e);}
    }
    @Override public void requireFixtureCompletion(ActionCommand parent,CompositeExecution cursor,FixtureBusinessObservation actual) {
        try{var same=context.writer().borrowedSession();actual.validateParent(parent);actual.validateChildren(cursor,canonical(same,cursor));
            FixtureQualificationTrace.verify(context,same,fixture,parent,actual.evidence());frontend.entryAuthority().verifyFixtureEntry(same,actual);
        }catch(IOException e){throw new UncheckedIOException(e);}
    }
    private void verifyArchived(ActionReceipt parent,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(parent.state() instanceof ActionState.CompositeSettled&&((ActionState.CompositeSettled)parent.state()).settlement() instanceof ActionState.FixtureBusinessCompleted,"fixture archived parent has no actual business/Entry settlement");
        var state=(ActionState.CompositeSettled)parent.state();requireFixtureCompletion(parent.command(),state.execution(),((ActionState.FixtureBusinessCompleted)state.settlement()).observation());
    }
    private FixtureFrontendProducer.Submitted reconstruct(ActionCommand parent,List<ActionReceipt> canonical,ActionReceipt start)throws IOException {
        var archive=context.archive().withSession(context.writer().borrowedSession());var args=DriverJson.toNode(start.command().arguments());
        var modelRef=ExactRef.fromJson(args.get("model"));var modelRead=archive.loadRead(modelRef);NativeRecordedEvidenceVerifier.requireRead(modelRead,archive);
        var definition=effects.models().model();
        var model=definition.decode(modelRead);boolean scenario=fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO;
        var candidate=model.selected(scenario?FrontendFixturePolicy.SCENARIO_TARGET.characterNameKey():FrontendFixturePolicy.ROBERT_KEY,scenario,true);
        var selected=new FixtureStartSubmission.Selected(fixture.policy().kind(),candidate.bookmarkGroupKey(),candidate.bookmarkKey(),candidate.characterNameKey(),candidate.governmentKey(),candidate.dateRaw(),
                scenario?Optional.of(modelRead.original().originalResultToken().orElseThrow()):Optional.empty(),Optional.empty());
        ObjectNode before=StrictJson.object().put("route",FrontendRulesData.Route.BOOKMARKS.wire());
        var pending=new FixtureStartSubmission(fixture.policy().kind(),model.source().binding(),fixture.binding(),new RawJson(StrictJson.canonical(before)),selected,
                acknowledgement(canonical,Primitive.SCENARIO_BOOKMARK),acknowledgement(canonical,scenario?Primitive.SCENARIO_CHARACTER:Primitive.SELECT_1066),FixtureFrontendProducer.ack(start));
        return new FixtureFrontendProducer.Submitted(pending,FixturePlan.requireParent(parent).claim(),List.of(ExactRef.fromJson(args.get("before_route")),modelRef),canonical);
    }
    private Optional<RawJson> acknowledgement(List<ActionReceipt> receipts,Primitive operation)throws IOException {
        var values=receipts.stream().filter(value->value.command().operation().equals(operation.operation())).toList();StrictJson.require(values.size()<=1,"original fixture setter repeated");return values.isEmpty()?Optional.empty():Optional.of(FixtureFrontendProducer.ack(values.getFirst()));
    }
    private void requireClaim(ActionCommand parent,FixturePlan plan,ActionPorts.OutcomeArchive archive) {
        ObjectNode claim=StrictJson.object(StrictJson.parse(archive.loadMaterial(plan.claim()).bytes()),Set.of("phase","action_id","binding","policy_binding","policy_source"));
        StrictJson.require(StrictJson.text(claim.get("phase")).equals("claimed-before-any-mutation")&&StrictJson.text(claim.get("action_id")).equals(parent.actionId())
                &&ExactRef.fromJson(claim.get("policy_source")).equals(fixture.policySource())&&FrontendFixturePolicy.Binding.fromJson(claim.get("policy_binding")).equals(fixture.binding()),"fixture original exclusive claim changed");
        var binding=StrictJson.object(claim.get("binding"),Set.of("bridge_pid","connection_generation"));
        StrictJson.require(StrictJson.integer(binding.get("bridge_pid"),1,0xffff_ffffL)==parent.origin().requireFrontend().bridgePid()
                &&StrictJson.integer(binding.get("connection_generation"),java.math.BigInteger.ONE,StrictJson.UINT64_MAX).equals(parent.origin().requireFrontend().connectionGeneration()),"fixture exclusive claim crossed actual original process/connection");
    }
    private Call call(ActionCommand parent){synchronized(calls){var value=calls.get(parent.actionId());StrictJson.require(value!=null&&value.parent.equals(parent),"same physical fixture producer custody unavailable; no reconstruction can grant a fresh Start");return value;}}
    private List<ActionReceipt> canonical(Session same,CompositeExecution cursor)throws IOException {
        var archive=context.archive().withSession(same);var result=new ArrayList<ActionReceipt>();for(var child:cursor.children()) {
            var value=ContinuityActionJournal.lookup(same.head().state(),child.actionId(),archive).orElseThrow();StrictJson.require(value.bodySha256().equals(child.bodySha256()),"fixture original child body changed");result.add(value);
        }return List.copyOf(result);
    }
    private ActionPorts.Pending pending(String reason,ActionCommand parent){var refs=new ArrayList<>(List.of(FixturePlan.requireParent(parent).policySource(),FixturePlan.requireParent(parent).claim(),implementation));
        synchronized(calls){var call=calls.get(parent.actionId());if(call!=null&&call.traceHead!=null)refs.add(call.traceHead);}return new ActionPorts.Pending(reason,refs);}
    private Duration transition(Instant deadline){Duration duration=Duration.between(context.clock().instant(),deadline);return duration.compareTo(Duration.ofMinutes(5))>0?Duration.ofMinutes(5):duration;}
    private void pause(Instant deadline)throws InterruptedException {long remaining=Duration.between(context.clock().instant(),deadline).toMillis();if(remaining>0)Thread.sleep(Math.min(50,remaining));}
    private static Claims emptyClaims(){return new Claims(Set.of(),Set.of(),Set.of(),Set.of());}
    private static final class FilesForFixture {
        static byte[] readExact(ExactRef ref,int maximum)throws IOException {byte[] bytes=java.nio.file.Files.readAllBytes(java.nio.file.Path.of(ref.path()));StrictJson.require(bytes.length<=maximum&&bytes.length==ref.bytes()&&DriverJson.sha256(bytes).equals(ref.sha256()),"actual external startup log changed");return bytes;}
    }
}
