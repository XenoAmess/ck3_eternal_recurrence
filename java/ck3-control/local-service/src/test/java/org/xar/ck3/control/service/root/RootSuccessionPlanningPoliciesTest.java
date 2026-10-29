package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.application.planning.prisoners.PrisonerOrdinaryPolicy12004;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Controlled original READ edge -> actual strict M3 producer -> complete typed planner -> wire.
 * These tests do not instantiate/qualify a live Root or manufacture a persisted expectation. */
final class RootSuccessionPlanningPoliciesTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef SOURCE=new ExactRef("software-succession-source",1,"a".repeat(64));
    private static final ExactRef READ=new ExactRef("controlled-original-root-read",1,"b".repeat(64));
    private static final OperationKey RELEASE=PrisonerOrdinaryPolicy12004.RELEASE;
    private static final OperationKey OTHER=new OperationKey("save-checkpoint");

    @Test void originalNativeEstateRunsThroughBothInstalledStagesAndCompletePlannerWire() {
        var calls=new AtomicInteger();var request=request(11,111);
        var installed=policies(false,calls);
        var planner=planner(installed,OTHER);
        assertTrue(planner.missingStages().isEmpty());
        var result=assertInstanceOf(PlanningResult.ActionSelected.class,planner.plan(request));
        assertEquals(command(request,OTHER),result.command());assertEquals(1,calls.get());
        var stages=result.trace().visits().stream().map(PlanTrace.StageVisit::stage).toList();
        assertEquals(33,stages.size());
        assertEquals(PlanningStage.SUCCESSION_PREFLIGHT,stages.getFirst());
        assertTrue(stages.indexOf(PlanningStage.DEFERRED_SUCCESSION_ROOT)>stages.indexOf(PlanningStage.FEAST));
        var observed=assertInstanceOf(Obj.class,result.trace().finalPlan().orElseThrow().detail().get("succession_preflight_observation"));
        assertEquals(new Bool(false),observed.get("persisted_expectation"));
        assertEquals(new Bool(false),observed.get("natural_succession_authority"));
        assertEquals(new Bool(false),observed.get("business_submission"));
        assertEquals(OpportunityJson.parse(StrictJson.canonical(READ.toJson())),observed.get("original_read"));
        assertEquals(request,PlanningWire.decodeRequest(PlanningWire.encodeRequest(request)));
        assertEquals(result,PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
        var second=request(11,112);
        assertInstanceOf(PlanningResult.ActionSelected.class,planner.plan(second));
        assertEquals(1,calls.get(),"the controlled revalidated read edge returns its original data without a second native query");
    }

    @Test void actualAcceptedReleaseRetainsPriorityEvenWhenAnIntermediateProducerReplacesAllDetails() {
        var calls=new AtomicInteger();var request=request(11,111);
        var result=assertInstanceOf(PlanningResult.ActionSelected.class,planner(policies(true,calls),RELEASE).plan(request));
        assertEquals(RELEASE,result.command().operation());assertEquals(0,calls.get());
        var detail=result.trace().finalPlan().orElseThrow().detail();
        assertNull(detail.get("succession_deferred_root_required"),"the actual core fixture replaces all old detail");
        assertEquals(new Bool(true),detail.get("prisoner_release_initial_expectation_root_deferred"));
        assertEquals(result,PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
    }

    @Test void anotherWinnerAfterReleaseDeferralReadsOriginalRootThenRequiresACompleteFreshPlan() {
        var calls=new AtomicInteger();var request=request(11,111);var installed=policies(true,calls);
        var planner=planner(installed,OTHER);
        var result=assertInstanceOf(PlanningResult.RefreshRequired.class,planner.plan(request));
        assertEquals(1,calls.get());
        assertEquals(PlanningStage.DEFERRED_SUCCESSION_ROOT,result.trace().visits().getLast().stage());
        assertEquals(result,PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
        var fresh=request(11,112);
        var next=assertInstanceOf(PlanningResult.ActionSelected.class,planner.plan(fresh));
        assertEquals(command(fresh,OTHER),next.command());assertEquals(1,calls.get());
        assertEquals(33,next.trace().visits().size(),"refresh must reenter the complete ordinary scheduler");
    }

    @Test void acceptedUnavailableRemainsReadOnlyAndDoesNotTurnIntoAnExpectationOrAction() {
        var installed=new RootSuccessionPlanningPolicies(SOURCE,RootSuccessionPlanningPoliciesTest::scope,ignored->false,
                ignored->new RootSuccessionPlanningPolicies.Unavailable("accepted source explicitly lacks the current root"));
        var result=assertInstanceOf(PlanningResult.ReadOnlyWait.class,planner(installed,OTHER).plan(request(11,111)));
        assertEquals(1,result.trace().visits().size());
        assertTrue(result.trace().finalPlan().orElseThrow().command().isEmpty());
        assertNull(result.trace().finalPlan().orElseThrow().detail().get("succession_expectation"));
        assertEquals(result,PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
    }

    @Test void completeSemanticHistoryAboveOneMiBReachesTheSoleEstateProducerAndFullPlannerWire() {
        var original=request(11,111);
        String completeHistory="retained-history:"+"x".repeat(1_048_576);
        var request=withSnapshot(original,original.observations().snapshot().with("retained_history",
                new Obj(Map.of("original_payload",new Text(completeHistory)))));
        byte[] fullSemantic=DriverJson.encode(request.observations().snapshot());
        assertTrue(fullSemantic.length>1_048_576);
        var estate=SuccessionNativeEstate12004.freeze(StrictJson.canonical(root(11)),fullSemantic);
        assertArrayEquals(fullSemantic,estate.originalSemantic());
        var calls=new AtomicInteger();
        var result=assertInstanceOf(PlanningResult.ActionSelected.class,planner(policies(false,calls),OTHER).plan(request));
        assertEquals(1,calls.get());assertEquals(command(request,OTHER),result.command());
        var observed=assertInstanceOf(Obj.class,result.trace().finalPlan().orElseThrow().detail().get("succession_preflight_observation"));
        assertEquals(OpportunityJson.parse(estate.wire()),observed.get("estate"));
        var decoded=PlanningWire.decodeRequest(PlanningWire.encodeRequest(request));
        assertEquals(request,decoded);
        assertEquals(completeHistory,text(object(decoded.observations().snapshot().get("retained_history"),"retained_history").get("original_payload"),"original_payload"));
        assertEquals(result,PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
    }

    @Test void aNewRootReadMustRefreshAndCannotSelectAnActionBeforeItsActualPublicationGate() {
        var published=new AtomicBoolean();var calls=new AtomicInteger();
        RootSuccessionPlanningPolicies.RootReader read=new RootSuccessionPlanningPolicies.RootReader(){
            public RootSuccessionPlanningPolicies.RootRead read(PlanningRequest request){
                if(calls.getAndIncrement()==0)return new RootSuccessionPlanningPolicies.AwaitingPublication("actual known root awaits READ-first publication");
                return new RootSuccessionPlanningPolicies.Unavailable("publication is still pending; no repeated native query");
            }
            public Optional<RootSuccessionPlanningPolicies.Observed> retained(PlanningRequest request){
                return published.get()?Optional.of(observed(request)):Optional.empty();
            }
        };
        var installed=new RootSuccessionPlanningPolicies(SOURCE,RootSuccessionPlanningPoliciesTest::scope,ignored->false,read);
        var planner=planner(installed,OTHER);var original=request(11,111);
        assertInstanceOf(PlanningResult.RefreshRequired.class,planner.plan(original));
        assertInstanceOf(PlanningResult.ReadOnlyWait.class,planner.plan(original));
        published.set(true); // Explicit controlled publication boundary, not a manufactured private writer proof.
        assertInstanceOf(PlanningResult.ActionSelected.class,planner.plan(request(11,112)));
        assertEquals(2,calls.get(),"the current-read edge must be consulted again until publication succeeds");
    }

    @Test void changedNativeIdentityNeedsANewOriginalButForeignSubjectAndScopeCannotReuseOne() {
        var calls=new AtomicInteger();var installed=policies(false,calls);var planner=planner(installed,OTHER);
        assertInstanceOf(PlanningResult.ActionSelected.class,planner.plan(request(11,111)));
        assertInstanceOf(PlanningResult.ActionSelected.class,planner.plan(request(12,112)));
        assertEquals(2,calls.get());
        var old=observed(request(11,111));
        var wrong=new RootSuccessionPlanningPolicies(SOURCE,RootSuccessionPlanningPoliciesTest::scope,ignored->false,ignored->old);
        assertInstanceOf(PlanningResult.ReadOnlyWait.class,planner(wrong,OTHER).plan(request(12,112)));
        var unavailable=new RootSuccessionPlanningPolicies(SOURCE,ignored->{throw new IOException("actual Root scope unavailable");},ignored->true,
                ignored->{throw new AssertionError("foreign source must not reach native read");});
        assertInstanceOf(PlanningResult.ReadOnlyWait.class,planner(unavailable,OTHER).plan(request(11,111)));
    }

    @Test void draftAnnotationCannotForgeThePrivateDeferralOfThisExactPlanningInvocation() {
        var calls=new AtomicInteger();var installed=policies(true,calls);var request=request(11,111);
        var forged=new Draft("fixture","fixture","fixture",Kind.ORDINARY,Optional.of(command(request,OTHER)),Purpose.WORLD_ACTION,
                Optional.empty(),empty().with("succession_deferred_root_required",new Bool(true)));
        assertInstanceOf(NotApplicable.class,installed.policies().get(1).evaluate(request,forged));
        assertInstanceOf(Annotate.class,installed.policies().getFirst().evaluate(request,Draft.empty()));
        assertInstanceOf(NotApplicable.class,installed.policies().get(1).evaluate(request(11,111),forged));
        assertEquals(0,calls.get());
    }

    @Test void changedPlayerStopsForTheOriginalLifecycleAndForegroundWorkSkipsPreflightReads() {
        var calls=new AtomicInteger();var installed=policies(false,calls);var request=request(11,111);
        var changed=withSnapshot(request,request.observations().snapshot().with("one_life_terminal_reason",new Text("played_character_changed")));
        var stopped=assertInstanceOf(PlanningResult.Stopped.class,planner(installed,OTHER).plan(changed));
        assertEquals(PlanningResult.StopReason.NATURAL_SUCCESSION_REQUIRED,stopped.reason());
        var foreground=withSnapshot(request,request.observations().snapshot().with("active_event",new Obj(Map.of("event_id",new Text("actual-foreground")))));
        assertInstanceOf(NotApplicable.class,installed.policies().getFirst().evaluate(foreground,Draft.empty()));
        var dead=withSnapshot(request,request.observations().snapshot().with("played_character",new Obj(Map.of("character_id",new IntegerValue(BigInteger.TWO),"alive",new Bool(false)))));
        assertInstanceOf(NotApplicable.class,installed.policies().getFirst().evaluate(dead,Draft.empty()));
        assertEquals(0,calls.get());
    }

    @Test void unavailableLifecycleProfileRetainsItsDiagnosticAndAllowsOtherOrdinaryPolicies() {
        var calls=new AtomicInteger();var installed=policies(false,calls);var request=request(11,111);
        Obj rogue=DriverJson.object(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue()),SuccessionLifecycleCodec.MAX_BYTES);
        assertInstanceOf(NotApplicable.class,installed.policies().getFirst().evaluate(
                withSnapshot(request,request.observations().snapshot().with("succession_lifecycle",rogue)),Draft.empty()));
        Obj unknown=DriverJson.object(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.unknown()),SuccessionLifecycleCodec.MAX_BYTES);
        Obj inconsistent=object(request.observations().snapshot().get("succession_lifecycle"),"actual lifecycle")
                .with("pact_contract",new Text("unsupported_actual_contract"));
        for(Value profile:List.of(unknown,inconsistent,empty().with("lifecycle",new Text("ordinary_campaign_succession")),Nil.INSTANCE)) {
            var current=withSnapshot(request,request.observations().snapshot().with("succession_lifecycle",profile));
            var deferred=assertInstanceOf(Defer.class,installed.policies().getFirst().evaluate(current,Draft.empty()));
            assertEquals(profile,deferred.evidence().get("succession_lifecycle"));
            assertEquals(new Bool(false),deferred.evidence().get("natural_succession_authority"));
            assertEquals(new Bool(false),deferred.evidence().get("business_submission"));
            var selected=assertInstanceOf(PlanningResult.ActionSelected.class,planner(installed,OTHER).plan(current));
            assertEquals(OTHER,selected.command().operation());
            var visit=selected.trace().visits().getFirst();assertEquals(PlanTrace.Outcome.DEFERRED_INPUT,visit.outcome());
            assertEquals(deferred.evidence(),visit.evidence().orElseThrow());
            assertEquals(selected,PlanningWire.decodeResult(PlanningWire.encodeResult(selected)));
            var changed=withSnapshot(current,current.observations().snapshot().with("one_life_terminal_reason",new Text("played_character_changed")));
            assertEquals(PlanningResult.StopReason.NATURAL_SUCCESSION_REQUIRED,
                    assertInstanceOf(PlanningResult.Stopped.class,planner(installed,OTHER).plan(changed)).reason());
            var dead=withSnapshot(current,current.observations().snapshot().with("played_character",
                    new Obj(Map.of("character_id",new IntegerValue(BigInteger.TWO),"alive",new Bool(false)))));
            assertInstanceOf(NotApplicable.class,installed.policies().getFirst().evaluate(dead,Draft.empty()));
        }
        assertEquals(0,calls.get(),"unsupported succession input grants no ROOT read or succession authority");
    }

    @Test void actualVanillaProfileContinuesWholePlannerWithoutAnySuccessionRootPreRead() {
        var request=request(11,111);
        Obj vanilla=DriverJson.object(StrictJson.canonical(
                org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla().toJson()),SuccessionLifecycleCodec.MAX_BYTES);
        var current=withSnapshot(request,request.observations().snapshot().with("succession_lifecycle",vanilla));
        var roots=new RootSuccessionPlanningPolicies.RootReader(){
            public RootSuccessionPlanningPolicies.RootRead read(PlanningRequest ignored){throw new AssertionError("vanilla ordinary planning cannot require a future succession ROOT read");}
            public Optional<RootSuccessionPlanningPolicies.Observed> retained(PlanningRequest ignored){throw new AssertionError("vanilla ordinary planning cannot require a retained succession ROOT");}
        };
        var installed=new RootSuccessionPlanningPolicies(SOURCE,RootSuccessionPlanningPoliciesTest::scope,
                ignored->{throw new AssertionError("vanilla succession preflight cannot require release arbitration");},roots);
        var selected=assertInstanceOf(PlanningResult.ActionSelected.class,planner(installed,OTHER).plan(current));
        assertEquals(OTHER,selected.command().operation());
        assertEquals(PlanTrace.Outcome.NOT_APPLICABLE,selected.trace().visits().getFirst().outcome());
        assertEquals(selected,PlanningWire.decodeResult(PlanningWire.encodeResult(selected)));
        var changed=withSnapshot(current,current.observations().snapshot().with("one_life_terminal_reason",new Text("played_character_changed")));
        assertEquals(PlanningResult.StopReason.NATURAL_SUCCESSION_REQUIRED,
                assertInstanceOf(PlanningResult.Stopped.class,planner(installed,OTHER).plan(changed)).reason());
    }

    private static RootSuccessionPlanningPolicies policies(boolean release,AtomicInteger calls) {
        RootSuccessionPlanningPolicies.RootReader controlled=new RootSuccessionPlanningPolicies.RootReader(){
            private RootSuccessionPlanningPolicies.Observed data;
            public RootSuccessionPlanningPolicies.RootRead read(PlanningRequest request){calls.incrementAndGet();data=observed(request);return data;}
            public Optional<RootSuccessionPlanningPolicies.Observed> retained(PlanningRequest request){
                // The current-read edge is explicitly controlled in this scheduler test. ActualRoots
                // must instead consume the sole publisher's private canonical ROOT witness and original decoder.
                return data!=null&&data.sameNative(request)?Optional.of(observed(request)):Optional.empty();
            }
        };
        return new RootSuccessionPlanningPolicies(SOURCE,RootSuccessionPlanningPoliciesTest::scope,ignored->release,controlled);
    }
    private static void scope(PlanningRequest request) {
        StrictJson.require(request.source().sourceRef().equals(SOURCE)&&request.sessionId().equals("controlled-session"),"controlled source scope differs");
    }
    private static RootSuccessionPlanningPolicies.Observed observed(PlanningRequest request) {
        byte[] raw=StrictJson.canonical(root(request.before().frame().identity().nativeRevision().intValueExact()));
        var estate=SuccessionNativeEstate12004.freeze(raw,DriverJson.encode(request.observations().snapshot()));
        return new RootSuccessionPlanningPolicies.Observed(request,READ,estate);
    }
    private static PlanningRequest request(int nativeRevision,int revision) {
        var snapshot=DriverJson.object(StrictJson.canonical(semantic(nativeRevision,revision)),DriverJson.MAX_NATIVE_BYTES);
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before=new ObservationIdentity("controlled-succession-machine",game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(2),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(100)),
                        "actual-"+nativeRevision,BigInteger.valueOf(revision),"old-episode"),1);
        return new PlanningRequest(before,new G2Source(before.machineId(),NOW.toString(),"controlled-build",SOURCE),"controlled-session",NOW.plusSeconds(60),
                new PlanningObservation(snapshot,List.of(),Set.of(RELEASE,OTHER),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static PlanningRequest withSnapshot(PlanningRequest request,Obj snapshot) {
        var o=request.observations();return new PlanningRequest(request.before(),request.source(),request.sessionId(),request.deadline(),
                new PlanningObservation(snapshot,o.history(),o.actionSteps(),o.bridgeCapabilities(),o.battleSpeedReadiness(),o.actionFacts(),o.campaignGoal(),o.crossRunPlan(),o.initialLifestyleFocusRequired()));
    }
    private static ActionCommand command(PlanningRequest request,OperationKey operation) {
        return new ActionCommand("controlled-succession-action",request.before(),request.source(),request.sessionId(),operation,empty(),
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),"controlled-observer/v1",
                        List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("native.gameplay_verified"),true))),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
    }
    private static OrdinaryPlanner planner(RootSuccessionPlanningPolicies installed,OperationKey winner) {
        var policies=new EnumMap<PlanningStage,OrdinaryPolicy>(PlanningStage.class);
        for(var stage:PlanningStage.values())policies.put(stage,absentSibling(stage));
        for(var policy:installed.policies())policies.put(policy.stage(),policy);
        var core=OrdinaryCorePolicy.assemble(SOURCE,continuation->{
            var leaves=new ArrayList<WarCorePlanner.Leaf>();
            for(var boundary:WarCorePlanner.Boundary.values())leaves.add(new WarCorePlanner.Leaf(boundary,SOURCE,(r,p)->new MilitaryPlanningDecision.Keep(empty())));
            PlanningReadPort reads=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("no military read in this source fixture");}};
            return new WarCorePlanner(leaves,r->new WarCorePlanner.KnownTactics(r.before(),new WarCorePlanner.RouteTactics(Set.of(),Set.of())),
                    (r,p)->{throw new AssertionError("no military world command");},reads,(r,p)->{throw new AssertionError("no military dynamic read");},continuation);
        },(request,previous)->new Replace(new Draft("controlled-registry","controlled-choice","controlled original command",Kind.ORDINARY,
                Optional.of(command(request,winner)),Purpose.WORLD_ACTION,Optional.empty(),
                // Deliberately replaces old detail. The two production policies must still arbitrate correctly.
                previous.detail().get("succession_preflight_observation") instanceof Obj data?empty().with("succession_preflight_observation",data):empty()),"controlled current registry selection"),
                (r,p)->new NotApplicable("controlled sibling has no council input"),(r,p)->new NotApplicable("controlled sibling has no marriage input"),
                (r,p)->new NotApplicable("controlled sibling has no war-entry input"),(r,o,a,p,u,d)->{throw new AssertionError("registry selected exact original command");},ignored->false).core();
        var realm=new RealmLifecycle(SOURCE);
        return pipeline(policies,core,realm).create(Clock.fixed(NOW,ZoneOffset.UTC));
    }
    /** Explicit test-only sibling edges; production Root installs actual domain producers. */
    private static OrdinaryPolicy absentSibling(PlanningStage stage) {
        return new OrdinaryPolicy(){public PlanningStage stage(){return stage;}public ExactRef implementationSource(){return SOURCE;}
            public Decision evaluate(PlanningRequest r,Draft p){return new NotApplicable("controlled sibling input absent");}};
    }
    private static OrdinaryPlanningPipeline pipeline(Map<PlanningStage,OrdinaryPolicy> p,OrdinaryCorePolicy core,RealmLifecycle realm) {
        return new OrdinaryPlanningPipeline(p.get(PlanningStage.SUCCESSION_PREFLIGHT),p.get(PlanningStage.PENDING_MATERIAL_PUBLICATION),p.get(PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS),
                p.get(PlanningStage.OPENING_LIFESTYLE_FOCUS),core,p.get(PlanningStage.THREE_WAY_WAR_EXIT),p.get(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION),
                p.get(PlanningStage.WAR_RENDEZVOUS),p.get(PlanningStage.SIEGE_AND_BATTLE_FORECAST),p.get(PlanningStage.ROUTE_ORIGIN_EXPOSURE),p.get(PlanningStage.ACTIVE_COMBAT_AND_DATE_GUARDS),
                p.get(PlanningStage.ORDINARY_RETREAT),p.get(PlanningStage.WAR_MERCENARY_CURRENT_CASH),p.get(PlanningStage.PRISONER_RELEASE_DISCOVERY),p.get(PlanningStage.HOLY_ORDER_REINFORCEMENT),
                p.get(PlanningStage.COMMANDER_QUALITY),p.get(PlanningStage.M5_JOINT_PEACETIME),p.get(PlanningStage.LIFESTYLE),p.get(PlanningStage.FACTION_GIFT),p.get(PlanningStage.CONSTRUCTION),
                p.get(PlanningStage.FAMILY_AND_EDUCATION),p.get(PlanningStage.PRISONER_RANSOM),p.get(PlanningStage.PRISONER_RELEASE),p.get(PlanningStage.M5_WARTIME_OBSERVATION),p.get(PlanningStage.COUNCIL),
                p.get(PlanningStage.CROWN_AUTHORITY),p.get(PlanningStage.FEAST),p.get(PlanningStage.DEFERRED_SUCCESSION_ROOT),p.get(PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION),p.get(PlanningStage.PREWAR_FORCE_COALITION),
                p.get(PlanningStage.ORDINARY_SWAY),p.get(PlanningStage.EVENT_MATERIAL_POSTCONDITION),p.get(PlanningStage.CAMPAIGN_ADVANCE_CAP),realm);
    }
    private static Obj empty(){return new Obj(Map.of());}
    private static ObjectNode root(int revision) {
        ObjectNode result=StrictJson.object().put("step","query-campaign-root-context-v1").put("accepted",true).put("status","available").put("query_sequence",revision).put("snapshot_revision",revision).put("backend_id","native-headless");
        ObjectNode root=result.putObject("campaign_root_context").put("schema_version",1).put("status","available").put("snapshot_revision",revision).put("date_raw",100).put("player_character_id",2).put("player_character_alive",true).putNull("unavailable_reason");
        root.set("primary_title",title(10));root.putArray("primary_title_succession_character_ids").add(3);
        root.putObject("provenance").put("game_version","1.20.0.4").put("executable_sha256",SuccessionNativeEstate12004.EXECUTABLE_SHA256).put("backend_id","ck3-1.20.0.4-native-campaign-root-context-v1").put("held_title_ids_offset","0x1E0").put("primary_title_rva","0x289DA10");
        var readiness=root.putObject("readiness");for(var key:List.of("player_identity_ready","primary_title_ready","primary_title_succession_ready","held_title_partition_ready","same_frame_ready"))readiness.put(key,true);
        var row=StrictJson.object().put("first_heir_character_id",3).put("primary",true).put("capital_province_id",11);row.set("title",title(10));root.putArray("held_title_partition").add(row);return result;
    }
    private static ObjectNode title(int id){return StrictJson.object().put("title_id",id).put("tier_raw",2).put("tier_key","county");}
    private static ObjectNode semantic(int nativeRevision,int revision) {
        var s=StrictJson.object().put("snapshot_id","actual-"+nativeRevision).put("revision",revision).put("native_revision",nativeRevision).put("date_raw",100).put("episode_run_id","old-episode").put("episode_character_id",2)
                .put("paused",true).put("map_ready",true).put("one_life_terminal",false).putNull("one_life_terminal_reason").putNull("active_event").putNull("pending_character_interaction");
        s.putObject("played_character").put("character_id",2).put("alive",true);
        s.set("succession_lifecycle",StrictJson.parse(SuccessionLifecycleCodec.encode(new SuccessionLifecycleBinding(
                SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF,"actual-frozen-xar-off","e".repeat(64))),SuccessionLifecycleCodec.MAX_BYTES));
        s.putArray("active_wars");s.putArray("player_armies");return s;
    }
}
