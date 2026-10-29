package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** Real pinned original consumer differential and strict integer/presence/readiness/round-trip regressions. */
final class BattleContextCodecsTest {
    @TempDir Path temporary;
    private int sequence;
    private static final String PYTHON="""
        import hashlib,json,sys
        from pathlib import Path
        root=Path(sys.argv[1]); source=root/'ck3_autonomous_player/src/xar_autoplayer/bridge'
        for name,sha in [('battle_context_source_inputs_contract.py','aef31456253ca7fd5160dfd73d244bc929c4284e621ca3a638eef38515a9d245'),
                         ('battle_context_admissions_v86_contract.py','996131b53fac8acf58895c6aa7e0133cdb6bf3b4e347f7a8c5fb6fdc42167fef'),
                         ('battle_task_position_context_contract.py','15dea34e3e0ecdb8c8122d624e16f85a90675a1f9fd6ccca01e6cb03d95e5eb6')]:
          if hashlib.sha256((source/name).read_bytes()).hexdigest()!=sha: raise RuntimeError('original context source drift: '+name)
        sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
        from xar_autoplayer.bridge.battle_task_position_context_contract import normalize_current_context_task_position_inputs
        normalize=normalize_current_context_source_inputs if sys.argv[2]=='source' else normalize_current_context_task_position_inputs
        print(json.dumps(normalize(json.load(sys.stdin)),sort_keys=True,ensure_ascii=False,separators=(',',':')))
        """;
    private static ObjectNode parsed(String json) { return (ObjectNode)StrictJson.parse(json.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode source() { return parsed("{\"status\":\"partial\",\"ready\":false,\"character_id\":29829,\"branch_291e210\":null,\"reason\":\"independent-source-unobserved\"}"); }
    private static ObjectNode pc() { return parsed("{\"keys_count\":0,\"values_count\":null,\"keys_u16\":null,\"values_q64\":null,\"reason\":null}"); }
    private static ObjectNode pre() { return parsed("{\"status\":\"available\",\"ready\":true,\"character_id\":29829,\"army_selection\":\"native_fallback\",\"army_key_f4_raw\":null,\"army_field_120_raw\":0,\"army_field_124_raw\":null,\"second_selection\":\"native_fallback\",\"second_field_174_raw\":0,\"admitted\":true,\"property_block\":null,\"unavailable_reason\":null}"); }
    private static ObjectNode branchB() { return parsed("{\"status\":\"available\",\"ready\":true,\"base_inputs_ready\":true,\"component_present\":false,\"selected_source\":\"\",\"source_count\":0,\"source_rows\":null,\"conditional_a_fallback_properties\":null,\"government_token_count\":null,\"government_token_ids_i32\":null,\"government_source\":\"\",\"condition_registry_guard\":null,\"condition_fallback_guard\":null,\"token_manager_present\":null,\"reason\":null}"); }
    private static ObjectNode taskBranch() { return parsed("{\"status\":\"available\",\"complete_no_contribution\":true,\"vectors_ready\":true,\"evaluated_rows\":[],\"prefix_before\":null,\"prefix_source\":\"unobserved\",\"aggregate_properties_after\":null,\"aggregate_source\":\"unobserved\",\"unavailable_reason\":null}"); }
    private static ObjectNode taskSource() {
        ObjectNode root=parsed("{\"schema_version\":1,\"status\":\"available\",\"character_id\":29829,\"raw_task_inputs_ready\":true,\"branch_vectors_ready\":true,\"owner_council_present\":false,\"ordered_owned_tasks\":[],\"councillor_task_link_present\":false,\"councillor_task\":null,\"owned_passive\":null,\"councillor_position_task\":null,\"unavailable_reason\":null}");
        root.set("owned_passive",taskBranch());root.set("councillor_position_task",taskBranch());return root;
    }
    private static ObjectNode branchA() {
        ObjectNode root=parsed("{\"status\":\"available\",\"ready\":true,\"component_present\":false,\"first_relation_resolution\":null,\"second_relation_resolution\":null,\"house_resolution\":null,\"house_extra_enabled\":false,\"selected_lifestyle_span\":null,\"selected_dynasty_span\":null,\"selected_house_span\":null,\"selected_house_extra_span\":null,\"definition_blocks\":[],\"reason\":null}");
        for(String key:List.of("first_relation_resolution","second_relation_resolution","house_resolution"))root.set(key,parsed("{\"status\":\"observed\",\"requested_full_id\":4294967295,\"selected_full_id\":0,\"reason\":null}"));
        for(String key:List.of("selected_lifestyle_span","selected_dynasty_span","selected_house_span","selected_house_extra_span"))root.set(key,parsed("{\"selected_source\":\"native-static\",\"count\":0,\"rows\":null,\"reason\":null}"));
        return root;
    }
    private static ObjectNode post() {
        return parsed("""
            {"status":"available","ready":true,"character_id":29829,"unavailable_reason":null,
             "guarded630":{"status":"available","ready":true,"carrier_1b0_present":false,"carrier280_present":null,
               "selection":"native_fallback5D1E308","selected_field38_raw":0,"character68_signed":null,"threshold_signed":null,
               "admitted":false,"property_block":null,"unavailable_reason":null},
             "carrier40":{"status":"available","ready":true,"carrier_1b0_present":false,"carrier288_present":null,
               "admitted":false,"property_block":null,"unavailable_reason":null},
             "ordered_d8":{"status":"available","ready":true,"carrier_1c0_present":false,"header_selection":"inline_static54E7270",
               "source_array_present":false,"source_count_raw":0,"occurrences":[],"unavailable_reason":null}}
            """);
    }
    @Test void missingNullAndEmptyArePreservedAndWrongTokensAreRejected() {
        assertTrue(BattleContextSourceCodec.normalize(NullNode.instance,"source").isNull());
        ObjectNode root=source();JsonNode first=BattleContextSourceCodec.normalize(root,"source");assertFalse(first.has("branch_291d7e0"));
        root.putNull("branch_291d7e0");assertTrue(BattleContextSourceCodec.normalize(root,"source").has("branch_291d7e0"));
        root.putNull("unrecognized_field");assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(root,"source"));
        for(JsonNode value:List.of(BooleanNode.TRUE,DecimalNode.valueOf(new BigDecimal("29829.0")),BigIntegerNode.valueOf(BigInteger.ONE.shiftLeft(31)))) {
            ObjectNode bad=source();bad.set("character_id",value);assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(bad,"source"));
        }
        ObjectNode missing=source();missing.remove("ready");assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(missing,"source"));
    }
    @Test void prePredicateKeepsSignedDwordAndZeroKeyShortcutWithoutUndemandedOperands() {
        ObjectNode root=source(),branch=pre();branch.set("property_block",pc());root.set("pre_291e210_1640",branch);
        JsonNode normalized=BattleContextSourceCodec.normalize(root,"source");assertTrue(normalized.get("pre_291e210_1640").get("ready").booleanValue());
        ObjectNode mismatch=branch.deepCopy();mismatch.put("character_id",29830);root.set("pre_291e210_1640",mismatch);assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(root,"source"));
        ObjectNode early=branch.deepCopy();early.put("army_field_120_raw",-1);early.put("admitted",false);early.putNull("army_field_124_raw");early.putNull("second_selection");early.putNull("second_field_174_raw");early.putNull("property_block");
        root.set("pre_291e210_1640",early);BattleContextSourceCodec.normalize(root,"source");
        early.put("second_field_174_raw",0);assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(root,"source"));
        ObjectNode signed=branch.deepCopy();signed.put("army_field_120_raw",Integer.MIN_VALUE);signed.put("second_field_174_raw",Integer.MIN_VALUE);root.set("pre_291e210_1640",signed);
        assertEquals(BigInteger.valueOf(Integer.MIN_VALUE),BattleContextSourceCodec.normalize(root,"source").get("pre_291e210_1640").get("army_field_120_raw").bigIntegerValue());
    }
    @Test void sourceArrayHeadersStayIndependentAndNativeOrderIsRequired() {
        ObjectNode root=source(),branch=branchB();root.set("branch_291d7e0",branch);
        BattleContextSourceCodec.normalize(root,"source");
        ObjectNode row=parsed("{\"native_index\":0,\"source_identity\":\"source:0\",\"base_properties\":null,\"auxiliary_410_provenance\":\"\",\"auxiliary_retained_identity\":null,\"auxiliary_retained_present\":null,\"auxiliary_tag_u32\":4294967295,\"conditional_a_count\":0,\"conditional_b_count\":0,\"conditional_c_count\":0,\"conditional_a_rows\":[],\"conditional_b_rows\":[],\"conditional_c_rows\":[],\"reason\":null}");
        ObjectNode properties=pc();properties.put("values_count",1);properties.putArray("keys_u16");properties.putArray("values_q64").add(BigInteger.valueOf(Long.MIN_VALUE));row.set("base_properties",properties);
        branch.put("source_count",1);branch.putArray("source_rows").add(row);BattleContextSourceCodec.normalize(root,"source");
        row.put("native_index",1);assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(root,"source"));row.put("native_index",0);
        properties.putArray("values_q64");assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(root,"source"));
    }
    @Test void v86PreservesPartialSelectorObservationsAndClassifiedReadiness() {
        ObjectNode root=source(),branch=branchB();root.set("branch_291d7e0",branch);
        branch.put("selector_a_selected_source","");branch.putArray("selector_a_key_identities").add("");
        branch.putArray("selector_b_nested_keys").add(parsed("{\"native_index\":null,\"count\":3,\"keys_i32\":[null,-2147483648],\"reason\":\"\"}"));
        JsonNode normalized=BattleContextSourceCodec.normalize(root,"source");assertTrue(normalized.get("branch_291d7e0").get("selector_b_nested_keys").get(0).get("keys_i32").get(0).isNull());
        ObjectNode locale=parsed("{\"status\":\"available\",\"ready\":true,\"first_signed_byte\":-1,\"locale_max_multibyte\":null,\"result_i32\":0,\"crt_index\":4294967295,\"thread_locale_flags\":null,\"flags_mask\":null,\"thread_state_present\":null,\"current_locale_present\":null,\"global_locale_present\":null,\"selected_locale_present\":null,\"cached_value_api_status\":\"\",\"thread_state_source\":\"\",\"locale_source\":\"\",\"table_element_u16\":65535,\"reason\":null}");
        BattleContextAdmissionsV86Codec.normalizeLocale(locale,"locale");locale.putNull("result_i32");assertThrows(IllegalArgumentException.class,()->BattleContextAdmissionsV86Codec.normalizeLocale(locale,"locale"));
    }
    @Test void weightedSpansRequireAllFourNativeHeadersAndDistinctDefinitions() {
        ObjectNode source=source(),branch=branchA();source.set("branch_291e210",branch);BattleContextSourceCodec.normalize(source,"source");
        ObjectNode span=(ObjectNode)branch.get("selected_lifestyle_span");span.put("count",1);span.putArray("rows").add(parsed("{\"native_index\":0,\"definition_identity\":\"native:definition\",\"weight_q64\":-9223372036854775808}"));
        ObjectNode definition=parsed("{\"definition_identity\":\"native:definition\",\"properties\":null}");definition.set("properties",pc());((ArrayNode)branch.get("definition_blocks")).add(definition);
        BattleContextSourceCodec.normalize(source,"source");((ArrayNode)branch.get("definition_blocks")).add(definition.deepCopy());assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(source,"source"));
        ((ArrayNode)branch.get("definition_blocks")).remove(1);branch.putNull("selected_house_extra_span");assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(source,"source"));
    }
    @Test void conditionalCRequiresActualGovernmentOperandsAndPreservesUnsignedCapacity() {
        ObjectNode source=source(),branch=branchB();source.set("branch_291d7e0",branch);branch.put("source_count",1);branch.put("government_token_count",0);branch.putArray("government_token_ids_i32");
        ObjectNode row=parsed("{\"native_index\":0,\"source_identity\":\"native:source\",\"base_properties\":{\"keys_count\":0,\"values_count\":0,\"keys_u16\":[],\"values_q64\":[],\"reason\":null},\"auxiliary_410_provenance\":\"\",\"auxiliary_retained_identity\":null,\"auxiliary_retained_present\":false,\"auxiliary_tag_u32\":null,\"conditional_a_count\":0,\"conditional_b_count\":0,\"conditional_c_count\":1,\"conditional_a_rows\":[],\"conditional_b_rows\":[],\"conditional_c_rows\":[],\"reason\":null}");
        ObjectNode condition=parsed("{\"native_index\":0,\"source_key_u32\":4294967295,\"masked_index_u32\":0,\"resolver_count_i32\":0,\"selected_native_fallback\":true,\"invert_u8\":255,\"property_block\":null,\"resolved_condition_identity\":null,\"condition_source\":\"\",\"condition_length\":0,\"condition_capacity\":18446744073709551615,\"condition_bytes\":[0,255],\"first_signed_byte\":null,\"classifier_mode_i32\":null,\"classifier_result_i32\":null,\"condition_token_id\":0,\"admitted\":false,\"token_origin\":\"\",\"lookup_status\":\"\",\"reason\":null,\"locale_classification\":null}");
        ((ArrayNode)row.get("conditional_c_rows")).add(condition);branch.putArray("source_rows").add(row);
        JsonNode normalized=BattleContextSourceCodec.normalize(source,"source");assertEquals(new BigInteger("18446744073709551615"),normalized.get("branch_291d7e0").get("source_rows").get(0).get("conditional_c_rows").get(0).get("condition_capacity").bigIntegerValue());
        condition.put("condition_capacity","18446744073709551615");assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(source,"source"));condition.put("condition_capacity",new BigInteger("18446744073709551615"));
        branch.putNull("government_token_ids_i32");assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(source,"source"));
    }
    @Test void postSourceGuardsKeepEarlyFalseAndDuplicateStoredOccurrences() {
        ObjectNode source=source(),post=post();source.set("post_291d7e0_sources",post);BattleContextSourceCodec.normalize(source,"source");
        ObjectNode guard=(ObjectNode)post.get("guarded630");guard.put("character68_signed",0);assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(source,"source"));guard.putNull("character68_signed");
        ObjectNode order=(ObjectNode)post.get("ordered_d8");order.put("source_count_raw",2);order.put("source_array_present",true);
        ArrayNode rows=order.putArray("occurrences");for(int index=0;index<2;index++) { ObjectNode row=parsed("{\"source_index\":0,\"source_identity\":\"same-native-pointer\",\"property_block\":null,\"unavailable_reason\":null}");row.put("source_index",index);row.set("property_block",pc());rows.add(row); }
        JsonNode normalized=BattleContextSourceCodec.normalize(source,"source");assertEquals(2,normalized.get("post_291d7e0_sources").get("ordered_d8").get("occurrences").size());
        order.putNull("occurrences");assertThrows(IllegalArgumentException.class,()->BattleContextSourceCodec.normalize(source,"source"));
    }
    @Test void taskVectorsDoNotInventCausalPrefixAndKeepOpaqueRaw64Exact() {
        ObjectNode source=taskSource();JsonNode normalized=BattleTaskPositionContextCodec.normalize(source,"task");assertTrue(normalized.get("owned_passive").get("prefix_before").isNull());
        ObjectNode branch=(ObjectNode)source.get("owned_passive");branch.put("complete_no_contribution",false);
        ObjectNode row=parsed("{\"task_native_index\":0,\"declaration_native_index\":-1,\"contributor_kind\":\"position_scoped\",\"scope_root_character_id_raw\":null,\"scope_saved_character_id_raw\":0,\"declaration_scale_q64\":-9223372036854775808,\"properties\":{\"count\":0,\"keys_u16\":[],\"values_q64\":[]},\"modifier_flags_raw\":18446744073709551615,\"source_provenance\":\"\"}");
        branch.putArray("evaluated_rows").add(row);normalized=BattleTaskPositionContextCodec.normalize(source,"task");
        assertEquals(new BigInteger("18446744073709551615"),normalized.get("owned_passive").get("evaluated_rows").get(0).get("modifier_flags_raw").bigIntegerValue());
        assertArrayEquals(StrictJson.canonical(normalized),StrictJson.canonical(BattleTaskPositionContextCodec.normalize(StrictJson.parse(StrictJson.canonical(normalized)),"task")));
        row.put("modifier_flags_raw",new BigInteger("18446744073709551616"));assertThrows(IllegalArgumentException.class,()->BattleTaskPositionContextCodec.normalize(source,"task"));
    }
    @Test void taskSchemaVersionsAndActualStageSourceAreStrict() {
        ObjectNode source=taskSource();source.set("schema_version",DecimalNode.valueOf(new BigDecimal("1.0")));assertThrows(IllegalArgumentException.class,()->BattleTaskPositionContextCodec.normalize(source,"task"));
        source.put("schema_version",1);((ObjectNode)source.get("owned_passive")).put("prefix_source","actual_before_291ded0");assertThrows(IllegalArgumentException.class,()->BattleTaskPositionContextCodec.normalize(source,"task"));
        ((ObjectNode)source.get("owned_passive")).put("prefix_source","unobserved");source.putNull("ordered_owned_tasks");assertThrows(IllegalArgumentException.class,()->BattleTaskPositionContextCodec.normalize(source,"task"));
    }
    @Test void actualPinnedOriginalNormalizersMatchJavaOutputForNativeDomainFixtures() throws Exception {
        ObjectNode original=source(),pre=pre();pre.set("property_block",pc());original.set("pre_291e210_1640",pre);original.set("branch_291d7e0",branchB());
        original.set("branch_291e210",branchA());original.set("post_291d7e0_sources",post());
        for(ObjectNode value:List.of(source(),original))assertArrayEquals(StrictJson.canonical(python("source",value)),StrictJson.canonical(BattleContextSourceCodec.normalize(value,"source")));
        assertArrayEquals(StrictJson.canonical(python("task",taskSource())),StrictJson.canonical(BattleTaskPositionContextCodec.normalize(taskSource(),"task")));
    }
    @Test void actualNativeSourceAndV86ProducerExecutablesFeedTheRealJavaAndOriginalConsumers() throws Exception {
        for(String fixture:List.of("xar.battle.context.source.fixture","xar.battle.context.admissions.fixture")) {
            Path executable=Path.of(required(fixture));String expected=required(fixture+".sha256");
            if(!executable.isAbsolute() || !expected.matches("[a-f0-9]{64}"))throw new IllegalStateException("NOT EXECUTED: qualified native fixture path/hash required");
            if(Files.size(executable)<1 || Files.size(executable)>64L*1024*1024)throw new IOException("actual native fixture exceeds the 64 MiB EXE identity read bound");
            String actual=java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(executable)));
            assertEquals(expected,actual,"actual native producer executable changed");
            int ordinal=++sequence;Path output=temporary.resolve("native-context-"+ordinal+".json"),error=temporary.resolve("native-context-"+ordinal+".stderr");
            Process process=new ProcessBuilder(executable.toString()).redirectOutput(output.toFile()).redirectError(error.toFile()).start();
            try {
                if(!process.waitFor(20,TimeUnit.SECONDS))throw new IOException("actual native context fixture timeout");
                if(process.exitValue()!=0)throw new IOException("actual native context fixture failed: "+Files.readString(error,StandardCharsets.UTF_8));
                if(Files.size(output)<1 || Files.size(output)>1_048_576)throw new IOException("actual native context stdout exceeds the 1 MiB JSON bound");
                JsonNode envelope=StrictJson.parse(Files.readAllBytes(output),1_048_576);assertTrue(envelope.get("lookup_abi_ok").booleanValue());
                JsonNode nativeSource=envelope.get("current_context_source_inputs");assertTrue(nativeSource.isObject());
                JsonNode java=BattleContextSourceCodec.normalize(nativeSource,"native-context");
                assertArrayEquals(StrictJson.canonical(python("source",nativeSource)),StrictJson.canonical(java));
                assertArrayEquals(StrictJson.canonical(java),StrictJson.canonical(BattleContextSourceCodec.normalize(StrictJson.parse(StrictJson.canonical(java)),"native-context")));
            } finally { process.destroyForcibly(); }
        }
    }
    private JsonNode python(String mode,JsonNode value) throws Exception {
        Path root=Path.of(required("xar.repository.root")),python=Path.of(required("xar.native.producer.python"));
        if(!root.isAbsolute() || !python.isAbsolute())throw new IllegalStateException("NOT EXECUTED: explicit original producer paths required");
        int ordinal=++sequence;Path output=temporary.resolve("context-"+ordinal+".json"),error=temporary.resolve("context-"+ordinal+".stderr");
        Process process=new ProcessBuilder(python.toString(),"-B","-X","utf8","-c",PYTHON,root.toString(),mode).redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        try {
            process.getOutputStream().write(StrictJson.canonical(value));process.getOutputStream().close();
            if(!process.waitFor(20,TimeUnit.SECONDS))throw new IOException("original context normalizer timeout");
            if(process.exitValue()!=0)throw new IOException("original context normalizer failed: "+Files.readString(error,StandardCharsets.UTF_8));
            return StrictJson.parse(Files.readAllBytes(output));
        } finally { process.destroyForcibly(); }
    }
    private static String required(String name) { String value=System.getProperty(name);if(value==null || value.isBlank())throw new IllegalStateException("NOT EXECUTED: missing original source fixture "+name);return value; }
}
