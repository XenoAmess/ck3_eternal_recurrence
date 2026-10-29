package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicCodec;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract;
import org.xar.ck3.control.nativebridge.capabilities.interactions.TitleClaimsPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionTitleSelectorReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTransportPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;

/** Mandatory actual SDK metadata, then each sole owner DATA codec. No current Root, native
 * availability, readback custody, permissions or business success is fabricated by these tests. */
final class PublicExpandedDescriptorConsumersTest {
    private static final String MAX="18446744073709551615";
    private static final List<String> POSITIVE=List.of("1","9007199254740991","\""+MAX+"\"");
    private static final List<String> NONNEGATIVE=List.of("0","9007199254740991","\""+MAX+"\"");

    @Test void sixCareerDescriptorsReachTheActualOwnerCodecWithoutWideningCharacterIds()throws Exception {
        for(var kind:ChinaCareerContract.Kind.values()) {
            var descriptor=descriptor(kind.publicName());
            for(String revision:NONNEGATIVE) {
                var input=StrictJson.object().put("request_nonce","schema-1");input.set("expected_revision",token(revision));
                if(kind.ownerArgument())input.put("owner_character_id",11);
                if(kind.subjectArgument())input.put("subject_character_id",12);
                descriptor.validateArguments(arguments(input));
                var typed=ChinaCareerCodec.decodeRequest(kind,raw(input));var encoded=ChinaCareerCodec.encodeRequest(typed);
                descriptor.validateArguments(arguments(node(encoded)));assertEquals(typed,ChinaCareerCodec.decodeRequest(kind,encoded));
                if(kind.ownerArgument())assertTrue(node(encoded).get("owner_character_id").isIntegralNumber());
                invalid(descriptor,input,"expected_revision",value->ChinaCareerCodec.decodeRequest(kind,value));
            }
        }
    }

    @Test void elevenChinaCasesDescriptorsPreserveOptionalRevisionAndFiveScoreboardWidths()throws Exception {
        for(var method:ChinaCasesContract.Method.values()) {
            var descriptor=descriptor(method.publicName());
            if(!method.readOnly()) {
                var input=StrictJson.object().put("request_nonce","schema-1")
                        .put("action",org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesActions.ScoreboardAction.values()[0].wire())
                        .put("expected_player_character_id",11).put("expected_provider_session_id","A".repeat(32))
                        .put("expected_tree_fingerprint_v1","A".repeat(64)).put("expected_semantic_fingerprint_v1","B".repeat(64))
                        .put("expected_window_instance_pointer","0xA").put("expected_target_instance_pointer","0xB").put("expected_target_vtable_pointer","0xC");
                for(String field:List.of("expected_revision","expected_native_revision","expected_connection_generation","expected_observation_sequence","expected_observed_state_revision"))input.put(field,MAX);
                descriptor.validateArguments(arguments(input));var typed=ChinaCasesCodec.decodeAction(input);
                var encoded=ChinaCasesCodec.encodeActionRequest(typed);descriptor.validateArguments(arguments(encoded));assertEquals(typed,ChinaCasesCodec.decodeAction(encoded));
                for(String field:List.of("expected_revision","expected_native_revision","expected_connection_generation","expected_observation_sequence","expected_observed_state_revision"))invalid(descriptor,input,field,value->ChinaCasesCodec.decodeAction(node(value)));
                assertTrue(encoded.get("expected_player_character_id").isIntegralNumber());continue;
            }
            var input=StrictJson.object().put("request_nonce","schema-1").put("expected_revision",MAX);
            switch(method) {
                case CASE->input.put("case_kind","zhongguo.b1.performance");
                case AI_OWNED->input.put("owner_character_id",11).put("subject_character_id",12);
                case RESULT,PIP,PROJECTS->input.put("owner_character_id",11);
                case INCIDENT->input.put("owner_character_id",11).put("profile","x");
                default->{ }
            }
            descriptor.validateArguments(arguments(input));var typed=ChinaCasesCodec.decodeRead(method,input);
            var encoded=ChinaCasesCodec.encodeReadRequest(typed);descriptor.validateArguments(arguments(encoded));assertEquals(typed,ChinaCasesCodec.decodeRead(method,encoded));
            if(method==ChinaCasesContract.Method.AI_OWNED) {
                for(boolean explicitNull:List.of(false,true)) {
                    var optional=input.deepCopy();optional.remove("expected_revision");if(explicitNull)optional.putNull("expected_revision");
                    descriptor.validateArguments(arguments(optional));var parsed=ChinaCasesCodec.decodeRead(method,optional);
                    var roundtrip=ChinaCasesCodec.encodeReadRequest(parsed);assertEquals(explicitNull,roundtrip.has("expected_revision"));
                    if(explicitNull)assertTrue(roundtrip.get("expected_revision").isNull());
                    assertEquals(parsed,ChinaCasesCodec.decodeRead(method,roundtrip));
                }
            } else invalid(descriptor,input,"expected_revision",value->ChinaCasesCodec.decodeRead(method,node(value)));
        }
    }

    @Test void allFiftyFiveReligionRevisionDescriptorsReachTheirOriginalTypedRequestContracts()throws Exception {
        int checked=0;
        for(var method:ReligionCodec.methods()) {
            if(!method.fields().contains(ReligionContract.Field.EXPECTED_REVISION))continue;
            var input=StrictJson.object();
            for(var field:method.required())input.set(field.wire(),religionArgument(field));
            if(method.name().equals("ck3_query_player_epidemic_recovery_private_v1"))input.put("requested_title_id",1);
            input.put("expected_revision",MAX);var descriptor=descriptor(method.name());descriptor.validateArguments(arguments(input));
            var typed=ReligionCodec.decode(method.name(),raw(input));var encoded=ReligionCodec.encode(typed);
            descriptor.validateArguments(arguments(node(encoded)));assertEquals(typed,ReligionCodec.decode(method.name(),encoded));
            invalid(descriptor,input,"expected_revision",value->ReligionCodec.decode(method.name(),value));checked++;
        }
        assertEquals(55,checked);
    }
    private static JsonNode religionArgument(ReligionContract.Field field) {
        return switch(field) {
            case EXPECTED_REVISION->token("\""+MAX+"\"");
            case ACTION->token("\"adopt\"");case OPERATION->token("\"open\"");
            case EXPECTED_PREVIEW_IDENTITY_SHA256->token("\""+"a".repeat(64)+"\"");
            case ACTION_ID,REQUEST_ID,SUBMITTED_REQUEST_ID,TYPE_KEY,CK3_BUILD,DOCTRINE_KEY,TENET_KEY,OPTION_KEY->token("\"schema-1\"");
            case REPLACE_EXISTING_TASK,INCLUDE_KNOWLEDGE_CATALOGUE,POLICY_POSITIVE->token("false");
            case FAITH_FULL_IDS->token("[1]");default->token("1");
        };
    }

    @Test void fiveGiftDescriptorsPreserveTheSignedUnboundedReservePolicyInsteadOfClippingToUint64()throws Exception {
        for(var method:FactionGiftPublicContract.Method.values()) {
            var input=StrictJson.object().put("expected_revision",MAX);
            switch(method) {
                case CANDIDATE->input.putObject("same_frame_root");
                case SEND->{input.putObject("candidate");input.putObject("checkpoint");}
                case RECEIPT,COLD_RECOVERY->input.putObject("pending");
                case RESOLVED->input.put("request_id","schema-1");
            }
            var descriptor=descriptor(method.originalName());descriptor.validateArguments(arguments(input));
            var typed=FactionGiftPublicCodec.decode(method,raw(input));var encoded=FactionGiftPublicCodec.encode(typed);
            descriptor.validateArguments(arguments(node(encoded)));assertEquals(typed,FactionGiftPublicCodec.decode(method,encoded));
            invalid(descriptor,input,"expected_revision",value->FactionGiftPublicCodec.decode(method,value));
            if(method!=FactionGiftPublicContract.Method.CANDIDATE)continue;
            for(String reserve:List.of("-9007199254740991","0","\"9223372036854775808\"","\"-"+"9".repeat(4300)+"\"","\""+"9".repeat(4300)+"\"")) {
                var wide=input.deepCopy();wide.set("minimum_gold_reserve_raw",token(reserve));descriptor.validateArguments(arguments(wide));
                var actual=FactionGiftPublicCodec.decode(method,raw(wide));var actualEncoded=FactionGiftPublicCodec.encode(actual);
                descriptor.validateArguments(arguments(node(actualEncoded)));assertEquals(actual,FactionGiftPublicCodec.decode(method,actualEncoded));
            }
            for(String bad:List.of("null","true","1.0","9007199254740992","\"-0\"","\"01\"","\"+1\"","\""+"9".repeat(4301)+"\"")) {
                var wrong=input.deepCopy();wrong.set("minimum_gold_reserve_raw",token(bad));
                assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(wrong)));
                assertThrows(IllegalArgumentException.class,()->FactionGiftPublicCodec.decode(method,raw(wrong)));
            }
        }
    }

    @Test void privateGovernanceMetadataLeavesLawBudgetActionSemanticErrorPriorityToItsSoleCodec()throws Exception {
        for(String name:List.of("ck3_query_council_composition_candidates_private_v1","ck3_query_council_final_gates_private_v1","ck3_assign_councillor_private_v1",
                "ck3_query_council_assign_receipt_private_v1","ck3_query_realm_law_final_terms_private_v1","ck3_query_realm_law_crown_action_private_v1",
                "ck3_query_realm_law_crown_receipt_private_v1","ck3_query_government_runtime_adapter_private_v1")) {
            var input=StrictJson.object().put("expected_revision",MAX);
            if(name.equals("ck3_assign_councillor_private_v1")){input.putObject("query");input.put("candidate_character_id",11);}
            if(name.equals("ck3_query_council_assign_receipt_private_v1"))input.putObject("pending");
            if(name.equals("ck3_query_realm_law_crown_receipt_private_v1"))input.put("submitted_request_id","schema-1");
            var descriptor=descriptor(name);descriptor.validateArguments(arguments(input));var encoded=governanceRoundtrip(name,raw(input));
            descriptor.validateArguments(arguments(node(encoded)));assertEquals(node(encoded),node(governanceRoundtrip(name,encoded)));
            invalid(descriptor,input,"expected_revision",value->governanceRoundtrip(name,value));
        }
        var descriptor=descriptor("ck3_enact_realm_law_crown_private_v1");
        var input=StrictJson.object().put("law_key","crown_authority_1").put("action_id","schema-1");input.putObject("readback");input.putObject("budgets").put("gold","9223372036854775807");
        descriptor.validateArguments(arguments(input));var typed=DriverGovernancePublicCodec.enact(raw(input));
        var encoded=DriverGovernancePublicCodec.encode(typed);descriptor.validateArguments(arguments(node(encoded)));assertEquals(typed,DriverGovernancePublicCodec.enact(encoded));
        input.putObject("budgets");descriptor.validateArguments(arguments(input));assertTrue(DriverGovernancePublicCodec.enact(raw(input)).budgets().isEmpty());
        var badLaw=input.deepCopy().put("law_key","bad");badLaw.putObject("budgets").put("unknown_currency","1");descriptor.validateArguments(arguments(badLaw));
        var first=assertThrows(PublicServiceFailure.class,()->DriverGovernancePublicCodec.enact(raw(badLaw)));
        assertEquals(PublicServiceFailure.Kind.VALUE_ERROR,first.kind());assertEquals("law_key must identify a crown-authority candidate",first.getMessage());
        var badBudget=input.deepCopy();badBudget.putObject("budgets").put("gold","-1");descriptor.validateArguments(arguments(badBudget));
        assertEquals("budgets must contain supported nonnegative raw currency limits",assertThrows(PublicServiceFailure.class,()->DriverGovernancePublicCodec.enact(raw(badBudget))).getMessage());
    }
    private static RawJson governanceRoundtrip(String name,RawJson raw) {
        if(name.equals("ck3_query_council_composition_candidates_private_v1"))return DriverGovernancePublicCodec.encode(DriverGovernancePublicCodec.council(raw));
        if(name.equals("ck3_assign_councillor_private_v1"))return DriverGovernancePublicCodec.encode(DriverGovernancePublicCodec.assign(raw));
        if(name.equals("ck3_query_council_assign_receipt_private_v1"))return DriverGovernancePublicCodec.encode(DriverGovernancePublicCodec.councilReceipt(raw));
        if(name.equals("ck3_query_realm_law_crown_receipt_private_v1"))return DriverGovernancePublicCodec.encode(DriverGovernancePublicCodec.crownReceipt(raw));
        return DriverGovernancePublicCodec.encode(DriverGovernancePublicCodec.revision(raw));
    }

    @Test void familySubjectUsesNativeRevisionWhileTheOtherTwoReadsUsePublicRevision()throws Exception {
        for(String name:List.of("ck3_query_player_child_marriage_subject_private_v1","ck3_query_family_obligations_private_v1","ck3_query_player_epidemic_treatment_presence_private_v1")) {
            boolean subject=name.contains("child_marriage_subject");String field=subject?"expected_native_revision":"expected_revision";
            var descriptor=descriptor(name);var input=StrictJson.object().put(field,MAX);if(subject)input.put("subject_character_id",11);
            descriptor.validateArguments(arguments(input));var encoded=familyRoundtrip(name,raw(input));descriptor.validateArguments(arguments(node(encoded)));
            assertEquals(node(encoded),node(familyRoundtrip(name,encoded)));invalid(descriptor,input,field,value->familyRoundtrip(name,value));
            if(subject)assertTrue(node(encoded).get("subject_character_id").isIntegralNumber());
        }
        var opaque=original("ck3_query_player_child_marriage_value_private_v1");assertSame(opaque,RootPublicCatalogCodec.executableTool(opaque));
    }
    private static RawJson familyRoundtrip(String name,RawJson raw) {
        if(name.contains("child_marriage_subject"))return FamilySupplementPublicCodec.encodeRequest(FamilySupplementPublicCodec.decodeSubject(raw));
        if(name.contains("epidemic"))return FamilySupplementPublicCodec.encodeRequest(FamilySupplementPublicCodec.decodeTreatment(raw));
        return FamilySupplementPublicCodec.encodeRequest(FamilySupplementPublicCodec.decodeObligations(raw));
    }

    @Test void fourTitleQueriesKeepBoundedNumericSelectorsAndCanonicalRevision()throws Exception {
        for(var kind:InteractionTitleSelectorReads.Kind.values()) {
            String name=switch(kind){case LAWS->"ck3_query_title_own_laws_v1";case CLAIMS->"ck3_query_player_claims_v1";case HOLDER->"ck3_query_title_holder_v1";case APPOINTMENT->"ck3_query_current_title_appointment_v1";};
            var descriptor=descriptor(name);var input=StrictJson.object().put("expected_revision",MAX);
            if(kind==InteractionTitleSelectorReads.Kind.CLAIMS)input.putArray("title_ids").add(1);
            else if(kind!=InteractionTitleSelectorReads.Kind.APPOINTMENT)input.put("title_id",1);
            descriptor.validateArguments(arguments(input));var typed=TitleClaimsPublicCodec.decode(kind,raw(input));var encoded=TitleClaimsPublicCodec.encode(typed);
            descriptor.validateArguments(arguments(node(encoded)));assertEquals(typed,TitleClaimsPublicCodec.decode(kind,encoded));
            invalid(descriptor,input,"expected_revision",value->TitleClaimsPublicCodec.decode(kind,value));
        }
    }

    @Test void originalNormalExitV2MetadataAlreadyRequiresStringsAndNeverGainsNumericAliases()throws Exception {
        for(String name:List.of("ck3_query_normal_exit_context_v1","ck3_request_normal_exit_v1")) {
            var original=original(name);assertSame(original,RootPublicCatalogCodec.executableTool(original));
            var input=StrictJson.object().put("expected_revision",MAX);boolean request=name.equals("ck3_request_normal_exit_v1");
            if(request)input.put("action","prepare_confirmation").put("expected_exit_context_signature","a".repeat(64));
            original.validateArguments(arguments(input));RawJson encoded=request?NormalExitPublicCodec.encodeRequest(NormalExitPublicCodec.decodeRequest(PublicBindings.present(raw(input))))
                    :NormalExitPublicCodec.encodeQuery(NormalExitPublicCodec.decodeQuery(PublicBindings.present(raw(input))));
            original.validateArguments(arguments(node(encoded)));input.put("expected_revision",1);
            assertThrows(IllegalArgumentException.class,()->original.validateArguments(arguments(input)));
            assertThrows(IllegalArgumentException.class,()->{if(request)NormalExitPublicCodec.decodeRequest(PublicBindings.present(raw(input)));else NormalExitPublicCodec.decodeQuery(PublicBindings.present(raw(input)));});
        }
    }

    @Test void fiveArmyTransportDescriptorsReachTheSoleRequestCodecAndPreserveSamplingPresence()throws Exception {
        for(String name:List.of("ck3_set_army_observer_research_sampling_v1","ck3_query_army_observer_research_sampling_v1",
                "ck3_set_army_private_auto_scalar_ab_v1","ck3_query_army_private_auto_scalar_ab_v1","ck3_compare_army_private_auto_scalar_ab_v1")) {
            var descriptor=descriptor(name);
            for(String revision:POSITIVE) {
                var input=StrictJson.object();input.set("expected_revision",token(revision));
                if(name.contains("observer_research"))input.put("observer_family","all");
                if(name.startsWith("ck3_set_army_observer"))input.put("enabled",true);
                if(name.startsWith("ck3_set_army_private"))input.put("mode","compare");
                descriptor.validateArguments(arguments(input));var encoded=transportRoundtrip(name,raw(input));
                descriptor.validateArguments(arguments(node(encoded)));assertEquals(node(encoded),node(transportRoundtrip(name,encoded)));
                invalid(descriptor,input,"expected_revision",value->transportRoundtrip(name,value));
                if(name.startsWith("ck3_set_army_observer")) {
                    assertFalse(node(encoded).has("regular_core_full_carmy_ids"));
                    var explicitNull=input.deepCopy().putNull("regular_core_full_carmy_ids");descriptor.validateArguments(arguments(explicitNull));
                    assertTrue(node(transportRoundtrip(name,raw(explicitNull))).get("regular_core_full_carmy_ids").isNull());
                }
            }
        }
    }
    private static RawJson transportRoundtrip(String name,RawJson input) {
        if(name.startsWith("ck3_set_army_observer"))return ArmyTransportPublicCodec.encode(ArmyTransportPublicCodec.samplingSet(input));
        if(name.contains("observer_research"))return ArmyTransportPublicCodec.encode(ArmyTransportPublicCodec.samplingQuery(input));
        if(name.startsWith("ck3_set_army_private"))return ArmyTransportPublicCodec.encode(ArmyTransportPublicCodec.scalarSet(input));
        return ArmyTransportPublicCodec.encode(ArmyTransportPublicCodec.revision(input));
    }

    private static void invalid(ToolDescriptor descriptor,ObjectNode input,String field,Function<RawJson,?> consumer) {
        for(String bad:List.of("true","1.0","9007199254740992","\"01\"","\"+1\"","\"18446744073709551616\"","null")) {
            var wrong=input.deepCopy();wrong.set(field,token(bad));assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(wrong)));
            assertThrows(IllegalArgumentException.class,()->consumer.apply(raw(wrong)));
        }
        var missing=input.deepCopy();missing.remove(field);assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(missing)));
        assertThrows(IllegalArgumentException.class,()->consumer.apply(raw(missing)));
    }
    private static ToolDescriptor original(String name)throws Exception {return RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst().orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));}
    private static ToolDescriptor descriptor(String name)throws Exception {return RootPublicCatalogCodec.executableTool(original(name));}
    private static JsonNode token(String json){return StrictJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static ObjectNode node(RawJson raw){return PublicDataJson.object(raw);}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static PublicMcpDirectory.Arguments arguments(JsonNode value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,java.util.Optional.of(raw(value)));}
}
