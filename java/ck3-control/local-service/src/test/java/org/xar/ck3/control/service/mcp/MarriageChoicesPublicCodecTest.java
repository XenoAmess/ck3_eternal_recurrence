package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageChoicesProjection;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Original native producer -> retained typed receipt -> public encoder; fixtures confer no live Game authority. */
final class MarriageChoicesPublicCodecTest {
    private static final BigInteger U64=new BigInteger("18446744073709551615");
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    @Test void missingNullAndProvidedRevisionKeepSeparateTypesThroughSerialization() {
        var missing=MarriageChoicesPublicCodec.decode(new PublicBindings.Missing());
        assertInstanceOf(MarriageChoicesPublicCodec.MissingRevision.class,missing.expectedRevision());
        assertEquals(missing,decode("{}"));
        var nullable=decode("{\"expected_revision\":null}");
        assertInstanceOf(MarriageChoicesPublicCodec.NullRevision.class,nullable.expectedRevision());
        for(var request:List.of(missing,nullable,decode("{\"expected_revision\":0}"),decode("{\"expected_revision\":\"18446744073709551615\"}")))
            assertEquals(request,MarriageChoicesPublicCodec.decode(PublicBindings.present(MarriageChoicesPublicCodec.encodeRequest(request))));
        assertNotEquals(missing,nullable);assertEquals(McpJson.object(McpJson.parse(McpJson.utf8("{}"))),McpJson.parse(MarriageChoicesPublicCodec.encodeRequest(missing).bytes()));
        assertDoesNotThrow(()->missing.requireCurrent(BigInteger.ONE));assertDoesNotThrow(()->nullable.requireCurrent(BigInteger.ONE));
        var zero=decode("{\"expected_revision\":0}");
        assertThrows(IllegalArgumentException.class,()->zero.requireCurrent(BigInteger.ONE));
        assertDoesNotThrow(()->decode("{\"expected_revision\":\"18446744073709551615\"}").requireCurrent(U64));
    }
    @Test void revisionBoundaryRefusesWrongTypesUnsafeNumbersAliasesAndNoncanonicalDecimals() {
        for(String invalid:List.of("null","[]","{\"expected_revision\":true}","{\"expected_revision\":1.0}",
                "{\"expected_revision\":-1}","{\"expected_revision\":9007199254740992}","{\"expected_revision\":\"00\"}",
                "{\"expected_revision\":\"+1\"}","{\"expected_revision\":\"-1\"}","{\"expected_revision\":\"1.0\"}",
                "{\"expected_revision\":\"18446744073709551616\"}","{\"expectedRevision\":1}","{\"expected_revision\":1,\"expected_revision\":1}"))
            assertThrows(IllegalArgumentException.class,()->decode(invalid),invalid);
        assertEquals(decode("{\"expected_revision\":9007199254740991}"),decode("{\"expected_revision\":\"9007199254740991\"}"));
    }
    @Test void completeOriginalProducerSurvivesPublicSerializationWithoutLosingRevisionRolesOrDiagnostics() {
        var original=known(packet());var response=new MarriageChoicesPublicCodec.Response(original);
        JsonNode encoded=McpJson.parse(MarriageChoicesPublicCodec.encode(response).bytes());
        assertEquals(U64.toString(),encoded.get("query_sequence").textValue());
        assertEquals(U64.toString(),encoded.get("queried_revision").textValue());
        assertEquals("7",encoded.get("queried_native_revision").textValue());
        assertEquals("native:7",encoded.get("queried_snapshot_id").textValue());
        var choice=encoded.get("arrange_marriage_choices").get(0);
        assertEquals("101-2147483647",choice.get("choice_id").textValue());
        assertTrue(choice.get("played_character_id").isIntegralNumber());assertEquals(101,choice.get("played_character_id").intValue());
        assertTrue(choice.get("candidate_character_id").isIntegralNumber());assertEquals(Integer.MAX_VALUE,choice.get("candidate_character_id").intValue());
        var diagnostic=encoded.get("arrange_marriage_diagnostics");
        assertTrue(diagnostic.get("storage_capacity").isIntegralNumber());
        assertTrue(diagnostic.get("validation_false_samples").get(0).get("actor_character_id").isIntegralNumber());
        assertEquals(Integer.MIN_VALUE,diagnostic.get("validation_false_samples").get(0).get("actor_character_id").intValue());
        assertTrue(diagnostic.get("validation_false_samples").get(0).get("intermediary_character_id").isIntegralNumber());
        assertEquals(-1,diagnostic.get("validation_false_samples").get(0).get("intermediary_character_id").intValue());
        assertEquals(response.original(),original);assertTrue(McpJson.parse(original.receipt().original().originalResultToken().orElseThrow().bytes()).get("query_sequence").isIntegralNumber());
        assertArrayEquals(MarriageChoicesPublicCodec.encode(response).bytes(),MarriageChoicesPublicCodec.encode(response).bytes());
        assertEquals(encoded,McpJson.parse(raw(encoded).bytes()));
    }
    @Test void actualEmptyListIsRetainedAndMissingNullOrIncompleteReadsAreUnavailable() {
        var empty=packet();empty.putArray("arrange_marriage_choices");
        assertTrue(McpJson.parse(MarriageChoicesPublicCodec.encode(new MarriageChoicesPublicCodec.Response(known(empty))).bytes()).get("arrange_marriage_choices").isEmpty());
        var missing=packet();missing.remove("arrange_marriage_choices");reject(missing);
        var nullable=packet();nullable.putNull("arrange_marriage_choices");reject(nullable);
        var partial=packet();((ObjectNode)partial.get("arrange_marriage_diagnostics")).put("slots_scanned",1);reject(partial);
        var unavailable=packet();unavailable.put("status","unavailable");reject(unavailable);
    }
    @Test void publicEncoderDoesNotBypassOriginalProducerRoleAndPacketValidation() {
        var wrong=packet();choice(wrong).put("candidate_character_id",true);reject(wrong);
        wrong=packet();choice(wrong).put("candidate_character_id",202.0);reject(wrong);
        wrong=packet();choice(wrong).put("candidate_character_id",2147483648L);reject(wrong);
        wrong=packet();choice(wrong).put("played_character_id",102);reject(wrong);
        wrong=packet();choice(wrong).put("choice_id","101-202");reject(wrong);
        wrong=packet();((ObjectNode)wrong.get("arrange_marriage_diagnostics").get("validation_false_samples").get(0)).putNull("intermediary_character_id");reject(wrong);
        var original=known(packet());var changed=new MarriageChoices(original.value().frame(),List.of(new MarriageChoice("101-202",101,202)));
        assertThrows(IllegalArgumentException.class,()->new MarriageChoicesPublicCodec.Response(new PlanningReadResult.Known<>(changed,original.receipt(),original.originalReceipt())));
        var frame=McpJson.object(McpJson.parse(original.receipt().original().originalFrame().bytes()));frame.put("request_id","another-read");
        var ack=new NativeActionPort.AckReceived(original.receipt().requestId(),true,original.receipt().original().originalResultToken(),raw(frame),raw(frame).bytes());
        var receipt=new PlanningReadReceipt(original.receipt().request(),original.receipt().contractId(),original.receipt().requestId(),original.receipt().before(),original.receipt().after(),ack);
        assertThrows(IllegalArgumentException.class,()->new MarriageChoicesPublicCodec.Response(new PlanningReadResult.Known<>(original.value(),receipt,original.originalReceipt())));
    }
    private static Context context() {
        var source=new G2Source("synthetic-public-marriage-machine",NOW.toString(),"1.20.0.4",new ExactRef("synthetic/source",1,"a".repeat(64)));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(7),BigInteger.valueOf(53146848)),"native:7",U64,"synthetic-episode");
        return new Context(new ObservationIdentity(source.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1),
                source,"synthetic-public-marriage-session",BigInteger.TWO,Build.CROZIER4,NOW.plusSeconds(30),new ControlFrame(true,true,true,1,19L,101,"synthetic-episode",false,null,null,List.of()));
    }
    private static PlanningReadResult.Known<MarriageChoices> known(ObjectNode nativeResult) {
        var context=context();var operation=new OperationKey(FamilyMarriageChoicesProjection.STEP);
        var request=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),operation,FamilyMarriageChoicesProjection.applicationArguments(context),context.deadline());
        var evidence=new ExactRef("synthetic/read-native",1,"b".repeat(64));var capabilities=new ExactRef("synthetic/capabilities",1,"c".repeat(64));
        var binding=new GuardEvidence(context.before(),context.source(),context.sessionId(),context.connectionGeneration(),operation,evidence,capabilities,"synthetic-marriage-authority",NOW,context.deadline());
        var guard=new PlanningReadGuard(binding,true,true,true,"d".repeat(64));
        var frame=McpJson.object(McpJson.parse(McpJson.utf8("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"synthetic-marriage-read\",\"ok\":true}")));
        frame.set("result",nativeResult);var ack=new NativeActionPort.AckReceived("synthetic-marriage-read",true,Optional.of(raw(nativeResult)),raw(frame),raw(frame).bytes());
        var receipt=new PlanningReadReceipt(request,"interactions:marriage-choices","synthetic-marriage-read",guard,guard,ack);
        return new PlanningReadResult.Known<>(FamilyMarriageChoicesProjection.decode(receipt).typed(),receipt,new ExactRef("synthetic/retained-read",1,"e".repeat(64)));
    }
    private static ObjectNode packet() {
        var packet=McpJson.object(McpJson.parse(McpJson.utf8("{\"step\":\"query-arrange-marriage-choices\",\"accepted\":true,\"status\":\"available\"}")));
        packet.put("query_sequence",U64);packet.putArray("arrange_marriage_choices").addObject().put("choice_id","101-2147483647").put("played_character_id",101).put("candidate_character_id",Integer.MAX_VALUE);
        var diagnostic=packet.putObject("arrange_marriage_diagnostics").put("storage_capacity",2).put("slots_scanned",2).put("empty_slots",0).put("live_candidates",2)
                .put("dead_candidates",0).put("self_candidates",0).put("generation_mismatch_candidates",0).put("contexts_constructed",2).put("context_construct_failures",0).put("native_validate_true",1).put("native_validate_false",1);
        diagnostic.putArray("validation_false_samples").addObject().put("slot_index",1).put("candidate_character_id",303).put("actor_character_id",Integer.MIN_VALUE).put("recipient_character_id",303)
                .put("secondary_actor_character_id",101).put("secondary_recipient_character_id",303).put("intermediary_character_id",-1);
        return packet;
    }
    private static MarriageChoicesPublicCodec.Request decode(String json) {return MarriageChoicesPublicCodec.decode(PublicBindings.present(new RawJson(McpJson.utf8(json))));}
    private static RawJson raw(JsonNode value) {return new RawJson(McpJson.utf8(value.toString()));}
    private static ObjectNode choice(ObjectNode packet) {return (ObjectNode)packet.get("arrange_marriage_choices").get(0);}
    private static void reject(ObjectNode packet) {assertThrows(IllegalArgumentException.class,()->new MarriageChoicesPublicCodec.Response(known(packet)));}
}
