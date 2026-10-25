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

/** Real Java products flow into the unchanged public import/preparation consumers.
 * Authored installed-game identity is explicit; these tests do not execute CK3.
 */
final class EmpireHeadFixtureTest {
    private static final List<FixtureEmitter.CaseKind> CASES = List.of(
            FixtureEmitter.CaseKind.EMPIRE_HEADS_PROCREATION,
            FixtureEmitter.CaseKind.EMPIRE_HEADS_VIVHITE,
            FixtureEmitter.CaseKind.EMPIRE_HEADS_PROCREATION_COLD,
            FixtureEmitter.CaseKind.EMPIRE_HEADS_VIVHITE_COLD,
            FixtureEmitter.CaseKind.EMPIRE_HEADS_PROCREATION_RESTORE,
            FixtureEmitter.CaseKind.EMPIRE_HEADS_VIVHITE_RESTORE);
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
            throw new IOException("empire head public consumer timed out");
        }
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertEquals(0, process.exitValue(), output);
        assertTrue(output.contains("PASS; engine_semantics_verified=false"), output);
    }

    @Test
    void allSixActualProducerVariantsReachPublicImportRegistryAndGenericPreparation()
            throws IOException, InterruptedException {
        ReleaseBuilder.BuildResult release = new ReleaseBuilder().build(ReleaseProduct.official(
                repository().resolve("mod_dynastic_esotericism"), ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION),
                repository(), temporary.resolve("release"), "0".repeat(40), null, null);
        assertEquals(56, release.payload().files().size());
        List<String> arguments = new ArrayList<>(List.of(repository().toString(), release.staging().toString(),
                temporary.resolve("consumers").toString()));
        for (FixtureEmitter.CaseKind kind : CASES) {
            FixtureEmitter.Emission emission = FixtureEmitter.emit(repository(), temporary.resolve(kind.wireValue()),
                    "authored-machine", kind);
            assertEquals(kind.empireHeadFresh() ? 6 : 4, emission.payload().files().size());
            assertEquals(kind.empireHeadFresh() ? 8 : kind.empireHeadRestore() ? 2 : 1,
                    emission.payload().receipt().requiredMarkers().size());
            assertEquals(kind.empireHeadFresh(), emission.payload().receipt().containsBusinessEffects());
            assertEquals(kind, FixtureEmitter.CaseKind.parse(kind.wireValue()));
            assertEquals(emission.payload().files().size() + 1, emission.payload().producerSourcePins().size());
            arguments.add(emission.manifest().toString());
        }
        String program = """
                from pathlib import Path
                import copy,json,sys
                from unittest.mock import patch
                repo,staging,outer=map(Path,sys.argv[1:4]);outer.mkdir()
                sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
                from ck3_mod_acceptance_prepare import materialize_prebuilt_fixture,pin,CONFIG_NAMES
                from ck3_mod_acceptance_cases import generic_product_adapter as adapter
                registry=json.loads((repo/'tools/ck3_mod_acceptance_products.json').read_bytes())
                cases={row['id']:row for row in registry['products']['dynastic-esotericism']['cases']}
                for source in map(Path,sys.argv[4:]):
                    manifest=json.loads(source.read_bytes());case=manifest['case_id']
                    saved=case.endswith(('_cold','_restore'));restore=case.endswith('_restore')
                    output=outer/case;output.mkdir()
                    runtime=output/'runtime.json';runtime.write_text(json.dumps({'machine_id':'authored-machine'}),encoding='utf-8')
                    context={'product':'dynastic-esotericism','case':case,'repo_root':str(repo),'runtime_manifest':pin(runtime)}
                    before=source.read_bytes()
                    imported,receipt,materialization=materialize_prebuilt_fixture(context,pin(source),output/'imported')
                    assert len([p for p in imported.rglob('*') if p.is_file()])==(4 if saved else 6)
                    assert receipt['fixture_contains_business_effects'] is (not saved)
                    assert materialization['game_started'] is False and materialization['business_acceptance']=='NOT_ASSESSED'
                    config_path=repo/'tools/ck3_mod_acceptance_cases'/('dynastic_esotericism_'+case+'.json')
                    config=json.loads(config_path.read_bytes());assert config['case_id']==case
                    registration=cases[case]
                    assert registration['adapter']['path'].endswith('/generic_product_adapter.py')
                    assert registration['adapter']['config']=='{repo_root}/'+config_path.relative_to(repo).as_posix()
                    assert registration['status']==('blocked' if restore else 'ready')
                    if restore: assert 'NOT_READY' in registration['implementation_credit']
                    assert registration['whole_product_acceptance_credit'] is False
                    assert config['allow_actor_change'] is (not saved)
                    assert config['maximum_natural_days']==(2 if restore else 0 if saved else 12)
                    plain={}
                    for name in CONFIG_NAMES:
                        path=output/name;path.parent.mkdir(parents=True,exist_ok=True)
                        path.write_text('authored plain configuration',encoding='utf-8');plain[name]=pin(path)
                    context.update(output=str(output/'prepared'),state_dir=str(output/'state'),case_contract=config,
                        case_inputs={'product_dir':str(staging),'plain_configuration':plain,
                                     'prebuilt_fixture_manifest':pin(source)})
                    if saved:
                        # This is a preparation-only authored identity, never an actual CK3 Save.
                        original=output/'authored-not-engine-save.ck3';original.write_bytes(b'authored test input')
                        context['saved_campaign']={'save':str(original),'bytes':original.stat().st_size,
                            'sha256':pin(original)['sha256'],'player_id':123,'date_raw':456}
                        context['case_inputs']['post_start']={'government_key':'feudal_government',
                            'primary_title_tier_key':'empire','independent':True}
                    (output/'prepared').mkdir()
                    with patch('ck3_mod_acceptance_prepare._engine',return_value=(None,
                                {'game_version':'authored-not-game-qualification','exe_sha256':'0'*64})):
                        result=adapter.prepare_case(context)
                    assert result['runtime_status']=='NOT_RUN' and result['business_pass'] is False
                    assert result['product_release_pass'] is False
                    profile=Path(result['profile_preparation']['profile'])
                    mounted=profile/'mod-content/fixture'
                    compiled=json.loads((mounted/'_case_contract.json').read_bytes())
                    assert compiled['case']==case and compiled['whole_product_release_pass'] is False
                    assert compiled['config']['allow_actor_change'] is (not saved)
                    assert json.loads((profile/'dlc_load.json').read_bytes())['enabled_mods']==['mod/product.mod','mod/fixture.mod']
                    assert len([p for p in (profile/'mod-content/product').rglob('*') if p.is_file()])==56
                    assert source.read_bytes()==before
                    def reject(label,mutate):
                        bad=copy.deepcopy(manifest);mutate(bad)
                        path=output/(label+'.json');path.write_text(json.dumps(bad),encoding='utf-8')
                        target=output/('rejected-'+label)
                        try:materialize_prebuilt_fixture(context,pin(path),target)
                        except (ValueError,KeyError):pass
                        else:raise AssertionError('accepted '+label)
                        assert not target.exists()
                    reject('wrong-case',lambda x:x.update(case_id='core'))
                    reject('missing-source',lambda x:x.update(producer_source_pins=[]))
                    reject('bool-bytes',lambda x:x['files']['descriptor.mod'].update(bytes=True))
                    reject('wrong-hash',lambda x:x['files']['descriptor.mod'].update(sha256='0'*64))
                    reject('missing-file',lambda x:x['files'].pop('descriptor.mod'))
                    reject('missing-marker',lambda x:x['receipt'].pop('required_markers'))
                    reject('wrong-marker-type',lambda x:x['receipt'].update(required_markers=[True]))
                    reject('wrong-effect-flag-type',lambda x:x['receipt'].update(fixture_contains_business_effects=1))
                print('six actual Java variants -> public registry/import/preparation; typed corruption negatives PASS; engine_semantics_verified=false')
                """;
        python(program, arguments);
    }

    @Test
    void emittedAstHasOnlyDisclosedCountyResourceFaithAndDeathInputs()
            throws IOException, InterruptedException {
        FixtureEmitter.Emission fresh = FixtureEmitter.emit(repository(), temporary.resolve("fresh"),
                "authored-machine", FixtureEmitter.CaseKind.EMPIRE_HEADS_PROCREATION);
        FixtureEmitter.Emission passive = FixtureEmitter.emit(repository(), temporary.resolve("passive"),
                "authored-machine", FixtureEmitter.CaseKind.EMPIRE_HEADS_PROCREATION_COLD);
        String program = """
                from pathlib import Path
                import io,sys
                repo,fresh,passive=map(Path,sys.argv[1:])
                sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'tools/lyd_i3b_checkpoint_readback/reader/dependencies')]
                from xar_autoplayer.campaign_score_save_reader import melt_tokens
                from bounded_save_parser import parse_block,one
                def read(root,name):
                    raw=(root/name).read_text(encoding='utf-8-sig').encode('utf-8')
                    assert b'@DES_EHF_' not in raw
                    return parse_block('{ '+' '.join(melt_tokens(io.BytesIO(raw)))+' }')
                def walk(entries,ancestors=()):
                    for row in entries:
                        yield ancestors,row
                        if isinstance(row['value'],list):yield from walk(row['value'],ancestors+(row['key'],))
                decisions=read(fresh,'common/decisions/des_empire_heads_acceptance_decisions.txt')
                start=read(fresh,'common/on_action/des_empire_heads_acceptance_on_actions.txt')
                events=read(fresh,'events/des_empire_heads_acceptance_events.txt')
                observed=read(passive,'common/decisions/des_empire_heads_readback_decisions.txt')
                forbidden={'set_religious_head_title','force_create_head_of_faith_title_effect','create_dynamic_title',
                    'destroy_title','set_player_character','set_house','set_dynasty','set_house_head','set_dynasty_head',
                    'set_head_of_rite','set_rite_head','set_coa','generate_coa','change_government','set_government_type',
                    'add_rite_doctrine','remove_rite_doctrine','add_realm_law_skip_effects','add_title_law'}
                for owner in [decisions,start,events,observed]:
                    for ancestors,row in walk(owner):
                        assert row['key'] not in forbidden,row
                        if row['key']=='set_variable':
                            assert one(row['value'],'name',required=True).startswith('des_ehf_fixture_')
                        if row['key']=='set_global_variable':
                            assert one(row['value'],'name',required=True)=='des_ehf_fixture_owner'
                        if row['key']=='change_title_holder':
                            assert 'title:c_santiago' in ancestors
                            assert one(row['value'],'holder',required=True)=='root'
                        if row['key']=='debug_log':assert 'TEST PASS' not in row['value']
                assert len(decisions)==6
                for decision in decisions:
                    branch=one(one(one(decision['value'],'effect',required=True),'hidden_effect',required=True),'if',required=True)
                    assert one(branch,'limit',required=True)==one(decision['value'],'is_valid',required=True)
                    assert branch[1]['key']=='add_character_flag'
                    assert branch[1]['value'].startswith('des_ehf_fixture_')
                transfers=[row for _,row in walk(decisions) if row['key']=='change_title_holder']
                assert len(transfers)==1
                deaths=[row for _,row in walk(events) if row['key']=='death']
                assert deaths==[{'key':'death','value':[{'key':'death_reason','value':'death_natural_causes'}]}]
                death_event=one(events,'des_empire_heads_acceptance.1',required=True)
                branch=one(one(death_event,'immediate',required=True),'if',required=True)
                guard=one(branch,'limit',required=True)
                assert {'key':'has_character_flag','value':'des_ehf_fixture_death_staged'} in guard
                assert {'key':'primary_heir','value':'var:des_ehf_fixture_heir'} in guard
                no_writes={'set_variable','set_global_variable','add_character_flag','change_title_holder',
                    'create_title_and_vassal_change','add_piety','set_character_faith','set_character_rite','death','trigger_event'}
                assert all(row['key'] not in no_writes for _,row in walk(observed))
                print('emitted AST: ordinary county only, one guarded stock death, no product/head/government setters; passive observers PASS; engine_semantics_verified=false')
                """;
        python(program, List.of(repository().toString(), fresh.fixture().toString(), passive.fixture().toString()));
    }

    @Test
    void currentSourceDriftRejectsBeforeFreshOrPassiveOutputAndOldCaseCountsRemain()
            throws IOException {
        for (FixtureEmitter.CaseKind kind : List.of(FixtureEmitter.CaseKind.EMPIRE_HEADS_VIVHITE,
                FixtureEmitter.CaseKind.EMPIRE_HEADS_VIVHITE_COLD)) {
            Path copied = temporary.resolve("drift-" + kind.wireValue());
            Path main = Path.of("mod_dynastic_esotericism/tools/src/main");
            Path original = repository().resolve(main);
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
            Path changed = destination.resolve("resources/acceptance-fixture/" + (kind.empireHeadFresh()
                    ? "common/decisions/des_empire_heads_acceptance_decisions.txt"
                    : "common/decisions/des_empire_heads_readback_decisions.txt"));
            Files.writeString(changed, "# source changed after application was packaged\n");
            Path output = temporary.resolve("rejected-" + kind.wireValue());
            assertThrows(IOException.class, () -> FixtureEmitter.emit(copied, output, "authored-machine", kind));
            assertFalse(Files.exists(output));
            assertFalse(Files.exists(Path.of(output + ".fixture.json")));
        }
        assertEquals(13, FixtureEmitter.emit(repository(), temporary.resolve("old-core"), "authored-machine",
                FixtureEmitter.CaseKind.CORE).payload().files().size());
        assertEquals(5, FixtureEmitter.emit(repository(), temporary.resolve("old-sect"), "authored-machine",
                FixtureEmitter.CaseKind.SECT_PRESETS).payload().files().size());
        assertEquals(3, FixtureEmitter.emit(repository(), temporary.resolve("old-initial"), "authored-machine",
                FixtureEmitter.CaseKind.INITIAL_REFORM).payload().files().size());
    }
}
