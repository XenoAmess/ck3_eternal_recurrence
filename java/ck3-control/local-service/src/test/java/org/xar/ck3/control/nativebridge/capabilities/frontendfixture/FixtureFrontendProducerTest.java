package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.FrontendGuardBinding;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;

/** Actual shared Java algorithm with the narrow package test port; no Root/Native/qualification is simulated as ready. */
final class FixtureFrontendProducerTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-24T22:00:00Z");
    private PreparedFixture fixture(boolean scenario)throws Exception {var f=new PreparedFixtureTest();f.temporary=temporary;return f.create(scenario).prepared();}
    @Test void realProducerClaimsBeforeEveryWriteAndEarlyReadNeverRepeatsSetter()throws Exception {
        PreparedFixture fixture=fixture(false);var port=new ControlledPort(fixture,false);var producer=new FixtureFrontendProducer(fixture,port,Duration.ofSeconds(1));
        var submitted=producer.submitRobert("robert-original");assertEquals(List.of(Primitive.SELECT_1066,Primitive.START_BOOKMARK),port.mutations);
        assertTrue(port.earlyReads>=2);assertEquals(FrontendFixturePolicy.ROBERT_KEY,submitted.submission().selectedCandidate().characterNameKey());
        assertFalse(submitted.submission().toJson().get("postcondition_verified").booleanValue());
        assertThrows(Exception.class,()->producer.submitRobert("second"));assertEquals(2,port.mutations.size());
        var reconnect=new FixtureFrontendProducer(fixture,new ControlledPort(fixture,false),Duration.ofSeconds(1));assertThrows(Exception.class,()->reconnect.submitRobert("reconnect"));
    }
    @Test void scenarioUnavailableProbeThenBookmarkCharacterAndStartEachOnce()throws Exception {
        PreparedFixture fixture=fixture(true);var port=new ControlledPort(fixture,true);var producer=new FixtureFrontendProducer(fixture,port,Duration.ofSeconds(1));
        var submitted=producer.submitScenario("scenario-original");
        assertEquals(List.of(Primitive.SCENARIO_BOOKMARK,Primitive.SCENARIO_CHARACTER,Primitive.SCENARIO_START),port.mutations);
        assertTrue(submitted.submission().bookmarkAcknowledgement().isPresent());assertTrue(submitted.submission().selectedCandidate().nativeModel().isPresent());
        var other=new FixtureFrontendProducer(fixture,new ControlledPort(fixture,true),Duration.ofSeconds(1));assertThrows(Exception.class,()->other.submitScenario("another-tool"));
    }
    @Test void lostAckAndSelectionTimeoutPersistClaimAndNeverReachAnotherSetterOrStart()throws Exception {
        PreparedFixture fixture=fixture(false);var port=new ControlledPort(fixture,false);port.lose=Primitive.SELECT_1066;
        var producer=new FixtureFrontendProducer(fixture,port,Duration.ofMillis(200));assertThrows(IOException.class,()->producer.submitRobert("lost-original"));
        assertEquals(List.of(Primitive.SELECT_1066),port.mutations);assertTrue(Files.isRegularFile(fixture.stateDir().resolve("frontend-fixture-start-requests.jsonl")));
        assertThrows(Exception.class,()->producer.submitRobert("repeat"));assertEquals(1,port.mutations.size());
        var support=new PreparedFixtureTest();support.temporary=Files.createDirectories(temporary.resolve("timeout"));
        PreparedFixture stalled=support.create(false).prepared();var waits=new ControlledPort(stalled,false);waits.stall=true;
        assertThrows(IOException.class,()->new FixtureFrontendProducer(stalled,waits,Duration.ofMillis(200)).submitRobert("timeout-original"));
        assertEquals(List.of(Primitive.SELECT_1066),waits.mutations);
    }
    @Test void qualificationBeforeStartAndChangedBindingRejectBeforeMutation()throws Exception {
        PreparedFixture fixture=fixture(false);Files.createDirectories(fixture.profileDirectory().resolve("logs"));Files.writeString(fixture.profileDirectory().resolve("logs/debug.log"),"FIXTURE: qualified\n");
        var port=new ControlledPort(fixture,false);assertThrows(Exception.class,()->new FixtureFrontendProducer(fixture,port,Duration.ofSeconds(1)).submitRobert("old-qualified"));
        assertTrue(port.mutations.isEmpty());assertFalse(Files.exists(fixture.stateDir().resolve("frontend-fixture-start-requests.jsonl")));
    }
    private final class ControlledPort implements FixtureFrontendProducer.Port {
        final PreparedFixture fixture;final boolean scenario;final List<Primitive> mutations=new ArrayList<>();
        final FrontendRulesData.Source source;final G2Source physical;final GameGeneration game;
        long millis;int sequence,earlyReads;boolean bookmark,selected,stall;Primitive lose;
        ControlledPort(PreparedFixture fixture,boolean scenario) {
            this.fixture=fixture;this.scenario=scenario;bookmark=!scenario;
            source=new FrontendRulesData.Source(new FrontendRulesData.Binding(71,BigInteger.TWO),scenario?FrontendRulesData.Build.CK3_12004:FrontendRulesData.Build.CK3_12003);
            physical=new G2Source("fixture-algorithm-software",NOW.toString(),scenario?"1.20.0.4":"1.20.0.3",ref("source"));
            game=new GameGeneration(71,new PythonOnlyUInt64(BigInteger.valueOf(123)));
        }
        ExactRef ref(String role){return new ExactRef(temporary.resolve(role).toString(),1,org.xar.ck3.control.application.driver.DriverJson.sha256(role.getBytes(java.nio.charset.StandardCharsets.UTF_8)));}
        FrontendIdentity identity(){int n=++sequence;return new FrontendIdentity(physical.machineId(),game,"fixture-session",BigInteger.TWO,71,new FrontendFrame.Menu(BigInteger.valueOf(n)),ref("packet-"+n),ref("hello"));}
        @Override public FrontendRulesData.Source currentSource(){return source;}
        @Override public PlanningReadResult.Known<FrontendRulesData.ObservedRoute> route(){var id=identity();return known(new FrontendRulesData.ObservedRoute(FrontendRulesData.Route.BOOKMARKS,source,id.frame().querySequence()),Primitive.ROUTE,id,new RawJson("{}".getBytes()));}
        @Override public PlanningReadResult.Known<FixtureModelContract.Observation> model(boolean branch) {
            assertEquals(scenario,branch);var id=identity();ObjectNode n=StrictJson.object();
            if(!bookmark)n.put("accepted",true).put("status","unavailable").put("selected_bookmark_key","bm_1066_rags_to_riches");
            else {
                String key=scenario?FrontendFixturePolicy.SCENARIO_TARGET.characterNameKey():FrontendFixturePolicy.ROBERT_KEY;
                n.put("candidate_identity_ready",true).put("supported_1066_candidate_index",0).put("selected_character_index",selected&&!stall&&earlyReads++>=2?0:-1);n.putArray("candidate_keys").add(key);
                n.put("accepted",true).put("status","identity_ready").put("selected_bookmark_key",scenario?"bm_xar_faith_h01_867":"bm_1066_rags_to_riches");
                n.put("selected_bookmark_group_key",scenario?"bm_group_867":"bm_group_1066").put("selected_date_low_raw",scenario?51394920:37791000)
                        .put("supported_1066_government_key",scenario?"clan_government":"feudal_government").put("supported_1066_date_matches",true).put("supported_1066_feudal",!scenario);
            }
            RawJson raw=new RawJson(StrictJson.canonical(n));return known(FixtureModelContract.decode(raw,source,id.frame().querySequence(),fixture.policy().kind()),scenario?Primitive.SCENARIO_PROBE:Primitive.BOOKMARK_MODEL,id,raw);
        }
        private <T>PlanningReadResult.Known<T> known(T value,Primitive step,FrontendIdentity id,RawJson result) {
            var command=new PlanningReadRequest(new CommandOrigin.Frontend(id),physical,"fixture-session",step.operation(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),deadline());
            var guard=new PlanningReadGuard(guard(id,step),FrontendGuardBinding.digest(id));String request="read-"+sequence;
            var receipt=new PlanningReadReceipt(command,"controlled."+step.operation().value(),request,guard,guard,ack(request,result));
            return new PlanningReadResult.Known<>(value,receipt,ref(request));
        }
        @Override public ActionReceipt mutate(String id,FixtureFrontendProducer.Mutation mutation)throws IOException {
            List<String> lines=Files.readAllLines(fixture.stateDir().resolve("frontend-fixture-start-requests.jsonl"));
            var intent=StrictJson.parse(lines.getLast().getBytes(java.nio.charset.StandardCharsets.UTF_8));assertFalse(intent.get("retry_allowed").booleanValue());assertEquals(mutation.primitive().operation().value(),intent.get("step").textValue());
            mutations.add(mutation.primitive());if(mutation.primitive()==lose)throw new IOException("controlled lost ACK after possible original mutation");
            if(mutation.primitive()==Primitive.SCENARIO_BOOKMARK)bookmark=true;
            if(mutation.primitive()==Primitive.SELECT_1066||mutation.primitive()==Primitive.SCENARIO_CHARACTER)selected=true;
            var before=identity();var expected=new FrontendExpectedPostcondition(before,physical,"controlled.selection.v1",List.of());
            var command=new ActionCommand(id,new CommandOrigin.Frontend(before),physical,"fixture-session",mutation.primitive().operation(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),new CommandExpectation.Frontend(expected),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline());
            var attempt=new ActionState.Attempt("action-"+sequence,clock().instant(),guard(before,mutation.primitive()),mutation.primitive().emptyRequest());
            ObjectNode result=StrictJson.object().put("step",mutation.primitive().operation().value()).put("accepted",true).put("status","acknowledged_verification_pending").put("backend_id","native-headless");
            var ack=ack(attempt.requestId(),new RawJson(StrictJson.canonical(result)));var after=identity();
            var observation=new FrontendEffectObservation(after,physical,"fixture-session","controlled.selection.v1",List.of(),"after-"+sequence,clock().instant(),after.nativeEvidence());
            return new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.FrontendApplied(observation)));
        }
        GuardEvidence guard(FrontendIdentity id,Primitive step){return new GuardEvidence(new CommandOrigin.Frontend(id),physical,"fixture-session",BigInteger.TWO,step.operation(),id.nativeEvidence(),id.capabilityEvidence(),"controlled-read",clock().instant(),deadline());}
        @Override public ActionReceipt reconcileSelection(ActionReceipt original){return original;}
        @Override public ExactRef preserveClaim(RawJson raw){return new ExactRef(fixture.stateDir().resolve("controlled-claim-material.json").toString(),raw.bytes().length,ActionCodec.sha256(raw.bytes()));}
        @Override public RawJson originalModel(PlanningReadResult.Known<FixtureModelContract.Observation> original){return original.value().original();}
        @Override public Clock clock(){return new Clock(){public ZoneId getZone(){return ZoneOffset.UTC;}public Clock withZone(ZoneId zone){return this;}public Instant instant(){return NOW.plusMillis(millis);}};}
        @Override public Instant deadline(){return NOW.plusSeconds(10);}
        @Override public void pause(Duration duration){millis+=duration.toMillis();}
        NativeActionPort.AckReceived ack(String request,RawJson token) {
            ObjectNode frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request).put("ok",true);frame.set("result",StrictJson.parse(token.bytes()));
            byte[] raw=StrictJson.canonical(frame);byte[] packet=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
            return new NativeActionPort.AckReceived(request,true,Optional.of(token),new RawJson(raw),packet);
        }
    }
}
