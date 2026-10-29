package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance;
import org.xar.ck3.control.nativebridge.capabilities.religion.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;

/** Original packet/guard/archive software edges. This does not mint a qualified Root or Native source. */
final class RootReligionTemporalFinanceTest {
    @TempDir Path directory;

    @Test void actualExplicitTitleReadUsesSoleDecoderArchiveReplayAndPublicBinding() throws Exception {
        var installed=new AtomicReference<ReadContract<ReligionModels.EpidemicResult>>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(PlayerReligionContext.Build.CROZIER4.sha256(),"ck3-1.20.0.4-msvc-x64",source->{
            var contract=RootReligionTemporalFinance.epidemicContract(new RootReligionTemporalFinance.EpidemicSelection(27,null),source,source,request->assertEquals("query-player-epidemic-recovery-v1-title-27",request.operation().value()));
            installed.set(contract);return List.of(contract);
        },request->{
            assertEquals("query-player-epidemic-recovery-v1-title-27",request.step());assertTrue(ReligionCodec.object(request.additionalFields()).isEmpty());return ReligionCodec.raw(epidemicEnvelope());
        },Optional.of("1.20.0.4"),Set.of());
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("epidemic"),false,scenario)){
            actual.ready();actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),Instant.now().plusSeconds(20),lease->{
                var frame=lease.frame();var args=StrictJson.object().put("expected_revision",frame.identity().frame().revision().toString()).put("requested_title_id",27);
                var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),installed.get().operation(),new OpportunityJson.Obj(java.util.Map.of()),Instant.now().plusSeconds(15));
                var read=ReligionService.readKnownRequest(actual.reads,actual.archive,same,installed.get(),request);
                assertEquals(27,read.value().requestedTitleId());assertFalse(read.value().counties().getFirst().minorPresent());
                var original=read.receipt().original().originalResultToken().orElseThrow();
                var restored=actual.archive.withSession(same).loadRead(read.originalReceipt());
                assertEquals(read.receipt(),restored);assertEquals(read.value(),installed.get().replay(restored));
                assertEquals(original,restored.original().originalResultToken().orElseThrow());
                var output=EpidemicOriginalDecoder.publicResult(restored,27,null);
                assertTrue(output.get("queried_event_instance_id").isNull());assertEquals("1",output.get("snapshot_revision").textValue());
                assertTrue(ReligionCodec.object(original).get("snapshot_revision").isIntegralNumber());
                var bindings=RootReligionTemporalFinance.bindings(installed.get().sourceRef(),decoded->{
                    assertEquals(new BigInteger("27"),decoded.integer(ReligionContract.Field.REQUESTED_TITLE_ID));
                    return new ReligionContract.Response(decoded.method(),ReligionCodec.raw(output));
                });
                var binding=bindings.stream().filter(value->value.name().equals(RootReligionTemporalFinance.EPIDEMIC)).findFirst().orElseThrow();
                ReligionExtensionTestWire.exercise(binding,args,output);
                assertEquals(1,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());
                return null;
            }));
        }
    }

    @Test void actualClergyCandidateReadRetainsDerivedPublicRevisionAndNativeSentinels()throws Exception {
        var installed=new AtomicReference<ReadContract<ReligionTemporalFinance.Observed>>();
        var selection=new ReligionTemporalFinance.Selection(ReligionTemporalFinance.Kind.CLERGY,BigInteger.valueOf(123));
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(PlayerReligionContext.Build.CROZIER4.sha256(),"ck3-1.20.0.4-msvc-x64",source->{
            var contract=ReligionTemporalFinance.contract(selection,new ReligionTemporalFinance.Sources(source,source,List.of(source)),request->assertEquals(selection.kind().step(),request.operation().value()));installed.set(contract);return List.of(contract);
        },request->{var fields=ReligionCodec.object(request.additionalFields());assertEquals(BigInteger.valueOf(123),fields.get("candidate_character_id").bigIntegerValue());assertTrue(fields.get("expected_public_revision").isIntegralNumber());return ReligionCodec.raw(clergyEnvelope());},Optional.of("1.20.0.4"),Set.of());
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("clergy"),false,scenario)){
            actual.ready();actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),Instant.now().plusSeconds(20),lease->{
                var frame=lease.frame();var selectors=OpportunityJson.object(OpportunityJson.parse(ReligionCodec.raw(ReligionTemporalFinance.selectionArguments(selection)).bytes()),"actual clergy selector");
                var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),installed.get().operation(),selectors,Instant.now().plusSeconds(15));
                var read=ReligionService.readKnownRequest(actual.reads,actual.archive,same,installed.get(),request);var original=actual.archive.withSession(same).loadRead(read.originalReceipt());
                assertEquals(read.value(),installed.get().replay(original));var output=read.value().publicResult();assertEquals("18446744073709551615",output.get("capture_epoch").textValue());
                assertEquals(new BigInteger("4294967295"),output.get("candidate_rite_id").bigIntegerValue());assertFalse(output.get("native_can_reassign").booleanValue());assertTrue(output.get("incumbent_character_id").isNull());assertFalse(output.has("native_can_fire"));
                var call=StrictJson.object().put("expected_revision",frame.identity().frame().revision().toString()).put("candidate_character_id",123);
                var binding=RootReligionTemporalFinance.bindings(installed.get().sourceRef(),decoded->new ReligionContract.Response(decoded.method(),ReligionCodec.raw(output))).stream().filter(value->value.name().equals(selection.kind().method())).findFirst().orElseThrow();
                ReligionExtensionTestWire.exercise(binding,call,output);assertEquals(0,actual.nativeActionWrites());return null;
            }));
        }
    }

    @Test void listEventAndExplicitTitleAreDistinctBeforeAnyNativeRead() {
        assertThrows(IllegalArgumentException.class,()->new RootReligionTemporalFinance.EpidemicSelection(0,null));
        assertThrows(IllegalArgumentException.class,()->new RootReligionTemporalFinance.EpidemicSelection(27,BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->new RootReligionTemporalFinance.EpidemicSelection(-1,null));
        var method=RootReligionTemporalFinance.EPIDEMIC;
        var list=StrictJson.object().put("expected_revision",1).put("expected_event_instance_id",2147483647);
        var request=ReligionCodec.decode(method,ReligionCodec.raw(list));assertEquals(request,ReligionCodec.decode(method,ReligionCodec.encode(request)));
        for(ObjectNode bad:List.of(list.deepCopy().put("expected_event_instance_id",true),list.deepCopy().put("expected_event_instance_id",1.0),list.deepCopy().putNull("expected_event_instance_id"),list.deepCopy().put("requested_title_id",27)))
            assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(method,ReligionCodec.raw(bad)));
    }

    private static ObjectNode epidemicEnvelope(){
        var n=StrictJson.object().put("step","query-player-epidemic-recovery-v1-title-27").put("accepted",true).put("status","available").put("query_sequence",1).put("observation_revision",1).put("snapshot_revision",1).put("private_build",true).put("read_only",true).put("advertised",false).put("backend_id","native-headless");
        var body=n.putObject("player_epidemic_recovery").put("schema","player-epidemic-recovery-v1").put("schema_version",1).put("snapshot_revision",1).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("played_character_id",73).put("list_key","formerly_infected_counties").put("requested_title_id",27).put("status","available").putNull("unavailable_reason");
        body.putArray("counties").addObject().put("landed_title_id",27).put("minor_present",false).put("tiny_present",true);
        body.putObject("remaining_days").put("status","unavailable").putNull("value").put("unavailable_reason","duration_abi_not_verified");return n;
    }
    private static ObjectNode clergyEnvelope(){
        var build=PlayerReligionContext.Build.CROZIER4;var n=StrictJson.object().put("step","query-player-clergy-appointment-v1").put("accepted",true).put("status","observed").put("private_build",true).put("read_only",true).put("advertised",false).put("game_version",build.version()).put("executable_sha256",build.sha256()).put("backend_id","ck3-1.20.0.4-native-player-clergy-appointment-v1").put("domain_key","player_clergy_appointment_v1").put("snapshot_revision",1).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW);
        var body=n.putObject("player_clergy_appointment").put("schema","xar.ck3.religion-clergy-appointment/v1").put("schema_version",1).put("status","available").put("failure","none").put("capture_epoch",new BigInteger("18446744073709551615")).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("owner_character_id",73).put("candidate_character_id",123).put("position_key","councillor_court_chaplain").put("position_present",true).putNull("active_task_id").putNull("incumbent_character_id").putNull("candidate_court_owner_id").putNull("owner_rite_id").put("candidate_rite_id",4294967295L).put("candidate_is_incumbent",false).putNull("candidate_matches_owner_context").put("native_valid_position",true).put("native_valid_character",true).put("native_can_reassign",false).put("action_eligibility_complete",false);
        body.putObject("exact_build").put("game_version",build.version()).put("executable_sha256",build.sha256());return n;
    }
}

final class ReligionExtensionTestWire {
    private ReligionExtensionTestWire(){ }
    static <Q,R> void exercise(McpExecutableDirectory.DirectBinding<Q,R> binding,ObjectNode args,ObjectNode expected)throws IOException {
        var call=new PublicMcpDirectory.ToolCall(binding.name(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(ReligionCodec.raw(args))),Optional.empty(),new McpCancellation());
        try {
            Q decoded=binding.decoder().decode(call);R result=binding.actual().invoke(decoded);var response=ReligionCodec.object(new RawJson(binding.encoder().encode(result).bytes()));
            assertEquals(expected,response.get("structuredContent"));
            assertEquals(expected,ReligionCodec.object(new RawJson(response.get("content").get(0).get("text").textValue().getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        } catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("software binding interrupted",interrupted);}
        catch(PublicMcpDirectory.ToolFailure|PublicMcpDirectory.RpcFailure failure){throw new IOException("actual public codec rejected software fixture",failure);}
    }
}
