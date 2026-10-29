package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.family.*;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual retained native fixture -> shared producer -> public typed Driver handler and serializer. No private Root is constructed. */
final class FamilyTreatmentPublicConsumerTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef REF=new ExactRef("controlled/public-treatment",1,"a".repeat(64));
    @Test void retainedNativePresenceAbsenceAndUnavailableFlowThroughRealContractAndPublicHandler()throws Exception {
        String root=System.getProperty("xar.repository.root");assertNotNull(root,"required complete-CI repository root");
        for(String name:List.of("present","absent","definition-unavailable")) {
            Path file=Path.of(root).resolve("ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_epidemic_treatment_mailbox/"+name+".json");
            JsonNode original=StrictJson.parse(Files.readAllBytes(file),1048576);
            var receipt=receipt(original.get("result"));var contract=EpidemicTreatmentPresenceQueries.contract(REF,request->{});
            var actual=contract.replay(receipt);
            var bindings=RootFamilySupplementReadPublicProducts.bindings(REF,request->{
                assertInstanceOf(FamilySupplementPublicCodec.Treatment.class,request);
                return FamilySupplementPublicCodec.publicResult(actual);
            });
            var binding=bindings.stream().filter(row->row.name().equals(RootFamilySupplementReadPublicProducts.TREATMENT)).findFirst().orElseThrow();
            var response=invoke(binding);JsonNode output=StrictJson.parse(response.bytes(),1048576);
            JsonNode body=output.has("structuredContent")?output.get("structuredContent"):output;
            assertEquals("123",body.get("snapshot_revision").textValue());assertEquals("56",body.get("queried_revision").textValue());
            assertTrue(body.get("player_epidemic_treatment_presence").get("played_character_id").isIntegralNumber());
            assertEquals(original.get("result").get("player_epidemic_treatment_presence").get("present"),
                    body.get("player_epidemic_treatment_presence").get("present"));
            assertEquals("duration_abi_not_verified",body.get("player_epidemic_treatment_presence").get("remaining_days").get("unavailable_reason").textValue());
            assertEquals(actual,contract.decode(receipt));
        }
    }
    private static <Q,R> RawJson invoke(McpExecutableDirectory.DirectBinding<Q,R> binding)throws Exception {
        var request=new RawJson("{\"expected_revision\":56}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var call=new PublicMcpDirectory.ToolCall(binding.name(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(request)),Optional.empty(),new McpCancellation());
        return new RawJson(binding.encoder().encode(binding.actual().invoke(binding.decoder().decode(call))).bytes());
    }
    private static PlanningReadReceipt receipt(JsonNode nativeResult) throws java.io.IOException {
        var source=new G2Source("controlled-treatment-public",NOW.toString(),FamilyObligations.Build.CURRENT4.exactBuild(),REF);
        var nativeFrame=new JointBudgetSelector.Frame(BigInteger.valueOf(50331652),BigInteger.valueOf(123),BigInteger.valueOf(53350560));
        var proposal=new JointBudgetSelector.ProposalFrame(nativeFrame,"native:123",BigInteger.valueOf(56),"controlled-treatment-episode");
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),proposal,1);
        var request=new PlanningReadRequest(identity,source,"controlled-treatment-session",new OperationKey(EpidemicTreatmentPresenceQueries.STEP),
                EpidemicTreatmentPresenceQueries.arguments(BigInteger.valueOf(56)),NOW.plusSeconds(30));
        ObjectNode packet=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","controlled-treatment").put("ok",true);packet.set("result",nativeResult);
        RawJson raw=new RawJson(StrictJson.canonical(packet));var ack=new NativeActionPort.AckReceived("controlled-treatment",true,
                Optional.of(new RawJson(StrictJson.canonical(nativeResult))),raw,NativeWire.packet(raw.bytes()));
        var evidence=new GuardEvidence(identity,source,request.sessionId(),BigInteger.TWO,request.operation(),REF,REF,"controlled-treatment-data",NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(evidence,true,true,true,"1".repeat(64));
        return new PlanningReadReceipt(request,EpidemicTreatmentPresenceQueries.CONTRACT_ID,"controlled-treatment",guard,guard,ack);
    }
}

