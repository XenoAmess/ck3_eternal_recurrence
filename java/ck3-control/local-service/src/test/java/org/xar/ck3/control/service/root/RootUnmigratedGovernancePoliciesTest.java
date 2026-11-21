package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.math.BigInteger;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Retired actual53 packets/bodies are DATA only. All unrelated stages are explicit software fixtures,
 * not an installed34-stage Root. No Managed/Root role, Native READ, receipt, world write or domain import is fabricated. */
@EnabledIfSystemProperty(named="governance.actual.inputs",matches=".+")
final class RootUnmigratedGovernancePoliciesTest {
    @Test void actual53TrueOpeningRunsTheProductionPlannerThroughTheBasicCandidate()throws Exception {
        var f=new Fixture();var chosen=command(f.request,"life-advance");
        var result=assertInstanceOf(PlanningResult.ActionSelected.class,planner(f,chosen).plan(f.request));
        assertTrue(f.request.observations().initialLifestyleFocusRequired());assertSame(chosen,result.command());
        assertEquals(ActionCodec.bodySha256(chosen),ActionCodec.bodySha256(result.command()));
        assertEquals(PlanningStage.REALM_MEMBERSHIP_PUBLICATION,result.trace().visits().getLast().stage());
        var visit=result.trace().visits().stream().filter(v->v.stage()==PlanningStage.OPENING_LIFESTYLE_FOCUS).findFirst().orElseThrow();
        assertEquals(PlanTrace.Outcome.DEFERRED_INPUT,visit.outcome());assertNotNull(visit.evidence().orElseThrow());
        assertEquals(0,f.queries);assertTrue(f.durableReads>0);assertTrue(f.feastReads>0);
    }

    @Test void missingDurableAndEveryMissingRequiredSlotKeepTheOriginalHardStop()throws Exception {
        var f=new Fixture();var stop=new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,"original missing producer");
        var original=policy(PlanningStage.LIFESTYLE,f.source,(request,previous)->stop);var draft=draft(command(f.request,"life-advance"));
        var wrapped=select(original,f);
        var actual=f.durable;
        f.durable=null;assertSame(stop,wrapped.evaluate(f.request,draft));
        for(int n=0;n<4;n++) {
            f.durable=new Durable(actual.observed(),actual.sessionId(),n==0?Optional.empty():actual.cadence(),n==1?Optional.empty():actual.opening(),
                    n==2?Optional.empty():actual.council(),n==3?Optional.empty():actual.crown());
            assertSame(stop,wrapped.evaluate(f.request,draft));
        }
    }

    @Test void pendingUnknownAndNonSubmitOpeningDataAreNeverDiscarded()throws Exception {
        var f=new Fixture();var wait=new OrdinaryPolicy.Wait("retain the supplied original continuation");
        var original=policy(PlanningStage.LIFESTYLE,f.source,(r,p)->wait);var wrapped=select(original,f);var draft=draft(command(f.request,"life-advance"));
        var actual=f.durable;
        // Explicit counterfactual typed state, not a forged receipt or a rewritten canonical body.
        for(var status:List.of(DomainStatus.UNKNOWN,DomainStatus.PENDING)) {
            var state=new DomainState(status,Optional.empty(),status==DomainStatus.PENDING?Optional.of(empty()):Optional.empty(),actual.council().orElseThrow().originalBody());
            f.durable=new Durable(actual.observed(),actual.sessionId(),actual.cadence(),actual.opening(),Optional.of(state),actual.crown());
            assertSame(wait,wrapped.evaluate(f.request,draft));
            f.durable=new Durable(actual.observed(),actual.sessionId(),actual.cadence(),actual.opening(),actual.council(),Optional.of(state));
            assertSame(wait,wrapped.evaluate(f.request,draft));
        }
        var gate=actual.opening().orElseThrow();
        f.durable=new Durable(actual.observed(),actual.sessionId(),actual.cadence(),Optional.of(new OpeningGate(gate.episodeRunId(),gate.dateRaw(),
                OpeningStage.COMPLETE,Optional.empty(),Optional.empty())),actual.council(),actual.crown());
        assertSame(wait,wrapped.evaluate(f.request,draft));assertEquals(0,f.queries);
    }

    @Test void feastUnavailableAndLegacyPendingUseTheOriginalDecision()throws Exception {
        var f=new Fixture();var wait=new OrdinaryPolicy.Wait("Feast originals must be preserved");
        var wrapped=select(policy(PlanningStage.FEAST,f.source,(r,p)->wait),f);var draft=draft(command(f.request,"life-advance"));
        f.feastState=null;assertSame(wait,wrapped.evaluate(f.request,draft));
        f.feastState=new FeastObservationSupplier.State(f.request.before(),f.request.sessionId(),f.durable.cadence().orElseThrow(),
                Optional.of(new OpportunityJson.Obj(Map.of("software_counterfactual_legacy_pending",new OpportunityJson.Bool(true)))),
                Optional.empty(),List.of(),f.feastBody);
        assertSame(wait,wrapped.evaluate(f.request,draft));assertEquals(0,f.queries);
    }

    @Test void foreignSourceAndEarlierActionKeepTheirOriginalPolicyRoute()throws Exception {
        var f=new Fixture();var keep=new OrdinaryPolicy.Keep("original route retained");
        var wrapped=select(policy(PlanningStage.LIFESTYLE,f.source,(r,p)->keep),f);
        var chosen=command(f.request,"pause-map");var draft=draft(chosen);
        assertSame(keep,wrapped.evaluate(f.request,draft));assertSame(chosen,draft.command().orElseThrow());
        var old=f.request;var foreign=new G2Source(old.source().machineId(),old.source().observedAtUtc(),"foreign-build",old.source().sourceRef());
        var request=new PlanningRequest(old.before(),foreign,old.sessionId(),old.deadline(),old.observations());
        assertSame(keep,wrapped.evaluate(request,draft(command(request,"life-advance"))));assertEquals(0,f.queries);
    }

    @Test void installedSourcesAndOtherBuildsKeepTheActualMissingProducerStop()throws Exception {
        var f=new Fixture();var actual=new GovernancePolicies.Lifestyle(f,f.source);
        assertSame(actual,RootUnmigratedGovernancePolicies.select(actual,f,f.feast,f.config,true,false));
        assertSame(actual,RootUnmigratedGovernancePolicies.select(actual,f,f.feast,f.config,false,true));
        var legacy=new GovernanceRuntimeInstaller.Config("1.20.0.4",ExactCk3Build.CK3_12004.executableSha256(),"software-qualified",Set.of(),1,3);
        assertSame(actual,RootUnmigratedGovernancePolicies.select(actual,f,f.feast,legacy,false,false));
        assertInstanceOf(OrdinaryPolicy.Stop.class,actual.evaluate(f.request,draft(command(f.request,"life-advance"))));
        assertEquals(1,f.queries);
    }

    @Test void openingNotApplicableWaitAndStopStillFinishBeforeBasicSelection()throws Exception {
        var f=new Fixture();var chosen=command(f.request,"life-advance");
        for(var decision:List.<OrdinaryPolicy.Decision>of(new OrdinaryPolicy.NotApplicable("original optional route"),
                new OrdinaryPolicy.Wait("retain the original wait"),new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,"original producer absent"))) {
            var result=planner(f,chosen,decision).plan(f.request);
            assertFalse(result instanceof PlanningResult.ActionSelected);
            assertTrue(result.trace().visits().stream().noneMatch(v->v.stage()==PlanningStage.ORDINARY_CORE));
        }
        assertEquals(0,f.queries);
    }

    private static OrdinaryPolicy select(OrdinaryPolicy policy,Fixture f) {return RootUnmigratedGovernancePolicies.select(policy,f,f.feast,f.config,false,false);}
    private static OrdinaryPolicy.Draft draft(ActionCommand command) {
        return new OrdinaryPolicy.Draft("software-basic-candidate","ordinary","explicit software registry candidate",OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),empty());
    }
    private static OpportunityJson.Obj empty(){return new OpportunityJson.Obj(Map.of());}
    private static OrdinaryPolicy policy(PlanningStage stage,ExactRef source,java.util.function.BiFunction<PlanningRequest,OrdinaryPolicy.Draft,OrdinaryPolicy.Decision> body) {
        return new OrdinaryPolicy(){public PlanningStage stage(){return stage;}public ExactRef implementationSource(){return source;}
            public Decision evaluate(PlanningRequest request,Draft previous){return body.apply(request,previous);}};
    }
    private static ActionCommand command(PlanningRequest request,String step) {
        var operation=new OperationKey(step);
        return new ActionCommand("software-governance-"+step,request.before(),request.source(),request.sessionId(),operation,empty(),
                new ExpectedPostcondition(1,request.before(),request.source(),"software-observer/v1",List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true))),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
    }
    private static OrdinaryPlanner planner(Fixture f,ActionCommand chosen) {return planner(f,chosen,null);}
    private static OrdinaryPlanner planner(Fixture f,ActionCommand chosen,OrdinaryPolicy.Decision openingDecision) {
        var all=new EnumMap<PlanningStage,OrdinaryPolicy>(PlanningStage.class);
        for(var stage:PlanningStage.values())all.put(stage,policy(stage,f.source,(r,p)->new OrdinaryPolicy.Keep("explicit unrelated software stage")));
        var council=new GovernancePolicies.Council(f,f.source);
        var feast=new OrdinaryFeastPolicy(f.source,f.feast,(operation,request,arguments)->{throw new AssertionError("no effect preparation");});
        for(var p:GovernanceOrdinaryRuntimeInstaller.ordinaryPolicies(f,f.source,council,feast))all.put(p.stage(),select(p,f));
        if(openingDecision!=null)all.put(PlanningStage.OPENING_LIFESTYLE_FOCUS,policy(PlanningStage.OPENING_LIFESTYLE_FOCUS,f.source,(r,p)->openingDecision));
        var assembly=OrdinaryCorePolicy.assemble(f.source,continuation->{
            var leaves=new ArrayList<WarCorePlanner.Leaf>();
            for(var boundary:WarCorePlanner.Boundary.values())leaves.add(new WarCorePlanner.Leaf(boundary,f.source,(r,p)->new MilitaryPlanningDecision.Keep(empty())));
            PlanningReadPort reads=new PlanningReadPort(){public <T>PlanningReadResult<T> read(ReadContract<T> c,PlanningReadRequest r){throw new AssertionError("no Native query");}};
            return new WarCorePlanner(leaves,r->new WarCorePlanner.KnownTactics(r.before(),new WarCorePlanner.RouteTactics(Set.of(),Set.of())),
                    (r,s)->{throw new AssertionError("no world action");},reads,(r,s)->{throw new AssertionError("no query");},continuation);
        },(r,p)->new OrdinaryPolicy.Replace(draft(chosen),"software registry selected exact basic candidate"),council::evaluateCoreCouncil,
                (r,p)->new OrdinaryPolicy.Keep("software marriage stage"),(r,p)->new OrdinaryPolicy.Keep("software entry stage"),
                (r,op,args,plan,purpose,domain)->new OrdinaryCorePolicy.Prepared(command(r,op.value())),step->step.equals("life-advance"));
        all.put(PlanningStage.ORDINARY_CORE,assembly.core());var realm=new RealmLifecycle(f.source);all.put(PlanningStage.REALM_MEMBERSHIP_PUBLICATION,realm);
        return new OrdinaryPlanner(new ArrayList<>(all.values()),Clock.fixed(f.now,ZoneOffset.UTC),realm);
    }

    private static final class Fixture implements GovernanceObservationSupplier {
        final com.fasterxml.jackson.databind.JsonNode inputs;final ExactRef source;final PlanningRequest request;final Instant now;
        final GovernanceRuntimeInstaller.Config config=new GovernanceRuntimeInstaller.Config("1.21.0.3",ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256(),"software-unmigrated",Set.of(),1,3);
        Durable durable;FeastObservationSupplier.State feastState;final OpportunityJson.Obj feastBody;int queries,durableReads,feastReads;
        Fixture()throws Exception {
            inputs=StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("governance.actual.inputs"))));
            var gate=GovernanceOpeningDocument.decode(payload("OPENING_GATE"));
            source=gate.source().sourceRef();now=Instant.parse(gate.source().observedAtUtc());
            var nativePacket=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(pinned(gate.originals().getFirst())));
            assertEquals(gate.observed().frame().snapshotId(),nativePacket.snapshotId());assertEquals(gate.observed().frame().identity().nativeRevision(),nativePacket.revision());
            var snapshot=NativeWire.object(NativeWire.parse(nativePacket.state().value())).deepCopy();
            snapshot.put("snapshot_id",nativePacket.snapshotId()).put("native_revision",nativePacket.revision())
                    .put("revision",gate.observed().frame().revision()).put("episode_run_id",gate.observed().frame().episodeRunId());
            var observation=new PlanningObservation((OpportunityJson.Obj)DriverJson.fromNode(snapshot),List.of(),Set.of(new OperationKey("life-advance"),new OperationKey("pause-map")),
                    Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),true);
            request=new PlanningRequest(gate.observed(),gate.source(),gate.sessionId(),now.plusSeconds(60),observation);
            var cadence=CadenceJson.readState(payload("OPTIONAL_CADENCE"),gate.observed().frame().episodeRunId());
            var council=clear("COUNCIL",List.of("applied","pending"));var crown=clear("CROWN",List.of("pending","resolved","retry"));
            assertEquals(OpeningStage.AWAIT_SUBMIT,gate.stage());assertTrue(gate.actionReceipt().isEmpty()&&gate.checkpoint().isEmpty());
            durable=new Durable(request.before(),request.sessionId(),Optional.of(cadence),Optional.of(new OpeningGate(gate.observed().frame().episodeRunId(),
                    gate.observed().frame().identity().dateRaw(),gate.stage(),Optional.empty(),gate.checkpoint())),Optional.of(council),Optional.of(crown));
            byte[] body=payload("FEAST");var ledger=FeastDomainRuntime.decode(body);assertTrue(ledger.pending().isEmpty()&&ledger.resolved().isEmpty());
            feastBody=(OpportunityJson.Obj)DriverJson.fromNode(StrictJson.parse(body));
            feastState=new FeastObservationSupplier.State(request.before(),request.sessionId(),cadence,Optional.empty(),Optional.empty(),List.of(),feastBody);
        }
        private DomainState clear(String slot,List<String> fields)throws Exception {
            var row=StrictJson.parse(payload(slot));for(String key:fields)assertTrue(row.has(key)&&row.get(key).isNull(),"actual canonical slot must explicitly contain null "+slot+"."+key);
            return new DomainState(DomainStatus.KNOWN_CLEAR,Optional.empty(),Optional.empty(),(OpportunityJson.Obj)DriverJson.fromNode(row));
        }
        private byte[] payload(String slot)throws Exception{return pinned(ExactRef.fromJson(inputs.path("domains").path(slot).path("payload")));}
        private static byte[] pinned(ExactRef ref)throws Exception {byte[] raw=Files.readAllBytes(Path.of(ref.path()));assertEquals(ref.bytes(),raw.length);assertEquals(ref.sha256(),ActionCodec.sha256(raw));return raw;}
        public Read<Durable> durable(PlanningRequest request){durableReads++;return durable==null?new Unavailable<>("missing canonical body"):new Known<>(durable,List.of(source));}
        private <T>Read<T> missing(){queries++;return new Unavailable<>("no installed Native governance producer");}
        public Read<Life> lifestyle(PlanningRequest r,String p,boolean o){return missing();}
        public Read<OpeningComparison> openingComparison(PlanningRequest r){return missing();}
        public Read<CouncilSelection.Query> council(PlanningRequest r,CouncilSelection.Position p){return missing();}
        public Read<CouncilSelection.Query> coreCouncil(PlanningRequest r){return missing();}
        public Read<CouncilRoot> councilRoot(PlanningRequest r){return missing();}
        public Read<Crown> crown(PlanningRequest r){return missing();}
        public Read<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest r,String key){return missing();}
        public Read<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest r){return missing();}
        final FeastObservationSupplier feast=new FeastObservationSupplier(){
            public Read<State> state(PlanningRequest r){feastReads++;return feastState==null?new Unavailable<>("missing Feast canonical body"):new Known<>(feastState,List.of(source));}
            public Read<Planner> planner(PlanningRequest r){throw new AssertionError("no Native Activity query");}
            public Read<Hosted> hosted(PlanningRequest r){throw new AssertionError("no Native Activity query");}
            public Read<OpportunityJson.Obj> root(PlanningRequest r){throw new AssertionError("no Native Activity query");}
            public Read<org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.Spending> spending(PlanningRequest r){throw new AssertionError("no spending query");}
            public Read<org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.Feast> feast(PlanningRequest r,org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.Spending s){throw new AssertionError("no Feast query");}
        };
    }
}
