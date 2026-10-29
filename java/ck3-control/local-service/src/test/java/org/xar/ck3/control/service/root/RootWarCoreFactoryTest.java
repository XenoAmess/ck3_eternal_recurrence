package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.application.planning.warexit.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyNativeRecipes;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Offline concrete-producer regressions. They do not qualify a physical Game, Native submit or Source. */
final class RootWarCoreFactoryTest {
    private static final ExactRef SOURCE=new ExactRef("D:/fixture/original-war-producer.java",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final G2Source G2=new G2Source("fixture-machine",NOW.toString(),"fixture-build",SOURCE);
    private static final GameGeneration GAME=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final PlanningReadPort NO_READS=new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> original,PlanningReadRequest actual) {
            throw new AssertionError("composition fixture must not contact Native");
        }
    };
    private static RootWarCoreFactory.Sources sources() {
        return new RootWarCoreFactory.Sources(SOURCE,new EarlyWarCoreLeaves.Sources(SOURCE,SOURCE,SOURCE),
                SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE);
    }
    private static KnownPendingInteractionPolicy pending() {
        ReadContract<PendingContext> actual=new ReadContract<>("fixture-canonical-pending",new OperationKey(PendingContextCodec.STEP),
                Optional.of(PendingContextCodec.CAPABILITY),"fixture-pending",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,SOURCE,
                request->{throw new AssertionError("no native fixture preparation");},
                receipt->{throw new AssertionError("no native fixture decode");});
        return new KnownPendingInteractionPolicy(SOURCE,request->{throw new AssertionError("unneeded interaction context");},
                NO_READS,actual,operation->Optional.empty());
    }
    private static Obj object(Object... pairs) {
        var fields=new java.util.LinkedHashMap<String,Value>();
        for(int index=0;index<pairs.length;index+=2)fields.put((String)pairs[index],(Value)pairs[index+1]);
        return new Obj(fields);
    }
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Obj war(int score) {
        return object("war_id",number(7),"player_side",new Text("attacker"),"player_is_primary_war_leader",new Bool(true),
                "player_relative_war_score",number(score),"primary_opponent_character_id",number(501),
                "targeted_title_ids",new Arr(List.of(number(901))),"allied_armies",new Arr(List.of()),"enemy_armies",new Arr(List.of()));
    }
    private static PlanningRequest request(int score,Set<OperationKey> steps) {
        var before=new ObservationIdentity(G2.machineId(),GAME,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(707),BigInteger.valueOf(41),BigInteger.valueOf(24000)),
                "fixture-current",BigInteger.valueOf(7),"episode-1"),1);
        Obj snapshot=object("snapshot_id",new Text("fixture-current"),"revision",number(7),"native_revision",number(41),
                "date_raw",number(24000),"episode_run_id",new Text("episode-1"),"paused",new Bool(true),"map_ready",new Bool(true),
                "played_character",object("character_id",number(707),"alive",new Bool(true)),
                "active_wars",new Arr(List.of(war(score))),"player_armies",new Arr(List.of()),
                "diagnostics",object("connection_generation",number(1),"bridge_pid",number(123)),
                "active_event",Nil.INSTANCE,"pending_character_interaction",Nil.INSTANCE);
        return new PlanningRequest(before,G2,"fixture-session",NOW.plusSeconds(60),
                new PlanningObservation(snapshot,List.of(),steps,Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static WarExitReads unavailableReads(AtomicInteger calls) {
        return new WarExitReads((request,key,arguments)->{
            calls.incrementAndGet();
            return new PlanningReadResult.Unavailable<>("actual native fixture intentionally unavailable",Optional.empty());
        });
    }
    @Test void concreteFactoriesInstallEveryOriginalBoundaryAndUseRealScoreAndRaiseProducers() {
        var calls=new AtomicInteger();var leaves=RootWarCoreFactory.productionLeaves(sources(),pending(),unavailableReads(calls),new EarlyWarCoreInputs());
        assertEquals(17,leaves.size());
        assertEquals(EnumSet.allOf(WarCorePlanner.Boundary.class),
                leaves.stream().map(WarCorePlanner.Leaf::boundary).collect(java.util.stream.Collectors.toSet()));
        var score=request(100,Set.of(new OperationKey("enforce-demands-7")));
        var scoreLeaf=leaves.stream().filter(value->value.boundary()==WarCorePlanner.Boundary.TERMINATION_SCORE_PRELUDE).findFirst().orElseThrow();
        var picked=assertInstanceOf(MilitaryPlanningDecision.ApplicationDecision.class,scoreLeaf.producer().evaluate(score,OrdinaryPolicy.Draft.empty()));
        var action=assertInstanceOf(OrdinaryPolicy.Replace.class,picked.decision()).draft().command().orElseThrow();
        assertEquals(new OperationKey("enforce-demands-7"),action.operation());
        assertSame(action,OriginalCommandClocks.requireCurrentProposal(score,action));
        var raise=request(0,Set.of(new OperationKey("raise-troops-default")));
        var raiseLeaf=leaves.stream().filter(value->value.boundary()==WarCorePlanner.Boundary.DEFAULT_RAISE_AND_PRIMARY_IDENTITY).findFirst().orElseThrow();
        var raised=assertInstanceOf(MilitaryPlanningDecision.Select.class,raiseLeaf.producer().evaluate(raise,OrdinaryPolicy.Draft.empty()));
        assertEquals(new OperationKey("raise-troops-default"),raised.operation());
        assertEquals(0,calls.get(),"factory construction must not invent a read or start Native");
    }
    @Test void ordinaryContinuationDoesNotRequireUnusedRaiktorInputsAndUnknownReadIsNotRetried() {
        var calls=new AtomicInteger();var reads=unavailableReads(calls);
        var ordinary=WarExitPolicies.ordinaryBeforeTactics(SOURCE,reads);
        var original=request(0,Set.of(new OperationKey("query-war-termination-options-7")));
        var withCapability=new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),
                new PlanningObservation(original.observations().snapshot(),List.of(),original.observations().actionSteps(),
                        Set.of("game.command.query-war-termination-options-N"),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        assertInstanceOf(OrdinaryPolicy.Defer.class,ordinary.evaluateBeforeTactics(withCapability,OrdinaryPolicy.Draft.empty()));
        assertInstanceOf(OrdinaryPolicy.Defer.class,ordinary.evaluateBeforeTactics(withCapability,OrdinaryPolicy.Draft.empty()));
        assertEquals(1,calls.get(),"an actual unavailable attempt must remain unavailable on the same frame");
        var misuse=assertInstanceOf(OrdinaryPolicy.Stop.class,ordinary.evaluate(withCapability,OrdinaryPolicy.Draft.empty()));
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,misuse.stopReason());
    }
    @Test void incompleteRouteEvidenceCannotBecomeTwoEmptyTacticalSets() {
        var incomplete=RootWarCoreFactory.actualRouteTactics(request(0,Set.of()));
        assertInstanceOf(WarCorePlanner.UnknownTactics.class,incomplete);
    }
    @Test void advancedPowerCollectorUsesTheActualOneTargetNativeRecipeOperation() {
        var original=request(0,Set.of());
        var context=new ArmyTypes.Context(original.before(),original.source(),original.sessionId(),original.deadline());
        for(int target:List.of(1,501,Integer.MAX_VALUE)) {
            var input=new ArmyCalls.WarEntry(new ArmyCalls.Revision(new ArmyTypes.Present<>(original.before().frame().revision())),
                    List.of(new ArmyTypes.PositiveId(target)));
            var nativeRecipe=assertInstanceOf(ArmyNativeRecipes.Primitive.class,
                    ArmyNativeRecipes.prepare(input,context,new ArmyNativeRecipes.NoFacts(),false));
            var key=new WarExitReads.Key(WarExitReads.Kind.POWER,target);
            assertEquals(nativeRecipe.request().step(),WarExitReads.step(key));
            assertEquals(Optional.of(WarExitReads.capability(WarExitReads.Kind.POWER)),nativeRecipe.request().requiredCapability());
            assertEquals(ArmyNativeRecipes.Effect.READ_ONLY,nativeRecipe.effect());
        }
        assertThrows(IllegalArgumentException.class,()->WarExitReads.step(new WarExitReads.Key(WarExitReads.Kind.POWER,0)));
    }
    @Test void originalCollectorEntryPassesTheCompletePlanToTheSameMilitaryReaderAndSurvivesJsonRoundtrip() {
        var current=request(0,Set.of());var calls=new AtomicInteger();
        for(var key:List.of(new WarExitReads.Key(WarExitReads.Kind.OPTIONS,7),
                new WarExitReads.Key(WarExitReads.Kind.TERMS,7),new WarExitReads.Key(WarExitReads.Kind.POWER,501))) {
            var result=RootWarCoreFactory.dispatchExit(current,key,new Obj(Map.of()),(request,selected)->{
                calls.incrementAndGet();assertSame(current,request);
                assertEquals(OrdinaryPolicy.Purpose.READ_ONLY,selected.purpose());
                assertEquals(new OperationKey(WarExitReads.step(key)),selected.operation());
                assertFalse(selected.reason().isBlank());assertTrue(selected.arguments().members().isEmpty());
                assertEquals(new Text(selected.policy()),selected.detail().get("policy"));
                assertEquals(new Text(selected.phase()),selected.detail().get("phase"));
                assertEquals(new Text(selected.reason()),selected.detail().get("reason"));
                assertEquals(new Text(selected.operation().value()),selected.detail().get("selected_step"));
                var roundtrip=org.xar.ck3.control.application.driver.DriverJson.object(
                        org.xar.ck3.control.application.driver.DriverJson.encode(selected.detail()),
                        org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
                var retained=new MilitaryPlanningDecision.Select(selected.policy(),selected.phase(),selected.reason(),
                        selected.operation(),selected.arguments(),selected.purpose(),roundtrip);
                assertEquals(selected,retained);
                assertThrows(IllegalArgumentException.class,()->new MilitaryPlanningDecision.Select(
                        selected.policy(),selected.phase(),selected.reason(),selected.operation(),selected.arguments(),
                        selected.purpose(),roundtrip.with("selected_step",new Text("query-another-original-read"))));
                assertThrows(IllegalArgumentException.class,()->new MilitaryPlanningDecision.Select(
                        selected.policy(),selected.phase(),selected.reason(),selected.operation(),selected.arguments(),
                        selected.purpose(),roundtrip.with("reason",new Text("another original reason"))));
                assertThrows(IllegalArgumentException.class,()->new MilitaryPlanningDecision.Select(
                        selected.policy(),selected.phase(),selected.reason(),selected.operation(),selected.arguments(),
                        selected.purpose(),new Obj(Map.of())));
                return new PlanningReadResult.Unavailable<Obj>("original military read unavailable",Optional.empty());
            });
            if(result instanceof PlanningReadResult.Unavailable<WarExitReads.Query> missing)
                assertEquals("original military read unavailable",missing.reason());
            else fail("the collector must preserve the sole military reader's actual unavailability");
        }
        assertEquals(3,calls.get(),"each original collector is forwarded exactly once, without retry or another catalogue");
        assertThrows(IllegalArgumentException.class,()->RootWarCoreFactory.exitReadSelection(
                new WarExitReads.Key(WarExitReads.Kind.POWER,0),new Obj(Map.of())));
        assertThrows(IllegalArgumentException.class,()->RootWarCoreFactory.exitReadSelection(
                new WarExitReads.Key(WarExitReads.Kind.POWER,501),object("unowned",new Bool(true))));
        assertThrows(IllegalArgumentException.class,()->RootWarCoreFactory.exitReadSelection(
                new WarExitReads.Key(WarExitReads.Kind.PREWAR_COALITION,0),new Obj(Map.of())));
    }
    @Test void actualNativeSerializerPayloadReachesTheCurrent4PowerConsumerWithoutProvenanceRepair()throws java.io.IOException {
        String path=System.getProperty("xar.warEntry.fullPower.nativeWire");
        String bytes=System.getProperty("xar.warEntry.fullPower.nativeWireBytes");
        String sha=System.getProperty("xar.warEntry.fullPower.nativeWireSha256");
        assertNotNull(path,"actual native serializer output FileRef must be produced by the full CI step");
        assertNotNull(bytes,"actual native serializer output byte length is required");
        assertNotNull(sha,"actual native serializer output SHA is required");
        assertTrue(bytes.matches("[1-9][0-9]*"),"canonical positive native artifact length required");
        var ref=new ExactRef(path,Long.parseLong(bytes),sha);
        var wire=RootRuntimeDefinitions.read(RootApplicationConfiguration.file(ref),RootWarPowerReads.MAX_NATIVE_PAYLOAD_BYTES);
        var payload=assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                StrictJson.parse(wire,RootWarPowerReads.MAX_NATIVE_PAYLOAD_BYTES));
        var current=request(0,Set.of());
        var key=new WarExitReads.Key(WarExitReads.Kind.POWER,501);
        var actual=RootWarPowerReads.requireCurrentPayload(current,key,payload);
        assertEquals(41,actual.snapshotRevision());
        assertEquals(BigInteger.valueOf(7),current.before().frame().revision(),"public and native revisions must differ");
        var row=actual.assessments().getFirst();
        assertEquals(120000,row.actorPowerTotalRaw());
        assertEquals(100000,row.targetPowerTotalRaw());
        assertEquals(83333,row.actualPowerRatioRaw());
        assertEquals(502,row.effectiveTargetCharacterId(),"requested and effective native characters stay separate");
        assertEquals(actual.toNativeJson(),RootWarPowerReads.requireCurrentPayload(current,key,actual.toNativeJson()).toNativeJson());
        var publicRevision=payload.deepCopy();publicRevision.put("snapshot_revision",7);
        assertThrows(IllegalArgumentException.class,()->RootWarPowerReads.requireCurrentPayload(current,key,publicRevision));
        var missing=payload.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("assessments").get(0)).remove("actor_network_contribution_raw");
        assertThrows(IllegalArgumentException.class,()->RootWarPowerReads.requireCurrentPayload(current,key,missing));
        var oldBuildFields=Map.of("game_version","1.20.0.2",
                "executable_sha256","AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
                "assessment_rva","0x1A23240","network_collector_rva","0x1A24010");
        for(var field:oldBuildFields.entrySet()) {
            var mixed=payload.deepCopy();
            ((com.fasterxml.jackson.databind.node.ObjectNode)mixed.get("provenance")).put(field.getKey(),field.getValue());
            assertThrows(IllegalArgumentException.class,()->RootWarPowerReads.requireCurrentPayload(current,key,mixed),
                    "one mismatched native provenance field cannot be silently repaired: "+field.getKey());
            var absent=payload.deepCopy();
            ((com.fasterxml.jackson.databind.node.ObjectNode)absent.get("provenance")).remove(field.getKey());
            assertThrows(IllegalArgumentException.class,()->RootWarPowerReads.requireCurrentPayload(current,key,absent));
        }
        var wrongType=payload.deepCopy();wrongType.put("snapshot_revision",true);
        assertThrows(IllegalArgumentException.class,()->RootWarPowerReads.requireCurrentPayload(current,key,wrongType));
    }
    @Test void originalProposalClocksRejectDeadlineSessionAndIntentReplacement() {
        var original=request(100,Set.of(new OperationKey("enforce-demands-7")));
        var selected=assertInstanceOf(OrdinaryPolicy.Replace.class,LegacyWarExitPolicy.evaluateScoreThresholds(original,OrdinaryPolicy.Draft.empty()));
        var command=selected.draft().command().orElseThrow();
        var extended=new ActionCommand(command.actionId(),command.origin(),command.source(),command.sessionId(),command.operation(),
                command.arguments(),command.expectation(),command.claims(),command.deadline().plusSeconds(1));
        assertThrows(IllegalArgumentException.class,()->OriginalCommandClocks.requireCurrentProposal(original,extended));
        var otherSession=new ActionCommand(command.actionId(),command.origin(),command.source(),"other-session",command.operation(),
                command.arguments(),command.expectation(),command.claims(),command.deadline());
        assertThrows(IllegalArgumentException.class,()->OriginalCommandClocks.requireCurrentProposal(original,otherSession));
        var otherIntent=new ActionCommand("another-intent",command.origin(),command.source(),command.sessionId(),command.operation(),
                command.arguments(),command.expectation(),command.claims(),command.deadline());
        assertThrows(IllegalArgumentException.class,()->OriginalCommandClocks.requireRebound(original,command,otherIntent));
        var otherOperation=new ActionCommand(command.actionId(),command.origin(),command.source(),command.sessionId(),
                new OperationKey("surrender-war-7"),command.arguments(),command.expectation(),command.claims(),command.deadline());
        assertThrows(IllegalArgumentException.class,()->OriginalCommandClocks.requireRebound(original,command,otherOperation));
        var droppedClaims=new ActionCommand(command.actionId(),command.origin(),command.source(),command.sessionId(),command.operation(),
                command.arguments(),command.expectation(),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),command.deadline());
        assertThrows(IllegalArgumentException.class,()->OriginalCommandClocks.requireRebound(original,command,droppedClaims));
        assertSame(command,OriginalCommandClocks.requireRebound(original,command,command));
    }
}

