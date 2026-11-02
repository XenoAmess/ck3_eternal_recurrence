package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.council.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure packet/selected-DATA regression. No live writer, endpoint, permit, Game or settlement authority. */
final class CouncilPrimitive285Test {
    private static final Instant T=Instant.parse("2026-10-23T22:35:00Z");
    private static final String BUILD="AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final String ID="controlled-original285";
    private static final ExactRef REF=new ExactRef("synthetic-policy-regression-not-live-qualified",1,"a".repeat(64));
    private record Scene(ActionCommand command,GuardEvidence guard,NativeRequest prepared) { }

    @Test void identical45458IntegerHasDifferentJacksonRepresentationWithoutNumericCoercion() {
        var request=new CouncilActionCodec.Request(ID,new CouncilModels.Frame("native:110",BigInteger.valueOf(110),BigInteger.valueOf(110),53146896,31254),CouncilModels.Position.STEWARD,45458,OptionalInt.empty());
        var typed=CouncilActionCodec.wireFields(request,true);
        var parsed=StrictJson.parse("{\"candidate_character_id\":45458}".getBytes(StandardCharsets.UTF_8));
        assertTrue(typed.get("candidate_character_id").isIntegralNumber());assertTrue(parsed.get("candidate_character_id").isIntegralNumber());
        assertNotEquals(typed.get("candidate_character_id").getClass(),parsed.get("candidate_character_id").getClass());
        assertNotEquals(typed,parsed);assertArrayEquals(StrictJson.canonical(typed),StrictJson.canonical(parsed));
        assertEquals(parsed,StrictJson.parse(StrictJson.canonical(typed)));
    }

    @Test void completeRealPreparerAndWireProducerRetainStrictSelectedPrimitive() throws Exception {
        Scene s=scene();var expected=GovernanceActionPreparation.councilRequest(s.command(),ID);
        assertEquals(16777232,expected.candidateId());
        byte[] outbound=NativeWire.execute(ID,CouncilActionCodec.PRIVATE_ASSIGN,BigInteger.valueOf(13),s.prepared().additionalFields().bytes());
        var ack=ack(ID,outbound,true,"pending");
        var attempt=new ActionState.Attempt(ID,T.plusSeconds(1),s.guard(),s.prepared());
        assertDoesNotThrow(()->CouncilContinuationPolicy.requireOriginalPending(s.command(),attempt,ack));
        assertTrue(CouncilContinuationPolicy.isPending(CouncilContinuationPolicy.result(ack),CouncilActionCodec.PRIVATE_ASSIGN));
        // This is only permission to examine original pending continuation, never applied/settled/receipt proof.
        assertEquals("pending",CouncilContinuationPolicy.result(ack).get("status").textValue());
    }

    @Test void changedCandidateAndAllEnvelopeTypeOrIdentityDriftRemainRejected() throws Exception {
        Scene s=scene();String good=new String(s.prepared().additionalFields().bytes(),StandardCharsets.UTF_8);
        int checked=0;
        for(String variant:List.of("candidate","both-candidate","float","string","boolean","missing","extra","id","step","revision","snapshot","negative-ack","idle")) {
            String fields=switch(variant) {
                case "candidate","both-candidate" -> "{\"candidate_character_id\":16777233}";
                case "float" -> "{\"candidate_character_id\":16777232.0}";
                case "string" -> "{\"candidate_character_id\":\"16777232\"}";
                case "boolean" -> "{\"candidate_character_id\":true}";
                case "missing" -> "{}";
                case "extra" -> "{\"candidate_character_id\":16777232,\"extra\":1}";
                default -> good;
            };
            String wireId=variant.equals("id")?"another-original":ID;
            String step=variant.equals("step")?"private-query-assign-councillor-receipt-v1":CouncilActionCodec.PRIVATE_ASSIGN;
            String revision=variant.equals("revision")?"14":"13";
            String extra=variant.equals("snapshot")?",\"expected_snapshot_revision\":13":"";
            String wire="{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\""+wireId+"\",\"step\":\""+step+"\",\"expected_revision\":"+revision+extra+(fields.equals("{}")?"":","+fields.substring(1,fields.length()-1))+"}";
            byte[] outbound=NativeWire.packet(wire.getBytes(StandardCharsets.UTF_8));
            var original=ack(ID,outbound,!variant.equals("negative-ack"),variant.equals("idle")?"idle":"pending");
            NativeRequest prepared=variant.equals("both-candidate")?new NativeRequest(CouncilActionCodec.PRIVATE_ASSIGN,Optional.empty(),new RawJson(fields.getBytes(StandardCharsets.UTF_8))):s.prepared();
            var attempt=new ActionState.Attempt(ID,T.plusSeconds(1),s.guard(),prepared);
            assertThrows(Exception.class,()->CouncilContinuationPolicy.requireOriginalPending(s.command(),attempt,original),variant);checked++;
        }
        assertEquals(13,checked);
    }

    private static ObjectNode fixture(String name)throws Exception {
        String root=System.getProperty("xar.repository.root");assertNotNull(root);
        return (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(root,"ck3_autonomous_player/tests/fixtures/native_12002/governance/"+name+".json")));
    }
    private static Scene scene()throws Exception {
        var available=((ObjectNode)fixture("council-private-query-available").get("result")).deepCopy();
        var gates=((ObjectNode)fixture("council-gates").get("result").get("council_final_gates")).deepCopy();
        gates.set("council_composition_candidates",available.get("council_composition_candidates"));
        available.put("step",CouncilPrivateCodec.GATES);available.remove("council_composition_candidates");available.set("council_final_gates",gates);
        var terminal=(CouncilPrivateCodec.Terminal)CouncilPrivateCodec.decodeReply(StrictJson.canonical(available),CouncilPrivateCodec.STATUS);
        var nativeFrame=new CouncilModels.Frame("native:13",BigInteger.valueOf(13),BigInteger.valueOf(13),53175816,16777217);
        var publicFrame=new CouncilModels.Frame("public:900",BigInteger.valueOf(900),BigInteger.valueOf(13),53175816,16777217);
        var normalized=CouncilPrivateCodec.normalize(terminal,CouncilPrivateCodec.GATES,nativeFrame,publicFrame,CouncilModels.Position.STEWARD,"1.20.0.2",BUILD);
        var tree=(ObjectNode)StrictJson.parse(normalized.bytes());
        var candidates=CouncilCodec.decode(StrictJson.canonical(tree.get("council_composition_candidates")),nativeFrame,CouncilModels.Position.STEWARD);
        var source=new G2Source("fixture-machine",T.toString(),"controlled-policy-only",REF);
        var before=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
            new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(16777217),BigInteger.valueOf(13),BigInteger.valueOf(53175816)),"public:900",BigInteger.valueOf(900),"controlled-policy-episode"),1);
        var args=new OpportunityJson.Obj(Map.of()).with("position_key",new OpportunityJson.Text("councillor_steward"))
            .with("candidate_character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(16777232)))
            .with("original_query",OpportunityJson.parse(normalized.bytes()))
            .with("expected_has_incumbent",new OpportunityJson.Bool(candidates.seat().incumbentId().isPresent()))
            .with("expected_incumbent_character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(candidates.seat().incumbentId().orElse(-1))));
        var operation=new OperationKey(CouncilActionCodec.PRIVATE_ASSIGN);
        var post=new ProposalLifecycle.ExpectedPostcondition(1,before,source,"controlled-policy/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
        var command=new ActionCommand("controlled-policy285",before,source,"controlled-session",operation,args,post,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),T.plusSeconds(30));
        var expected=GovernanceActionPreparation.councilRequest(command,ID);
        var prepared=new NativeRequest(operation.value(),Optional.empty(),new RawJson(StrictJson.canonical(CouncilActionCodec.wireFields(expected,true))));
        var guard=new GuardEvidence(before,source,command.sessionId(),BigInteger.ONE,operation,REF,REF,"software-only",T,T.plusSeconds(30));
        return new Scene(command,guard,prepared);
    }
    private static NativeActionPort.AckReceived ack(String id,byte[] outbound,boolean ok,String status)throws Exception {
        var result=StrictJson.object().put("private_council_transport",true).put("advertised",false).put("step",CouncilActionCodec.PRIVATE_ASSIGN).put("status",status);
        var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",ok);frame.set("result",result);
        byte[] body=StrictJson.canonical(frame),packet=NativeWire.packet(body);
        return new NativeActionPort.AckReceived(id,ok,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(body),packet,Optional.of(new NativeActionPort.OutboundPacket(id,outbound)),Optional.empty());
    }
}
