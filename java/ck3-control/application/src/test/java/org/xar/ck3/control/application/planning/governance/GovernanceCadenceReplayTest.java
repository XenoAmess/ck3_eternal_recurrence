package org.xar.ck3.control.application.planning.governance;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.optionalcadence.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual ordinary Feast producer -> private typed transcript -> same-head material replay -> real cadence reducer. */
final class GovernanceCadenceReplayTest {
    private static final ExactRef CODE_TRACE=new ExactRef("missing-java/GovernanceCadenceReplay.java",1,"c".repeat(64));
    private static final class Session implements ContinuityStorePort.Session {
        final byte[] original=CadenceJson.writeState(CadenceModels.State.empty("unit-episode"));
        final DomainBodies.BodyRef body;final ContinuityState state;int pinChecks;
        final List<ExactRef> captured=new ArrayList<>();
        Optional<ExactRef> unavailable=Optional.empty();
        Session() {
            var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",SOURCE.machineId())
                    .put("sequence",0).put("window_id",1).put("status","running").put("start_date_raw",100)
                    .put("target_days",1).put("target_date_raw",124).put("last_settled_cycles",0).put("last_settled_date_raw",100);
            var ref=new ExactRef("synthetic-cadence-body.json",original.length,ActionCodec.sha256(original));
            body=new DomainBodies.BodyRef(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,ref,
                    new FileIdentity("1","2","133700000000000001",NOW.toString(),original.length),List.of(REF));
            state=DomainBodies.reduceImport(ContinuityState.fromJson(row,SOURCE.machineId()),body);
        }
        public void requireWriter(Path path) { }
        public Pin capturePin(ExactRef ref,int maximum)throws IOException {
            captured.add(ref);
            if(unavailable.filter(ref::equals).isPresent())throw new IOException("actual requested evidence is unavailable: "+ref.path());
            return new Pin(ref,new FileIdentity("1","2","133700000000000001",NOW.toString(),ref.bytes()));
        }
        public void verifyPin(Pin pin) {pinChecks++;}
        public Head head() {return new Head(state,List.of(),List.of(),List.of(),false);}
        public ExactRef persistedHead() {return REF;}
        public Prepared preview(Request request) {throw new AssertionError("material replay is read-only");}
        public Receipt commit(Prepared request) {throw new AssertionError("material replay is read-only");}
    }
    private static final class ActualFeastReads implements FeastObservationSupplier {
        int calls;boolean unavailable;
        public Read<State> state(PlanningRequest request) {calls++;return new Known<>(new State(request.before(),request.sessionId(),
                CadenceModels.State.empty("unit-episode"),Optional.empty(),Optional.empty(),List.of(),new Obj(Map.of())),List.of(REF));}
        public Read<Planner> planner(PlanningRequest request) {
            calls++;return unavailable?new Unavailable<>("new native read must not run during replay"):
                    new Known<>(new Planner(ActivityPlannerDiagnostic.Kind.OTHER,new Obj(Map.of())),List.of(REF));
        }
        public Read<Hosted> hosted(PlanningRequest request) {throw new AssertionError("this native diagnostic never requires hosted query");}
        public Read<Obj> root(PlanningRequest request) {throw new AssertionError("this native diagnostic never requires root query");}
        public Read<OrdinaryFinanceCollector.Spending> spending(PlanningRequest request) {throw new AssertionError("this native diagnostic never requires spending");}
        public Read<OrdinaryFinanceCollector.Feast> feast(PlanningRequest request,OrdinaryFinanceCollector.Spending spending) {throw new AssertionError("this native diagnostic never requires Start");}
    }
    private PlanningRequest actualRequest() {
        var original=request();var old=original.observations();var actions=new HashSet<>(old.actionSteps());actions.addAll(OrdinaryFeastPolicy.OWNED);
        return new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),new PlanningObservation(old.snapshot(),old.history(),actions,
                old.bridgeCapabilities(),old.battleSpeedReadiness(),old.actionFacts(),old.campaignGoal(),old.crossRunPlan(),old.initialLifestyleFocusRequired()));
    }
    @Test void actualProducerReplaysAllTypedReadsWithoutDispatchingOrTrustingTheRequestedPlan()throws Exception {
        var session=new Session();var actual=new ActualFeastReads();var request=actualRequest();
        var replay=new GovernanceCadenceReplay(()->session,same->assertSame(session,same),(same,ref)->{assertSame(session,same);assertEquals(session.body.payload(),ref);return session.original;});
        var policy=replay.record(new OrdinaryFeastPolicy(REF,replay.observe(actual),(operation,frame,args)->Optional.empty()));
        var result=assertInstanceOf(OrdinaryPolicy.Annotate.class,policy.evaluate(request,advance(request)));
        var plan=GovernanceCadencePublication.fromDetail(result.retained().detail()).orElseThrow();
        assertEquals(List.of(CadenceModels.Domain.FEAST),plan.completeNoActionDomains());assertEquals(2,actual.calls);actual.unavailable=true;
        var material=replay.replay(session.head(),session.body,plan,List.of(REF));
        assertEquals(plan,material.actualReplayedPlan());assertArrayEquals(session.original,material.previousBody());
        assertEquals(2,actual.calls);assertEquals(1,session.pinChecks);
        assertEquals(1,GovernanceCadencePublication.reduce(material.actualReplayedPlan()).row(CadenceModels.Domain.FEAST).consecutiveNoAction());
    }
    @Test void handwrittenPlanHasNoPrivateProducerTranscriptAndCannotQualify() {
        var session=new Session();var replay=new GovernanceCadenceReplay(()->session,same->{},(same,ref)->session.original);var request=actualRequest();
        var plan=GovernanceCadencePublication.fromDetail(GovernanceCadencePublication.append(new Obj(Map.of()),CadenceModels.Domain.FEAST,request,
                CadenceModels.State.empty("unit-episode"))).orElseThrow();
        assertThrows(IOException.class,()->replay.replay(session.head(),session.body,plan,List.of(REF)));
    }
    @Test void wrongEvidenceOrAnotherFrameCannotRebindAnActualCompleteRead() {
        var session=new Session();var actual=new ActualFeastReads();var request=actualRequest();
        var replay=new GovernanceCadenceReplay(()->session,same->{},(same,ref)->session.original);
        var policy=replay.record(new OrdinaryFeastPolicy(REF,replay.observe(actual),(operation,frame,args)->Optional.empty()));
        var produced=assertInstanceOf(OrdinaryPolicy.Annotate.class,policy.evaluate(request,advance(request)));
        var plan=GovernanceCadencePublication.fromDetail(produced.retained().detail()).orElseThrow();
        assertThrows(IllegalArgumentException.class,()->replay.replay(session.head(),session.body,plan,List.of(new ExactRef("wrong",1,"b".repeat(64)))));
        var other=new GovernanceCadencePublication.Plan(identity(10),SOURCE,request.sessionId(),plan.before(),plan.completeNoActionDomains());
        assertThrows(IOException.class,()->replay.replay(session.head(),session.body,other,List.of(REF)));
    }
    @Test void technicalCouncilPlanRoundTripsWithoutActionOrNoActionCredit() {
        var request=actualRequest();var prior=new CadenceModels.Marker(java.math.BigInteger.valueOf(90),java.math.BigInteger.valueOf(8));
        var council=new CadenceModels.Row(2,Optional.empty(),Optional.of(prior),Optional.of(prior),Optional.of("retained-catalogue"),Optional.empty());
        var before=CadenceModels.State.empty("unit-episode").with(CadenceModels.Domain.COUNCIL,council);
        var detail=GovernanceCadencePublication.appendCouncilTechnical(new Obj(Map.of()),request,before,REF);
        var plan=GovernanceCadencePublication.fromDetail(detail).orElseThrow();
        assertTrue(plan.completeNoActionDomains().isEmpty());assertEquals(Optional.of(REF),plan.councilTechnicalFailure());
        var encoded=GovernanceCadencePublication.encode(plan);
        assertEquals(GovernanceCadencePublication.TECHNICAL_SCHEMA,StrictJson.text(StrictJson.parse(encoded).get("schema")));
        assertEquals(plan,GovernanceCadencePublication.decode(encoded));
        var after=GovernanceCadencePublication.reduce(plan);var actual=after.row(CadenceModels.Domain.COUNCIL);
        assertEquals(2,actual.consecutiveNoAction());assertEquals(council.lastActualActionFrame(),actual.lastActualActionFrame());
        assertEquals(council.nativeCatalogue(),actual.nativeCatalogue());assertEquals(REF.path(),actual.technicalDefer().orElseThrow().evidencePath());
        assertTrue(actual.nextDueDateRaw().orElseThrow().compareTo(request.before().frame().identity().dateRaw())>0);
        assertEquals(after,GovernanceCadencePublication.reduce(new GovernanceCadencePublication.Plan(request.before(),SOURCE,request.sessionId(),after,List.of(),Optional.of(REF))));
        assertEquals(after,CadenceJson.readState(CadenceJson.writeState(after),"unit-episode"));
    }
    @Test void normalV1AndMixedTechnicalV2KeepEveryOtherDomain() {
        var request=actualRequest();var before=CadenceModels.State.empty("unit-episode");
        var normal=GovernanceCadencePublication.append(new Obj(Map.of()),CadenceModels.Domain.LIFESTYLE,request,before);
        var first=GovernanceCadencePublication.fromDetail(normal).orElseThrow();
        assertEquals(GovernanceCadencePublication.SCHEMA,StrictJson.text(StrictJson.parse(GovernanceCadencePublication.encode(first)).get("schema")));
        assertTrue(first.councilTechnicalFailure().isEmpty());
        var technical=GovernanceCadencePublication.appendCouncilTechnical(normal,request,before,REF);
        var mixed=GovernanceCadencePublication.append(technical,CadenceModels.Domain.CROWN,request,before);
        var plan=GovernanceCadencePublication.fromDetail(mixed).orElseThrow();
        assertEquals(List.of(CadenceModels.Domain.LIFESTYLE,CadenceModels.Domain.CROWN),plan.completeNoActionDomains());
        assertEquals(Optional.of(REF),plan.councilTechnicalFailure());
        var after=GovernanceCadencePublication.reduce(GovernanceCadencePublication.decode(GovernanceCadencePublication.encode(plan)));
        assertEquals(1,after.row(CadenceModels.Domain.LIFESTYLE).consecutiveNoAction());
        assertEquals(1,after.row(CadenceModels.Domain.CROWN).consecutiveNoAction());
        assertEquals(0,after.row(CadenceModels.Domain.COUNCIL).consecutiveNoAction());
        assertThrows(IllegalArgumentException.class,()->GovernanceCadencePublication.append(mixed,CadenceModels.Domain.COUNCIL,request,before));
    }
    @Test void technicalSchemaRejectsMissingNullWrongTypedDiagnosticAndCompletedCouncilCredit() {
        var request=actualRequest();var before=CadenceModels.State.empty("unit-episode");
        var plan=new GovernanceCadencePublication.Plan(request.before(),SOURCE,request.sessionId(),before,List.of(),Optional.of(REF));
        var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(GovernanceCadencePublication.encode(plan));
        var absent=row.deepCopy();absent.remove("council_technical_failure");
        assertThrows(IllegalArgumentException.class,()->GovernanceCadencePublication.decode(StrictJson.canonical(absent)));
        for(var token:List.of(com.fasterxml.jackson.databind.node.NullNode.instance,com.fasterxml.jackson.databind.node.BooleanNode.TRUE,com.fasterxml.jackson.databind.node.TextNode.valueOf("missing-ref"))) {
            var changed=row.deepCopy();changed.set("council_technical_failure",token);
            assertThrows(IllegalArgumentException.class,()->GovernanceCadencePublication.decode(StrictJson.canonical(changed)));
        }
        assertThrows(IllegalArgumentException.class,()->new GovernanceCadencePublication.Plan(request.before(),SOURCE,request.sessionId(),before,List.of(CadenceModels.Domain.COUNCIL),Optional.of(REF)));
        assertThrows(IllegalArgumentException.class,()->new GovernanceCadencePublication.Plan(request.before(),SOURCE,request.sessionId(),before,List.of()));
    }
    @Test void handwrittenTechnicalDeferStillHasNoActualProducerTranscript() {
        var session=new Session();var request=actualRequest();
        var replay=new GovernanceCadenceReplay(()->session,same->{},(same,ref)->session.original);
        var plan=new GovernanceCadencePublication.Plan(request.before(),SOURCE,request.sessionId(),CadenceModels.State.empty("unit-episode"),List.of(),Optional.of(REF));
        assertThrows(IOException.class,()->replay.replay(session.head(),session.body,plan,List.of(REF)));
    }

    private PlanningResult planned(PlanningRequest request,OrdinaryPolicy policy,OrdinaryPolicy.Draft draft) {
        var visit=new PlanTrace.StageVisit(policy.stage(),PlanTrace.Outcome.KEPT,"actual typed Feast no-action observation",
                Optional.of(policy.implementationSource()),Optional.of(draft.detail()));
        return new PlanningResult.ActionSelected(draft.command().orElseThrow(),
                new PlanTrace(request.before(),List.of(visit),Optional.of(draft)));
    }
    @Test void missingImplementationTraceIsNotBusinessEvidenceButActualReadPinsRemain()throws Exception {
        var session=new Session();session.unavailable=Optional.of(CODE_TRACE);
        var actual=new ActualFeastReads();var request=actualRequest();var materialReads=new AtomicInteger();
        var replay=new GovernanceCadenceReplay(()->session,same->assertSame(session,same),(same,ref)->{
            assertSame(session,same);assertEquals(session.body.payload(),ref);materialReads.incrementAndGet();return session.original;
        });
        var policy=replay.record(new OrdinaryFeastPolicy(CODE_TRACE,replay.observe(actual),(operation,frame,args)->Optional.empty()));
        var produced=assertInstanceOf(OrdinaryPolicy.Annotate.class,policy.evaluate(request,advance(request)));
        var plan=GovernanceCadencePublication.fromDetail(produced.retained().detail()).orElseThrow();
        var planned=planned(request,policy,produced.retained());
        var evidence=replay.originals(request,planned,plan);actual.unavailable=true;
        // Old code reaches capturePin(CODE_TRACE) here; no early expected-list assertion hides the real failure.
        var material=replay.replay(session.head(),session.body,plan,evidence);
        assertEquals(List.of(REF),evidence);assertEquals(List.of(REF),session.captured);assertEquals(1,session.pinChecks);
        assertEquals(CODE_TRACE,policy.implementationSource());
        assertEquals(Optional.of(CODE_TRACE),planned.trace().visits().getFirst().source());
        assertEquals(2,actual.calls,"replay consumes the original typed reads instead of querying again");
        assertEquals(1,materialReads.get());assertArrayEquals(session.original,material.previousBody());
        assertEquals(plan,material.actualReplayedPlan());
        assertEquals(1,GovernanceCadencePublication.reduce(material.actualReplayedPlan()).row(CadenceModels.Domain.FEAST).consecutiveNoAction());
    }
    @Test void missingActualReadEvidenceStillRefusesMaterialReplay()throws Exception {
        var session=new Session();session.unavailable=Optional.of(REF);
        var actual=new ActualFeastReads();var request=actualRequest();var materialReads=new AtomicInteger();
        var replay=new GovernanceCadenceReplay(()->session,same->assertSame(session,same),(same,ref)->{
            materialReads.incrementAndGet();return session.original;
        });
        var policy=replay.record(new OrdinaryFeastPolicy(CODE_TRACE,replay.observe(actual),(operation,frame,args)->Optional.empty()));
        var produced=assertInstanceOf(OrdinaryPolicy.Annotate.class,policy.evaluate(request,advance(request)));
        var plan=GovernanceCadencePublication.fromDetail(produced.retained().detail()).orElseThrow();
        var evidence=replay.originals(request,planned(request,policy,produced.retained()),plan);
        IOException failure=assertThrows(IOException.class,()->replay.replay(session.head(),session.body,plan,evidence));
        assertTrue(failure.getMessage().contains(REF.path()));assertEquals(List.of(REF),session.captured);
        assertEquals(0,session.pinChecks);assertEquals(0,materialReads.get());assertEquals(2,actual.calls);
    }

}
