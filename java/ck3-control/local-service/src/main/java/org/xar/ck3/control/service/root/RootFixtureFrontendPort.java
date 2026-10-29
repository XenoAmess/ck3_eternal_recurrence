package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;

/** Named production consumer of the original Root menu, writer, read coordinator and action coordinator. */
public final class RootFixtureFrontendPort implements FixtureFrontendProducer.Port {
    private final RootRuntimeContext context;
    private final RootFrontendRuntime frontend;
    private final RootMenuSession menu;
    private final PreparedFixture fixture;
    private final FixtureFrontendEffects effects;
    private final FrontendRulesDefinitions definitions;
    private final Instant deadline;
    private FrontendIdentity identity;
    private CompositeActionPort.Children children;
    private ActionCommand parent;
    private FixtureCompositeActionPort handler;
    public RootFixtureFrontendPort(RootRuntimeContext context,RootFrontendRuntime frontend,RootMenuSession menu,
            PreparedFixture fixture,FixtureFrontendEffects effects,FrontendIdentity actualMenu,Instant deadline)throws IOException {
        this.context=Objects.requireNonNull(context);this.frontend=Objects.requireNonNull(frontend);this.menu=Objects.requireNonNull(menu);
        this.fixture=Objects.requireNonNull(fixture);this.effects=Objects.requireNonNull(effects);this.identity=Objects.requireNonNull(actualMenu);this.deadline=Objects.requireNonNull(deadline);
        frontend.requireContext(context);definitions=frontend.rules().definitions();
        StrictJson.require(frontend.fixture().orElseThrow()==fixture&&frontend.fixtureEffects().orElseThrow()==effects
                &&menu.writer==context.writer()&&menu.coordinator==context.core().requireFrontendMenu(context).coordinator&&menu.source.equals(context.source())
                &&menu.game==context.game()&&effects.fixture()==fixture&&actualMenu.game().equals(menu.game.generation())
                &&actualMenu.frontendSessionId().equals(menu.game.sessionId()),"fixture consumer requires identical actual Root menu/coordinator/writer/Game");
        frontend.initialPolicy().requireFixtureProjection(fixture);
        menu.game.launchPlan().sources().requireLoadedClass(getClass());fixture.verifySources();context.requireCurrent(deadline);
    }
    public void requireFixture(PreparedFixture same) { StrictJson.require(same==fixture,"fixture producer cannot replace prepared source custody"); }
    public RootMenuSession menu() { return menu; }
    public RootRuntimeContext context() { return context; }
    public FixtureFrontendEffects effects() { return effects; }
    public FrontendIdentity identity(){return identity;}
    @FunctionalInterface interface ChildWork<T>{T run()throws IOException,InterruptedException;}
    synchronized <T>T withChildren(ActionCommand original,FixtureCompositeActionPort actualHandler,CompositeActionPort.Children actual,ChildWork<T> work)throws IOException,InterruptedException {
        StrictJson.require(children==null,"fixture child callback cannot nest");var same=context.writer().borrowedSession();
        var held=ActionChildPlanningScope.fixtureCurrent(same,same.head(),original,actualHandler.handlerId());
        StrictJson.require(held.parent().command().equals(original),"fixture callback changed its actual canonical upfront parent");
        parent=original;handler=actualHandler;children=Objects.requireNonNull(actual);
        try{return work.run();}finally{children=null;parent=null;handler=null;}
    }
    @Override public synchronized FrontendRulesData.Source currentSource()throws IOException {
        return route().value().source();
    }
    @Override public synchronized PlanningReadResult.Known<FrontendRulesData.ObservedRoute> route()throws IOException {
        return read(definitions.route());
    }
    @Override public synchronized PlanningReadResult.Known<FixtureModelContract.Observation> model(boolean scenario)throws IOException {
        StrictJson.require(scenario==(fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO),"fixture query crossed its prepared branch");
        return read(effects.models().model());
    }
    private <T> PlanningReadResult.Known<T> read(ReadContract<T> contract)throws IOException {
        fixture.verifySources();context.requireCurrent(deadline);
        var request=new PlanningReadRequest(new CommandOrigin.Frontend(identity),menu.source,menu.game.sessionId(),contract.operation(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),deadline);
        var result=menu.read(contract,request);
        if(!(result instanceof PlanningReadResult.Known<T> known))throw new IOException("actual fixture native query unavailable; no mutation submitted");
        context.writer().locked(borrowed->{NativeRecordedEvidenceVerifier.requireRead(known.receipt(),context.archive().withSession(borrowed));return null;});
        StrictJson.require(identity.sameSession(known.receipt().after().binding().origin().requireFrontend()),"fixture native read reconnected to another process");
        identity=known.receipt().after().binding().origin().requireFrontend();return known;
    }
    @Override public synchronized ActionReceipt mutate(String actionId,FixtureFrontendProducer.Mutation mutation)throws IOException {
        fixture.verifySources();context.requireCurrent(deadline);
        StrictJson.require(children!=null&&parent!=null&&handler!=null,"fixture writes require actual upfront Composite Children custody");
        var same=context.writer().borrowedSession();ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handler.handlerId());
        var step=mutation.primitive();var origin=new CommandOrigin.Frontend(identity);
        org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj arguments;
        FrontendExpectedPostcondition expected;
        arguments=effects.arguments(mutation,FixturePlan.requireParent(parent));expected=effects.expected(identity,menu.source,step);
        StrictJson.require(menu.bindings.actualActionBinding(step.operation()).orElseThrow().observer()==effects,"fixture primitive is not installed in actual Root action registry");
        var command=new ActionCommand(children.nextActionId(step.operation()),origin,menu.source,menu.game.sessionId(),step.operation(),arguments,new CommandExpectation.Frontend(expected),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
        ActionReceipt result=children.submit(command);
        StrictJson.require(result.command().equals(command),"fixture original coordinator returned another immutable request");
        return result;
    }
    @Override public ExactRef preserveClaim(RawJson original)throws IOException {
        return context.writer().locked(borrowed->context.archive().withSession(borrowed).preserveMaterial(original));
    }
    @Override public synchronized ActionReceipt reconcileSelection(ActionReceipt original)throws IOException {
        StrictJson.require(!FixtureFrontendEffects.start(java.util.Arrays.stream(Primitive.values()).filter(p->p.operation().equals(original.command().operation())).findFirst().orElseThrow()),"selection reconciliation cannot submit another Start");
        fixture.verifySources();context.requireCurrent(deadline);ActionReceipt result=menu.reconcile(original.command().actionId());
        StrictJson.require(result.command().equals(original.command()),"fixture reconciliation changed original selection request");return result;
    }
    @Override public RawJson originalModel(PlanningReadResult.Known<FixtureModelContract.Observation> model)throws IOException {
        context.writer().locked(borrowed->{NativeRecordedEvidenceVerifier.requireRead(model.receipt(),context.archive().withSession(borrowed));return null;});
        return model.receipt().original().originalResultToken().orElseThrow(()->new IOException("original fixture model token missing"));
    }
    @Override public Clock clock() { return context.clock(); }
    @Override public Instant deadline() { return deadline; }
    @Override public void pause(Duration duration)throws InterruptedException { if(!duration.isNegative()&&!duration.isZero())Thread.sleep(duration.toMillis(),duration.toNanosPart()%1_000_000); }
}
