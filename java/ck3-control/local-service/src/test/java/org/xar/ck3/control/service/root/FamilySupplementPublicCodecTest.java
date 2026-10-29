package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.FamilySupplementPublicCodec.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class FamilySupplementPublicCodecTest {
    @Test void selectorsPreserveMissingNullAndFullUint32ThroughRealNativeRequestAndPublicSerde() {
        Obligations missing=FamilySupplementPublicCodec.decodeObligations(raw("{\"expected_revision\":172,\"enumerate_current_allies\":true}"));
        Obligations nullable=FamilySupplementPublicCodec.decodeObligations(raw("{\"expected_revision\":\"172\",\"subject_character_id\":null,\"candidate_character_id\":null,\"ally_character_id\":4294967295}"));
        assertEquals(Presence.MISSING,missing.subject().presence());assertEquals(Presence.NULL,nullable.subject().presence());
        assertEquals(4294967295L,nullable.nativeRequest().ally().getAsLong());assertTrue(nullable.nativeRequest().pair().isEmpty());
        assertEquals(missing,FamilySupplementPublicCodec.decodeObligations(FamilySupplementPublicCodec.encodeRequest(missing)));
        assertEquals(nullable,FamilySupplementPublicCodec.decodeObligations(FamilySupplementPublicCodec.encodeRequest(nullable)));
        var pair=FamilySupplementPublicCodec.decodeObligations(raw("{\"expected_revision\":172,\"subject_character_id\":4294967295,\"candidate_character_id\":2,\"request_matrilineal_option\":true}"));
        var canonical=org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligationsQueries.arguments(pair.nativeRequest());
        assertEquals(BigInteger.valueOf(4294967295L),OpportunityJson.toNode(canonical).get("subject_character_id").bigIntegerValue());
    }
    @Test void requiredRevisionsArePositiveExactDualDomainWhileChildIdsRetainSignedInt32() {
        var max=FamilySupplementPublicCodec.decodeTreatment(raw("{\"expected_revision\":\"18446744073709551615\"}"));
        assertEquals(StrictJson.UINT64_MAX,max.expectedRevision());
        assertEquals(max,FamilySupplementPublicCodec.decodeTreatment(FamilySupplementPublicCodec.encodeRequest(max)));
        for(String number:List.of("0","null","true","1.0","9007199254740992","\"01\"","\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class,()->FamilySupplementPublicCodec.decodeTreatment(raw("{\"expected_revision\":"+number+"}")));
        var subject=FamilySupplementPublicCodec.decodeSubject(raw("{\"expected_native_revision\":171,\"subject_character_id\":2147483647,\"diagnose_family_arrays\":true}"));
        assertEquals(subject,FamilySupplementPublicCodec.decodeSubject(FamilySupplementPublicCodec.encodeRequest(subject)));
        assertThrows(IllegalArgumentException.class,()->FamilySupplementPublicCodec.decodeSubject(raw("{\"expected_native_revision\":171,\"subject_character_id\":2147483648}")));
        assertThrows(IllegalArgumentException.class,()->FamilySupplementPublicCodec.decodeSubject(raw("{\"expected_native_revision\":171,\"subject_character_id\":2,\"diagnose_family_arrays\":null}")));
    }
    @Test void incompletePairUnknownFieldAndWrongOptionalSelectorTypesAreRefused() {
        for(String row:List.of("{\"expected_revision\":1}","{\"expected_revision\":1,\"subject_character_id\":2}",
                "{\"expected_revision\":1,\"subject_character_id\":2,\"candidate_character_id\":2}",
                "{\"expected_revision\":1,\"ally_character_id\":true}","{\"expected_revision\":1,\"ally_character_id\":2.0}",
                "{\"expected_revision\":1,\"ally_character_id\":2,\"action_id\":\"forged\"}"))
            assertThrows(IllegalArgumentException.class,()->FamilySupplementPublicCodec.decodeObligations(raw(row)));
        assertThrows(IllegalArgumentException.class,()->FamilySupplementPublicCodec.decodeValue(raw("{\"legality\":null,\"candidate_character_id\":2}")));
        assertThrows(IllegalArgumentException.class,()->FamilySupplementPublicCodec.decodeTreatment(raw("null")));
    }
    @Test void nativeLegalityPublicWideFieldsRoundTripWithoutChangingBoundedRolesOrDiagnostics() {
        ObjectNode original=legality();original.putArray("native_legal_candidates").addObject().put("candidate_character_id",8).put("recipient_ai_accept_raw",Long.MIN_VALUE);
        original.put("definition_stable_hash",4294967295L);var value=new ChildValue(obj(original),8,true);
        RawJson encoded=FamilySupplementPublicCodec.encodeRequest(value);JsonNode publicValue=StrictJson.parse(encoded.bytes());
        assertEquals("18446744073709551615",publicValue.get("legality").get("query_sequence").textValue());
        assertTrue(publicValue.get("legality").get("subject_character_id").isIntegralNumber());
        assertTrue(publicValue.get("legality").get("definition_stable_hash").isIntegralNumber());
        assertEquals(Long.toString(Long.MIN_VALUE),publicValue.get("legality").get("native_legal_candidates").get(0).get("recipient_ai_accept_raw").textValue());
        assertEquals(-1,publicValue.get("legality").get("diagnostic_character_id").intValue());
        assertEquals(value,FamilySupplementPublicCodec.decodeValue(encoded));
    }
    @Test void allFourTypedDirectBindingsActuallyDecodeInvokeAndEncodeTheirOwnRequest()throws Exception {
        var source=new ExactRef("controlled/public-family-reads",1,"a".repeat(64));int[] calls={0};
        var bindings=RootFamilySupplementReadPublicProducts.bindings(source,request->{calls[0]++;return FamilySupplementPublicCodec.encodeRequest(request);});
        assertEquals(Set.copyOf(RootFamilySupplementReadPublicProducts.NAMES),bindings.stream().map(McpExecutableDirectory.DirectBinding::name).collect(java.util.stream.Collectors.toSet()));
        for(var binding:bindings) {
            RawJson input=switch(binding.name()) {
                case RootFamilySupplementReadPublicProducts.OBLIGATIONS->raw("{\"expected_revision\":172,\"enumerate_current_allies\":true}");
                case RootFamilySupplementReadPublicProducts.SUBJECT->raw("{\"expected_native_revision\":171,\"subject_character_id\":3}");
                case RootFamilySupplementReadPublicProducts.VALUE->FamilySupplementPublicCodec.encodeRequest(new ChildValue(obj(legality()),8,false));
                case RootFamilySupplementReadPublicProducts.TREATMENT->raw("{\"expected_revision\":172}");
                default->throw new AssertionError();
            };
            invoke(binding,input);assertEquals(PublicMcpBindings.Kind.DRIVER_DIRECT,binding.kind());
        }
        assertEquals(4,calls[0]);
        var broken=RootFamilySupplementReadPublicProducts.bindings(source,request->{throw new IllegalArgumentException("actual native unavailable");});
        assertThrows(IllegalArgumentException.class,()->invoke(broken.getLast(),raw("{\"expected_revision\":172}")));
    }
    private static <Q,R> PublicMcpDirectory.CallResult invoke(McpExecutableDirectory.DirectBinding<Q,R> binding,RawJson input)throws Exception {
        var call=new PublicMcpDirectory.ToolCall(binding.name(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(input)),Optional.empty(),new McpCancellation());
        return binding.encoder().encode(binding.actual().invoke(binding.decoder().decode(call)));
    }
    private static ObjectNode legality() {
        return StrictJson.object().put("schema","xar.ck3.player-child-marriage-subject.v1").put("status","available")
                .put("player_child_verified",true).put("read_only",true).put("advertised",false)
                .put("query_sequence",StrictJson.UINT64_MAX).put("native_revision",171).put("subject_character_id",3).put("diagnostic_character_id",-1);
    }
    private static OpportunityJson.Obj obj(JsonNode node){return org.xar.ck3.control.application.driver.DriverJson.object(StrictJson.canonical(node),1048576);}
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
}

