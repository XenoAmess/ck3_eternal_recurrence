package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real Finance ROOT producer/decoder enters the Sway typed view with the identical native contract. */
final class SwaySharedRootTest {
    @Test void actualFinanceContractIsUsedOnceWithoutAnotherRegistrationAndUnavailableRootNeverBecomesReady() {
        var source=new ExactRef("software:definition",1,"a".repeat(64));
        var registrations=new FinanceReadContracts(query->new FinanceReadContracts.Registration(source,new FinanceReadContracts.Permission(Optional.empty(),"software-root",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        var actual=registrations.contract(FinanceReadContracts.Query.ROOT);
        var bound=SwayNativeFormalTest.binding(73,7,53220000);var now=Instant.parse("2026-10-24T00:00:00Z");var currentSource=new G2Source(bound.before().machineId(),now.toString(),SwayNativeWire.BUILD,source);
        var request=new PlanningReadRequest(bound.before(),currentSource,bound.sessionId(),actual.operation(),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),now.plusSeconds(30));var count=new AtomicInteger();
        PlanningReadPort reads=new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> definition,PlanningReadRequest input) {
                assertSame(actual,definition);assertSame(request,input);assertEquals(1,count.incrementAndGet());assertEquals(actual.operation().value(),definition.prepare(input,"software-root-read").step());
                var packet=packet();var guard=new GuardEvidence(input.before(),input.source(),input.sessionId(),bound.connectionGeneration(),definition.operation(),source,source,bound.authorityId(),now,now.plusSeconds(30));
                var held=new PlanningReadGuard(guard,true,true,true,"b".repeat(64));byte[] raw=StrictJson.canonical(packet,SwayNativeWire.MAX);
                var ack=new NativeActionPort.AckReceived("software-root-read",true,Optional.of(new RawJson(StrictJson.canonical(packet.get("result")))),new RawJson(raw),framed(raw));
                var original=new PlanningReadReceipt(input,definition.contractId(),ack.requestId(),held,held,ack);
                return new PlanningReadResult.Known<>(definition.decode(original),original,new ExactRef("software:archived-read",1,"c".repeat(64)));
            }
        };
        var view=SwaySharedRoot.finance(actual,reads);assertSame(actual,view.actualContract());assertEquals(FinanceReadContracts.ROOT_CONTRACT_ID,view.contractId());
        assertEquals(FinanceReadContracts.RootCapture.PUBLIC_QUERY,FinanceReadContracts.rootCapture(view.arguments()));
        PlanningReadPort directContextPort=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> definition,PlanningReadRequest input){throw new AssertionError("Sway must use the single finance canonical ROOT port");}};
        var result=view.read(directContextPort,request);if(!(result instanceof PlanningReadResult.Known<OpportunityJson.Obj> known))throw new AssertionError("actual typed ROOT result required");
        assertEquals(OrdinarySwayReadSource.originalResult(known.receipt()),known.value());assertEquals(1,count.get());
        assertEquals(new OpportunityJson.Text("unavailable"),known.value().get("status"));
        var empty=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),request.operation(),new OpportunityJson.Obj(java.util.Map.of()),request.deadline());
        assertThrows(IllegalArgumentException.class,()->actual.prepare(empty,"software-root-read"),"old empty request cannot alias ROOT/v2");
        var internal=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),request.operation(),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS),request.deadline());
        var receipt=known.receipt();var notPublic=new PlanningReadReceipt(internal,receipt.contractId(),receipt.requestId(),receipt.before(),receipt.after(),receipt.original());
        assertThrows(IllegalArgumentException.class,()->SwaySharedRoot.requirePublicCapture(notPublic),"preclock originals cannot stand in for ordinary current public capture");
    }
    private static ObjectNode packet() {
        var packet=StrictJson.object();packet.put("type","command_result");packet.put("protocol_version",1);packet.put("request_id","software-root-read");packet.put("ok",true);
        var result=packet.putObject("result");result.put("step",OrdinarySwayReadSource.ROOT.value());result.put("accepted",true);result.put("status","unavailable");result.put("query_sequence",1);result.put("snapshot_revision",7);result.put("backend_id","native-headless");
        var root=result.putObject("campaign_root_context");root.put("schema_version",1);root.put("status","unavailable");root.put("snapshot_revision",7);root.put("date_raw",53220000);root.put("unavailable_reason","map_not_ready");root.put("native_selected_game_rule_token_count",0);root.putArray("selected_game_rule_tokens");
        for(String field:List.of("capital_province_id","government","immediate_liege_character_id","independent","local_player_id","player_character_alive","player_character_id","primary_title","top_liege_character_id"))root.putNull(field);
        var ready=root.putObject("readiness");for(String field:List.of("capital_ready","government_ready","lieges_ready","player_identity_ready","primary_title_ready","ready","same_frame_ready","selected_game_rule_tokens_ready"))ready.put(field,false);
        var provenance=root.putObject("provenance");provenance.put("game_version",SwayNativeWire.BUILD);provenance.put("executable_sha256",SwayNativeWire.EXE);provenance.put("backend_id","ck3-1.20.0.4-native-campaign-root-context-v1");
        provenance.put("primary_title_rva","0x289DA10");provenance.put("capital_province_rva","0x28B1CB0");provenance.put("immediate_liege_rva","0x28BFC50");provenance.put("top_liege_rva","0x28BFD80");provenance.put("government_rva","0x28C2DF0");provenance.put("selected_game_rule_service_slot_rva","0x5CB3D78");return packet;
    }
    private static byte[] framed(byte[] body){return java.nio.ByteBuffer.allocate(body.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();}
}
