package org.xar.ck3.control.service.root;

import java.io.IOException;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Private live custody of one registered fixture parent's actual first Driver. */
public final class RootFixtureQualifiedScope implements QualifiedFixtureScope,ReadinessAuthority,RootActionGuard.DerivedChildAdmission {
    @FunctionalInterface public interface Work<T> {T run(QualifiedFixtureScope actual)throws IOException,InterruptedException;}
    private static final ThreadLocal<RootFixtureQualifiedScope> ACTIVE=new ThreadLocal<>();
    private final RootRuntimeContext context;
    private final RootMenuSession menu;
    private final InitialDriverBootstrap.Staged staged;
    private final ActionCommand parent;
    private final FixtureCompositeActionPort handler;
    private final RootInstalledCatalog catalog;
    private final Instant deadline;
    private final FixturePlan plan;
    private final RootActionGuard actions;
    private final RootPlanningReadGuard reads;
    private final RootDomainIntentPreparation intents;
    private RootInstalledCatalog.FixtureProducts products;
    private boolean retired;
    private int observationDepth;

    private RootFixtureQualifiedScope(RootRuntimeContext context,RootMenuSession menu,InitialDriverBootstrap.Staged staged,
            ActionCommand parent,FixtureCompositeActionPort handler,RootInstalledCatalog catalog,Instant deadline)throws IOException {
        this.context=Objects.requireNonNull(context);this.menu=Objects.requireNonNull(menu);this.staged=Objects.requireNonNull(staged);
        this.parent=Objects.requireNonNull(parent);this.handler=Objects.requireNonNull(handler);this.catalog=Objects.requireNonNull(catalog);
        this.deadline=Objects.requireNonNull(deadline);plan=FixturePlan.requireParent(parent);
        StrictJson.require(context.core().requireFrontendMenu(context)==menu&&catalog.context()==context
                &&context.bindings()==menu.bindings&&menu.bindings.composites().find(parent.operation()).orElseThrow()==handler,
                "fixture requires this exact installed Root/Menu/catalog/handler");
        context.game().launchPlan().sources().requireLoadedClass(handler.getClass());
        var same=context.borrowedSession();staged.requireFixtureOwner(same,context.game(),context.source());
        cursor(same,Optional.empty());
        actions=new RootActionGuard(this,context.core().borrowedSessions(),context.archive(),context.source(),context.clock(),
                menu.authorityId,context.originals(),menu.bindings,this);
        reads=new RootPlanningReadGuard(this,context.core().borrowedSessions(),context.archive(),context.source(),context.clock(),
                menu.authorityId,context.originals(),menu.bindings.readCatalog());
        intents=new RootDomainIntentPreparation(context.writer(),catalog.pendingBindings(),catalog.requiredPending());
    }
    public static <T>T withFixture(RootRuntimeContext context,RootMenuSession menu,InitialDriverBootstrap.Staged staged,
            ActionCommand exactParent,FixtureCompositeActionPort identicalInstalledHandler,RootInstalledCatalog identicalCatalog,
            Instant deadline,Work<T> callback)throws IOException,InterruptedException {
        Objects.requireNonNull(callback);StrictJson.require(ACTIVE.get()==null,"fixture live callbacks cannot nest");
        var same=context.borrowedSession();
        return staged.withFixtureDeadline(same,exactParent,identicalInstalledHandler.handlerId(),deadline,()->{
            var actual=new RootFixtureQualifiedScope(context,menu,staged,exactParent,identicalInstalledHandler,identicalCatalog,deadline);
            ACTIVE.set(actual);
            try {
                actual.requireCurrent(same);actual.products=identicalCatalog.stageFixture(staged);
                identicalCatalog.requireFixtureProducts(staged,actual.products);
                context.core().bindFixtureHistory(context,staged,actual.products);
                return callback.run(actual);
            } finally {actual.retired=true;ACTIVE.remove();}
        });
    }
    static RootFixtureQualifiedScope required() {
        var actual=ACTIVE.get();
        if(actual==null||actual.retired)throw new IllegalStateException("no privately issued actual fixture callback is active");
        return actual;
    }
    static Optional<RootFixtureQualifiedScope> optional(){return Optional.ofNullable(ACTIVE.get()).filter(value->!value.retired);}
    private ActionChildPlanningScope.FixtureCursor cursor(Session same,Optional<ActionCommand> child)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);
        StrictJson.require(!retired&&!staged.fixtureRetired()&&parent.source().equals(context.source())
                &&parent.sessionId().equals(context.game().sessionId())&&parent.origin().game().equals(context.game().generation()),
                "fixture callback lost its actual initial physical owner/source");
        var cursor=child.isPresent()
                ?ActionChildPlanningScope.fixtureReservedChild(same,same.head(),child.orElseThrow(),parent,handler.handlerId())
                :ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handler.handlerId());
        StrictJson.require(cursor.parent().bodySha256().equals(ActionCodec.bodySha256(parent))
                &&FixturePlan.requireParent(cursor.parent().command()).equals(plan),"fixture changed its actual canonical parent");
        var starts=cursor.recordedChildren().stream().filter(value->value.command().operation().equals(plan.kind().startOperation())).toList();
        StrictJson.require(starts.size()==1&&starts.getFirst().settled()&&starts.getFirst().command().equals(staged.command())
                &&starts.getFirst().state() instanceof ActionState.Settled settled
                &&settled.settlement() instanceof ActionState.FixtureStarted,"fixture needs its unique canonically settled real first-map Start");
        var first=((ActionState.FixtureStarted)((ActionState.Settled)starts.getFirst().state()).settlement()).observation();
        StrictJson.require(first.fixture().equals(plan)&&first.firstMap().equals(staged.firstMapSemantic())
                &&first.fullBindingSha256().equals(staged.firstMapFrame().fullBindingSha256())
                &&first.independentRead().equals(staged.independentRead().acknowledgement())
                &&first.snapshotReceived().equals(staged.independentRead().snapshotReceived()),
                "fixture scope changed its actual independent first-map originals");
        for(var ref:List.of(plan.policySource(),plan.claim(),plan.producerSource(),context.source().sourceRef()))same.verifyPin(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
        staged.requireFixtureOwner(same,context.game(),context.source());return cursor;
    }
    @Override public void requireContext(RootRuntimeContext identical)throws IOException {
        StrictJson.require(identical==context&&ACTIVE.get()==this,"fixture scope escaped its original Root context or callback");
        requireCurrent(context.borrowedSession());
    }
    @Override public void requireCurrent(Session identicalBorrowed)throws IOException {
        StrictJson.require(ACTIVE.get()==this,"fixture scope is unavailable outside its source-owned callback");
        var action=ActionScope.currentActionId().orElseThrow();
        if(action.equals(parent.actionId()))cursor(identicalBorrowed,Optional.empty());
        else{
            var child=ContinuityActionJournal.lookup(identicalBorrowed.head().state(),action,
                    context.archive().withSession(identicalBorrowed)).orElseThrow();
            cursor(identicalBorrowed,Optional.of(child.command()));
        }
        if(products!=null)catalog.requireFixtureProducts(staged,products);
    }
    @Override public String parentActionId(){return parent.actionId();}
    @Override public ExactRef policySource(){return plan.policySource();}
    @Override public List<OpportunityJson.Obj> history(Session same)throws IOException {
        requireCurrent(same);
        return staged.fixtureDriver(same).driver().commandHistory().stream()
                .map(row->DriverJson.object(row.originalRow().json(),DriverJson.MAX_NATIVE_BYTES)).toList();
    }
    @Override public <T>T withCurrent(Session same,Instant originalDeadline,QualifiedFixtureScope.Work<T> work)throws IOException {
        Objects.requireNonNull(work);requireCurrent(same);
        StrictJson.require(!originalDeadline.isAfter(deadline)&&context.clock().instant().isBefore(originalDeadline),"fixture read deadline changed");
        observationDepth++;
        try {return staged.scopedRead(()->staged.current(same,staged.frame().identity(),originalDeadline,work::apply));}
        finally {observationDepth--;if(observationDepth==0&&products!=null)products.readHistory().flushActualReads(same);}
    }
    @Override public <T>T current(Session same,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity expected,
            Instant callerDeadline,ReadinessAuthority.CheckedWork<T> work)throws IOException {
        Objects.requireNonNull(callerDeadline);
        StrictJson.require(ACTIVE.get()==this&&!retired&&expected.equals(staged.frame().identity()),"fixture guard changed its actual full frame");
        Instant effectiveDeadline=callerDeadline.isBefore(deadline)?callerDeadline:deadline;
        return staged.scopedRead(()->staged.current(same,expected,effectiveDeadline,work));
    }
    @Override public <T>PlanningReadResult.Known<T> read(Session same,ReadContract<T> identicalContract,PlanningReadRequest request)throws IOException {
        requireCurrent(same);
        StrictJson.require(menu.bindings.readCatalog().containsIdentity(identicalContract)&&request.source().equals(context.source())
                &&request.sessionId().equals(context.game().sessionId())&&request.before().equals(staged.frame().identity())
                &&request.operation().equals(identicalContract.operation())&&request.origin() instanceof CommandOrigin.Gameplay,
                "fixture READ changed its identical installed contract or original current frame/source/session");
        PlanningReadResult<T> result=staged.scopedRead(()->menu.readEntry(same,identicalContract,request));
        if(observationDepth==0)products.readHistory().flushActualReads(same);
        if(result instanceof PlanningReadResult.Known<T> known){
            if(identicalContract.operation().equals(GameplayEntryRoot.OPERATION))staged.retainFixtureRoot(known);
            return known;
        }
        throw new IOException("actual fixture independent native READ is unavailable");
    }
    @Override public Optional<DriverObservationAssembler.Complete> after(Session same,ActionCommand originalChild,Instant originalDeadline)throws IOException {
        var current=ActionScope.currentActionId();
        var held=cursor(same,current.filter(parent.actionId()::equals).isPresent()?Optional.empty():Optional.of(originalChild));
        StrictJson.require(held.execution().children().stream().anyMatch(value->value.actionId().equals(originalChild.actionId())
                &&value.bodySha256().equals(ActionCodec.bodySha256(originalChild))),
                "fixture after READ cannot observe an unrelated or unreserved action");
        var actual=ContinuityActionJournal.lookup(same.head().state(),originalChild.actionId(),context.archive().withSession(same)).orElseThrow();
        NativeActionPort.DispatchOutcome dispatch;
        if(actual.state() instanceof ActionState.AckReceived value)dispatch=value.dispatch();
        else if(actual.state() instanceof ActionState.Unknown value&&value.dispatch().isPresent())dispatch=value.dispatch().orElseThrow();
        else if(actual.state() instanceof ActionState.Settled value)dispatch=value.dispatch();
        else return Optional.empty();
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return Optional.empty();
        try {staged.pollFixture(ack,originalDeadline);return Optional.of(staged.frame());}
        catch(InterruptedException failure){Thread.currentThread().interrupt();var interrupted=new java.io.InterruptedIOException("fixture independent after READ interrupted");interrupted.initCause(failure);throw interrupted;}
    }
    GuardEvidence guard(WriterContracts.Head head,ActionCommand child) {
        try {cursor(context.borrowedSession(),Optional.of(child));return actions.verify(head,child);}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    <T> T withOriginalReadSource(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract,
            java.util.function.Supplier<T> work) {
        Objects.requireNonNull(work);
        try {
            requireCurrent(context.borrowedSession());
            return reads.withOriginalReadSource(head,request,contract,work);
        } catch(IOException failure) { throw new UncheckedIOException(failure); }
        finally {
            try { requireCurrent(context.borrowedSession()); }
            catch(IOException failure) { throw new UncheckedIOException(failure); }
        }
    }
    PlanningReadGuard readGuard(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
        try {requireCurrent(context.borrowedSession());return reads.verify(head,request,contract);}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    void prepare(Session same,ActionCommand child){try{cursor(same,Optional.of(child));intents.prepare(same,child);}catch(IOException failure){throw new UncheckedIOException(failure);}}
    void completed(Session same,ActionReceipt child){
        try {cursor(same,Optional.of(child.command()));products.capabilities().afterMarriageAttempt(same,child);products.actionHistory().completed(same,child);}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    void barrier(Session same,ActionCommand child){try{cursor(same,Optional.of(child));products.readHistory().requireBeforeIntent(same,child);}catch(IOException failure){throw new UncheckedIOException(failure);}}
    DriverCapabilityRuntime capabilities(Session same)throws IOException {requireCurrent(same);return products.capabilities();}
    InitialDriverBootstrap.Staged staged(Session same)throws IOException {requireCurrent(same);return staged;}
    RootRuntimeContext context(){return context;}
    RootInstalledCatalog catalog(){return catalog;}
    FixtureCompositeActionPort handler(){return handler;}
    void requireHistoryComplete(Session same)throws IOException {
        requireCurrent(same);products.readHistory().flushActualReads(same);
        StrictJson.require(!products.readHistory().hasPending(same)&&!products.actionHistory().hasPending(same),
                "unpublished original fixture READ/ACTION history cannot be discarded by entry");
    }
    ActionCommand parent(){return parent;}
    void retire(){StrictJson.require(ACTIVE.get()==this,"only the actual fixture callback may retire its scope");retired=true;}
    @Override public ExactRef verify(Session same,WriterContracts.Head actualHead,ActionCommand child,ReadinessAuthority.LeaseSnapshot frame,
            ExecutableStepBindings.InstalledStep definition,ActionPorts.OutcomeArchive originals)throws IOException {
        var retained=cursor(same,Optional.of(child));handler.requireFixtureChild(parent,retained.execution(),child);
        StrictJson.require(frame.frame().identity().equals(child.before())&&definition.operation().equals(child.operation()),
                "fixture derived child changed its actual full frame or installed definition");
        return RootFixtureGuardEvidence.preserve(same,retained,parent,child,handler.handlerId(),plan,originals);
    }
}

