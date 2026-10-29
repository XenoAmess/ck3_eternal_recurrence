package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.ArrayList;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.dynastic.release.ReleaseBuilder;
import org.xar.ck3.dynastic.release.ReleaseProduct;

final class SharedRuntimeComposerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    @TempDir Path temporary;

    private static ObjectNode pin(Path path) throws IOException, NoSuchAlgorithmException {
        byte[] bytes = Files.readAllBytes(path);
        ObjectNode result = JSON.createObjectNode();
        result.put("path", path.toRealPath().toString());
        result.put("bytes", bytes.length);
        result.put("sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return result;
    }

    private static void write(Path path, JsonNode node) throws IOException {
        Files.writeString(path, JSON.writeValueAsString(node));
    }

    private record PythonResult(int exitCode, String output) { }

    private static PythonResult python(String program, List<String> arguments) throws IOException, InterruptedException {
        String interpreter = System.getProperty("dynastic.python", "python");
        List<String> command = new ArrayList<>(List.of(interpreter, "-B", "-X", "utf8", "-c", program));
        command.addAll(arguments);
        Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor();
            throw new IOException("Existing public Selection consumer timed out");
        }
        return new PythonResult(process.exitValue(), new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8));
    }

    private static void assertPublicSelectionConsumesProducedRuntime(Path runtime, Path products,
            Path presetManifest, Path initialReformManifest, Path coreManifest, Path presetProduct, List<Path> headManifests)
            throws IOException, InterruptedException {
        Path repository = Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
        String program = """
                from pathlib import Path
                import copy,json,sys
                repository,runtime_path,products_path=map(Path,sys.argv[1:])
                sys.path.insert(0,str(repository/'tools'))
                from ck3_mod_acceptance import Selection,pin
                tool='ck3_query_player_rite_members_v1'
                original_runtime=json.loads(runtime_path.read_bytes())
                manifest_path=Path(original_runtime['manifest']['path'])
                original_manifest=json.loads(manifest_path.read_bytes())
                original_bytes=manifest_path.read_bytes()
                selected=Selection(runtime_path,products_path,'authored-product','core')
                result=selected.preflight()
                assert result['blockers']==[],result
                assert result['status']=='READY_FOR_EXISTING_REVIEWED_LAUNCH',result
                assert result['business_acceptance']=='NOT_ASSESSED',result
                status=result['tool_status'][tool]
                assert status['source_build_ready'] is True,status
                assert status['actual_live_qualified'] is False,status
                prisoner_status=result['tool_status']['ck3_query_player_prisoner_collection_private_v1']
                assert prisoner_status['source_build_ready'] is True,prisoner_status
                assert prisoner_status['actual_live_qualified'] is False,prisoner_status
                evidence=status['evidence']
                assert pin(Path(evidence['path']))==evidence,evidence
                assert result['tool_status']['ck3_take_snapshot']==original_manifest['capabilities']['ck3_take_snapshot']
                declared=[selected.argv[i+1] for i,value in enumerate(selected.argv)
                          if value=='--case-read-only-mcp-tool']
                assert tool in declared,selected.argv
                failure='Required MCP tool has no shared build-ready evidence: '+tool
                for label,status in [('missing',None),('false',{'source_build_ready':False}),
                                     ('integer',{'source_build_ready':1}),('null',{'source_build_ready':None})]:
                    manifest=copy.deepcopy(original_manifest)
                    if status is None: del manifest['capabilities'][tool]
                    else: manifest['capabilities'][tool]=status
                    candidate_manifest=runtime_path.parent/(label+'-manifest.json')
                    candidate_manifest.write_text(json.dumps(manifest),encoding='utf-8')
                    candidate=copy.deepcopy(original_runtime)
                    candidate['manifest']=pin(candidate_manifest)
                    candidate_runtime=runtime_path.parent/(label+'-runtime.json')
                    candidate_runtime.write_text(json.dumps(candidate),encoding='utf-8')
                    rejected=Selection(candidate_runtime,products_path,'authored-product','core').preflight()
                    assert rejected['status']=='BLOCKED',rejected
                    assert rejected['blockers']==[failure],rejected
                root_tool='ck3_query_campaign_root_context_v1'
                root_status=result['tool_status'][root_tool]
                assert root_status['source_build_ready'] is True and root_status['actual_live_qualified'] is False
                root_failure='Required MCP tool has no shared build-ready evidence: '+root_tool
                for label,value in [('root-missing',None),('root-false',False),('root-integer',1),('root-null',None)]:
                    candidate_manifest=copy.deepcopy(original_manifest)
                    if label=='root-missing':del candidate_manifest['capabilities'][root_tool]
                    else:candidate_manifest['capabilities'][root_tool]={'source_build_ready':value,'actual_live_qualified':False}
                    mp=runtime_path.parent/(label+'-manifest.json')
                    mp.write_text(json.dumps(candidate_manifest),encoding='utf-8')
                    candidate=copy.deepcopy(original_runtime);candidate['manifest']=pin(mp)
                    rp=runtime_path.parent/(label+'-runtime.json');rp.write_text(json.dumps(candidate),encoding='utf-8')
                    rejected=Selection(rp,products_path,'authored-product','core').preflight()
                    assert rejected['status']=='BLOCKED' and rejected['blockers']==[root_failure],rejected
                assert manifest_path.read_bytes()==original_bytes
                sys.path[:0]=[str(repository/'ck3_autonomous_player/src'),
                              str(repository/'ck3_autonomous_player/tests/unit')]
                from test_ck3_mod_acceptance_failed_resource_closure import assert_java_produced_source_consumers
                assert_java_produced_source_consumers(runtime_path)
                from test_canonical_host_successor import assert_prisoner_preview_runtime_consumers
                assert_prisoner_preview_runtime_consumers(runtime_path,selected.argv)
                print('actual Java runtime -> public Selection.preflight; ready plus four missing/type negatives; live false')
                print('actual Java source index -> CaseClient.normal_close and preserved typed observer consumers; originals unchanged')
                """;
        PythonResult result = python(program, List.of(repository.toString(), runtime.toString(), products.toString()));
        assertEquals(0, result.exitCode(), result.output());
        assertTrue(result.output().contains("actual Java runtime -> public Selection.preflight"), result.output());
        String presetProgram = """
                from pathlib import Path
                import copy,json,sys
                repository,runtime_path,preset_manifest,initial_reform_manifest,core_manifest,preset_product=map(Path,sys.argv[1:])
                sys.path.insert(0,str(repository/'tools'))
                from ck3_mod_acceptance import Selection,pin
                original_runtime=json.loads(runtime_path.read_bytes())
                original_manifest=json.loads(Path(original_runtime['manifest']['path']).read_bytes())
                # Use the normal registry templates and unchanged runtime.repo_root.
                # Prepared pins are the actual consumer inputs; the composer index
                # must contain byte-identical copies, not substitute test-only paths.
                from unittest.mock import patch
                from ck3_mod_acceptance_prepare import CONFIG_NAMES
                source=Path(original_runtime['paths']['source_root'])
                repo=Path(original_runtime['repo_root'])
                prepared_cases=[]
                for case_id,fixture_manifest in [('core',core_manifest),('sect_presets',preset_manifest),('initial_reform',initial_reform_manifest)]:
                    case_output=runtime_path.parent/case_id;case_output.mkdir()
                    registry=json.loads((repository/'tools/ck3_mod_acceptance_products.json').read_bytes())
                    preset=next(c for c in registry['products']['dynastic-esotericism']['cases'] if c['id']==case_id)
                    public={'schema':registry['schema'],'product_inventory':registry['product_inventory'],
                            'products':{'dynastic-esotericism':{'cases':[preset]}}}
                    catalog=case_output/'preset-products.json';catalog.write_text(json.dumps(public),encoding='utf-8')
                    preset_selected=Selection(runtime_path,catalog,'dynastic-esotericism',case_id)
                    assert preset_selected.adapter_config==repo/f'tools/ck3_mod_acceptance_cases/dynastic_esotericism_{case_id}.json'
                    assert '--private-player-rite-creation-actions' in preset_selected.argv
                    assert '--case-read-only-mcp-tool' in preset_selected.argv
                    declared=[preset_selected.argv[i+1] for i,v in enumerate(preset_selected.argv) if v=='--case-read-only-mcp-tool']
                    assert 'ck3_query_player_religion_reform_context_v1' in declared
                    for unavailable in ('ck3_query_player_religion_tenets_v1','ck3_query_player_rite_governance_v1'):
                        assert unavailable not in preset['required_mcp_tools']
                        assert unavailable not in declared
                        assert unavailable not in original_manifest['capabilities']
                    for key in ('opt_in_player_rite_creation_actions','ck3_query_player_rite_creation_action_context_v1',
                                'ck3_execute_player_rite_creation_action_v1','ck3_collect_player_rite_creation_action_result_v1'):
                        bad=copy.deepcopy(public);case=bad['products']['dynastic-esotericism']['cases'][0]
                        if key=='opt_in_player_rite_creation_actions':case[key]=False
                        else:case['required_mcp_tools'].remove(key)
                        path=case_output/(key+'-invalid-products.json');path.write_text(json.dumps(bad),encoding='utf-8')
                        try:Selection(runtime_path,path,'dynastic-esotericism',case_id)
                        except ValueError:pass
                        else:raise AssertionError('accepted invalid public rite action gate '+key)
                    inputs=case_output/'preset-inputs.json';plain={}
                    for name in CONFIG_NAMES:
                        path=case_output/('plain-'+name);path.parent.mkdir(parents=True,exist_ok=True)
                        path.write_text('authored plain configuration',encoding='utf-8');plain[name]=pin(path)
                    inputs.write_text(json.dumps({'state_dir':str(case_output/'preset-state'),
                        'case_inputs':{'product_dir':str(preset_product),'plain_configuration':plain,
                                      'prebuilt_fixture_manifest':pin(fixture_manifest)}}),encoding='utf-8')
                    # Installed-engine identity is an authored boundary only. Exercise
                    # Selection.prepare -> generic.prepare_case -> actual profile builder.
                    identity={'game_version':original_manifest['game']['version'],'exe_sha256':original_manifest['game']['exe_sha256']}
                    with patch('ck3_mod_acceptance_prepare._engine',return_value=(None,identity)):
                        prepared_result=preset_selected.prepare(inputs,case_output/'preset-prepared')
                    assert prepared_result['status']=='CASE_PREPARED_NOT_ALLOCATED_NOT_RUN'
                    prepared_path=Path(prepared_result['prepared_case']['path'])
                    prepared=json.loads(prepared_path.read_bytes())
                    mounted=Path(prepared['preparation']['profile_preparation']['profile'])/'mod-content/product'
                    actual_product={p.relative_to(mounted).as_posix():p.read_bytes() for p in mounted.rglob('*') if p.is_file()}
                    assert len(actual_product)==56
                    assert actual_product=={p.relative_to(preset_product).as_posix():p.read_bytes()
                                            for p in preset_product.rglob('*') if p.is_file()}
                    if case_id=='core':
                        manifest=json.loads(fixture_manifest.read_bytes())
                        assert len(manifest['files'])==13 and len(manifest['receipt']['required_markers'])==25
                        fixture=Path(prepared['preparation']['profile_preparation']['profile'])/'mod-content/fixture'
                        compiled=json.loads((fixture/'_case_contract.json').read_bytes())
                        current=json.loads((repo/'tools/ck3_mod_acceptance_cases/dynastic_esotericism_core.json').read_bytes())
                        assert compiled['config']==current and len(current['gui_phases'])==6
                        phase=current['gui_phases'][0]
                        assert len(phase['requirements'])==7
                        assert phase['requirements'][-1]=='actual_reused_dynasty_and_join_house_renamed_to_rite_preserve_original_coa_fields_objects_and_designs_no_product_new_dynasty_or_founder_NPC'
                        assert 'both_original_coa_objects_designs_unchanged' not in json.dumps(compiled)
                        assert compiled['required_markers']==manifest['receipt']['required_markers']
                        source_fixture=Path(manifest['fixture_root'])
                        for relative in manifest['files']:
                            assert (fixture/relative).read_bytes()==(source_fixture/relative).read_bytes()
                    index=json.loads(Path(original_runtime['paths']['source_index']).read_bytes())
                    for field,relative in [('adapter','tools/ck3_mod_acceptance_cases/generic_product_adapter.py'),
                                           ('contract',f'tools/ck3_mod_acceptance_cases/dynastic_esotericism_{case_id}.json')]:
                        active=pin(repo/relative);frozen=pin(source/relative)
                        assert prepared[field]==active
                        assert {k:active[k] for k in ('bytes','sha256')}==index['files'][relative]
                        assert active['bytes']==frozen['bytes'] and active['sha256']==frozen['sha256']
                        assert (repo/relative).read_bytes()==(source/relative).read_bytes()
                    resumed=Selection(runtime_path,catalog,'dynastic-esotericism',case_id,prepared_path=prepared_path)
                    assert resumed.prepared['contract']==prepared['contract']
                    assert resumed.prepared['adapter']==prepared['adapter']
                    if case_id in ('sect_presets','initial_reform'):
                        preflight=resumed.preflight()
                        assert preflight['blockers']==[],preflight
                        assert preflight['status']=='READY_FOR_EXISTING_REVIEWED_LAUNCH',preflight
                        assert preflight['business_acceptance']=='NOT_ASSESSED',preflight
                        root_status=preflight['tool_status']['ck3_query_campaign_root_context_v1']
                        assert root_status['source_build_ready'] is True,root_status
                        assert root_status['actual_live_qualified'] is False,root_status
                        assert pin(Path(root_status['evidence']['path']))==root_status['evidence']
                    assert prepared['preparation']['business_pass'] is False and prepared['runtime_status']=='NOT_RUN'
                    prepared_cases.append((case_id,catalog,prepared_path,preset_selected.adapter_config))
                    print('actual '+case_id+' Java fixture/release -> normal registry Selection.prepare -> generic consumer -> Prepared exact pins and composer index; gate/source corruption negatives; live false')
                for case_id,catalog,prepared_path,config in prepared_cases:
                    original=config.read_bytes()
                    config.write_bytes(original+b' ')
                    try:
                        bad=Selection(runtime_path,catalog,'dynastic-esotericism',case_id,prepared_path=prepared_path)
                        result=bad.preflight()
                        assert any('Pinned input changed:' in e and str(config) in e for e in result['blockers']),result
                    finally:config.write_bytes(original)
                """;
        PythonResult presetResult = python(presetProgram, List.of(repository.toString(), runtime.toString(),
                presetManifest.toString(), initialReformManifest.toString(), coreManifest.toString(), presetProduct.toString()));
        assertEquals(0, presetResult.exitCode(), presetResult.output());
        assertTrue(presetResult.output().contains("actual core Java fixture/release -> normal registry Selection.prepare"),
                presetResult.output());
        assertTrue(presetResult.output().contains("actual sect_presets Java fixture/release -> normal registry Selection.prepare"),
                presetResult.output());
        assertTrue(presetResult.output().contains("actual initial_reform Java fixture/release -> normal registry Selection.prepare"),
                presetResult.output());
        String headProgram = """
                from pathlib import Path
                import json,sys
                from unittest.mock import patch
                repository,runtime_path,product=map(Path,sys.argv[1:4])
                runtime=json.loads(runtime_path.read_bytes())
                manifest=json.loads(Path(runtime['manifest']['path']).read_bytes())
                source=Path(runtime['paths']['source_root']);repo=Path(runtime['repo_root'])
                # The real host starts from frozen tools. Preserve that lookup order
                # for lazy saved-profile imports instead of falling back to Main12.
                sys.path[:0]=[str(source/'tools'),str(repository/'tools')]
                from ck3_mod_acceptance import Selection,pin
                from ck3_mod_acceptance_prepare import CONFIG_NAMES
                index=json.loads(Path(runtime['paths']['source_index']).read_bytes())
                registry=json.loads((repository/'tools/ck3_mod_acceptance_products.json').read_bytes())
                declared={c['id']:c for c in registry['products']['dynastic-esotericism']['cases']}
                prepared_count=blocked_count=0
                for fixture_manifest in map(Path,sys.argv[4:]):
                    fixture=json.loads(fixture_manifest.read_bytes());case_id=fixture['case_id']
                    saved=case_id.endswith(('_cold','_restore'));restore=case_id.endswith('_restore')
                    root=runtime_path.parent/('public-'+case_id);root.mkdir()
                    case=declared[case_id]
                    assert case['status']=='ready'
                    catalog=root/'products.json'
                    catalog.write_text(json.dumps({'schema':registry['schema'],'product_inventory':registry['product_inventory'],
                        'products':{'dynastic-esotericism':{'cases':[case]}}}),encoding='utf-8')
                    selected=Selection(runtime_path,catalog,'dynastic-esotericism',case_id)
                    assert selected.case['status']=='ready'
                    plain={}
                    for name in CONFIG_NAMES:
                        path=root/('plain-'+name);path.parent.mkdir(parents=True,exist_ok=True)
                        path.write_text('authored plain configuration',encoding='utf-8');plain[name]=pin(path)
                    values={'state_dir':str(root/'state'),'case_inputs':{'product_dir':str(product),
                        'plain_configuration':plain,'prebuilt_fixture_manifest':pin(fixture_manifest)}}
                    if saved:
                        original=root/'authored-not-engine-save.ck3';original.write_bytes(b'authored test input')
                        values['saved_campaign']={'save':str(original),'bytes':original.stat().st_size,
                            'sha256':pin(original)['sha256'],'player_id':123,'date_raw':456}
                        values['case_inputs']['post_start']={'government_key':'feudal_government',
                            'primary_title_tier_key':'empire','independent':True}
                    inputs=root/'inputs.json';inputs.write_text(json.dumps(values),encoding='utf-8')
                    identity={'game_version':manifest['game']['version'],'exe_sha256':manifest['game']['exe_sha256']}
                    if restore:
                        # Public preparation requires the frozen shared verifier and genuine S1 input.
                        with patch('ck3_mod_acceptance_prepare._engine',return_value=(None,identity)):
                            try:selected.prepare(inputs,root/'prepared')
                            except (ValueError,KeyError):pass
                            else:raise AssertionError('restoration without typed S1 prepared')
                        assert not (root/'state').exists()
                        assert not any((root/'prepared').rglob('dlc_load.json'))
                        blocked_count+=1
                        continue
                    with patch('ck3_mod_acceptance_prepare._engine',return_value=(None,identity)):
                        result=selected.prepare(inputs,root/'prepared')
                    prepared_count+=1
                    assert result['status']=='CASE_PREPARED_NOT_ALLOCATED_NOT_RUN'
                    prepared_path=Path(result['prepared_case']['path'])
                    prepared=json.loads(prepared_path.read_bytes())
                    for field,relative in [('adapter','tools/ck3_mod_acceptance_cases/generic_product_adapter.py'),
                                           ('contract',f'tools/ck3_mod_acceptance_cases/dynastic_esotericism_{case_id}.json')]:
                        active=pin(repo/relative);frozen=pin(source/relative)
                        assert prepared[field]==active
                        assert {k:active[k] for k in ('bytes','sha256')}==index['files'][relative]
                        assert active['bytes']==frozen['bytes'] and active['sha256']==frozen['sha256']
                    resumed=Selection(runtime_path,catalog,'dynastic-esotericism',case_id,prepared_path=prepared_path)
                    assert resumed.prepared['contract']==prepared['contract']
                    assert prepared['preparation']['business_pass'] is False and prepared['runtime_status']=='NOT_RUN'
                    if saved:
                        import xar_autoplayer
                        import xar_autoplayer.saved_campaign_profile_inventory_v2 as inventory
                        import ck3_mod_acceptance_saved_profile_v2 as saved_tool
                        assert Path(xar_autoplayer.__file__).resolve()==(source/'ck3_autonomous_player/src/xar_autoplayer/__init__.py').resolve()
                        for module,relative in [(inventory,'ck3_autonomous_player/src/xar_autoplayer/saved_campaign_profile_inventory_v2.py'),
                            (saved_tool,'tools/ck3_mod_acceptance_saved_profile_v2.py')]:
                            frozen=source/relative;active=repo/relative
                            assert Path(module.__file__).resolve()==frozen.resolve()
                            actual=pin(frozen)
                            assert {k:actual[k] for k in ('bytes','sha256')}==index['files'][relative]
                            assert active.read_bytes()==frozen.read_bytes()
                assert prepared_count==5 and blocked_count==2,(prepared_count,blocked_count)
                print('actual five executable scoped Java fixtures/runtime -> normal Selection.prepare/Prepared and frozen source pins; two restore preparations rejected; live false')
                """;
        List<String> headArguments = new ArrayList<>(List.of(repository.toString(), runtime.toString(), presetProduct.toString()));
        headArguments.addAll(headManifests.stream().map(Path::toString).toList());
        PythonResult headResult = python(headProgram, headArguments);
        assertEquals(0, headResult.exitCode(), headResult.output());
        assertTrue(headResult.output().contains("actual five executable scoped Java fixtures/runtime -> normal Selection.prepare"),
                headResult.output());

    }

    @Test
    void freezesCurrentInputsPreservesParentFieldsAndRecordsRealDifferences()
            throws IOException, NoSuchAlgorithmException, InterruptedException {
        Path repo = temporary.resolve("repo");
        Path sdk = repo.resolve("ck3_autonomous_player/src/xar_autoplayer");
        Path tools = repo.resolve("tools");
        Files.createDirectories(sdk);
        Files.createDirectories(tools.resolve("ck3_mod_acceptance_cases"));
        Path changed = sdk.resolve("__init__.py");
        Files.writeString(changed, "# actual source now differs\n");
        Path currentFactory = sdk.resolve("bridge/mcp_server.py");
        Files.createDirectories(currentFactory.getParent());
        Path actualRepository = Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
        Files.copy(actualRepository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"), currentFactory);
        for (String name : List.of("native_driver.py", "player_prisoner_collection_private_transport.py",
                "prisoner_release_preview_contract_12003.py", "prisoner_negotiated_preview_contract_12003.py",
                "prisoner_selected_quote_source_contract_12004.py", "frontend_fixture_start_contract.py", "frontend_fixture_scenario_start_v1.py")) {
            Files.copy(actualRepository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge").resolve(name),
                    currentFactory.getParent().resolve(name));
        }
        // Cold profile preparation consumes this real tool/model pair lazily.
        // Include both in the actual Java composer input, not ambient SDK fallback.
        Files.copy(actualRepository.resolve("ck3_autonomous_player/src/xar_autoplayer/saved_campaign_profile_inventory_v2.py"),
                sdk.resolve("saved_campaign_profile_inventory_v2.py"));
        Files.copy(actualRepository.resolve("tools/ck3_mod_acceptance_saved_profile_v2.py"),
                tools.resolve("ck3_mod_acceptance_saved_profile_v2.py"));
        String fixtureMachine = JSON.readTree(actualRepository.resolve("tools/fixtures/ck3_r11_failed_resource_closure.json").toFile())
                .path("machine_id").textValue();
        for (String name : List.of("normal_exit_process_observer_v1.py", "normal_exit_contract_v1.py",
                "normal_exit_public_wire_v2.py", "normal_exit_pending_observer_v1.py")) {
            Files.copy(actualRepository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge").resolve(name),
                    currentFactory.getParent().resolve(name));
        }
        Path canonicalHost = repo.resolve("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py");
        Files.createDirectories(canonicalHost.getParent());
        Files.copy(actualRepository.resolve("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"),
                canonicalHost);
        for (String name : List.of("ck3_mod_acceptance_launcher.py", "ck3_mod_acceptance_queue.py", "ck3_mod_acceptance_keeper.py",
                "ck3_mod_acceptance_build_runtime.py", "codex_task_bus.py", "build_normal_exit_source_inventory_v1.py")) {
            Files.writeString(tools.resolve(name), "# authored tool\n");
        }
        Path normalExitBuilder = tools.resolve("build_normal_exit_source_inventory_v1.py");
        Files.writeString(normalExitBuilder, "# authored normal-exit source inventory builder\n");
        Path leaseHelper = repo.resolve("promo/ck3_native_war_ai/integration/screen_bus_lease.py");
        Files.createDirectories(leaseHelper.getParent());
        Files.writeString(leaseHelper, "# authored clean checkout lease helper\n");
        for (String name : List.of("__init__.py", "generic_product_adapter.py", "dynastic_esotericism_core.json",
                "dynastic_esotericism_cold_reload.json", "dynastic_esotericism_old_save_bootstrap.json",
                "dynastic_esotericism_pre_product_seed.json", "dynastic_esotericism_sect_presets.json",
                "dynastic_esotericism_initial_reform.json",
                "dynastic_esotericism_native_binding_transfer.json",
                "dynastic_esotericism_empire_heads_procreation.json",
                "dynastic_esotericism_empire_heads_procreation_cold.json",
                "dynastic_esotericism_empire_heads_procreation_restore.json",
                "dynastic_esotericism_empire_heads_vivhite.json",
                "dynastic_esotericism_empire_heads_vivhite_cold.json",
                "dynastic_esotericism_empire_heads_vivhite_restore.json")) {
            Files.writeString(tools.resolve("ck3_mod_acceptance_cases").resolve(name), "{}\n");
        }
        for (String name : List.of("generic_product_adapter.py", "dynastic_esotericism_core.json", "dynastic_esotericism_sect_presets.json",
                "dynastic_esotericism_initial_reform.json",
                "dynastic_esotericism_native_binding_transfer.json",
                "dynastic_esotericism_empire_heads_procreation.json",
                "dynastic_esotericism_empire_heads_procreation_cold.json",
                "dynastic_esotericism_empire_heads_procreation_restore.json",
                "dynastic_esotericism_empire_heads_vivhite.json",
                "dynastic_esotericism_empire_heads_vivhite_cold.json",
                "dynastic_esotericism_empire_heads_vivhite_restore.json")) {
            Files.copy(actualRepository.resolve("tools/ck3_mod_acceptance_cases").resolve(name),
                    tools.resolve("ck3_mod_acceptance_cases").resolve(name), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
        Path fixtureMain = Path.of("mod_dynastic_esotericism/tools/src/main");
        for (String relative : List.of("java/org/xar/ck3/dynastic/acceptance/FixtureEmitter.java",
                "resources/acceptance-fixture/descriptor.mod",
                "resources/acceptance-fixture/common/on_action/des_acceptance_on_actions.txt",
                "resources/acceptance-fixture/common/decisions/des_acceptance_decisions.txt",
                "resources/acceptance-fixture/localization/english/des_acceptance_l_english.yml",
                "resources/acceptance-fixture/localization/simp_chinese/des_acceptance_l_simp_chinese.yml",
                "resources/acceptance-fixture/common/scripted_effects/des_acceptance_extended_effects.txt",
                "resources/acceptance-fixture/common/decisions/des_acceptance_extended_decisions.txt",
                "resources/acceptance-fixture/common/on_action/des_acceptance_extended_on_actions.txt",
                "resources/acceptance-fixture/events/des_acceptance_extended_events.txt",
                "resources/acceptance-fixture/localization/english/des_acceptance_extended_l_english.yml",
                "resources/acceptance-fixture/localization/simp_chinese/des_acceptance_extended_l_simp_chinese.yml",
                "resources/acceptance-fixture/common/on_action/des_preset_acceptance_on_actions.txt",
                "resources/acceptance-fixture/common/decisions/des_preset_acceptance_decisions.txt",
                "resources/acceptance-fixture/localization/english/des_preset_acceptance_l_english.yml",
                "resources/acceptance-fixture/localization/simp_chinese/des_preset_acceptance_l_simp_chinese.yml",
                "resources/acceptance-fixture/common/on_action/des_initial_reform_acceptance_on_actions.txt",
                "resources/acceptance-fixture/common/scripted_effects/des_initial_reform_acceptance_effects.txt",
                "resources/acceptance-fixture/common/scripted_effects/des_acceptance_effects.txt",
                "resources/acceptance-fixture/events/des_acceptance_events.txt",
                "resources/acceptance-fixture/common/decisions/des_transfer_acceptance_decisions.txt",
                "resources/acceptance-fixture/localization/english/des_transfer_acceptance_l_english.yml",
                "resources/acceptance-fixture/localization/simp_chinese/des_transfer_acceptance_l_simp_chinese.yml",
                "resources/acceptance-fixture/common/bookmarks/bookmarks/des_empire_1066_byzantium.txt",
                "resources/acceptance-fixture/common/on_action/des_empire_heads_acceptance_on_actions.txt",
                "resources/acceptance-fixture/common/decisions/des_empire_heads_acceptance_decisions.txt",
                "resources/acceptance-fixture/events/des_empire_heads_acceptance_events.txt",
                "resources/acceptance-fixture/common/decisions/des_empire_heads_readback_decisions.txt",
                "resources/acceptance-fixture/localization/english/des_empire_heads_acceptance_l_english.yml",
                "resources/acceptance-fixture/localization/simp_chinese/des_empire_heads_acceptance_l_simp_chinese.yml")) {
            Path destination = repo.resolve(fixtureMain).resolve(relative);
            Files.createDirectories(destination.getParent());
            Files.copy(actualRepository.resolve(fixtureMain).resolve(relative), destination);
        }
        FixtureEmitter.Emission presetFixture = FixtureEmitter.emit(repo, temporary.resolve("preset-fixture"),
                fixtureMachine, FixtureEmitter.CaseKind.SECT_PRESETS);
        FixtureEmitter.Emission initialReformFixture = FixtureEmitter.emit(repo, temporary.resolve("initial-reform-fixture"),
                fixtureMachine, FixtureEmitter.CaseKind.INITIAL_REFORM);
        FixtureEmitter.Emission coreFixture = FixtureEmitter.emit(repo, temporary.resolve("core-fixture"),
                fixtureMachine, FixtureEmitter.CaseKind.CORE);
        assertEquals(13, coreFixture.payload().files().size());
        assertEquals(25, coreFixture.payload().receipt().requiredMarkers().size());
        List<Path> headManifests = new ArrayList<>();
        for (FixtureEmitter.CaseKind kind : List.of(FixtureEmitter.CaseKind.EMPIRE_HEADS_PROCREATION,
                FixtureEmitter.CaseKind.EMPIRE_HEADS_VIVHITE,
                FixtureEmitter.CaseKind.EMPIRE_HEADS_PROCREATION_COLD,
                FixtureEmitter.CaseKind.EMPIRE_HEADS_VIVHITE_COLD,
                FixtureEmitter.CaseKind.EMPIRE_HEADS_PROCREATION_RESTORE,
                FixtureEmitter.CaseKind.EMPIRE_HEADS_VIVHITE_RESTORE,
                FixtureEmitter.CaseKind.NATIVE_BINDING_TRANSFER)) {
            headManifests.add(FixtureEmitter.emit(repo, temporary.resolve("head-" + kind.wireValue()),
                    fixtureMachine, kind).manifest());
        }
        ReleaseBuilder.BuildResult presetProduct = new ReleaseBuilder().build(ReleaseProduct.official(
                actualRepository.resolve("mod_dynastic_esotericism"), ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION),
                actualRepository, temporary.resolve("preset-release"), "0".repeat(40), null, null);
        assertEquals(56, presetProduct.payload().files().size());
        Path oldRepo = temporary.resolve("previous-repo");
        ObjectNode old = pin(changed);
        old.put("path", oldRepo.resolve("ck3_autonomous_player/src/xar_autoplayer/__init__.py").toString());
        old.put("sha256", "0".repeat(64));
        Path parentIndex = temporary.resolve("parent-source.json");
        ObjectNode parentSource = JSON.createObjectNode();
        parentSource.put("schema", "xar.e04.r15.selected-source-index.v1");
        parentSource.put("machine_id", fixtureMachine);
        parentSource.putArray("files").add(old);
        write(parentIndex, parentSource);
        ObjectNode manifest = JSON.createObjectNode();
        manifest.put("schema", "ck3-mod-acceptance-shared-runtime-v1");
        manifest.put("machine_id", fixtureMachine);
        manifest.putObject("native");
        ObjectNode retainedCapability = manifest.putObject("capabilities").putObject("ck3_take_snapshot");
        retainedCapability.put("source_build_ready", true);
        retainedCapability.put("actual_live_qualified", false);
        retainedCapability.put("parent_marker", "preserve exact parent capability");
        manifest.putObject("host_features");
        manifest.putObject("source_root").put("path_key", "source_root");
        ObjectNode parentSourceMetadata = manifest.putObject("source_index");
        ObjectNode sourceIdentity = pin(parentIndex);
        parentSourceMetadata.put("path_key", "source_index");
        parentSourceMetadata.set("bytes", sourceIdentity.get("bytes"));
        parentSourceMetadata.set("sha256", sourceIdentity.get("sha256"));
        manifest.put("preserved_unknown_parent_field", "retain exactly");
        Path game = temporary.resolve("game");
        Files.createDirectories(game.resolve("binaries"));
        Path executable = game.resolve("binaries/ck3.exe");
        Files.writeString(executable, "authored test bytes, never executed");
        manifest.putObject("game").put("version", "authored-not-a-game-qualification")
                .put("exe_sha256", pin(executable).path("sha256").textValue());
        Path parentManifest = temporary.resolve("parent-manifest.json");
        write(parentManifest, manifest);
        ObjectNode runtime = JSON.createObjectNode();
        runtime.put("schema", "ck3-mod-acceptance-runtime-v1");
        runtime.put("machine_id", fixtureMachine);
        runtime.put("repo_root", oldRepo.toString());
        PythonResult interpreter = python("import sys; print(sys.executable)", List.of());
        assertEquals(0, interpreter.exitCode(), interpreter.output());
        runtime.put("python", interpreter.output().strip());
        runtime.put("game_dir", game.toString());
        runtime.set("manifest", pin(parentManifest));
        runtime.putObject("paths").put("source_index", parentIndex.toString()).put("source_root", oldRepo.toString())
                .put("host", canonicalHost.toString());
        ObjectNode allocation = runtime.putObject("allocation");
        allocation.put("preserved_allocation_field", 7);
        allocation.set("task_bus", pin(tools.resolve("codex_task_bus.py")));
        Path parentRegistration = temporary.resolve("old-global/registration_mcp.py");
        Files.createDirectories(parentRegistration.getParent());
        Files.writeString(parentRegistration, "# authored predecessor registration provider\n");
        ObjectNode parentOverlay = runtime.putObject("allocator_overlay");
        parentOverlay.set("parent-registration", pin(parentRegistration));
        parentOverlay.set("old-sdk", old.deepCopy());
        ObjectNode oldHost = pin(canonicalHost);
        oldHost.put("path", oldRepo.resolve("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py").toString());
        oldHost.put("sha256", "0".repeat(64));
        parentOverlay.set("old-host", oldHost);
        ObjectNode unselected = old.deepCopy();
        unselected.put("path", oldRepo.resolve("tools/unselected_previous_case.py").toString());
        parentOverlay.set("old-unselected", unselected);
        runtime.putObject("runtime_environment").putArray("PYTHONPATH").add(temporary.resolve("old-import").toString());
        Path parentRuntime = temporary.resolve("parent-runtime.json");
        write(parentRuntime, runtime);
        ObjectNode projection = JSON.createObjectNode();
        projection.put("schema", "ck3-common-canonical-host-successor-v1");
        projection.put("machine_id", fixtureMachine);
        projection.put("qualification", "SOURCE_PROJECTION_ONLY_LIVE_NOT_QUALIFIED");
        projection.put("runtime_binding", temporary.resolve("successor/runtime.json").toString());
        projection.set("parent_runtime", pin(parentRuntime));
        projection.set("parent_manifest", pin(parentManifest));
        projection.set("parent_host", pin(canonicalHost));
        projection.set("canonical_host", pin(canonicalHost));
        projection.set("producer", pin(tools.resolve("ck3_mod_acceptance_build_runtime.py")));
        projection.set("projected_host", pin(canonicalHost));
        projection.put("game_started", false);
        projection.put("allocated", false);
        projection.put("actual_live_qualified", false);
        Path projectedRegistration = temporary.resolve("registration_mcp.py");
        Files.writeString(projectedRegistration, "# authored same-service current-factory projection\n");
        ObjectNode registrationProjection = projection.putObject("registration_projection");
        registrationProjection.set("parent", pin(parentRegistration));
        registrationProjection.set("current_factory", pin(currentFactory));
        registrationProjection.set("projected", pin(projectedRegistration));
        registrationProjection.put("binding", "existing_same_service_builder_to_current_global_factory");
        Path projectionPath = temporary.resolve("host-projection.json");
        write(projectionPath, projection);
        Path dll = temporary.resolve("authored.dll");
        Files.writeString(dll, "authored compile output, not native qualification");
        Path flagsPath = temporary.resolve("flags.json");
        ObjectNode flags = JSON.createObjectNode();
        for (String part : List.of("CONTEXT", "DOCTRINES", "DOCTRINE_KNOWLEDGE", "DOCTRINE_CATALOGUE", "REFORM_CONTEXT", "DRAFT_GROUPS", "DRAFT_DOCTRINE_CHOICES", "DRAFT_TENET_CHOICES", "DRAFT_RESOURCE_COSTS")) {
            flags.put("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_" + part + "_PRIVATE_QUERY_V1", "ON");
        }
        flags.put("XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1", "ON");
        flags.put("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1", "OFF");
        flags.put("XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1", "OFF");
        flags.put("XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1", "ON");
        flags.put("XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1", "ON");
        flags.put("XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1", "OFF");
        flags.put("XAR_ENABLE_RELIGION_UI12004_PRESENTATION", "ON");
        flags.put("XAR_ENABLE_RITE_CREATION_ACTIONS12004", "ON");
        flags.put("XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1", "ON");
        flags.put("XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1", "ON");
        write(flagsPath, flags);
        ObjectNode nativeIndex = JSON.createObjectNode();
        nativeIndex.put("schema", "xar.common-native-qualified-producer-index.v1");
        nativeIndex.put("machine_id", fixtureMachine);
        nativeIndex.put("live_qualified", false);
        ObjectNode nativeTools = nativeIndex.putObject("runtime_native_tools");
        nativeTools.set("dll", pin(dll));
        nativeTools.set("injector", pin(dll));
        nativeIndex.set("feature_flags", pin(flagsPath));
        nativeIndex.set("cmake_cache", pin(dll));
        nativeIndex.set("native_source_manifest", pin(dll));
        Path waitPath = temporary.resolve("producer-wait.json");
        ObjectNode wait = JSON.createObjectNode();
        wait.put("machine_id", fixtureMachine);
        wait.put("returncode", 0);
        wait.put("game_execution", false);
        wait.put("live_qualified", false);
        write(waitPath, wait);
        nativeIndex.set("producer_original_wait", pin(waitPath));
        Path buildPath = temporary.resolve("build-output.json");
        ObjectNode build = JSON.createObjectNode();
        build.put("machine_id", fixtureMachine);
        build.put("compiler_linker_returncode", 0);
        build.put("outer_producer_returncode", 0);
        build.put("game_execution", false);
        build.put("live_qualified", false);
        build.set("bridge_DLL", pin(dll));
        build.set("reused_injector", pin(dll));
        build.set("feature_flags", pin(flagsPath));
        build.set("cache", pin(dll));
        build.set("source_manifest", pin(dll));
        build.set("producer_original_wait", pin(waitPath));
        write(buildPath, build);
        nativeIndex.set("build_output", pin(buildPath));
        nativeIndex.set("production_qualification", pin(buildPath));
        Path nativePath = temporary.resolve("native-index.json");
        write(nativePath, nativeIndex);
        Path output = temporary.resolve("successor");
        SharedRuntimeComposer.Result result = SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, output, fixtureMachine);
        JsonNode actual = JSON.readTree(Path.of(result.runtime()).toFile());
        JsonNode actualManifest = JSON.readTree(Path.of(result.manifest()).toFile());
        JsonNode actualIndex = JSON.readTree(Path.of(result.sourceIndex()).toFile());
        assertEquals("retain exactly", actualManifest.path("preserved_unknown_parent_field").textValue());
        assertEquals(7, actual.path("allocation").path("preserved_allocation_field").intValue());
        assertEquals(1, actualIndex.path("actual_changed_parent_files").size());
        assertEquals(38, result.copiedFiles(),
                "36 existing sources plus frontend_fixture_start_contract.py and frontend_fixture_scenario_start_v1.py");
        assertEquals("ck3-common-source-index-v1", actualIndex.path("schema").textValue());
        assertTrue(actualIndex.path("files").isObject());
        assertEquals(result.copiedFiles(), actualIndex.path("files").size());
        for (String name : List.of("dynastic_esotericism_native_binding_transfer.json",
                "dynastic_esotericism_empire_heads_procreation.json",
                "dynastic_esotericism_empire_heads_procreation_cold.json",
                "dynastic_esotericism_empire_heads_procreation_restore.json",
                "dynastic_esotericism_empire_heads_vivhite.json",
                "dynastic_esotericism_empire_heads_vivhite_cold.json",
                "dynastic_esotericism_empire_heads_vivhite_restore.json")) {
            assertTrue(actualIndex.path("files").has("tools/ck3_mod_acceptance_cases/" + name));
        }
        for (String name : List.of("frontend_fixture_start_contract.py", "frontend_fixture_scenario_start_v1.py")) {
            String relative = "ck3_autonomous_player/src/xar_autoplayer/bridge/" + name;
            Path frozen = output.resolve("source").resolve(relative);
            assertEquals(Files.readString(repo.resolve(relative)), Files.readString(frozen));
            assertEquals(pin(frozen).path("sha256"), actualIndex.path("files").path(relative).path("sha256"));
            assertFalse(repo.resolve(relative).toRealPath().equals(frozen.toRealPath()));
        }
        Path presetSource = tools.resolve("ck3_mod_acceptance_cases/dynastic_esotericism_sect_presets.json");
        Path frozenPreset = output.resolve("source/tools/ck3_mod_acceptance_cases/dynastic_esotericism_sect_presets.json");
        assertEquals(Files.readString(presetSource), Files.readString(frozenPreset));
        JsonNode presetMetadata = actualIndex.path("files").path("tools/ck3_mod_acceptance_cases/dynastic_esotericism_sect_presets.json");
        assertEquals(pin(frozenPreset).path("bytes"), presetMetadata.path("bytes"));
        assertEquals(pin(frozenPreset).path("sha256"), presetMetadata.path("sha256"));
        Path frozenNormalExitBuilder = output.resolve("source/tools/build_normal_exit_source_inventory_v1.py");
        assertEquals(Files.readString(normalExitBuilder), Files.readString(frozenNormalExitBuilder));
        assertFalse(normalExitBuilder.toRealPath().equals(frozenNormalExitBuilder.toRealPath()));
        ObjectNode frozenNormalExitBuilderPin = pin(frozenNormalExitBuilder);
        JsonNode normalExitBuilderMetadata = actualIndex.path("files").path("tools/build_normal_exit_source_inventory_v1.py");
        assertEquals(2, normalExitBuilderMetadata.size());
        assertEquals(frozenNormalExitBuilderPin.path("bytes"), normalExitBuilderMetadata.path("bytes"));
        assertEquals(frozenNormalExitBuilderPin.path("sha256"), normalExitBuilderMetadata.path("sha256"));
        assertEquals(38, SharedRuntimeComposer.parentSourceFiles((ObjectNode) actualIndex,
                output.resolve("source"), fixtureMachine).size());
        assertEquals(pin(Path.of(result.sourceIndex())).path("sha256"), actualManifest.path("source_index").path("sha256"));
        assertEquals(pin(Path.of(result.manifest())), actual.path("manifest"));
        JsonNode admission = JSON.readTree(output.resolve("SOURCE-BUILD-ADMISSION.json").toFile());
        assertEquals(pin(Path.of(result.sourceIndex())), admission.path("source_index"));
        assertEquals(admission, actualManifest.path("shared_successor"));
        assertEquals(projectedRegistration.toRealPath().toString(), actual.path("allocator_overlay")
                .path("current-global-registration-provider").path("path").textValue());
        assertEquals(leaseHelper.toRealPath().toString(), actual.path("allocator_overlay")
                .path("clean-lease-screen-helper").path("path").textValue());
        assertEquals(output.resolve("source/ck3_autonomous_player/src/xar_autoplayer/__init__.py").toRealPath().toString(),
                actual.path("allocator_overlay").path("old-sdk").path("path").textValue());
        assertEquals(canonicalHost.toRealPath().toString(), actual.path("allocator_overlay").path("old-host").path("path").textValue());
        assertFalse(actual.path("allocator_overlay").has("old-unselected"));
        assertEquals(parentOverlay, actual.path("parent_allocator_overlay"));
        assertEquals(3, actualIndex.path("allocator_overlay_projection").size());
        assertTrue(Files.isDirectory(output.resolve("userdirs")));
        assertEquals(SharedRuntimeComposer.Qualification.SHARED_SOURCE_AND_NATIVE_BUILD_SUCCESSOR_LIVE_NOT_QUALIFIED,
                result.qualification());
        assertFalse(actualManifest.path("capabilities").path("ck3_execute_player_rite_creation_action_v1").path("actual_live_qualified").booleanValue());
        assertEquals(retainedCapability, actualManifest.path("capabilities").path("ck3_take_snapshot"));
        JsonNode campaignRoot = actualManifest.path("capabilities").path("ck3_query_campaign_root_context_v1");
        assertTrue(campaignRoot.path("source_build_ready").isBoolean());
        assertTrue(campaignRoot.path("source_build_ready").booleanValue());
        assertTrue(campaignRoot.path("actual_live_qualified").isBoolean());
        assertFalse(campaignRoot.path("actual_live_qualified").booleanValue());
        assertEquals(pin(output.resolve("SOURCE-BUILD-ADMISSION.json")), campaignRoot.path("evidence"));
        JsonNode members = actualManifest.path("capabilities").path("ck3_query_player_rite_members_v1");
        assertTrue(members.path("source_build_ready").isBoolean());
        assertTrue(members.path("source_build_ready").booleanValue());
        assertTrue(members.path("actual_live_qualified").isBoolean());
        assertFalse(members.path("actual_live_qualified").booleanValue());
        assertEquals(pin(output.resolve("SOURCE-BUILD-ADMISSION.json")), members.path("evidence"));
        Path products = temporary.resolve("products.json");
        ObjectNode registry = JSON.createObjectNode();
        registry.put("schema", "ck3-mod-acceptance-products-v1");
        ObjectNode selectedCase = registry.putObject("products").putObject("authored-product").putArray("cases").addObject();
        selectedCase.put("id", "core");
        selectedCase.put("status", "ready");
        selectedCase.putObject("startup").put("mode", "ordinary_gui_campaign").put("state_dir", "{run_dir}/state");
        Path plan = temporary.resolve("plan.json");
        write(plan, JSON.createArrayNode());
        selectedCase.put("initial_plan", plan.toString());
        selectedCase.putArray("required_mcp_tools").add("ck3_take_snapshot").add("ck3_query_player_rite_members_v1")
                .add("ck3_query_player_prisoner_collection_private_v1").add("ck3_query_campaign_root_context_v1");
        selectedCase.putArray("opt_in_read_only_mcp_tools").add("ck3_query_player_rite_members_v1")
                .add("ck3_query_player_prisoner_collection_private_v1");
        selectedCase.putObject("budgets").put("command_timeout", 300).put("readiness_timeout", 1800)
                .put("timeout", 3600).put("poll_interval", 0.05).put("hold_seconds", 0);
        write(products, registry);
        assertPublicSelectionConsumesProducedRuntime(Path.of(result.runtime()), products,
                presetFixture.manifest(), initialReformFixture.manifest(), coreFixture.manifest(), presetProduct.staging(), headManifests);
        assertTrue(Files.isRegularFile(output.resolve("source/tools/ck3_mod_acceptance_cases/generic_product_adapter.py")));
        assertThrows(IllegalArgumentException.class,
                () -> SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, output, fixtureMachine));
        // Exercise the same composer path that freezes the real verifier artifact/source closure.
        for (String root : List.of("mod_dynastic_esotericism/tools/src/main/java", "java/ck3-save-core/src/main/java")) {
            try (var stream = Files.walk(actualRepository.resolve(root))) {
                for (Path sourceFile : stream.filter(p -> p.toString().endsWith(".java")).toList()) {
                    Path target = repo.resolve(actualRepository.relativize(sourceFile));
                    Files.createDirectories(target.getParent());
                    Files.copy(sourceFile, target, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                }
            }
        }
        for (String relative : List.of("mod_dynastic_esotericism/tools/pom.xml", "java/ck3-save-core/pom.xml")) {
            Path target = repo.resolve(relative); Files.createDirectories(target.getParent());
            Files.copy(actualRepository.resolve(relative), target);
        }
        Path app = Files.createDirectory(temporary.resolve("authored-verifier-app"));
        Files.writeString(app.resolve("quarkus-run.jar"), "authored artifact bytes; not executable/native/live qualification");
        Path java = Path.of(System.getProperty("java.home"), "bin",
                System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        var declaration = EmpireRestoreEvidence.packageArtifact(repo, app, java, temporary.resolve("verifier-input.json"), fixtureMachine);
        Path verifierOutput = temporary.resolve("with-verifier");
        projection.put("runtime_binding", verifierOutput.resolve("runtime.json").toString()); write(projectionPath, projection);
        var withVerifier = SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath,
                verifierOutput, fixtureMachine, Path.of(declaration.path()));
        JsonNode verifierRuntime = JSON.readTree(Path.of(withVerifier.runtime()).toFile());
        var frozenPin = org.xar.ck3.save.SaveJson.read(JSON.writeValueAsBytes(verifierRuntime.path("empire_restore_verifier")),
                org.xar.ck3.save.SaveContracts.Pin.class);
        var frozen = EmpireRestoreEvidence.readPackage(frozenPin);
        assertEquals(EmpireRestoreEvidence.pin(verifierOutput.resolve("empire-restore-verifier/quarkus-run.jar")), frozen.entrypoint());
        for (var file : frozen.producerSources()) {
            assertEquals(EmpireRestoreEvidence.pin(verifierOutput.resolve("source").resolve(file.relative())), file.pin());
            assertEquals(EmpireRestoreEvidence.pin(repo.resolve(file.relative())).sha256(), file.pin().sha256());
        }
        assertTrue(verifierRuntime.path("allocator_overlay").path("empire-restore-verifier:java").isObject());
        Path extra = app.resolve("unlisted.jar"); Files.writeString(extra, "undeclared");
        assertThrows(IllegalArgumentException.class, () -> EmpireRestoreEvidence.readPackage(declaration));
        int defect = 0;
        for (String flag : List.of("XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1",
                "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1",
                "XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1",
                "XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1",
                "XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1")) {
            boolean actionFlag = flag.equals("XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1");
            for (JsonNode invalid : List.of(JSON.getNodeFactory().textNode(actionFlag ? "ON" : "OFF"),
                    JSON.getNodeFactory().booleanNode(true), JSON.getNodeFactory().numberNode(1),
                    JSON.getNodeFactory().nullNode(), JSON.getNodeFactory().textNode("MISSING"))) {
                if (invalid.isTextual() && invalid.textValue().equals("MISSING")) flags.remove(flag);
                else flags.set(flag, invalid);
                write(flagsPath, flags);
                nativeIndex.set("feature_flags", pin(flagsPath));
                build.set("feature_flags", pin(flagsPath));
                write(buildPath, build);
                nativeIndex.set("build_output", pin(buildPath));
                nativeIndex.set("production_qualification", pin(buildPath));
                write(nativePath, nativeIndex);
                Path rejected = temporary.resolve("rejected-provider-" + defect++);
                projection.put("runtime_binding", rejected.resolve("runtime.json").toString());
                write(projectionPath, projection);
                IllegalArgumentException invalidFlag = assertThrows(IllegalArgumentException.class,
                        () -> SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, rejected, fixtureMachine));
                assertTrue(invalidFlag.getMessage().contains(actionFlag
                        ? "read-only prisoner preview requires prisoner actions compiled OFF" : "native provider not compiled: " + flag));
                assertFalse(Files.exists(rejected));
            }
            flags.put(flag, actionFlag ? "OFF" : "ON");
        }
        flags.put("XAR_ENABLE_RITE_CREATION_ACTIONS12004", "OFF");
        write(flagsPath, flags);
        nativeIndex.set("feature_flags", pin(flagsPath));
        build.set("feature_flags", pin(flagsPath));
        write(buildPath, build);
        nativeIndex.set("build_output", pin(buildPath));
        nativeIndex.set("production_qualification", pin(buildPath));
        write(nativePath, nativeIndex);
        projection.put("runtime_binding", temporary.resolve("rejected/runtime.json").toString());
        write(projectionPath, projection);
        IllegalArgumentException offFlag = assertThrows(IllegalArgumentException.class,
                () -> SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, temporary.resolve("rejected"), fixtureMachine));
        assertTrue(offFlag.getMessage().contains("native provider not compiled"));
        assertFalse(Files.exists(temporary.resolve("rejected")));
        build.put("outer_producer_returncode", true);
        write(buildPath, build);
        nativeIndex.set("build_output", pin(buildPath));
        nativeIndex.set("production_qualification", pin(buildPath));
        write(nativePath, nativeIndex);
        projection.put("runtime_binding", temporary.resolve("boolean-code-rejected/runtime.json").toString());
        write(projectionPath, projection);
        IllegalArgumentException booleanCode = assertThrows(IllegalArgumentException.class,
                () -> SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, temporary.resolve("boolean-code-rejected"), fixtureMachine));
        assertTrue(booleanCode.getMessage().contains("producer completion"));
    }

    @Test
    void canonicalParentRoundTripRejectsAliasPathsAndWrongSignatureTypes() throws IOException {
        Path root = temporary.resolve("frozen-source").toAbsolutePath();
        ObjectNode index = JSON.createObjectNode();
        index.put("schema", "ck3-common-source-index-v1").put("machine_id", "authored-machine");
        ObjectNode files = index.putObject("files");
        files.putObject("sdk/module.py").put("bytes", 3).put("sha256", "a".repeat(64));
        List<SharedRuntimeComposer.FilePin> expected = List.of(new SharedRuntimeComposer.FilePin(
                root.resolve("sdk/module.py").toString(), 3, "a".repeat(64)));
        assertEquals(expected, SharedRuntimeComposer.parentSourceFiles(index, root, "authored-machine"));
        assertEquals(expected, SharedRuntimeComposer.parentSourceFiles(
                (ObjectNode) JSON.readTree(JSON.writeValueAsBytes(index)), root, "authored-machine"));
        for (JsonNode invalid : List.of(JSON.getNodeFactory().booleanNode(true),
                JSON.getNodeFactory().numberNode(3.0), JSON.getNodeFactory().nullNode())) {
            ObjectNode bad = index.deepCopy();
            ((ObjectNode) bad.path("files").path("sdk/module.py")).set("bytes", invalid);
            assertThrows(IllegalArgumentException.class,
                    () -> SharedRuntimeComposer.parentSourceFiles(bad, root, "authored-machine"));
        }
        for (String invalid : List.of("../sdk/module.py", "/sdk/module.py", "sdk//module.py", "sdk\\module.py")) {
            ObjectNode bad = index.deepCopy();
            ObjectNode badFiles = (ObjectNode) bad.path("files");
            badFiles.set(invalid, badFiles.remove("sdk/module.py"));
            assertThrows(IllegalArgumentException.class,
                    () -> SharedRuntimeComposer.parentSourceFiles(bad, root, "authored-machine"));
        }
        ObjectNode missing = index.deepCopy();
        ((ObjectNode) missing.path("files").path("sdk/module.py")).remove("bytes");
        assertThrows(IllegalArgumentException.class,
                () -> SharedRuntimeComposer.parentSourceFiles(missing, root, "authored-machine"));
    }
}
