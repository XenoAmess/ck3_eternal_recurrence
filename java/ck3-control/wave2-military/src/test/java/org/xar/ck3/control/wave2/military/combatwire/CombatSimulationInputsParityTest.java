package org.xar.ck3.control.wave2.military.combatwire;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Runs the unchanged original producer; the narrow shim loads only its existing fixture functions. */
final class CombatSimulationInputsParityTest {
    private static final CombatRequest REQUEST=new CombatRequest(900,800,List.of(12),List.of(22),null);
    @Test void originalProducerAndNormalizedRevalidationMatch() throws Exception {
        JsonNode corpus=capture();
        assertEquals("unchanged-original-combat-contract",corpus.get("producer").textValue());
        assertTrue(corpus.get("source_pins").size()>=3);
        CombatEncounterScope scope=CombatEncounterScope.fromSnapshot(corpus.get("snapshot"),REQUEST);
        CombatSimulationInputsCodec codec=new CombatSimulationInputsCodec();
        assertArrayEquals(StrictJson.canonical(corpus.get("scope")),StrictJson.canonical(scope.toJson(REQUEST)));
        int accepted=0,rejected=0;
        for(JsonNode row:corpus.get("cases")){
            String id=row.get("id").textValue();
            if(row.get("accepted").booleanValue()){
                CombatRequest request=row.path("constructor_zero").asBoolean()?new CombatRequest(900,null,List.of(12),List.of(22),0):REQUEST;
                CombatSimulationInputs result=codec.normalize(row.get("input"),request,scope);
                assertArrayEquals(StrictJson.canonical(row.get("expected")),StrictJson.canonical(result.toJson()),id);
                assertArrayEquals(StrictJson.canonical(result.toJson()),StrictJson.canonical(codec.normalize(result.toJson(),request,scope).toJson()),id+" revalidation");
                ObjectNode copy=result.toJson();copy.removeAll();assertTrue(result.toJson().has("scenario"),"detached normalized transport");
                assertFalse(result.completeness().monteCarloReady());accepted++;
            }else{assertThrows(IllegalArgumentException.class,()->codec.normalize(row.get("input"),REQUEST,scope),id);rejected++;}
        }
        assertTrue(accepted>=8);assertTrue(rejected>=18);
    }
    @Test void canonicalRequestPartitionAndPublicZeroAreStrict(){
        CombatRequest request=new CombatRequest(900,800,List.of(0,Integer.MAX_VALUE),List.of(22),null);
        assertEquals(request,CombatRequest.parseStep(request.toStep()).orElseThrow());
        for(String raw:List.of("query-combat-simulation-inputs-v2-0900-800-a-1-12-d-1-22",
                "query-combat-simulation-inputs-v2-900-800-a-1-012-d-1-22",
                "query-combat-simulation-inputs-v2-900-800-a-1-12-d-1-12",
                "query-combat-simulation-inputs-v2-９００-800-a-1-12-d-1-22",
                "query-combat-simulation-inputs-v2-900-800-a-1-12-d-0"))
            assertTrue(CombatRequest.parseStep(raw).isEmpty(),raw);
        assertThrows(IllegalArgumentException.class,()->CombatRequest.decode(parse("900.0"),parse("800"),parse("[12]"),parse("[22]"),null));
        assertThrows(IllegalArgumentException.class,()->CombatRequest.decode(parse("900"),parse("800"),parse("[true]"),parse("[22]"),null));
        assertThrows(IllegalArgumentException.class,()->CombatRequest.decode(parse("900"),null,parse("[12]"),parse("[22]"),parse("0.0")));
        assertEquals(new CombatRequest(900,null,List.of(0),List.of(22),0),CombatRequest.parseStep("query-combat-simulation-inputs-v2-900-ctor0-a-1-0-d-1-22").orElseThrow());
    }
    @Test void fixedPointScaleStrengthensLegacyFloatEquality(){
        assertThrows(IllegalArgumentException.class,()->CombatWire.scale(parse("100000.0"),"scale"));
        assertThrows(IllegalArgumentException.class,()->CombatWire.scale(parse("true"),"scale"));
    }
    private static JsonNode parse(String value){return StrictJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static JsonNode capture() throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"-Dxar.repository.root must name the retained original source root; missing configuration fails rather than skips");
        assertNotNull(python,"-Dxar.python must name its actual compatible interpreter");
        Path root=Path.of(repository).toAbsolutePath().normalize();
        ProcessBuilder builder=new ProcessBuilder(python,"-B","-X","utf8","-c",PROGRAM,root.toString());builder.directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src")+File.pathSeparator+root);builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process=builder.start();byte[] raw;
        try(var reader=Executors.newSingleThreadExecutor()){
            var future=reader.submit(()->{try(var stream=process.getInputStream()){return stream.readNBytes(1_048_577);}});
            if(!process.waitFor(60,TimeUnit.SECONDS)){process.descendants().forEach(ProcessHandle::destroyForcibly);process.destroyForcibly();throw new IOException("original combat producer timeout");}
            raw=future.get();
        }
        assertEquals(0,process.exitValue(),"original producer must actually finish");assertTrue(raw.length>0&&raw.length<=1_048_576);return StrictJson.parse(raw,1_048_576);
    }
    private static final String PROGRAM="""
        import sys,ast,types,importlib,json,copy,hashlib
        from pathlib import Path
        root=Path(sys.argv[1]); src=root/'ck3_autonomous_player/src'
        import xar_autoplayer
        bridge=types.ModuleType('xar_autoplayer.bridge'); bridge.__path__=[str(src/'xar_autoplayer/bridge')];sys.modules[bridge.__name__]=bridge
        producer=importlib.import_module('xar_autoplayer.bridge.combat_contract')
        fixture=root/'ck3_autonomous_player/tests/unit/test_combat_simulation_inputs_contract.py'
        tree=ast.parse(fixture.read_text(encoding='utf-8'))
        names={'_army','_snapshot','_combat_regiment','_combat_army','_combat_inputs'}
        selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
        namespace={}
        exec(compile(ast.Module(body=selected,type_ignores=[]),str(fixture),'exec'),namespace)
        snapshot=namespace['_snapshot'](); base=namespace['_combat_inputs']()
        scope=producer.combat_simulation_encounter_scope(snapshot,[12],[22]); cases=[]
        def add(name,value,ctor=False):
            kwargs=dict(expected_target_province_id=900,expected_attacker_entry_province_id=None if ctor else 800,expected_encounter_scope=scope)
            if ctor: kwargs['expected_constructor_adjacency_kind_raw']=0
            try:
                expected=producer.normalize_combat_simulation_inputs(value,**kwargs)
                assert producer.normalize_combat_simulation_inputs(expected,**kwargs)==expected
                cases.append(dict(id=name,input=value,accepted=True,expected=expected,constructor_zero=ctor))
            except (ValueError,TypeError) as error:
                cases.append(dict(id=name,input=value,accepted=False,error_type=type(error).__name__))
        add('actual-fixture-available',copy.deepcopy(base))
        value=copy.deepcopy(base);value['armies'][0]['owner']['character_id']=0
        value['counter_resolutions'][0]['countered_modifier_owner_character_id']=0
        value['counter_resolutions'][1]['countering_modifier_owner_character_id']=0
        add('owner-zero-is-legal',value)
        value=copy.deepcopy(base);value['armies'][0]['regiments']=[];add('empty-composition-is-observed',value)
        value=copy.deepcopy(base);value['scenario'].update(attacker_entry_province_id=None,contact_geometry_mode='native_defender_constructor_zero',constructor_adjacency_kind_raw=0,attacker_position_policy='fixed_at_target_hypothetical');add('constructor-zero',value,True)
        value=copy.deepcopy(base);value['armies'][0]['knights']['members']=[dict(eligible=True,character_id=0,source_regiment_id=31,army_id=1012,participant_army_membership_verified=True,prowess=-3,knight_effectiveness_raw=185000,effective_damage_raw=9250000,effective_toughness_raw=1850000,scale=100000)];add('knight-zero-and-clamped-prowess',value)
        value=copy.deepcopy(value);value['armies'][0]['knights'].update(loaded_damage_multiplier=None);value['armies'][0]['knights']['members'][0]['effective_damage_raw']=17;add('present-null-multiplier-remains-unknown',value)
        value=copy.deepcopy(value);value['armies'][0]['knights']['members'][0]['effectiveness_components']=dict(status='unavailable',modifier_raw=[0]*9,operand_raw=[0]*9);add('same-frame-components',value)
        value=copy.deepcopy(base);value['ongoing_combats']=[dict(status='available',combat_id=335544325,province_id=900,phase=1,phase_day=2,base_combat_width=400,final_combat_width=320,side_0_roll=11,side_1_roll=7,base_advantage=-(1<<63),resolved_advantage=(1<<63)-1,orientation='native_side_0_attacker_side_1_defender',unavailable_reason=None)];add('ongoing-int64-extremes',value)
        value=copy.deepcopy(base);value['target_province']['defender_context'].update(holding_defender_status='unavailable',holding_defender=None,holding_unavailable_reason='holding_owner_unavailable')
        value['completeness'].update(input_observation_ready=False,missing_required_domains=['attacker_defender_holding']+producer._SIMULATOR_GAPS);add('partial-holding-preserves-armies',value)
        context=dict(schema_version=1,status='available',scope='hypothetical_nonreligious_constructor_context',scale=100000,target_province_id=900,sides=[],base_nonreligious_accumulator_raw=0,synthetic_zero_roll_total_raw=0,synthetic_helper_total_match=True,partial_context_observation_ready=True,complete_encounter_advantage_ready=False,missing_domains=['religion_constructor_sources'],unavailable_reason=None)
        for index,army in enumerate((12,22)):
            context['sides'].append(dict(side_index=index,ordered_public_cunit_ids=[army],selected_commander_character_id=None,relation_kind_raw=0,commander_dynamic_raw=0,side_dynamic_raw=0,target_conditionals_residual_raw=0,side_total_raw=0))
        value=copy.deepcopy(base);value['contextual_advantage']=copy.deepcopy(context);add('contextual-schema1',value)
        value['contextual_advantage']['sides'][0]['side_total_raw']=1;add('contextual-partial-arithmetic-is-scoped-unavailable',value)
        value=copy.deepcopy(base);value['contextual_advantage']=copy.deepcopy(context);value['contextual_advantage']['extra']=False;add('contextual-malformed-fragment-only',value)
        context.update(schema_version=2,scope='hypothetical_constructor_context',religion_constructor_sources_ready=True,base_constructor_accumulator_raw=0,religion_constructor_sources=[],missing_domains=[])
        for index,army in enumerate((12,22)):
            context['religion_constructor_sources'].append(dict(side_index=index,primary_public_cunit_id=army,owner_character_id=index+7,target_rite_id=0,target_faith_id=0,target_main_rite_id=0,owner_rite_id=None,owner_faith_id=None,owner_rite_observed=False,target_faith_unreformed=False,owner_faith_matches_target=None,selected=False,applied=False,source_key=None,effect_advantage_points=None,scale_raw=100000,signed_contribution_raw=0,accumulator_before_raw=0,accumulator_after_raw=0,append_order=0,skip_reason='fixture_observed_unselected'))
        value=copy.deepcopy(base);value['contextual_advantage']=copy.deepcopy(context);add('contextual-schema2',value)
        context['nonreligious_constructor_sources']=[]
        for index,stage in enumerate(producer._CONTEXTUAL_NONRELIGIOUS_SOURCE_ORDER):
            context['nonreligious_constructor_sources'].append(dict(stage_order=index,append_order=None,stage=stage,side=producer._V3_ADVANTAGE_STAGE_SIDES[stage],selected=False,applied=False,source_key=None,effect_advantage_points=None,scale_raw=100000,signed_contribution_raw=0,accumulator_before_raw=0,accumulator_after_raw=0,skip_reason='fixture_observed_unselected'))
        value=copy.deepcopy(base);value['contextual_advantage']=copy.deepcopy(context);add('contextual-complete-nonreligious-ledger',value)
        paths=[
            ('target_province_id',),('scenario','attacker_entry_province_id'),
            ('armies',0,'army_id'),('armies',0,'native_carmy_id'),('armies',0,'owner','character_id'),
            ('armies',0,'regiments',0,'regiment_id'),('armies',0,'regiments',0,'current_soldiers'),
            ('counter_resolutions',0,'class_count'),('target_province','precontact_width','base'),
        ]
        for path in paths:
            for token in (True,1.0,None):
                value=copy.deepcopy(base);parent=value
                for key in path[:-1]:parent=parent[key]
                parent[path[-1]]=token;add('wrong-token:'+str(path)+':'+repr(token),value)
        for path in [('scenario',),('armies',0,'owner'),('armies',0,'commander'),('armies',0,'regiments',0),('target_province','terrain'),('counter_resolutions',0),('completeness',)]:
            value=copy.deepcopy(base);row=value
            for key in path:row=row[key]
            row['unrecognized_extra']=False;add('extra-field:'+str(path),value)
            value=copy.deepcopy(base);row=value
            for key in path:row=row[key]
            del row[next(iter(row))];add('missing-field:'+str(path),value)
        pins=[]
        for path in [fixture,src/'xar_autoplayer/bridge/combat_contract.py',src/'xar_autoplayer/bridge/war_contract.py',src/'xar_autoplayer/bridge/public_unit_contract.py']:
            body=path.read_bytes();pins.append(dict(path=str(path.relative_to(root)),bytes=len(body),sha256=hashlib.sha256(body).hexdigest()))
        output=dict(producer='unchanged-original-combat-contract',snapshot=snapshot,scope=scope,cases=cases,source_pins=pins)
        sys.stdout.write(json.dumps(output,ensure_ascii=False,separators=(',',':')))
        """;
}

