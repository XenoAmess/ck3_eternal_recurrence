package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.disembark.DisembarkCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyManagersModel.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.Stage;

/** Original Python producer differential and real Java registry/pipeline closure. Controlled frames grant no Game/writer credit. */
final class ArmyStrengthsManagersTest {
    private static final String SHA3="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    private static final String CORE="{\"status\":\"available\",\"army_id\":0,\"native_carmy_id\":0,\"scope_role\":\"player\",\"war_ids\":[],\"regiment_count\":0,\"current_soldiers\":0,\"maximum_soldiers\":0,\"ai_base_power_raw\":0,\"ai_base_power_scale\":100000,\"unavailable_reason\":null}";
    private static final String ORACLE="""
            import copy,hashlib,importlib,json,re,sys
            from pathlib import Path
            m=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
            def checkref(r):
                if type(r) is not dict or set(r)!={'path','bytes','sha256'}:raise RuntimeError('exact source/fixture FileRef required')
                b=Path(r['path']).read_bytes()
                if type(r['bytes']) is not int or len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('original manager source/fixture drift')
                return b
            for r in m['original_sources']:checkref(r)
            sys.path.insert(0,m['python_source_root']);sys.path.insert(0,m['python_test_root'])
            f=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
            if type(f) is not dict or set(f)!={'schema_version','machine_id','fixtures'} or type(f['schema_version']) is not int or f['schema_version']!=1 or type(f['machine_id']) is not str or f['machine_id']=='unknown' or re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',f['machine_id']) is None:raise RuntimeError('explicit source fixture machine and strict manifest required')
            modules={
             'PENDING':('army_pre_date_pending_update_contract','normalize_current_pre_date_pending_update_inputs_v1','army_pre_date_pending_update_12003','project_current_pre_date_pending_update_v1'),
             'DATED':('army_pre_date_dated_append_contract','normalize_current_pre_date_dated_append_inputs_v1','army_pre_date_dated_append_12003','project_pre_date_dated_append_12003'),
             'CHARACTER':('army_pre_date_character_prefix_contract','normalize_current_pre_date_character_prefix_inputs_v1','army_pre_date_character_prefix_12003','project_current_pre_date_character_prefix_v1'),
             'REFRESH':('army_current_post_admission_refresh_contract','normalize_current_post_admission_refresh_inputs_v1','army_current_post_admission_refresh_12003','project_current_post_admission_refresh_12003'),
             'CONDITION30':('army_current_condition30_inputs_contract','normalize_current_army_condition30_inputs_v1','army_current_condition30_inputs_12003','project_current_army_condition30_inputs_12003'),
             'FLAG20':('army_current_flag20_inputs_contract','normalize_current_army_flag20_inputs_v1','army_current_flag20_inputs_12003','project_current_army_flag20_inputs_12003'),
             'FLAG21':('army_current_flag21_inputs_contract','normalize_current_army_flag21_inputs_v1','army_current_flag21_inputs_12003','project_current_army_flag21_inputs_12003'),
             'HOLDER_RELATION':('army_current_selected_title_holder_owner_relation_contract','normalize_current_selected_title_holder_owner_relation_v1','army_current_selected_title_holder_owner_relation_12003','project_current_selected_title_holder_owner_relation_12003'),
             'FLAG31':('army_current_flag31_inputs_contract','normalize_current_army_flag31_inputs_v1','army_current_flag31_inputs_12003','project_current_army_flag31_inputs_12003')}
            keys={'PENDING':'current_pre_date_pending_update_inputs_v1','DATED':'current_pre_date_dated_append_inputs_v1','CHARACTER':'current_pre_date_character_prefix_inputs_v1','REFRESH':'current_post_admission_refresh_inputs_v1','CONDITION30':'current_army_condition30_inputs_v1','FLAG20':'current_army_flag20_inputs_v1','FLAG21':'current_army_flag21_inputs_v1','HOLDER_RELATION':'current_selected_title_holder_owner_relation_v1','FLAG31':'current_army_flag31_inputs_v1'}
            provenance={'snapshot_id':'controlled-manager-frame','revision':18446744073709551615,'native_revision':9007199254740993,'date_raw':10000,'game_version':'1.20.0.3','executable_sha256':'94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'}
            cases=[]
            def add(kind,raw,name,pending=None):
                normalizer=getattr(importlib.import_module('xar_autoplayer.bridge.'+modules[kind][0]),modules[kind][1]);projector=getattr(importlib.import_module('xar_autoplayer.simulation.'+modules[kind][2]),modules[kind][3])
                n=normalizer(copy.deepcopy(raw));row={keys[kind]:n}
                if kind=='PENDING':p=projector(row)
                elif kind=='CHARACTER':
                    from xar_autoplayer.simulation.army_pre_date_pending_update_12003 import project_current_pre_date_pending_update_v1
                    row['current_pre_date_pending_update_inputs_v1']=pending;p=projector(row)
                elif kind=='DATED':p=projector(n)
                else:p=projector(n,source_provenance=provenance)
                cases.append({'kind':kind,'name':name,'raw':raw,'normalized':n,'pending':pending,'projection':p})
            import pre_date_pending_update_fixture as pending
            for name,raw in [('existing',pending.source()),('empty',pending.source(mode='empty')),('collision-unobserved',pending.source(mode='collision')),('zero',pending.zero_source()),('missing',pending.missing_context_source()),('later-partial',pending.later_partial_source()),('combat-bypass',pending.bypass_source('combat')),('counter-bypass',pending.bypass_source('counter')),('all-arms',pending.source(branches=['current_zero','contract_nonzero','state_not_one','persistent_sentinel','war_magic_invalid','war_full_id_invalid','valid_war']))]:add('PENDING',raw,name)
            from daily_assault_roster_admission_fixture import state,references,fnv
            def physical(roster,threshold=0x3f800000):
                raw=pending.source(mode='empty',roster=tuple(roster));raw['pending_table_frame_v1']={**state(True),'schema_version':1,'entries_identity':'native:controlled-physical','entries_present':True,'data_is_native_empty_buffer':False,'map_count_raw_i32':0,'mask_raw_i32':7,'tail_raw_u8':4,'threshold_bits_u32':threshold,'physical_control_extent_last_slot_i64':12,'physical_controls_complete':True,'rehash_prefix_complete':True,'rehash_nonzero_records_observed_i32':0,'records':[{**state(True),'native_index':i,'physical_slot_i64':i,'control_raw_u8':255 if i==12 else 0,'stored_hash_raw_u32':None,'key_raw_full_id_u32':None,'vector_capacity_raw_i32':0,'vector_allocator_identity':'native:controlled-allocator','vector_allocator_matches_expected':True,'references':references([])} for i in range(13)]};return raw
            home={i:[k for k in range(1,500) if fnv(k)&7==i] for i in range(8)}
            for name,roster,threshold in [('physical-direct',[home[1][0]],0x3f800000),('physical-fast-shift',[home[1][0],home[2][0],home[1][1]],0x3f800000),('physical-carry',[home[1][0],home[2][0],home[3][0],home[1][1]],0x3f800000),('physical-growth',[home[1][0],home[2][0],home[3][0]],0x3e800000)]:add('PENDING',physical(roster,threshold),name)
            import pre_date_dated_append_fixture as dated
            for name,raw in [('ordered-repeats',dated.source()),('partial-date',dated.partial_date_source()),('missing-clock',dated.missing_clock_source())]:add('DATED',raw,name)
            wrap=dated.source();wrap['current_date_raw_i32']=2147483640;wrap['tomorrow_date_low_i32']=-2147483632
            from xar_autoplayer.simulation.army_pre_date_dated_append_12003 import project_pre_date_dated_append_12003
            p=project_pre_date_dated_append_12003(wrap)
            for r,d in zip(wrap['occurrences'],p['occurrences']):r.update(state(d['ready'],'controlled_wrapped_date_unavailable',partial=not d['ready']));r['date_scan_ready']=d['branch'] in {'first_due_date_append','all_dates_later_skip'}
            wrap.update(state(p['conditional_append_requests_ready'],'controlled_wrapped_date_unavailable',partial=not p['conditional_append_requests_ready']))
            add('DATED',wrap,'signed-wrap')
            import pre_date_character_prefix_fixture as character
            for name,pack in [('short-circuits',character.source_package()),('unavailable-verdict',character.unavailable_availability_package()),('unavailable-owner',character.unavailable_owner_package())]:add('CHARACTER',pack['prefix'],name,pack['pending'])
            import post_admission_refresh_source_builder as refresh
            for name,raw in [('independent-sums',refresh.post_admission_refresh_source()),('missing-demanded40',refresh.missing_demanded40_source()),('zero-unused-data',refresh.zero_count_unused_data_source()),('negative-count',refresh.negative_count_diagnostic_source())]:add('REFRESH',raw,name)
            expected={'CONDITION30','FLAG20','FLAG21','HOLDER_RELATION','FLAG31'}
            if type(f['fixtures']) is not list or {r['kind'] for r in f['fixtures']}!=expected or len(f['fixtures'])!=5:raise RuntimeError('all five genuine manager fixture roles required')
            loaders={'CONDITION30':('army_condition30_source_builder','load_compiled_condition30_wire'),'FLAG20':('army_flag20_compiled_wire_builder','load_compiled_flag20_wire'),'FLAG21':('army_flag21_compiled_wire_builder','load_compiled_flag21_wire'),'HOLDER_RELATION':('army_selected_title_holder_owner_relation_compiled_wire_builder','load_compiled_selected_title_holder_owner_relation_wire')}
            for r in f['fixtures']:
                if type(r) is not dict or set(r)!={'kind','container','source_ref'}:raise RuntimeError('fixture role schema')
                kind=r['kind'];b=checkref(r['source_ref']);wire=json.loads(b.decode('utf-8-sig'))
                if kind in loaders:
                    mod,fun=loaders[kind];checked=getattr(importlib.import_module(mod),fun)(r['source_ref']['path'])
                    if checked!=wire:raise RuntimeError('original fixture loader mismatch')
                names31={'source-zero-1d4-undemanded','active-combat-fullgen0-undemanded','inactive-combat-wrong-magic-rule24-true','inactive-combat-sentinel-rule24-false','null-stores-character-fallback-sentinel-rule24-false','missing-rule-evaluator-callable','missing-demanded-combat-magic'}
                if kind=='FLAG31' and (set(wire)!={'samples','qualification'} or set(wire['samples'])!=names31):raise RuntimeError('seven original current31 sample roles required')
                if r['container']!=('LEAF_SAMPLES_V1' if kind=='CONDITION30' else 'WHOLE_QUERY_SAMPLES_V1'):raise RuntimeError('whole query/leaf container must be explicit')
                for name,row in wire['samples'].items():add(kind,row if kind=='CONDITION30' else row[keys[kind]],'genuine-wire:'+name)
            # Controlled optional capsule exercises the actual optional decoder/consumer; this invents no capture evidence.
            pinbase=next(c for c in cases if c['kind']=='FLAG31' and any(r['inline_rule_identity'] is not None for r in c['raw']['occurrences']))
            pinned=copy.deepcopy(pinbase['raw'])
            for row in pinned['occurrences']:
                if row['inline_rule_identity'] is None:continue
                row['rule24_source_pins_v1']={'status':'available','unavailable_reason':'','schema_version':1,'source':'native_current_rule24_source_pins','pins_captured_ready':True,'provider_array_borrowed':True,'rule_receiver_identity':row['inline_rule_identity'],'rule_vtable_identity':'native:controlled-vtable','condition_mode_raw_u8':255,'vtable_read_ready':True,'mode_read_ready':True,'pin_requested_bytes_u32':33,'pin_captured_bytes_u32':33,'native_calls_executed':0,'native_writes_executed':0}
                for prefix in ('expected_scope','scope_mask','rule_evaluator'):row['rule24_source_pins_v1'].update({prefix+'_function_identity':'native:controlled-'+prefix,prefix+'_function_rva':None,prefix+'_pin_read_ready':True})
            add('FLAG31',pinned,'controlled-optional-borrowed-pins')
            # All null paths and version/unknown/missing/type mutations are compared against the actual original decoder.
            for kind in modules:add(kind,None,'explicit-null')
            invalid=[]
            for c in cases:
                if c['raw'] is None:continue
                normalizer=getattr(importlib.import_module('xar_autoplayer.bridge.'+modules[c['kind']][0]),modules[c['kind']][1])
                for mutation in ('unknown','missing','boolean-version','float-version','text-version','reason-null'):
                    bad=copy.deepcopy(c['raw'])
                    if mutation=='unknown':bad['unexpected_manager_field']=0
                    elif mutation=='missing':bad.pop('source')
                    elif mutation=='boolean-version':bad['schema_version']=True
                    elif mutation=='float-version':bad['schema_version']=1.0
                    elif mutation=='text-version':bad['schema_version']='1'
                    else:bad['unavailable_reason']=None
                    accepted=True
                    try:normalizer(bad)
                    except (ValueError,TypeError):accepted=False
                    invalid.append({'kind':c['kind'],'mutation':mutation,'raw':bad,'accepted':accepted})
                if c['name'].startswith('genuine-wire:'):continue
            from xar_autoplayer.bridge.army_current_disembark_penalty_contract import normalize_current_disembark_penalty_v1,project_current_disembark_penalty_v1
            landing=[{'schema_version':1,'source':'native_current_disembark_penalty_days_12003','status':'available','remaining_days':days,'unavailable_reason':None} for days in (-2147483648,-3,0,2147483647)]
            landing.append({'schema_version':1,'source':'native_current_disembark_penalty_days_12003','status':'unavailable','remaining_days':None,'unavailable_reason':'controlled-read-unavailable'})
            landing.append(None)
            disembark=[{'raw':raw,'normalized':None if raw is None else normalize_current_disembark_penalty_v1(raw),'projection':project_current_disembark_penalty_v1(raw,source_provenance=provenance)} for raw in landing]
            for r in m['original_sources']:checkref(r)
            for r in f['fixtures']:checkref(r['source_ref'])
            print(json.dumps({'cases':cases,'mutations':invalid,'provenance':provenance,'disembark':disembark},separators=(',',':')))
            """;
    @Test void completeOriginalNormalizersProjectionsAndJavaRegistryPipelineAgree() throws Exception {
        JsonNode oracle=oracle();JsonNode provenance=oracle.get("provenance");EnumMap<Kind,JsonNode> first=new EnumMap<>(Kind.class);int checked=0;
        ArmyStrengthsFamilies.Registry registry=new ArmyStrengthsFamilies.Registry();ArmyStrengthsPipeline pipeline=new ArmyStrengthsPipeline();ArmyStrengthsManagers.install(registry,pipeline,actualSource());registry.freeze();pipeline.freeze();
        assertEquals(10,registry.coverage().installed().size()-1);assertEquals(12,pipeline.coverage().installed().size());assertFalse(registry.coverage().complete());assertFalse(pipeline.coverage().complete());
        var core=ArmyStrengthsCodec.core(parse(CORE));var context=new ArmyStrengths.RowContext(core,new ArmyTypes.Missing<>());
        for(JsonNode sample:oracle.get("cases")){Kind kind=Kind.valueOf(sample.get("kind").textValue());Inputs normalized=ArmyStrengthsManagers.decode(kind,sample.get("raw"));assertEquals(sample.get("normalized"),ArmyStrengthsManagers.encode(normalized,false),sample.get("name").asText());
            if(normalized!=null){assertEquals(normalized,ArmyStrengthsManagers.decode(kind,parse(ArmyJson.bytes(ArmyStrengthsManagers.encode(normalized,false)))));first.putIfAbsent(kind,sample);}
            JsonNode projected=projection(kind,normalized,sample.get("pending"),provenance,false);assertEquals(sample.get("projection"),parse(ArmyJson.bytes(projected)),kind+":"+sample.get("name").asText());
            var family=registry.normalize(key(kind),sample.get("raw").isNull()?new ArmyTypes.NullValue<>():new ArmyTypes.Present<>(raw(sample.get("raw"))),context);assertEquals(sample.get("normalized"),ArmyStrengthsCodec.parseValue(family.normalizedJson()));checked++;
        }
        assertTrue(checked>=60,"all original fixture families/branches must actually run");assertEquals(9,first.size());
        for(JsonNode mutation:oracle.get("mutations")){Kind kind=Kind.valueOf(mutation.get("kind").textValue());assertFalse(mutation.get("accepted").booleanValue(),"original malformed-input oracle unexpectedly accepted fixture mutation");assertThrows(IllegalArgumentException.class,()->ArmyStrengthsManagers.decode(kind,mutation.get("raw")),kind+":"+mutation.get("mutation").asText());}
        for(JsonNode sample:oracle.get("disembark")){ObjectNode request=ArmyJson.empty();request.set("raw",sample.get("raw"));request.set("source_provenance",provenance);assertEquals(sample.get("projection"),parse(DisembarkCodec.encodeProjection(DisembarkCodec.decodeProjectionRequest(ArmyJson.bytes(request)))));if(!sample.get("raw").isNull()){var value=registry.normalize(Key.CURRENT_DISEMBARK_PENALTY_V1,new ArmyTypes.Present<>(raw(sample.get("raw"))),context);assertEquals(sample.get("normalized"),ArmyStrengthsCodec.parseValue(value.normalizedJson()));}}
        List<ArmyStrengths.FamilyValue<?>> families=new ArrayList<>();for(var entry:first.entrySet())families.add(registry.normalize(key(entry.getKey()),new ArmyTypes.Present<>(raw(entry.getValue().get("raw"))),context));
        ObjectNode disembark=parse("{\"schema_version\":1,\"source\":\"native_current_disembark_penalty_days_12003\",\"status\":\"available\",\"remaining_days\":-3,\"unavailable_reason\":null}");families.add(registry.normalize(Key.CURRENT_DISEMBARK_PENALTY_V1,new ArmyTypes.Present<>(raw(disembark)),context));assertThrows(IllegalArgumentException.class,()->registry.normalize(Key.CURRENT_DISEMBARK_PENALTY_V1,new ArmyTypes.NullValue<>(),context));
        var row=new ArmyStrengths.Row(core,List.of(),new ArmyTypes.Missing<>(),new ArmyTypes.Missing<>(),families);var snapshot=snapshot();var read=new ArmyStrengths.Read(ArmyStrengths.Profile.ORDINARY_CORE_V1,ArmyStrengths.Status.AVAILABLE,BigInteger.ONE,"controlled",List.of(row),new ArmyTypes.Missing<>(),new ArmyTypes.Missing<>(),receipt(snapshot));var query=new ArmyStrengths.Query(ArmyStrengths.Profile.ORDINARY_CORE_V1,ArmyStrengths.Mode.EXPLICIT_RICH,new ArmyTypes.Present<>(List.of(core.army())),ArmyStrengths.EntryMode.OBSERVED_PREPARED,ArmyStrengths.EntryMode.OBSERVED_PREPARED);
        var actual=pipeline.projectAvailable(new ArmyStrengthsPipeline.Input(snapshot,read,query,List.of(row)));
        assertSame(actual.required(Stage.SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_CHARACTER_PREFIX_V1,ArmyStrengthsManagers.CharacterBatch.class),actual.required(Stage.CURRENT_PRE_DATE_CHARACTER_PREFIX_INPUTS_V1,ArmyStrengthsManagers.CharacterBatch.class));
        JsonNode before=actual.rowJson(row).get(Stage.SAME_INPUT_CONDITIONAL_CURRENT_PRE_DATE_CHARACTER_PREFIX_V1.wire());assertEquals(before,actual.topLevelJson().get(Stage.CURRENT_PRE_DATE_CHARACTER_PREFIX_INPUTS_V1.wire()).get(0).get("projection"));
        JsonNode publicCurrent=actual.topLevelPublicV2Json().get(Stage.CURRENT_ARMY_FLAG21_INPUTS_V1.wire()).get(0).get("projection");assertTrue(publicCurrent.get("source_provenance").get("revision").isTextual());assertTrue(publicCurrent.get("source_provenance").get("date_raw").isTextual());assertTrue(actual.topLevelJson().get(Stage.CURRENT_ARMY_FLAG21_INPUTS_V1.wire()).get(0).get("projection").get("source_provenance").get("revision").isIntegralNumber());
    }
    @Test void exactWideValuesSourceOverridesAndBorrowedRulePinDeclarationsStayStrict(){
        ObjectNode held=parse("{\"snapshot_id\":\"source\",\"revision\":18446744073709551615,\"native_revision\":9007199254740993,\"date_raw\":-2147483648,\"diagnostics\":{\"hello\":{\"game_version\":\"old\",\"expected_ck3_version\":null,\"executable_sha256\":\"old\",\"expected_ck3_sha256\":null}}}");var source=ArmyStrengthsManagers.provenance(held);assertNull(source.gameVersion());assertNull(source.executableSha256());assertEquals("18446744073709551615",source.encode(true).get("revision").textValue());assertEquals("-2147483648",source.encode(true).get("date_raw").textValue());assertEquals(new BigInteger("9007199254740993"),source.encode(false).get("native_revision").bigIntegerValue());
        ObjectNode pins=parse("{\"status\":\"available\",\"unavailable_reason\":\"\",\"schema_version\":1,\"source\":\"native_current_rule24_source_pins\",\"pins_captured_ready\":true,\"provider_array_borrowed\":true,\"rule_receiver_identity\":\"native:receiver\",\"rule_vtable_identity\":\"native:vtable\",\"condition_mode_raw_u8\":255,\"expected_scope_function_identity\":\"native:a\",\"expected_scope_function_rva\":null,\"scope_mask_function_identity\":\"native:b\",\"scope_mask_function_rva\":1,\"rule_evaluator_function_identity\":\"native:c\",\"rule_evaluator_function_rva\":4294967295,\"vtable_read_ready\":true,\"mode_read_ready\":true,\"expected_scope_pin_read_ready\":true,\"scope_mask_pin_read_ready\":true,\"rule_evaluator_pin_read_ready\":true,\"pin_requested_bytes_u32\":33,\"pin_captured_bytes_u32\":33,\"native_calls_executed\":0,\"native_writes_executed\":0}");var typed=ArmyManagersModel.decodeShape(pins,Shape.PINS,"pins");ArmyManagersCurrent.validatePins(typed);assertEquals(pins,ArmyManagersModel.encode(typed,false));assertThrows(IllegalArgumentException.class,()->ArmyManagersCurrent.validatePins(ArmyManagersModel.decodeShape(pins.deepCopy().put("rule_vtable_identity","native:0"),Shape.PINS,"pins")));assertThrows(IllegalArgumentException.class,()->ArmyManagersCurrent.validatePins(ArmyManagersModel.decodeShape(pins.deepCopy().put("pin_captured_bytes_u32",32),Shape.PINS,"pins")));
        ObjectNode value=ArmyManagersPendingPlacement.encode(ArmyManagersPendingPlacement.create(frameAtLargeSlot()),true);assertEquals("9007199254740993",value.get("physical_records").get(0).get("physical_slot_i64").textValue());assertEquals("9223372036854775807",value.get("terminal_slot_i64").textValue());
    }
    private static Document frameAtLargeSlot(){return ArmyManagersModel.decodeShape(parse("{\"status\":\"available\",\"ready\":true,\"unavailable_reason\":\"\",\"schema_version\":1,\"entries_identity\":\"native:frame\",\"entries_present\":true,\"data_is_native_empty_buffer\":false,\"map_count_raw_i32\":0,\"mask_raw_i32\":7,\"tail_raw_u8\":4,\"threshold_bits_u32\":1065353216,\"physical_control_extent_last_slot_i64\":9223372036854775807,\"physical_controls_complete\":false,\"rehash_prefix_complete\":true,\"rehash_nonzero_records_observed_i32\":0,\"records\":[{\"status\":\"available\",\"ready\":true,\"unavailable_reason\":\"\",\"native_index\":0,\"physical_slot_i64\":9007199254740993,\"control_raw_u8\":0,\"stored_hash_raw_u32\":null,\"key_raw_full_id_u32\":null,\"vector_capacity_raw_i32\":0,\"vector_allocator_identity\":null,\"vector_allocator_matches_expected\":true,\"references\":{\"status\":\"available\",\"ready\":true,\"unavailable_reason\":\"\",\"references_ready\":true,\"count_raw_i32\":0,\"data_identity\":null,\"data_present\":false,\"occurrences\":[],\"observed_occurrence_count\":0}}]}"),Shape.PENDING_FRAME,"frame");}
    private static JsonNode projection(Kind kind,Inputs value,JsonNode pending,JsonNode provenance,boolean publicV2){return switch(kind){case PENDING->ArmyManagersPending.encodeProjection(ArmyManagersPending.project(value),publicV2);case DATED->ArmyManagersPrefixes.encodeDated(ArmyManagersPrefixes.projectDated(value));case CHARACTER->ArmyManagersPrefixes.encodeCharacter(ArmyManagersPrefixes.projectCharacter(value,ArmyManagersPending.project(pending==null||pending.isNull()?null:ArmyStrengthsManagers.decode(Kind.PENDING,pending))));case REFRESH->ArmyManagersRefresh.encodeProjection(ArmyManagersRefresh.project(value),provenance,publicV2);default->ArmyManagersCurrent.encodeProjection(ArmyManagersCurrent.project(kind,value),provenance,publicV2);};}
    private static Key key(Kind kind){return switch(kind){case PENDING->Key.CURRENT_PRE_DATE_PENDING_UPDATE_INPUTS_V1;case DATED->Key.CURRENT_PRE_DATE_DATED_APPEND_INPUTS_V1;case CHARACTER->Key.CURRENT_PRE_DATE_CHARACTER_PREFIX_INPUTS_V1;case REFRESH->Key.CURRENT_POST_ADMISSION_REFRESH_INPUTS_V1;case CONDITION30->Key.CURRENT_ARMY_CONDITION30_INPUTS_V1;case FLAG20->Key.CURRENT_ARMY_FLAG20_INPUTS_V1;case FLAG21->Key.CURRENT_ARMY_FLAG21_INPUTS_V1;case HOLDER_RELATION->Key.CURRENT_SELECTED_TITLE_HOLDER_OWNER_RELATION_V1;case FLAG31->Key.CURRENT_ARMY_FLAG31_INPUTS_V1;};}
    private static ArmyStrengths.Snapshot snapshot(){Instant now=Instant.now();ExactRef ref=actualSource();G2Source source=new G2Source("fixture-machine",now.toString(),"controlled",ref);var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ZERO,BigInteger.valueOf(11),BigInteger.valueOf(10000)),"controlled-manager-frame",BigInteger.valueOf(7),"fixture-episode");var context=new ArmyTypes.Context(new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1),source,"fixture-session",now.plusSeconds(60));ObjectNode raw=ArmyJson.empty().put("snapshot_id","controlled-manager-frame").put("revision",7).put("native_revision",11).put("date_raw",10000).put("episode_run_id","fixture-episode").put("paused",true).put("map_ready",true);raw.putObject("played_character").put("character_id",0).put("alive",true);raw.putObject("diagnostics").put("connection_generation",5).putObject("hello").put("game_version","1.20.0.3").put("executable_sha256",SHA3);raw.putArray("player_armies").addObject().put("army_id",0);raw.putArray("active_wars");return ArmyStrengthsCodec.snapshot(context,raw(raw));}
    private static PlanningReadReceipt receipt(ArmyStrengths.Snapshot snapshot){var c=snapshot.context();OperationKey operation=new OperationKey(ArmyStrengths.STEP);var request=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),operation,new OpportunityJson.Obj(Map.of()),c.deadline());var guard=new PlanningReadGuard(new GuardEvidence(c.before(),c.source(),c.sessionId(),snapshot.binding().connectionGeneration(),operation,c.source().sourceRef(),c.source().sourceRef(),"controlled",Instant.now(),c.deadline()),true,true,true,"b".repeat(64));byte[] body="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"controlled-read\",\"ok\":true,\"result\":{}}".getBytes(StandardCharsets.UTF_8);try{return new PlanningReadReceipt(request,"controlled-read","controlled-read",guard,guard,new NativeActionPort.AckReceived("controlled-read",true,Optional.of(raw(ArmyJson.empty())),new RawJson(body),org.xar.ck3.control.nativebridge.NativeWire.packet(body)));}catch(java.io.IOException error){throw new IllegalArgumentException(error);}}
    private static JsonNode oracle()throws Exception{String executable=required("xar.python"),manifest=checked("xar.army.managers.manifest","xar.army.managers.manifest.sha256"),fixtures=checked("xar.army.managers.fixtures","xar.army.managers.fixtures.sha256");Process process=new ProcessBuilder(executable,"-I","-c",ORACLE,manifest,fixtures).redirectErrorStream(true).start();CompletableFuture<byte[]> output=CompletableFuture.supplyAsync(()->{try{return process.getInputStream().readNBytes(16*1024*1024+1);}catch(java.io.IOException error){throw new java.io.UncheckedIOException(error);}});if(!process.waitFor(90,TimeUnit.SECONDS)){process.destroyForcibly();throw new IllegalStateException("original manager oracle timed out");}byte[] body=output.get(10,TimeUnit.SECONDS);assertTrue(body.length<=16*1024*1024,"bounded manager differential output");assertEquals(0,process.exitValue(),new String(body,StandardCharsets.UTF_8));return StrictJson.parse(body,16*1024*1024);}
    private static String checked(String pathProperty,String digestProperty)throws Exception{String value=required(pathProperty);Path path=Path.of(value);assertTrue(Files.isRegularFile(path),"original source/fixture manifest must exist");String expected=required(digestProperty);assertTrue(expected.matches("[a-f0-9]{64}"));assertEquals(expected,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))),"original manifest drift");return value;}
    private static ExactRef actualSource(){try{
        String target="native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/ArmyStrengthsManagers.java";
        Path root=Path.of(required("xar.army.managers.java.root")).toAbsolutePath().normalize();
        Path path=Path.of(required("xar.army.managers.source")).toAbsolutePath().normalize();
        assertEquals(root.resolve(target).normalize(),path,"manager source must be the actual assembled production target");
        JsonNode manifest=StrictJson.parse(Files.readAllBytes(Path.of(checked("xar.army.managers.manifest","xar.army.managers.manifest.sha256"))),2*1024*1024);
        JsonNode selected=manifest.get("selected_files");assertNotNull(selected,"complete selected production source table required");assertTrue(selected.isArray());
        JsonNode winner=null;for(JsonNode row:selected)if(target.equals(row.path("target_relative").asText())){assertNull(winner,"manager target must have exactly one production source");winner=row;}
        assertNotNull(winner,"pinned production graph has no manager source target");
        JsonNode reference=winner.get("source_ref");assertNotNull(reference,"pinned manager body reference required");
        byte[] bytes=Files.readAllBytes(path);String digest=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        assertTrue(reference.path("bytes").isIntegralNumber());assertEquals(reference.path("bytes").longValue(),bytes.length,"assembled manager source bytes differ from selected body");
        assertEquals(reference.path("sha256").textValue(),digest,"assembled manager source digest differs from selected body");
        return new ExactRef(path.toString(),bytes.length,digest);
    }catch(Exception error){throw new IllegalStateException("actual manager production mapping unavailable",error);}}
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("NOT EXECUTED: manager source/fixture property missing: "+name);return value;}
    private static ObjectNode parse(String value){return ArmyJson.parse(value.getBytes(StandardCharsets.UTF_8));}
    private static JsonNode parse(byte[] value){return ArmyStrengthsCodec.parseValue(new RawJson(value));}
    private static RawJson raw(JsonNode value){return new RawJson(ArmyJson.bytes(value));}
}
