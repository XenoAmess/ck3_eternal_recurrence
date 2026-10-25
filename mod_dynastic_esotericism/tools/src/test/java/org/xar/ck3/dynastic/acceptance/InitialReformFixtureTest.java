package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Qualification-input contracts only; actual creation/edit Can remains native. */
final class InitialReformFixtureTest {
    private static final List<String> ASSETS = List.of("descriptor.mod",
            "common/on_action/des_initial_reform_acceptance_on_actions.txt",
            "common/scripted_effects/des_initial_reform_acceptance_effects.txt");
    @TempDir Path temporary;

    private static Path repository() {
        return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
    }

    @Test
    void realProducerRetainsFourCompleteQualificationDefinitionsAndOneStockSetup()
            throws IOException, InterruptedException {
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository(), temporary.resolve("initial"),
                "authored-machine", FixtureEmitter.CaseKind.INITIAL_REFORM);
        assertEquals(Set.copyOf(ASSETS), emitted.payload().files().keySet());
        assertEquals(6, emitted.payload().producerSourcePins().size());
        assertEquals(List.of("DESIRF: FIXTURE_ARMED initial_reform", "DESIRF: QUALIFICATION_INPUT_APPLIED initial_reform"),
                emitted.payload().receipt().requiredMarkers());
        assertTrue(emitted.payload().receipt().containsBusinessEffects());
        for (String relative : ASSETS) {
            byte[] bytes = Files.readAllBytes(emitted.fixture().resolve(relative));
            if (!relative.equals("descriptor.mod")) {
                assertTrue(bytes[0] == (byte) 0xef && bytes[1] == (byte) 0xbb && bytes[2] == (byte) 0xbf);
            }
        }
        String program = """
                from pathlib import Path
                import copy,io,json,sys
                repository,fixture,manifest_path=map(Path,sys.argv[1:])
                sys.path.insert(0,str(repository/'ck3_autonomous_player/src'))
                from xar_autoplayer.campaign_score_save_reader import melt_tokens
                sys.path.insert(0,str(repository/'tools/lyd_i3b_checkpoint_readback/reader/dependencies'))
                from bounded_save_parser import parse_block,one
                resources=repository/'mod_dynastic_esotericism/tools/src/main/resources/acceptance-fixture'
                def read(path):
                    raw=path.read_text(encoding='utf-8-sig').encode('utf-8')
                    return parse_block('{ '+' '.join(melt_tokens(io.BytesIO(raw)))+' }')
                old=read(resources/'common/scripted_effects/des_acceptance_effects.txt')
                core_setup=one(one(read(resources/'events/des_acceptance_events.txt'),'des_acceptance.1',required=True),'immediate',required=True)
                effects=read(fixture/'common/scripted_effects/des_initial_reform_acceptance_effects.txt')
                actions=read(fixture/'common/on_action/des_initial_reform_acceptance_on_actions.txt')
                names=['prepare_original_rite_input_effect','read_original_rite_relation_effect',
                       'read_original_rite_input_effect','read_original_edit_input_effect']
                prefix='des_initial_reform_acceptance_'
                def renamed(value):
                    if isinstance(value,str):
                        return value.replace('des_acceptance_',prefix).replace('des_test_','des_irf_fixture_').replace(
                            'des_rite_input_actor','des_irf_fixture_relation_actor').replace('DESAF:','DESIRF:').replace(
                            'PRECONDITION PASS','QUALIFICATION_OBSERVED').replace('NOT_READY','QUALIFICATION_UNAVAILABLE')
                    if isinstance(value,list):return [renamed(v) for v in value]
                    if isinstance(value,dict):return {k:renamed(v) for k,v in value.items()}
                    return value
                expected=[{'key':prefix+name,'value':renamed(one(old,'des_acceptance_'+name,required=True))} for name in names]
                def row(key,value):return {'key':key,'value':value}
                def require(entries,key,value):assert row(key,value) in entries,(key,value)
                def walk(entries):
                    for r in entries:
                        yield r
                        if isinstance(r['value'],list):yield from walk(r['value'])
                def validate(current,setup_actions):
                    assert current==expected,'qualification closure differs from four complete source definitions'
                    assert {r['key'] for r in setup_actions}=={'on_game_start_after_lobby',prefix+'arm',prefix+'setup'}
                    arm=one(one(one(setup_actions,prefix+'arm',required=True),'effect',required=True),'every_player',required=True)
                    require(arm,'trigger_event',[row('on_action',prefix+'setup'),row('days','1')])
                    require(one(arm,'limit',required=True),'NOT',[row('has_character_flag','des_irf_fixture_armed')])
                    assert arm[1]==row('add_character_flag','des_irf_fixture_armed')
                    setup=one(setup_actions,prefix+'setup',required=True)
                    branch=one(one(setup,'effect',required=True),'if',required=True)
                    trigger=one(setup,'trigger',required=True)
                    assert trigger==one(branch,'limit',required=True)
                    for key,value in [('is_alive','yes'),('is_ai','no'),('this','root'),('is_incapable','no'),
                                      ('exists','primary_title'),('exists','dynasty'),('exists','house'),
                                      ('has_character_flag','des_irf_fixture_armed'),
                                      ('NOT',[row('has_character_flag','des_irf_fixture_input_applied')])]:
                        require(trigger,key,value)
                    assert branch[1]==row('add_character_flag','des_irf_fixture_input_applied')
                    pins={'des_irf_fixture_ref_actor':'this','des_irf_fixture_ref_primary_title':'primary_title',
                          'des_irf_fixture_source_faith':'faith','des_irf_fixture_source_rite':'rite',
                          'des_irf_fixture_input_date':'current_date','des_irf_fixture_original_dynasty':'dynasty',
                          'des_irf_fixture_original_house':'house'}
                    actual=[r for r in branch if r['key']=='set_variable']
                    assert actual==[row('set_variable',[row('name',n),row('value',v)]) for n,v in pins.items()]
                    assert branch[2:9]==actual
                    assert branch[9]==row('if',[row('limit',[row('is_dynast','yes')]),row('add_character_flag','des_irf_fixture_original_is_dynast')])
                    assert branch[10:]==[row('add_piety','100000'),row('change_spiritual_fulfillment',[row('value','100')]),
                        row('if',[row('limit',[row('has_perk','prophet_perk')]),row('remove_perk','prophet_perk')]),
                        row(prefix+'prepare_original_rite_input_effect','yes'),row(prefix+'read_original_rite_input_effect','yes'),
                        row('debug_log',json.dumps('DESIRF: QUALIFICATION_INPUT_APPLIED initial_reform'))]
                    assert all(r in core_setup for r in branch[10:13]),'qualification stock input lost its original setup source'
                    forbidden={'create_character','create_dynamic_rite','create_dynamic_faith','create_dynasty',
                               'set_character_rite','set_character_faith','add_rite_doctrine','remove_rite_doctrine',
                               'set_house','set_dynasty','set_house_head','set_dynasty_head','set_coa','set_player_character',
                               'set_global_variable','add_to_variable_list'}
                    for r in walk(current+setup_actions):
                        assert r['key'] not in forbidden,r
                        if r['key']=='set_variable':assert one(r['value'],'name',required=True).startswith('des_irf_fixture_')
                        if r['key'] in ('remove_variable','remove_global_variable'):raise AssertionError('stock/product clearing')
                        if r['key']=='trigger_event':assert r['value']==[row('on_action',prefix+'setup'),row('days','1')]
                        if r['key']=='debug_log':assert 'PASS' not in r['value'] and 'TEST PASS' not in r['value']
                        assert not (isinstance(r['key'],str) and r['key'].startswith('des_acceptance_'))
                validate(effects,actions)
                def negative(label,mutation):
                    e,a=copy.deepcopy(effects),copy.deepcopy(actions);mutation(e,a)
                    try:validate(e,a)
                    except (AssertionError,ValueError,KeyError):return
                    raise AssertionError('accepted '+label)
                negative('missing-helper',lambda e,a:e.pop())
                negative('altered-helper',lambda e,a:e[0]['value'].append(row('set_house_head','root')))
                def branch(actions):return one(one(one(actions,prefix+'setup',required=True),'effect',required=True),'if',required=True)
                negative('product-setter',lambda e,a:branch(a).append(row('set_dynasty_head','root')))
                negative('clear-stock-lock',lambda e,a:branch(a).append(row('remove_variable','has_edited_a_rite')))
                negative('late-once',lambda e,a:branch(a).append(branch(a).pop(1)))
                def wrong_root(e,a):
                    setup=one(a,prefix+'setup',required=True)
                    one(setup,'trigger',required=True)[:]=[row('always','yes')]
                negative('wrong-root',wrong_root)
                def wrong_delay(e,a):
                    arm=one(one(one(a,prefix+'arm',required=True),'effect',required=True),'every_player',required=True)
                    one(arm,'trigger_event',required=True)[1]['value']='0'
                negative('wrong-delay',wrong_delay)
                manifest=json.loads(manifest_path.read_bytes())
                assert len(manifest['files'])==3 and len(manifest['producer_source_pins'])==6
                sources={Path(p['path']).name for p in manifest['producer_source_pins']}
                assert {'des_acceptance_effects.txt','des_acceptance_events.txt'}<=sources
                config=json.loads((repository/'tools/ck3_mod_acceptance_cases/dynastic_esotericism_initial_reform.json').read_bytes())
                assert len(config['gui_phases'])==2 and config['maximum_natural_days']==8
                assert config['allow_actor_change'] is False
                assert all(p['when_markers']==['DESIRF: QUALIFICATION_INPUT_APPLIED initial_reform'] for p in config['gui_phases'])
                print('actual initial_reform3/sourcepins6/markers2: exact four-helper AST, one delayed stock setup and seven negatives; engine_semantics_verified=false')
                """;
        List<String> command = new ArrayList<>(List.of(System.getProperty("dynastic.python", "python"),
                "-B", "-X", "utf8", "-c", program, repository().toString(), emitted.fixture().toString(), emitted.manifest().toString()));
        Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor();
            throw new IOException("initial reform qualification AST probe timed out");
        }
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertEquals(0, process.exitValue(), output);
        assertTrue(output.contains("engine_semantics_verified=false"), output);
    }

    @Test
    void changedInitialReformPackagedAssetsCannotEmit() throws IOException {
        Path main = Path.of("mod_dynastic_esotericism/tools/src/main");
        for (int index = 0; index < ASSETS.size(); index++) {
            Path repo = temporary.resolve("changed-" + index);
            for (String relative : List.of("java/org/xar/ck3/dynastic/acceptance/FixtureEmitter.java",
                    "resources/acceptance-fixture/descriptor.mod",
                    "resources/acceptance-fixture/common/on_action/des_initial_reform_acceptance_on_actions.txt",
                    "resources/acceptance-fixture/common/scripted_effects/des_initial_reform_acceptance_effects.txt")) {
                Path destination = repo.resolve(main).resolve(relative);
                Files.createDirectories(destination.getParent());
                Files.copy(repository().resolve(main).resolve(relative), destination);
            }
            Files.writeString(repo.resolve(main).resolve("resources/acceptance-fixture").resolve(ASSETS.get(index)), "changed");
            Path output = temporary.resolve("rejected-" + index);
            IOException failure = assertThrows(IOException.class,
                    () -> FixtureEmitter.emit(repo, output, "authored-machine", FixtureEmitter.CaseKind.INITIAL_REFORM));
            assertEquals("packaged fixture resource differs from current source: " + ASSETS.get(index), failure.getMessage());
            assertFalse(Files.exists(output));
        }
    }
}
