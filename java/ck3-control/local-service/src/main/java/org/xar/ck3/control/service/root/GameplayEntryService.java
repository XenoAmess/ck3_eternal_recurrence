package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

/** Executable ordinary bookmark entry, retaining the one Root writer/read/action graph through promotion. */
public final class GameplayEntryService {
    public sealed interface Result permits Awaiting,EntryCommitUnknown,Admitted { }
    public record Awaiting(ActionReceipt actual,String reason) implements Result {
        public Awaiting { Objects.requireNonNull(actual);StrictJson.text(reason); }
    }
    public record EntryCommitUnknown(ActionReceipt actual,String eventIdentity,String reason) implements Result {
        public EntryCommitUnknown { Objects.requireNonNull(actual);WriterContracts.requireDigest(eventIdentity);StrictJson.text(reason); }
    }
    public record Admitted(ActionReceipt actual,DriverBootstrap.Adopted driver,WriterContracts.Receipt entry) implements Result {
        public Admitted { Objects.requireNonNull(actual);Objects.requireNonNull(driver);Objects.requireNonNull(entry); }
    }
    private final RootApplicationAssembly.Core core;
    private final RootMenuSession menu;
    private final FrontendRulesDefinitions definitions;
    private final GameplayStartEffects effects;
    private final InitialDriverBootstrap bootstrap;
    private final GameplayEntryAuthority authority;
    private ActionCommand submitted;
    private ActionReceipt actualStart;
    private WriterContracts.Prepared prepared;
    private WriterContracts.Receipt committed;
    private Admitted admitted;
    public GameplayEntryService(RootApplicationAssembly.Core core,RootMenuSession menu,FrontendRulesDefinitions definitions,
            GameplayStartEffects effects,InitialDriverBootstrap bootstrap,GameplayEntryReadGuard exactReadGuard,
            GameplayEntryAuthority authority,ExactRef actualGuardSource,ExactRef actualAuthoritySource)throws IOException {
        this(core,menu,definitions,effects,bootstrap,exactReadGuard,authority,actualGuardSource,actualAuthoritySource,false);
    }
    public static GameplayEntryService fixture(RootApplicationAssembly.Core core,RootMenuSession menu,FrontendRulesDefinitions definitions,
            GameplayStartEffects effects,InitialDriverBootstrap bootstrap,GameplayEntryReadGuard exactReadGuard,
            GameplayEntryAuthority authority,ExactRef actualGuardSource,ExactRef actualAuthoritySource)throws IOException {
        return new GameplayEntryService(core,menu,definitions,effects,bootstrap,exactReadGuard,authority,actualGuardSource,actualAuthoritySource,true);
    }
    private GameplayEntryService(RootApplicationAssembly.Core core,RootMenuSession menu,FrontendRulesDefinitions definitions,
            GameplayStartEffects effects,InitialDriverBootstrap bootstrap,GameplayEntryReadGuard exactReadGuard,
            GameplayEntryAuthority authority,ExactRef actualGuardSource,ExactRef actualAuthoritySource,boolean explicitFixture)throws IOException {
        this.core=Objects.requireNonNull(core);this.menu=Objects.requireNonNull(menu);this.definitions=Objects.requireNonNull(definitions);
        this.effects=Objects.requireNonNull(effects);this.bootstrap=Objects.requireNonNull(bootstrap);this.authority=Objects.requireNonNull(authority);
        StrictJson.require(menu.writer==core.writer() && menu.bindings.readCatalog().containsIdentity(definitions.route())
                && menu.bindings.readCatalog().containsIdentity(definitions.bookmark()),"entry must retain Core's identical writer and native model contracts");
        StrictJson.require(explicitFixture==bootstrap.fixture().isPresent(),"ordinary and explicit fixture entry cannot exchange their bootstrap producers");
        if(!explicitFixture){
            var start=menu.bindings.actualActionBinding(FrontendRulesRequests.Primitive.START_BOOKMARK.operation()).orElseThrow();
            StrictJson.require(start.observer()==effects,"Root Start operation belongs to another actual verifier");effects.bindMenu(menu);
        }else bootstrap.fixture().orElseThrow().verifySources();
        authority.bindFixtureBindings(menu.bindings);
        menu.installEntryReads(exactReadGuard,actualGuardSource);menu.installEntryAuthority(authority,actualAuthoritySource);
    }
    public synchronized Result startRobert(String actionId,FrontendIdentity actualMenu,Instant deadline)throws IOException {
        return startSelected(actionId,actualMenu,"bookmark_rags_to_riches_duke_robert",deadline);
    }
    public synchronized Result startSelected(String actionId,FrontendIdentity actualMenu,String characterNameKey,Instant deadline)throws IOException {
        StrictJson.require(bootstrap.fixture().isEmpty(),"explicit fixture startup must use its source-owned upfront parent");
        StrictJson.text(actionId);Objects.requireNonNull(actualMenu);Objects.requireNonNull(deadline);
        if(submitted!=null) {
            StrictJson.require(submitted.actionId().equals(actionId)
                    && GameplayStartEffects.Arguments.decode(submitted.arguments()).characterNameKey().equals(characterNameKey),
                    "initial Start already has another immutable action identity or selected character");
            return resume();
        }
        var route=known(menu.read(definitions.route(),new PlanningReadRequest(new CommandOrigin.Frontend(actualMenu),menu.source,
                menu.game.sessionId(),definitions.route().operation(),new OpportunityJson.Obj(Map.of()),deadline)));
        FrontendIdentity afterRoute=route.receipt().after().binding().origin().requireFrontend();
        var model=known(menu.read(definitions.bookmark(),new PlanningReadRequest(new CommandOrigin.Frontend(afterRoute),menu.source,
                menu.game.sessionId(),definitions.bookmark().operation(),new OpportunityJson.Obj(Map.of()),deadline)));
        Candidate selected=model.value().selected(characterNameKey,false,true);
        FrontendIdentity origin=model.receipt().after().binding().origin().requireFrontend();
        var arguments=new GameplayStartEffects.Arguments(route.originalReceipt(),model.originalReceipt(),characterNameKey).encode();
        var expected=effects.expected(origin,menu.source,selected);
        submitted=new ActionCommand(actionId,new CommandOrigin.Frontend(origin),menu.source,menu.game.sessionId(),
                FrontendRulesRequests.Primitive.START_BOOKMARK.operation(),arguments,new CommandExpectation.GameplayEntry(expected),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
        // Retain the immutable request before execute: any exception after dispatch must use reconcile.
        actualStart=menu.execute(submitted);return complete();
    }
    /** Reconciles an already attempted action. It never calls Native submit or constructs another Start. */
    public synchronized Result resume()throws IOException {
        if(admitted!=null)return admitted;
        StrictJson.require(submitted!=null,"no original Start request exists to reconcile");
        if(prepared==null)actualStart=menu.reconcile(submitted.actionId());
        return complete();
    }
    private Result complete()throws IOException {
        if(admitted!=null)return admitted;
        StrictJson.require(actualStart!=null,"actual canonical Start receipt is unavailable");
        if(!(actualStart.state() instanceof ActionState.Settled settled) || !(settled.settlement() instanceof ActionState.GameplayEntered))
            return new Awaiting(actualStart,"original Start has no verified first full Driver/SEM/root/paused-pump settlement");
        if(prepared==null) {
            prepared=core.writer().locked(borrowed -> borrowed.preview(authority.request(borrowed,actualStart)));
        }
        if(committed==null) {
            try { committed=core.writer().commit(prepared); }
            catch(IOException failure) { return new EntryCommitUnknown(actualStart,prepared.request().identity(),String.valueOf(failure.getMessage())); }
        }
        // Reuse the identical producer/repository/public revision owner through Core's private registration.
        DriverBootstrap.Adopted driver=core.adoptInitial(bootstrap.current(submitted.actionId()),prepared,committed);
        admitted=new Admitted(actualStart,driver,committed);return admitted;
    }
    private ActionCommand fixtureParent;
    private WriterContracts.Prepared fixturePrepared;
    private WriterContracts.Receipt fixtureCommitted;
    private ExactRef fixturePreparedRef;
    private FixtureBusinessObservation fixtureObservation;
    private FixtureBusinessEvidence fixtureBusiness;
    /** Actual same-writer entry of the already executed upfront fixture parent. It never submits Start or a child. */
    public synchronized FixtureBusinessObservation finishFixture(ContinuityStorePort.Session same,QualifiedFixtureScope actualScope,
            ActionCommand exactParent,FixtureBusinessEvidence original)throws IOException {
        core.writer().requireSession(same);Objects.requireNonNull(actualScope);Objects.requireNonNull(original);
        if(fixtureObservation!=null){
            StrictJson.require(fixtureParent.equals(exactParent)&&fixtureObservation.evidence().equals(original),
                    "fixture completion cannot replace its committed original parent/evidence");
            authority.verifyFixtureEntry(same,fixtureObservation);return fixtureObservation;
        }
        StrictJson.require(actualScope instanceof RootFixtureQualifiedScope,"fixture entry requires the sole privately issued Root scope");
        var actual=(RootFixtureQualifiedScope)actualScope;actual.requireCurrent(same);actual.requireContext(actual.context());
        StrictJson.require(actual.context().core()==core&&actual.parent().equals(exactParent)
                &&actual.handler()==menu.bindings.composites().find(exactParent.operation()).orElseThrow()
                &&bootstrap.fixture().isPresent(),"fixture entry crossed its actual Core/menu/handler/bootstrap");
        var staged=actual.staged(same);staged.requireFixtureBootstrap(same,bootstrap);
        actual.requireHistoryComplete(same);original.validateParent(exactParent);
        if(fixtureParent==null)fixtureParent=exactParent;
        StrictJson.require(fixtureParent.equals(exactParent),"entry already retains another immutable fixture parent");
        if(fixtureBusiness==null)fixtureBusiness=original;
        StrictJson.require(fixtureBusiness.equals(original),"fixture entry cannot replace its original prepared business evidence");
        if(fixturePrepared==null){
            fixturePrepared=same.preview(authority.requestFixture(same,original.originalStart(),exactParent,actual.handler().handlerId(),original));
            fixturePreparedRef=core.archive().preserveArtifact(same,WriterTransactionCodec.encodePrepared(fixturePrepared),WriterTransactionCodec.MAXIMUM_BYTES);
        }
        if(fixtureCommitted==null){
            var known=same.queryCommitted(fixturePrepared);
            fixtureCommitted=known.isPresent()?known.orElseThrow():same.commit(fixturePrepared);
        }
        same.requireCommitted(fixturePrepared,fixtureCommitted);
        ExactRef committedRef=core.archive().preserveArtifact(same,WriterTransactionCodec.encodeReceipt(fixtureCommitted),WriterTransactionCodec.MAXIMUM_BYTES);
        // Core reuses this exact retained provisional repository and authority; no synthetic Adopted is constructed.
        core.adoptInitial(staged,fixturePrepared,fixtureCommitted);
        var result=new FixtureBusinessObservation(original,fixturePreparedRef,committedRef);
        authority.verifyFixtureEntry(same,result);fixtureObservation=result;actual.retire();return result;
    }
    /** Resolves only this live producer's retained original Entry transaction. It performs no new native READ or action. */
    public synchronized java.util.Optional<FixtureBusinessObservation> resumeFixtureEntry(ContinuityStorePort.Session same,
            ActionCommand exactParent)throws IOException {
        core.writer().requireSession(same);
        if(fixturePrepared==null)return java.util.Optional.empty();
        StrictJson.require(fixtureParent.equals(exactParent)&&fixtureBusiness!=null,
                "fixture Entry recovery cannot replace the retained original parent or business evidence");
        if(fixtureObservation!=null){authority.verifyFixtureEntry(same,fixtureObservation);return java.util.Optional.of(fixtureObservation);}
        var known=same.queryCommitted(fixturePrepared);
        if(known.isEmpty())return java.util.Optional.empty();
        fixtureCommitted=known.orElseThrow();same.requireCommitted(fixturePrepared,fixtureCommitted);
        var ref=core.archive().preserveArtifact(same,WriterTransactionCodec.encodeReceipt(fixtureCommitted),WriterTransactionCodec.MAXIMUM_BYTES);
        core.adoptInitial(bootstrap.current(fixtureBusiness.originalStart().command().actionId()),fixturePrepared,fixtureCommitted);
        var actual=new FixtureBusinessObservation(fixtureBusiness,fixturePreparedRef,ref);authority.verifyFixtureEntry(same,actual);
        fixtureObservation=actual;return java.util.Optional.of(actual);
    }
    private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> result)throws IOException {
        if(result instanceof PlanningReadResult.Known<T> actual)return actual;
        throw new IOException("actual independent native frontend read unavailable; no Start submitted");
    }
}


