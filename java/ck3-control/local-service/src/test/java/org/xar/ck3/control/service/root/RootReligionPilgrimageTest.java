package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Full software Native packet/read/retained-original/public consumers; private Root installation remains a separate fixture. */
final class RootReligionPilgrimageTest {
    @TempDir Path directory;

    @Test void sameInstalledRecipeStillPerformsTwoActualReadsAndPreservesFullWidthOriginals()throws Exception {
        var contract=new AtomicReference<ReadContract<Observed>>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(Build.CROZIER4.sha256(),"ck3-1.20.0.4-msvc-x64",source->{
            var installed=ReligionPilgrimage.contract(new Activities(BigInteger.ONE),new ReligionTemporalFinance.Sources(source,source,List.of(source)),request->assertEquals(ACTIVITIES_STEP,request.operation().value()));contract.set(installed);return List.of(installed);
        },request->{
            assertEquals(ACTIVITIES_STEP,request.step());var fields=ReligionCodec.object(request.additionalFields());
            assertEquals(BigInteger.valueOf(73),fields.get("expected_actor_character_id").bigIntegerValue());assertEquals(BigInteger.valueOf(ActionWriterIntegrationFixture.INITIAL_DATE_RAW),fields.get("expected_date_raw").bigIntegerValue());assertEquals("activity_pilgrimage",fields.get("expected_activity_key").textValue());
            return ReligionCodec.raw(activitiesEnvelope());
        },Optional.of("1.20.0.4"),Set.of());
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("activities"),false,scenario)){
            actual.ready();actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),Instant.now().plusSeconds(20),lease->{
                var frame=lease.frame();var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.get().operation(),new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(15));
                var first=ReligionService.readKnownRequest(actual.reads,actual.archive,same,contract.get(),request);
                var second=ReligionService.readKnownRequest(actual.reads,actual.archive,same,contract.get(),request);
                assertNotEquals(first.receipt().requestId(),second.receipt().requestId());assertEquals(2,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());
                var original=actual.archive.withSession(same).loadRead(second.originalReceipt());assertEquals(second.receipt(),original);
                var replayed=contract.get().replay(original);assertEquals(second.value(),replayed);
                var output=replayed.publicResult();assertEquals("18446744073709551615",output.get("activities").get(0).get("native_completion_stamp_raw").textValue());
                var untouched=ReligionCodec.object(original.original().originalResultToken().orElseThrow());assertTrue(untouched.get("player_pilgrimage_activities").get("activities").get(0).get("native_completion_stamp_raw").isIntegralNumber());
                var args=StrictJson.object().put("expected_revision",frame.identity().frame().revision().toString());
                var binding=RootReligionPilgrimage.bindings(contract.get().sourceRef(),decoded->new ReligionContract.Response(decoded.method(),ReligionCodec.raw(output))).stream().filter(value->value.name().equals(ACTIVITIES_METHOD)).findFirst().orElseThrow();
                ReligionExtensionTestWire.exercise(binding,args,output);return null;
            }));
        }
    }

    @Test void actualIndependentPlannerReadClassifiesUiButAbsenceCannotProveStart()throws Exception {
        var contract=new AtomicReference<ReadContract<Observed>>();var selected=new PlannerRead(new ReligionPilgrimage.Request(Operation.READ,BigInteger.ONE,BigInteger.ZERO,0,Option.PIOUS,false,Reserves.zero(),java.math.BigDecimal.valueOf(30)));
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(Build.CROZIER4.sha256(),"ck3-1.20.0.4-msvc-x64",source->{
            var installed=ReligionPilgrimage.contract(selected,new ReligionTemporalFinance.Sources(source,source,List.of(source)),request->assertEquals(QUERY_STEP,request.operation().value()));contract.set(installed);return List.of(installed);
        },request->ReligionCodec.raw(plannerEnvelope("read",true)),Optional.of("1.20.0.4"),Set.of());
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("planner"),false,scenario)){
            actual.ready();actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),Instant.now().plusSeconds(20),lease->{
                var frame=lease.frame();var args=OpportunityJson.object(OpportunityJson.parse(ReligionCodec.raw(selectionFields(selected)).bytes()),"actual selectors");
                var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.get().operation(),args,Instant.now().plusSeconds(15));
                var read=ReligionService.readKnownRequest(actual.reads,actual.archive,same,contract.get(),request);var original=contract.get().replay(actual.archive.withSession(same).loadRead(read.originalReceipt()));
                var open=new ReligionPilgrimage.Request(Operation.OPEN,original.frame().publicRevision(),BigInteger.ZERO,0,Option.PIOUS,true,Reserves.zero(),java.math.BigDecimal.valueOf(30));
                assertEquals(Readback.UI_OBSERVED,classifyReadback(ReligionCodec.raw(plannerEnvelope("open",false)),original.frame(),open,original));
                var pending=plannerEnvelope("open",false);((ObjectNode)pending.get("player_pilgrimage_planner")).put("needs_recovery",true);
                assertEquals(Readback.PENDING,classifyReadback(ReligionCodec.raw(pending),original.frame(),open,original));
                var start=new ReligionPilgrimage.Request(Operation.START,open.expectedRevision(),BigInteger.valueOf(4294967294L),0,Option.PIOUS,true,Reserves.zero(),java.math.BigDecimal.ONE);
                assertThrows(IllegalArgumentException.class,()->classifyReadback(ReligionCodec.raw(plannerEnvelope("start",false)),original.frame(),start,original),"READ cannot substitute the actual POST identity consumer");
                var call=StrictJson.object().put("expected_revision",frame.identity().frame().revision().toString()).put("operation","read");
                var binding=RootReligionPilgrimage.bindings(contract.get().sourceRef(),decoded->new ReligionContract.Response(decoded.method(),ReligionCodec.raw(original.publicResult()))).stream().filter(value->value.name().equals(QUERY_METHOD)).findFirst().orElseThrow();
                ReligionExtensionTestWire.exercise(binding,call,original.publicResult());assertEquals(0,actual.nativeActionWrites());return null;
            }));
        }
    }

    @Test void malformedNativeTerminalAvailabilityDoesNotBecomeKnownOrAnAction()throws Exception {
        var contract=new AtomicReference<ReadContract<Observed>>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(Build.CROZIER4.sha256(),"ck3-1.20.0.4-msvc-x64",source->{
            var installed=ReligionPilgrimage.contract(new Activities(BigInteger.ONE),new ReligionTemporalFinance.Sources(source,source,List.of(source)),request->assertEquals(ACTIVITIES_STEP,request.operation().value()));contract.set(installed);return List.of(installed);
        },request->{var bad=activitiesEnvelope();((ObjectNode)bad.get("player_pilgrimage_activities").get("activities").get(0)).put("native_completed",false);return ReligionCodec.raw(bad);},Optional.of("1.20.0.4"),Set.of());
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("malformed-native"),false,scenario)){
            actual.ready();actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),Instant.now().plusSeconds(20),lease->{
                var frame=lease.frame();var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.get().operation(),new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(15));
                assertInstanceOf(PlanningReadResult.Unavailable.class,actual.reads.read(same,contract.get(),request));
                assertEquals(1,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());return null;
            }));
        }
    }

    @Test void fullWidthPublicRequestFeedsActualPrivateRequestValidatorAndFiniteCombinations() {
        var input=StrictJson.object().put("expected_revision","18446744073709551615").put("operation","start").put("province_id",4294967294L).put("policy_positive",true).put("reserve_gold_raw","9223372036854775807").put("timeout_seconds",0.25);
        var decoded=ReligionCodec.decode(SUBMIT_METHOD,ReligionCodec.raw(input));var request=ReligionPilgrimage.Request.from(decoded);assertEquals(decoded,ReligionCodec.decode(SUBMIT_METHOD,ReligionCodec.encode(decoded)));
        var frame=new ReligionTemporalFinance.Frame(Build.CROZIER4,request.expectedRevision(),new BigInteger("18446744073709551615"),BigInteger.valueOf(1000),BigInteger.valueOf(73),42,BigInteger.valueOf(5),"actual-data-snapshot","same-episode");
        var fields=submitFields(request,frame);var nativeRequest=new NativeRequest(SUBMIT_STEP,Optional.empty(),ReligionCodec.raw(fields));
        assertEquals(request.reserves(),validateSubmit(nativeRequest).reserves());assertTrue(fields.get("reserve_gold_raw").isIntegralNumber());assertEquals(Duration.ofMillis(250),ReligionTemporalFinance.timeout(decoded,Duration.ofSeconds(20)));
        for(ObjectNode bad:List.of(input.deepCopy().put("operation","open"),input.deepCopy().put("policy_positive",false),input.deepCopy().put("province_id",0),input.deepCopy().put("province_id",4294967295L)))assertThrows(IllegalArgumentException.class,()->ReligionPilgrimage.Request.from(ReligionCodec.decode(SUBMIT_METHOD,ReligionCodec.raw(bad))));
        var bad=fields.deepCopy().put("reserve_gold_raw",1.0);assertThrows(IllegalArgumentException.class,()->validateSubmit(new NativeRequest(SUBMIT_STEP,Optional.empty(),ReligionCodec.raw(bad))));
        assertThrows(IllegalArgumentException.class,()->validateSubmit(new NativeRequest(QUERY_STEP,Optional.empty(),ReligionCodec.raw(fields))));
    }

    private static ObjectNode activitiesEnvelope(){
        var n=envelope(ACTIVITIES_STEP,true);var body=n.putObject("player_pilgrimage_activities").put("schema","ck3_12004_player_pilgrimage_activities_v1").put("read_only",true).put("snapshot_revision",1).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("played_character_id",73).put("scope","currently-hosted-by-current-player").put("activity_type_key","activity_pilgrimage").put("activity_count",1).put("absence_is_completion",false).put("raw_pointer_fields_persisted",false);
        body.putArray("activities").addObject().put("activity_id",0).put("host_character_id",73).put("type_key","activity_pilgrimage").put("terminal_flags_observed",false).putNull("native_completed").putNull("native_invalidated").put("native_completion_stamp_observed",true).put("native_completion_stamp_raw",new BigInteger("18446744073709551615"));return n;
    }
    private static ObjectNode plannerEnvelope(String operation,boolean readOnly){
        var n=envelope(readOnly?QUERY_STEP:SUBMIT_STEP,readOnly);var body=n.putObject("player_pilgrimage_planner").put("schema","ck3_12004_player_pilgrimage_planner_v1").put("read_only",readOnly).put("snapshot_revision",1).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("played_character_id",73).put("activity_type_key","activity_pilgrimage").put("special_option_key",Option.PIOUS.key()).put("operation",operation).put("operation_status","observed").put("invoked",!readOnly).put("needs_recovery",false).put("ledger_state","idle").put("failure","").putNull("quote").putNull("new_identity").put("absence_is_completion",false).put("raw_pointer_fields_persisted",false);
        body.putObject("planner").put("stage",2).put("selected_option_key",Option.PIOUS.key()).putNull("destination_province_id").putNull("can_select").put("can_progress",true);return n;
    }
    private static ObjectNode envelope(String step,boolean readOnly){return StrictJson.object().put("step",step).put("accepted",true).put("status","available").put("private_build",true).put("read_only",readOnly).put("advertised",false).put("backend_id","native-headless");}
}
