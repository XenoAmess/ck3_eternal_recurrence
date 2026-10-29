package org.xar.ck3.control.wave2.military.combatwire;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.File;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Executes unchanged Python producers and their actual fixture constructors in a fresh process. */
final class CombatOptionalLeavesParityTest {
    private static final CombatRequest REQUEST=new CombatRequest(900,800,List.of(12),List.of(22),null);
    @Test void completeInstallationMatchesActualProducerAndEveryConsumerRoundtrip() throws Exception {
        JsonNode corpus=capture();assertEquals("original-combat-optional-producers",corpus.path("producer").asText());assertTrue(corpus.path("source_pins").size()>=14);
        CombatEncounterScope scope=CombatEncounterScope.fromSnapshot(corpus.get("snapshot"),REQUEST);CombatSimulationInputsCodec codec=new CombatSimulationInputsCodec();
        for(JsonNode row:corpus.get("whole_cases")){CombatSimulationInputs value=codec.normalize(row.get("input"),REQUEST,scope);same(row.get("expected"),value.toJson(),row.path("id").asText());same(value.toJson(),codec.normalize(value.toJson(),REQUEST,scope).toJson(),"complete installation revalidation");ObjectNode copy=value.toJson();copy.removeAll();assertTrue(value.toJson().has("armies"));}
        for(JsonNode row:corpus.get("leaf_cases")){CombatOptionalLeaves.Leaf leaf=CombatOptionalLeaves.Leaf.valueOf(row.path("leaf").asText());Integer character=row.path("character").isNull()?null:row.path("character").intValue();CombatSimulationInputs base=codec.normalize(corpus.get("base"),REQUEST,scope);var context=new CombatOptionalLeaves.Context(leaf.wireName(),character,base.armies(),(ObjectNode)row.get("root"));
            if(row.path("accepted").asBoolean()){JsonNode actual=CombatOptionalLeaves.complete().normalize(leaf,row.get("input"),context);same(row.get("expected"),actual,row.path("id").asText());same(actual,CombatOptionalLeaves.complete().normalize(leaf,actual,context),"leaf canonical revalidation");}
            else assertThrows(IllegalArgumentException.class,()->CombatOptionalLeaves.complete().normalize(leaf,row.get("input"),context),row.path("id").asText());
        }
    }
    @Test void strictIntegerRepairsAndUnsupportedInstallationsFailClosed(){
        assertThrows(IllegalArgumentException.class,()->CombatPhysicalStatLeaves.ordinary(parse("{\"status\":\"unavailable\",\"selected_character_full_id\":null,\"character_resolution\":null,\"aggregate_properties\":{\"count\":null,\"keys_u16\":null,\"values_q64\":null},\"loaded_bases\":{\"siege_raw\":null,\"damage_raw\":null,\"toughness_raw\":null,\"pursuit_raw\":null,\"screen_raw\":null},\"scale\":100000.0,\"unavailable_reason\":\"unread\"}")));
        assertThrows(IllegalArgumentException.class,()->CombatOptionalLeaves.unpublishedOnly().normalize(CombatOptionalLeaves.Leaf.PHASE_RITE_PARAMETERS,parse("{}"),new CombatOptionalLeaves.Context("rite",0,List.of(),null)));
        assertThrows(IllegalArgumentException.class,()->CombatNativeValues.number(parse("9007199254740993.0"),64,true,false,"identity",true,true));
        assertEquals(new java.math.BigInteger("18446744073709551615"),CombatNativeValues.number(parse("\"18446744073709551615\""),64,true,false,"identity",true,true));
    }
    @Test void malformedRosterDiagnosticsRemainScopedAndCannotGrantEffects() throws Exception {
        JsonNode corpus=capture();CombatEncounterScope scope=CombatEncounterScope.fromSnapshot(corpus.get("snapshot"),REQUEST);CombatSimulationInputsCodec codec=new CombatSimulationInputsCodec();ObjectNode input=(ObjectNode)corpus.get("whole_cases").get(2).get("input").deepCopy();
        ((ObjectNode)input.get("phase_event_calendar_observation_v1")).put("complete_phase_effects_ready",true);CombatSimulationInputs result=codec.normalize(input,REQUEST,scope);assertEquals("unavailable",result.toJson().path("phase_event_calendar_observation_v1").path("status").asText());assertFalse(result.toJson().path("phase_event_calendar_observation_v1").path("complete_phase_effects_ready").asBoolean());assertEquals(codec.normalize(corpus.get("base"),REQUEST,scope).completeness(),result.completeness());
    }
    private static void same(JsonNode expected,JsonNode actual,String name){assertArrayEquals(StrictJson.canonical(expected),StrictJson.canonical(actual),name);}
    private static JsonNode parse(String json){return StrictJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static JsonNode capture() throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");assertNotNull(repository,"missing original producer root must fail");assertNotNull(python,"missing Python oracle interpreter must fail");Path root=Path.of(repository).toAbsolutePath().normalize();ProcessBuilder builder=new ProcessBuilder(python,"-B","-X","utf8","-c",PROGRAM,root.toString());builder.directory(root.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src")+File.pathSeparator+root);builder.redirectError(ProcessBuilder.Redirect.INHERIT);Process process=builder.start();byte[] raw;
        try(var reader=Executors.newSingleThreadExecutor()){var future=reader.submit(()->{try(var in=process.getInputStream()){return in.readNBytes(4_194_305);}});if(!process.waitFor(60,TimeUnit.SECONDS)){process.descendants().forEach(ProcessHandle::destroyForcibly);process.destroyForcibly();fail("original optional producer timeout");}raw=future.get();}assertEquals(0,process.exitValue(),"oracle process exit");assertTrue(raw.length>0&&raw.length<=4_194_304,"bounded complete corpus");return StrictJson.parse(raw,4_194_304);
    }
    private static final String PROGRAM="""
        import ast,copy,hashlib,importlib,json,sys,types
        from pathlib import Path
        root=Path(sys.argv[1]);src=root/'ck3_autonomous_player/src';tests=root/'ck3_autonomous_player/tests/unit'
        import xar_autoplayer
        bridge=types.ModuleType('xar_autoplayer.bridge');bridge.__path__=[str(src/'xar_autoplayer/bridge')];sys.modules[bridge.__name__]=bridge
        def module(name):return importlib.import_module('xar_autoplayer.bridge.'+name)
        combat=module('combat_contract');version=module('version_identity')
        def fixture(filename,names,namespace,assign=False):
            path=tests/filename;tree=ast.parse(path.read_text(encoding='utf-8'))
            selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names or assign and isinstance(n,ast.Assign)]
            exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
            return namespace
        ns=fixture('test_combat_simulation_inputs_contract.py',{'_army','_snapshot','_combat_regiment','_combat_army','_combat_inputs'},{});snapshot=ns['_snapshot']();base=ns['_combat_inputs']();scope=combat.combat_simulation_encounter_scope(snapshot,[12],[22])
        def normal(value):return combat.normalize_combat_simulation_inputs(value,expected_target_province_id=900,expected_attacker_entry_province_id=800,expected_encounter_scope=scope)
        normalized=normal(copy.deepcopy(base));whole=[];leaves=[];pins=set()
        def whole_case(name,value):whole.append(dict(id=name,input=value,expected=normal(copy.deepcopy(value))))
        def leaf_case(name,leaf,mod,fn,value,char=None,kwargs=None,source=None):
            m=module(mod);pins.add(mod);args=kwargs or {};args.update({'expected_character_id':char} if char is not None and 'expected_character_id' not in args and leaf in ('PHASE_RITE_PARAMETERS','PHASE_WARMONGER_CORE','PHASE_BERSERKER_VALIDITY','PHASE_BERSERKER_CHANCE') else {})
            try:expected=getattr(m,fn)(copy.deepcopy(value),**args);leaves.append(dict(id=name,leaf=leaf,character=char,input=value,accepted=True,expected=expected,root=source or {}))
            except (ValueError,TypeError):leaves.append(dict(id=name,leaf=leaf,character=char,input=value,accepted=False,root=source or {}))
        rite=dict(status='available',source_character_id=0,raw_adopted_rite_id=0,rite_id=0,faith_id=None,boolean_parameters_complete=True,boolean_parameter_keys=['doctrine_parameter'],unavailable_reason=None)
        warm=dict(status='available',source_character_id=0,raw_adopted_rite_id=0,rite_id=0,rite_resolution='adopted',requested_tenet_key='tenet_warmonger',target_tenet_key='tenet_warmonger',warmonger_core_membership=False,unavailable_reason=None)
        for name,leaf,mod,fn,value in [('rite-zero','PHASE_RITE_PARAMETERS','phase_rite_parameters_contract','normalize_phase_rite_parameters_v1',rite),('warmonger-zero-false','PHASE_WARMONGER_CORE','phase_warmonger_core_contract','normalize_phase_warmonger_core_v1',warm)]:
            leaf_case(name,leaf,mod,fn,value,0)
            for token in (True,0.0,None):bad=copy.deepcopy(value);bad['source_character_id']=token;leaf_case(name+'-bad-id-'+repr(token),leaf,mod,fn,bad,0)
            bad=copy.deepcopy(value);bad['extra']=True;leaf_case(name+'-extra',leaf,mod,fn,bad,0)
            bad=copy.deepcopy(value);del bad['status'];leaf_case(name+'-missing',leaf,mod,fn,bad,0)
        validity=fixture('test_phase_berserker_validity_12003.py',{'_remaining'},{})['_remaining'](True,False,(False,None,False),zero=True)
        chance_ns=fixture('test_phase_berserker_chance_12003.py',{'_bool','_chance'},{'CHANCE_TRAIT_KEYS':module('phase_berserker_chance_contract').CHANCE_TRAIT_KEYS});chance=chance_ns['_chance'](ai=None,acclaimed=False,zero=True)
        leaf_case('berserker-validity-zero-null','PHASE_BERSERKER_VALIDITY','phase_berserker_validity_contract','normalize_phase_berserker_validity_inputs_v1',validity,77)
        leaf_case('berserker-chance-zero-null','PHASE_BERSERKER_CHANCE','phase_berserker_chance_contract','normalize_phase_berserker_chance_inputs_v1',chance,77)
        payload_ns=fixture('test_phase_berserker_validity_12003.py',{'_payload'},{'_combat_inputs':ns['_combat_inputs']});phase_whole=payload_ns['_payload'](copy.deepcopy(validity),False,zero=True);phase_member=phase_whole['armies'][0]['knights']['members'][0];phase_rite=copy.deepcopy(rite);phase_rite['source_character_id']=77;phase_member['phase_rite_parameters_v1']=phase_rite;phase_member['phase_berserker_chance_inputs_v1']=copy.deepcopy(chance);whole_case('whole-phase-four',phase_whole)
        ordinary=dict(status='available',selected_character_full_id=0,character_resolution='generation_resolved',aggregate_properties=dict(count=1,keys_u16=[65535],values_q64=[-(1<<63)]),loaded_bases=dict(siege_raw=0,damage_raw=(1<<63)-1,toughness_raw=0,pursuit_raw=0,screen_raw=0),scale=100000,unavailable_reason=None)
        leaf_case('ordinary-signed64','ORDINARY_STAT_INPUTS','ordinary_stat_inputs_contract','normalize_ordinary_stat_inputs_v1',ordinary,kwargs={'name':'ordinary'})
        maa_module=module('maa_stat_inputs_contract');maa=dict.fromkeys(maa_module.FIELDS);maa.update(status='available',source_target_province_id=900,source_regiment_full_id=31,selected_character_full_id=0,character_resolution='native_fallback',inner_type_is_gdbo=False,selector_mode=False,environment_components=dict.fromkeys(maa_module.ENV_NAMES),fallback_ordinary_bases=dict.fromkeys(maa_module.STAT_NAMES[1:],0),selected_properties=dict(count=0,keys_u16=[],values_q64=[]),scale=100000)
        leaf_case('maa-fallback','MAA_STAT_INPUTS','maa_stat_inputs_contract','normalize_maa_stat_inputs_v1',maa,kwargs={'name':'maa'})
        association=dict(schema='ck3_12003_knight_current_model_association_v1',read_scope='frozen_current_character_values',selected_character_id=0,current_installed=dict(status='partial',context_source=None,unavailable_reason=None,carrier_present=None,installed_model_present=None,owner_present=None,owner_matches_selected=None,getter_receiver_matches_model_inline=None),queue_census=dict(status='partial',old_count_raw=0,pair_count_raw=0,first_unread_occurrence=None,relevant_occurrences=[],unavailable_reason=None))
        leaf_case('model-empty-observed','KNIGHT_CURRENT_MODEL_ASSOCIATION','knight_current_model_association_contract','normalize_knight_current_model_association_v1',association,0,{'name':'association','selected_character_id':0})
        kns=fixture('test_knight_stat_consumption_stage_lineage_12004.py',{'_pc','_owned_capture','_wire'},{'deepcopy':copy.deepcopy,'CK3_12004':version.CK3_12004},True);knight=kns['_wire']();leaf_case('knight-owned-stage-lineage','KNIGHT_STAT_CONSUMPTION','knight_stat_consumption_contract_12004','normalize_knight_stat_consumption_12004',knight)
        for token in (True,1.0,None):bad=copy.deepcopy(knight);bad['events'][0]['sequence']=token;leaf_case('knight-bad-sequence-'+repr(token),'KNIGHT_STAT_CONSUMPTION','knight_stat_consumption_contract_12004','normalize_knight_stat_consumption_12004',bad)
        value=copy.deepcopy(base);value['knight_stat_consumption_v1']=knight;value['armies'][0]['regiments'][0]['ordinary_stat_inputs_v1']=ordinary;value['armies'][0]['regiments'][0]['maa_stat_inputs_v1']=maa;whole_case('whole-physical-three',value)
        calendar_mod=module('phase_event_calendar_contract');role_mod=module('phase_event_role_compatibility_contract');identity_mod=module('phase_event_commander_side_identity_contract');trigger_mod=module('phase_event_commander_trigger_conditions_contract');chance_mod=module('phase_event_commander_chance_weights_contract');armies=normalized['armies'];occ=calendar_mod._expected_occurrences(armies);cmd=identity_mod._expected_commanders(armies);sha=version.CK3_12004.executable_sha256
        calendar=dict(schema_version=1,scope=calendar_mod.PHASE_EVENT_CALENDAR_SCOPE,status='available',date_low32=0x029c55a8,next_date_low32=0x029c55a8+24,day_index=0,next_day_index=1,loaded_interval_days_raw=3,loaded_interval_source_closed=True,calendar_predicate_source_closed=True,complete_phase_effects_ready=False,source_ck3_sha256=sha,unavailable_reason=None,occurrences=[])
        role=dict(schema_version=1,scope=role_mod.PHASE_EVENT_ROLE_COMPATIBILITY_SCOPE,status='available',source_ck3_sha256=sha,loaded_registry_source_closed=True,role_compare_source_closed=True,native_candidate_admission_observed=False,complete_phase_effects_ready=False,unavailable_reason=None,loaded_registry=dict(status='available',count_raw=1,rows=[dict(loaded_row_index=0,role_operand_raw=0,status='available',unavailable_reason=None)],unavailable_reason=None),occurrences=[])
        for source in occ:
            current=source['character_id']%3;next_rem=((source['character_id']+1)&0xffffffff)%3;calendar['occurrences'].append(dict(source,current_calendar_predicate=current==0,next_day_calendar_predicate=next_rem==0,current_remainder_raw=current,next_remainder_raw=next_rem));requested=0 if source['phase_role']=='commander' else 1;role['occurrences'].append(dict(source,requested_role_raw=requested,native_role_argument_source_closed=True,conditions=[dict(loaded_row_index=0,role_compatible=requested==0,unavailable_reason=None)]))
        identity=dict(schema_version=1,scope=identity_mod.PHASE_EVENT_COMMANDER_SIDE_IDENTITY_SCOPE,status='available',source_ck3_sha256=sha,commander_side_identity_source_closed=True,native_candidate_admission_observed=False,complete_phase_effects_ready=False,unavailable_reason=None,occurrences=[])
        trigger=dict(schema_version=1,scope=trigger_mod.PHASE_EVENT_COMMANDER_TRIGGER_SCOPE,status='available',source_ck3_sha256=sha,trigger_source_closed=True,native_role_and_trigger_evaluation_observed=bool(cmd),complete_phase_effects_ready=False,unavailable_reason=None,occurrences=[])
        weights=dict(schema_version=1,scope=chance_mod.PHASE_EVENT_COMMANDER_CHANCE_WEIGHTS_SCOPE,status='available',source_ck3_sha256=sha,chance_source_closed=True,native_chance_evaluation_observed=bool(cmd),complete_phase_effects_ready=False,unavailable_reason=None,occurrences=[],effect_emptiness_source_closed=True)
        for source in cmd:
            identity['occurrences'].append(dict(source,status='available',unavailable_reason=None,actual_physical_army_full_id_raw=source['source_native_carmy_id'],actual_selected_combat_full_id_raw=5,source_active_combat=True,attacker_membership_count=1,defender_membership_count=0,unique_physical_membership=True,actual_side_index=0,actual_side_role='attacker',actual_side_parent_matches_selected_combat=True,actual_side_commander_full_id_raw=source['character_id'],actual_side_commander_present=True,full_id_equal=True))
            trigger['occurrences'].append(dict(source,requested_role_raw=0,actual_combat_full_id_raw=5,actual_side_index=0,current_commander_context_ready=True,loaded_named_side_key_raw=0,conditions=[dict(loaded_row_index=0,role_compatible=True,native_trigger_valid=True,role_and_trigger_valid=True,unavailable_reason=None)],role_compatible_count=1,evaluated_count=1,admitted_count=1,unknown_count=0,role_trigger_observation_ready=True,status='available',unavailable_reason=None))
            weights['occurrences'].append(dict(source,actual_combat_full_id_raw=5,actual_side_index=0,current_commander_context_ready=True,loaded_named_side_key_raw=0,conditions=[dict(loaded_row_index=0,role_and_trigger_valid=True,chance_raw=700000,selection_weight_raw=7,unavailable_reason=None,effect_empty_operand_raw=0,native_effect_empty=True,effect_emptiness_unavailable_reason=None)],admitted_count=1,evaluated_count=1,not_admitted_count=0,unknown_count=0,chance_weight_observation_ready=True,status='available',unavailable_reason=None))
        value=copy.deepcopy(base)
        for leaf,payload in [('phase_event_calendar_observation_v1',calendar),('phase_event_role_compatibility_v1',role),('phase_event_commander_side_identity_v1',identity),('phase_event_commander_trigger_conditions_v1',trigger),('phase_event_commander_chance_weights_v1',weights)]:value[leaf]=payload
        whole_case('whole-roster-five-same-query',value)
        for mod in ('phase_event_calendar_contract','phase_event_role_compatibility_contract','phase_event_commander_side_identity_contract','phase_event_commander_trigger_conditions_contract','phase_event_commander_chance_weights_contract','battle_person_six_stage_capture_12004','combat_contract'):pins.add(mod)
        output=dict(producer='original-combat-optional-producers',base=base,snapshot=snapshot,whole_cases=whole,leaf_cases=leaves,source_pins=[])
        for name in sorted(pins):path=src/'xar_autoplayer/bridge'/f'{name}.py';body=path.read_bytes();output['source_pins'].append(dict(path=str(path.relative_to(root)),bytes=len(body),sha256=hashlib.sha256(body).hexdigest()))
        sys.stdout.write(json.dumps(output,ensure_ascii=False,separators=(',',':')))
        """;
}
