package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.CompositeActionPort;
import org.xar.ck3.control.application.action.CompositeExecution;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.sway.OrdinarySwayPolicy;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** New software registration and policy inputs; no Root session, issue, submit, native read or dispatch. */
public final class OrdinarySwayCandidate235Test {
    private static final String STEP=OrdinarySwayService.STEP;
    private static final OperationKey OP=new OperationKey(STEP);
    private static final ExactRef PIN=new ExactRef("fixture:software235-metadata",1,"5".repeat(64));
    private static final BigInteger REV=BigInteger.valueOf(23),DATE=BigInteger.valueOf(72000);
    private static final AtomicInteger forbidden=new AtomicInteger();
    private static int scenes,checks;
    private OrdinarySwayCandidate235Test() { }
    public static void main(String[] args) {
        run("registeredCandidateReachesActualPolicy",OrdinarySwayCandidate235Test::registeredCandidateReachesActualPolicy);
        run("frameShortCircuit",OrdinarySwayCandidate235Test::frameShortCircuit);
        run("missingArchiveAndUninstalled",OrdinarySwayCandidate235Test::missingArchiveAndUninstalled);
        run("otherOperationAndOrigin",OrdinarySwayCandidate235Test::otherOperationAndOrigin);
        run("metadataFamilyDoesNotIssue",OrdinarySwayCandidate235Test::metadataFamilyDoesNotIssue);
        run("contradictoryRegistrationPropagates",OrdinarySwayCandidate235Test::contradictoryRegistrationPropagates);
        run("nativeAdvertisementIsIndependent",OrdinarySwayCandidate235Test::nativeAdvertisementIsIndependent);
        run("readersDisabledStillKeep",OrdinarySwayCandidate235Test::readersDisabledStillKeep);
        run("nonLifeStepSkipsCollection",OrdinarySwayCandidate235Test::nonLifeStepSkipsCollection);
        equal(forbidden.get(),0);
        System.out.println("PASS scenes="+scenes+" checks="+checks+" softwareOnly=true actualPolicy=true privateRootAuthority=false naturalSway=false Native=false Game=false");
    }
    private static void registeredCandidateReachesActualPolicy() {
        var catalog=catalog(STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,true);
        check(catalog.installed().isEmpty()); // Static composite is absent from the old generic ACTION inventory.
        var old=nativeSteps(Set.of());check(!old.contains(STEP));
        var before=planning(old);var policy=policy(new OrdinarySwayService.Capabilities(true,true,true),new AtomicInteger());
        var retained=policy.evaluate(before,previous(before,"life-advance"));
        check(retained instanceof OrdinaryPolicy.Keep);
        equal(((OrdinaryPolicy.Keep)retained).reason(),"ordinary Sway composite is not registered for this observed frame");
        DynamicCapabilities.addOrdinarySwayCandidate(old,semantic(true,true),catalog);
        equal(old,Set.of(STEP));
        var request=planning(old);var result=policy.evaluate(request,previous(request,"life-advance"));
        check(result instanceof OrdinaryPolicy.Replace);
        var command=((OrdinaryPolicy.Replace)result).draft().command().orElseThrow();
        equal(command.operation(),OP);equal(command.before(),request.before());
        var staged=OrdinarySwayPolicy.restoreStaged(command);
        equal(staged.decision().targetCharacterId(),Optional.of(12L));check(!staged.decision().submitAllowed());
    }
    private static void frameShortCircuit() {
        var catalog=catalog(STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,true);
        for(var flags:List.of(semantic(false,true),semantic(true,false),semantic(false,false))) {
            var actual=new TreeSet<String>();DynamicCapabilities.addOrdinarySwayCandidate(actual,flags,catalog);check(actual.isEmpty());
        }
    }
    private static void missingArchiveAndUninstalled() {
        for(var catalog:List.of(catalog(STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,false),
                RootExecutableBindings.freeze(List.of(),reads(),List.of(),16))) {
            var actual=new TreeSet<String>();DynamicCapabilities.addOrdinarySwayCandidate(actual,semantic(true,true),catalog);check(actual.isEmpty());
        }
    }
    private static void otherOperationAndOrigin() {
        for(var catalog:List.of(catalog("fixture-unrelated235",ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,true),
                catalog(STEP,ReadContract.GuardMode.FRONTEND_SESSION,true))) {
            var actual=new TreeSet<String>(Set.of("existing235"));DynamicCapabilities.addOrdinarySwayCandidate(actual,semantic(true,true),catalog);equal(actual,Set.of("existing235"));
        }
    }
    private static void metadataFamilyDoesNotIssue() {
        var binding=binding(STEP,"family235",ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        AtomicInteger issued=new AtomicInteger();
        var family=new RootExecutableBindings.CompositeFamily<String>("fixture-family235",String.class,binding,PIN,
                ignored->new RawJson(new byte[]{123,125}),ignored->OP,ignored->{issued.incrementAndGet();throw new AssertionError("issue forbidden");},
                operation->operation.equals(OP)?Optional.of(STEP):Optional.empty());
        var catalog=RootExecutableBindings.freeze(List.of(),reads(),List.of(binding),List.of(),List.of(),List.of(family),16);
        var actual=new TreeSet<String>();DynamicCapabilities.addOrdinarySwayCandidate(actual,semantic(true,true),catalog);
        equal(actual,Set.of(STEP));equal(issued.get(),0);check(catalog.archivedBindings().isEmpty());
    }
    private static void contradictoryRegistrationPropagates() {
        var catalog=RootExecutableBindings.freeze(List.of(),reads(),List.of(
                binding(STEP,"conflict-a235",ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP),
                binding(STEP,"conflict-b235",ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)),16);
        reject(()->DynamicCapabilities.addOrdinarySwayCandidate(new TreeSet<>(),semantic(true,true),catalog));
    }
    private static void nativeAdvertisementIsIndependent() {
        var advertised=nativeSteps(Set.of("game.command."+STEP));check(advertised.contains(STEP));
        DynamicCapabilities.addOrdinarySwayCandidate(advertised,semantic(true,true),catalog(STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,true));
        equal(advertised,Set.of(STEP));
    }
    private static void readersDisabledStillKeep() {
        var steps=new TreeSet<String>();DynamicCapabilities.addOrdinarySwayCandidate(steps,semantic(true,true),catalog(STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,true));
        var request=planning(steps);AtomicInteger loads=new AtomicInteger();
        var result=policy(new OrdinarySwayService.Capabilities(false,false,false),loads).evaluate(request,previous(request,"life-advance"));
        check(result instanceof OrdinaryPolicy.Keep);equal(loads.get(),0);
        equal(((OrdinaryPolicy.Keep)result).reason(),"ordinary Sway readers_disabled");
    }
    private static void nonLifeStepSkipsCollection() {
        var request=planning(Set.of(STEP));AtomicInteger collections=new AtomicInteger();
        var policy=new OrdinarySwayPolicy(PIN,ignored->{collections.incrementAndGet();throw new AssertionError("collection forbidden");},OrdinarySwayCandidate235Test::expected);
        check(policy.evaluate(request,previous(request,"pause-map")) instanceof OrdinaryPolicy.Keep);equal(collections.get(),0);
    }
    private static RootReadContractCatalog reads(){return new RootReadContractCatalog(List.of(),List.of());}
    private static RootExecutableBindings catalog(String op,ReadContract.GuardMode guard,boolean archived) {
        return RootExecutableBindings.freeze(List.of(),reads(),List.of(binding(op,"handler-"+op,guard)),
                archived?List.of(new NativeRecordedEvidenceVerifier.Binding(new OperationKey(op),PIN,(head,receipt,archive)->{forbidden.incrementAndGet();throw new AssertionError("verifier forbidden");})):List.of(),List.of(),16);
    }
    private static RootExecutableBindings.CompositeBinding binding(String op,String id,ReadContract.GuardMode guard) {
        var handler=new CompositeActionPort(){
            @Override public String handlerId(){return id;}
            @Override public boolean supports(OperationKey operation){return operation.value().equals(op);}
            @Override public void validate(ActionCommand parent){forbidden.incrementAndGet();throw new AssertionError("validate forbidden");}
            @Override public ActionPorts.PostconditionResult run(ActionCommand parent,Children children){forbidden.incrementAndGet();throw new AssertionError("run forbidden");}
            @Override public ActionPorts.PostconditionResult observe(ActionCommand parent,CompositeExecution retained){forbidden.incrementAndGet();throw new AssertionError("observe forbidden");}
        };
        return new RootExecutableBindings.CompositeBinding(handler,guard,Optional.empty(),PIN,PIN);
    }
    private static OpportunityJson.Obj semantic(boolean paused,boolean ready){return new OpportunityJson.Obj(Map.of("paused",new OpportunityJson.Bool(paused),"map_ready",new OpportunityJson.Bool(ready),"active_event",OpportunityJson.Nil.INSTANCE,"pending_character_interaction",OpportunityJson.Nil.INSTANCE,"active_wars",new OpportunityJson.Arr(List.of()),"player_armies",new OpportunityJson.Arr(List.of())));}
    private static TreeSet<String> nativeSteps(Set<String> caps){return new TreeSet<>(NativeActionSteps.candidates(new NativeActionSteps.Input(caps,semantic(true,true),List.of(),Set.of())));}
    private static G2Source source(){return new G2Source("xenoamess-full-tower-eb9d2c1186","2026-11-03T03:00:00Z","1.20.0.4",PIN);}
    private static PlanningRequest planning(Set<String> steps) {
        var identity=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(11),REV,DATE);
        var proposal=new ProposalFrame(identity,"fixture:native235",BigInteger.valueOf(29),"fixture:episode235");
        var before=new ObservationIdentity(source().machineId(),new GameGeneration(73,new PythonOnlyUInt64(new BigInteger("134370000000000001"))),proposal,1);
        var values=new java.util.LinkedHashMap<String,OpportunityJson.Value>(semantic(true,true).members());
        values.put("snapshot_id",new OpportunityJson.Text(proposal.snapshotId()));values.put("episode_run_id",new OpportunityJson.Text(proposal.episodeRunId()));
        values.put("revision",new OpportunityJson.IntegerValue(proposal.revision()));values.put("native_revision",new OpportunityJson.IntegerValue(REV));values.put("date_raw",new OpportunityJson.IntegerValue(DATE));
        values.put("played_character",new OpportunityJson.Obj(Map.of("character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(11)),"alive",new OpportunityJson.Bool(true))));
        var observation=new PlanningObservation(new OpportunityJson.Obj(values),List.of(),steps.stream().map(OperationKey::new).collect(java.util.stream.Collectors.toSet()),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(before,source(),"fixture:session235",Instant.parse("2030-01-01T00:00:00Z"),observation);
    }
    private static OrdinarySwayPolicy policy(OrdinarySwayService.Capabilities caps,AtomicInteger loads) {
        return new OrdinarySwayPolicy(PIN,request->new OrdinarySwayPolicy.CapturedView(request.before(),Optional.of(new Root(true,11,true,REV,DATE,Optional.of(List.of(12L,13L)))),caps,
                ()->{loads.incrementAndGet();return Optional.of(new OrdinarySwayService.Inputs(Ledger.empty(),Optional.empty()));}),OrdinarySwayCandidate235Test::expected);
    }
    private static ExpectedPostcondition expected(PlanningRequest request,OrdinarySwayService.Staged ignored){return new ExpectedPostcondition(1,request.before(),request.source(),"fixture:observer235",List.of(new ExpectedBoolean(new FieldKey("software235.observed"),true)));}
    private static OrdinaryPolicy.Draft previous(PlanningRequest request,String step) {
        var command=new ActionCommand("fixture:previous235",request.before(),request.source(),request.sessionId(),new OperationKey(step),new OpportunityJson.Obj(Map.of()),expected(request,null),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
        return new OrdinaryPolicy.Draft("fixture:policy235",step,"software235",OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),new OpportunityJson.Obj(Map.of()));
    }
    private static void run(String name,Runnable body){body.run();scenes++;System.out.println("PASS "+name);}
    private static void equal(Object actual,Object expected){checks++;if(!java.util.Objects.equals(actual,expected))throw new AssertionError("check "+checks+" actual="+actual+" expected="+expected);}
    private static void check(boolean value){checks++;if(!value)throw new AssertionError("check "+checks);}
    private static void reject(Runnable body){checks++;try{body.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("expected contradiction rejection");}
}
