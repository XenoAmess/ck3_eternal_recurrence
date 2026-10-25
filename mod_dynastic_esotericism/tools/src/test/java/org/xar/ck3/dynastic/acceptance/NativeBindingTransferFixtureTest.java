package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.dynastic.release.ReleaseBuilder;
import org.xar.ck3.dynastic.release.ReleaseProduct;

/** Actual Java emission reaches the existing public consumers; no CK3 execution. */
final class NativeBindingTransferFixtureTest {
    @TempDir Path temporary;

    private static Path repository() {
        return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
    }

    private static void python(String program, List<String> arguments) throws IOException, InterruptedException {
        List<String> command = new ArrayList<>(List.of(System.getProperty("dynastic.python", "python"),
                "-B", "-X", "utf8", "-c", program));
        command.addAll(arguments);
        Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
        if (!process.waitFor(60, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor();
            throw new IOException("native transfer public consumer timed out");
        }
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertEquals(0, process.exitValue(), output);
        assertTrue(output.contains("PASS; engine_semantics_verified=false"), output);
    }

    @Test
    void actualProducerReachesPublicRegistryImportAndGenericPreparation()
            throws IOException, InterruptedException {
        ReleaseBuilder.BuildResult release = new ReleaseBuilder().build(ReleaseProduct.official(
                repository().resolve("mod_dynastic_esotericism"), ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION),
                repository(), temporary.resolve("release"), "0".repeat(40), null, null);
        assertEquals(56, release.payload().files().size());
        FixtureEmitter.Emission emission = FixtureEmitter.emit(repository(), temporary.resolve("fixture"),
                "authored-machine", FixtureEmitter.CaseKind.NATIVE_BINDING_TRANSFER);
        assertEquals(9, emission.payload().files().size());
        assertEquals(12, emission.payload().producerSourcePins().size());
        assertEquals(4, emission.payload().receipt().requiredMarkers().size());
        assertTrue(emission.payload().receipt().containsBusinessEffects());
        assertEquals(FixtureEmitter.CaseKind.NATIVE_BINDING_TRANSFER,
                FixtureEmitter.CaseKind.parse("native_binding_transfer"));
        String program = """
                from pathlib import Path
                import copy,json,sys
                from unittest.mock import patch
                repo,staging,source,outer=map(Path,sys.argv[1:]);outer.mkdir()
                sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
                from ck3_mod_acceptance_prepare import materialize_prebuilt_fixture,pin,CONFIG_NAMES
                from ck3_mod_acceptance_cases import generic_product_adapter as adapter
                manifest=json.loads(source.read_bytes());case='native_binding_transfer'
                assert manifest['case_id']==case
                registry=json.loads((repo/'tools/ck3_mod_acceptance_products.json').read_bytes())
                registration=next(c for c in registry['products']['dynastic-esotericism']['cases'] if c['id']==case)
                assert registration['status']=='ready'
                assert registration['whole_product_acceptance_credit'] is False
                assert registration['opt_in_player_rite_creation_actions'] is True
                assert registration['adapter']['path'].endswith('/generic_product_adapter.py')
                required=registration['required_mcp_tools']
                for action in ('context','result'):
                    assert any('rite_creation_action_'+action in name for name in required)
                assert 'ck3_execute_player_rite_creation_action_v1' in required
                assert 'ck3_verify_player_rite_creation_action_completed_v1' in required
                runtime=outer/'runtime.json';runtime.write_text(json.dumps({'machine_id':'authored-machine'}),encoding='utf-8')
                context={'product':'dynastic-esotericism','case':case,'repo_root':str(repo),'runtime_manifest':pin(runtime)}
                before=source.read_bytes()
                imported,receipt,materialization=materialize_prebuilt_fixture(context,pin(source),outer/'imported')
                assert len([p for p in imported.rglob('*') if p.is_file()])==9
                assert receipt['fixture_contains_business_effects'] is True
                assert receipt['required_markers']==['DESPAF: FIXTURE_ARMED sect_presets',
                    'DESPAF: INPUT APPLIED procreation_adopt','DESPAF: INPUT APPLIED procreation_leave',
                    'DESTRF: INPUT APPLIED qualification_and_stock_crime']
                assert materialization['game_started'] is False and materialization['business_acceptance']=='NOT_ASSESSED'
                config_path=repo/'tools/ck3_mod_acceptance_cases/dynastic_esotericism_native_binding_transfer.json'
                assert registration['adapter']['config']=='{repo_root}/'+config_path.relative_to(repo).as_posix()
                config=json.loads(config_path.read_bytes())
                assert config['case_id']==case and config['allow_actor_change'] is False
                assert config['maximum_natural_days']==40 and len(config['gui_phases'])==3
                requirements=[r for phase in config['gui_phases'] for r in phase['requirements']]
                assert len(requirements)==len(set(requirements))
                for required in ('actual_T0_all_character_ID_inventory_including_dead',
                    'actual_Tpost_minus_T0_all_character_ID_set_empty_including_dead',
                    'actual_old_P_complete_doctrines_None_present_Dynastic_absent',
                    'actual_independent_stock_attempted_murder_source_preserved',
                    'actual_normal_30_day_maintenance_cycle_crossed_without_manual_product_effect'):
                    assert required in requirements
                for relative in config['source_contracts']:assert (repo/relative).is_file(),relative
                plain={}
                for name in CONFIG_NAMES:
                    path=outer/name;path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_text('authored plain configuration',encoding='utf-8');plain[name]=pin(path)
                context.update(output=str(outer/'prepared'),state_dir=str(outer/'state'),case_contract=config,
                    case_inputs={'product_dir':str(staging),'plain_configuration':plain,
                                 'prebuilt_fixture_manifest':pin(source)})
                (outer/'prepared').mkdir()
                with patch('ck3_mod_acceptance_prepare._engine',return_value=(None,
                    {'game_version':'authored-not-game-qualification','exe_sha256':'0'*64})):
                    result=adapter.prepare_case(context)
                assert result['runtime_status']=='NOT_RUN' and result['business_pass'] is False
                assert result['product_release_pass'] is False
                profile=Path(result['profile_preparation']['profile']);mounted=profile/'mod-content/fixture'
                compiled=json.loads((mounted/'_case_contract.json').read_bytes())
                assert compiled['case']==case and compiled['whole_product_release_pass'] is False
                assert compiled['config']['maximum_natural_days']==40
                assert len([p for p in (profile/'mod-content/product').rglob('*') if p.is_file()])==56
                assert json.loads((profile/'dlc_load.json').read_bytes())['enabled_mods']==['mod/product.mod','mod/fixture.mod']
                assert source.read_bytes()==before
                def reject(label,mutate):
                    bad=copy.deepcopy(manifest);mutate(bad)
                    path=outer/(label+'.json');path.write_text(json.dumps(bad),encoding='utf-8')
                    target=outer/('rejected-'+label)
                    try:materialize_prebuilt_fixture(context,pin(path),target)
                    except (ValueError,KeyError):pass
                    else:raise AssertionError('accepted '+label)
                    assert not target.exists()
                reject('wrong-case',lambda x:x.update(case_id='sect_presets'))
                reject('missing-source',lambda x:x.update(producer_source_pins=[]))
                reject('bool-bytes',lambda x:x['files']['descriptor.mod'].update(bytes=True))
                reject('wrong-hash',lambda x:x['files']['descriptor.mod'].update(sha256='0'*64))
                reject('missing-file',lambda x:x['files'].pop('descriptor.mod'))
                reject('missing-marker',lambda x:x['receipt'].pop('required_markers'))
                reject('wrong-marker-type',lambda x:x['receipt'].update(required_markers=[True]))
                reject('wrong-effect-flag-type',lambda x:x['receipt'].update(fixture_contains_business_effects=1))
                print('actual Java transfer fixture -> public registry/import/preparation; typed negatives PASS; engine_semantics_verified=false')
                """;
        python(program, List.of(repository().toString(), release.staging().toString(),
                emission.manifest().toString(), temporary.resolve("public").toString()));
    }

    @Test
    void emittedInputAstCannotChangeProductBindingCrimeSourcesHeadsOrGovernment()
            throws IOException, InterruptedException {
        FixtureEmitter.Emission emission = FixtureEmitter.emit(repository(), temporary.resolve("ast"),
                "authored-machine", FixtureEmitter.CaseKind.NATIVE_BINDING_TRANSFER);
        String program = """
                from pathlib import Path
                import io,sys
                repo,fixture=map(Path,sys.argv[1:])
                sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'tools/lyd_i3b_checkpoint_readback/reader/dependencies')]
                from xar_autoplayer.campaign_score_save_reader import melt_tokens
                from bounded_save_parser import parse_block,one
                raw=(fixture/'common/decisions/des_transfer_acceptance_decisions.txt').read_text(encoding='utf-8-sig').encode('utf-8')
                entries=parse_block('{ '+' '.join(melt_tokens(io.BytesIO(raw)))+' }')
                assert len(entries)==1
                decision=one(entries,'des_transfer_prepare_decision',required=True)
                branch=one(one(one(decision,'effect',required=True),'hidden_effect',required=True),'if',required=True)
                assert one(branch,'limit',required=True)==one(decision,'is_valid',required=True)
                assert branch[1]=={'key':'add_character_flag','value':'des_transfer_fixture_input_applied'}
                def walk(items):
                    for row in items:
                        if row['key']=='limit':continue
                        yield row
                        if isinstance(row['value'],list):yield from walk(row['value'])
                allowed={'limit','if','else','name','value','target','modifier','add_character_flag',
                    'set_variable','add_opinion','add_piety','change_spiritual_fulfillment','has_perk','remove_perk',
                    'des_initial_reform_acceptance_prepare_original_rite_input_effect',
                    'des_initial_reform_acceptance_read_original_rite_input_effect','debug_log'}
                # Validate write-capable statements only, retaining the full read-only guard.
                writes=[r for r in branch if r['key']!='limit']
                nested=[r for r in walk(writes) if r['key']!='limit']
                for row in nested:
                    assert row['key'] in allowed,row
                    if row['key']=='set_variable':
                        assert one(row['value'],'name',required=True).startswith('des_transfer_fixture_')
                    if row['key']=='add_character_flag':assert row['value']=='des_transfer_fixture_input_applied'
                    if row['key']=='add_opinion':
                        assert one(row['value'],'modifier',required=True)=='attempted_murder_me_crime'
                        assert one(row['value'],'target',required=True)=='var:des_preset_fixture_ref_target'
                    if row['key']=='debug_log':assert 'TEST PASS' not in row['value']
                assert len([r for r in nested if r['key']=='add_opinion'])==1
                print('emitted guarded stock inputs only; no product/head/government setters PASS; engine_semantics_verified=false')
                """;
        python(program, List.of(repository().toString(), emission.fixture().toString()));
    }

    @Test
    void currentNewAssetSourceDriftRejectsBeforeOutput() throws IOException {
        Path main = Path.of("mod_dynastic_esotericism/tools/src/main");
        Path original = repository().resolve(main);
        Path copied = temporary.resolve("drift");
        Path destination = copied.resolve(main);
        try (Stream<Path> paths = Files.walk(original)) {
            for (Path source : paths.filter(Files::isRegularFile).filter(path ->
                    path.startsWith(original.resolve("resources")) ||
                    path.equals(original.resolve("java/org/xar/ck3/dynastic/acceptance/FixtureEmitter.java"))).toList()) {
                Path target = destination.resolve(original.relativize(source));
                Files.createDirectories(target.getParent());
                Files.copy(source, target, StandardCopyOption.REPLACE_EXISTING);
            }
        }
        Files.writeString(destination.resolve("resources/acceptance-fixture/common/decisions/des_transfer_acceptance_decisions.txt"),
                "# source changed after application packaging\n");
        Path output = temporary.resolve("rejected");
        assertThrows(IOException.class, () -> FixtureEmitter.emit(copied, output,
                "authored-machine", FixtureEmitter.CaseKind.NATIVE_BINDING_TRANSFER));
        assertFalse(Files.exists(output));
        assertFalse(Files.exists(Path.of(output + ".fixture.json")));
    }
}
