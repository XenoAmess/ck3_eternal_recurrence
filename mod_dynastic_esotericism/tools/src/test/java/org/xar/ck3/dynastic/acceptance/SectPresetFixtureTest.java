package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
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
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.dynastic.release.ReleaseBuilder;
import org.xar.ck3.dynastic.release.ReleaseProduct;

/** Real producers and public consumers; none of these tests executes CK3. */
final class SectPresetFixtureTest {
    private static final List<String> ASSETS = List.of(
            "descriptor.mod", "common/on_action/des_preset_acceptance_on_actions.txt",
            "common/decisions/des_preset_acceptance_decisions.txt",
            "localization/english/des_preset_acceptance_l_english.yml",
            "localization/simp_chinese/des_preset_acceptance_l_simp_chinese.yml");
    @TempDir Path temporary;

    private static Path repository() {
        return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
    }

    private static void python(String program, List<String> arguments) throws IOException, InterruptedException {
        List<String> command = new ArrayList<>(List.of(System.getProperty("dynastic.python", "python"),
                "-B", "-X", "utf8", "-c", program));
        command.addAll(arguments);
        Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
        if (!process.waitFor(45, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor();
            throw new IOException("public preset fixture consumer timed out");
        }
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        assertEquals(0, process.exitValue(), output);
        assertTrue(output.contains("PASS; engine_semantics_verified=false"), output);
    }

    @Test
    void actualJavaPresetAndReleaseFeedSharedGenericPreparation() throws IOException, InterruptedException {
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository(), temporary.resolve("fixture"),
                "authored-machine", FixtureEmitter.CaseKind.SECT_PRESETS);
        assertEquals(Set.copyOf(ASSETS), emitted.payload().files().keySet());
        assertEquals(6, emitted.payload().producerSourcePins().size());
        assertEquals(7, emitted.payload().receipt().requiredMarkers().size());
        assertTrue(emitted.payload().receipt().containsBusinessEffects());
        assertEquals(FixtureEmitter.CaseKind.SECT_PRESETS, FixtureEmitter.CaseKind.parse("sect_presets"));
        for (String name : ASSETS) {
            byte[] actual = Files.readAllBytes(emitted.fixture().resolve(name));
            if (!name.equals("descriptor.mod")) {
                assertArrayEquals(new byte[]{(byte) 0xef, (byte) 0xbb, (byte) 0xbf},
                        new byte[]{actual[0], actual[1], actual[2]});
            }
        }
        ReleaseProduct product = ReleaseProduct.official(repository().resolve("mod_dynastic_esotericism"),
                ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION);
        ReleaseBuilder.BuildResult release = new ReleaseBuilder().build(product, repository(),
                temporary.resolve("release"), "0".repeat(40), null, null);
        assertEquals(52, release.payload().files().size());
        String program = """
                from pathlib import Path
                import copy,json,sys
                from unittest.mock import patch
                repository,manifest_path,staging,output=map(Path,sys.argv[1:])
                sys.path[:0]=[str(repository/'tools'),str(repository/'ck3_autonomous_player/src')]
                from ck3_mod_acceptance_prepare import materialize_prebuilt_fixture,pin,CONFIG_NAMES
                from ck3_mod_acceptance_cases import generic_product_adapter as adapter
                output.mkdir()
                runtime=output/'authored-runtime-manifest.json'
                runtime.write_text(json.dumps({'machine_id':'authored-machine'}),encoding='utf-8')
                config=json.loads((repository/'tools/ck3_mod_acceptance_cases/dynastic_esotericism_sect_presets.json').read_bytes())
                context={'product':'dynastic-esotericism','case':'sect_presets','repo_root':str(repository),
                    'runtime_manifest':pin(runtime)}
                manifest=json.loads(manifest_path.read_bytes())
                before=manifest_path.read_bytes()
                fixture,receipt,materialization=materialize_prebuilt_fixture(context,pin(manifest_path),output/'imported')
                assert len(list(p for p in fixture.rglob('*') if p.is_file()))==5
                assert len(receipt['required_markers'])==7 and receipt['fixture_contains_business_effects'] is True
                assert materialization['game_started'] is False and materialization['business_acceptance']=='NOT_ASSESSED'
                def reject(label,change):
                    bad=copy.deepcopy(manifest);change(bad)
                    path=output/(label+'.json');path.write_text(json.dumps(bad),encoding='utf-8')
                    try: materialize_prebuilt_fixture(context,pin(path),output/('rejected-'+label))
                    except (ValueError,KeyError): pass
                    else: raise AssertionError('accepted '+label)
                    assert not (output/('rejected-'+label)).exists()
                reject('wrong-case',lambda x:x.update(case_id='core'))
                reject('no-source',lambda x:x.update(producer_source_pins=[]))
                reject('wrong-hash',lambda x:x['files']['descriptor.mod'].update(sha256='0'*64))
                reject('missing-file',lambda x:x['files'].pop('common/decisions/des_preset_acceptance_decisions.txt'))
                reject('missing-markers',lambda x:x['receipt'].pop('required_markers'))
                extra=Path(manifest['fixture_root'])/'core-unlisted.txt';extra.write_text('unlisted core input',encoding='utf-8')
                try: reject('mixed-unlisted-core',lambda x:None)
                finally: extra.unlink()
                plain={}
                for name in CONFIG_NAMES:
                    path=output/name;path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_text('authored plain configuration',encoding='utf-8');plain[name]=pin(path)
                # Only the installed-game identity boundary is authored. The actual public
                # profile builder, prebuilt consumer and generic prepare remain unmodified.
                context.update(output=str(output/'prepared'),state_dir=str(output/'state'),case_contract=config,
                    case_inputs={'product_dir':str(staging),'plain_configuration':plain,
                                 'prebuilt_fixture_manifest':pin(manifest_path)})
                (output/'prepared').mkdir()
                with patch('ck3_mod_acceptance_prepare._engine',return_value=(None,
                           {'game_version':'authored-not-game-qualification','exe_sha256':'0'*64})):
                    result=adapter.prepare_case(context)
                assert result['runtime_status']=='NOT_RUN' and result['business_pass'] is False
                assert result['product_release_pass'] is False
                profile=Path(result['profile_preparation']['profile'])
                assert json.loads((profile/'dlc_load.json').read_bytes())['enabled_mods']==['mod/product.mod','mod/fixture.mod']
                product_files={p.relative_to(staging).as_posix():p.read_bytes() for p in staging.rglob('*') if p.is_file()}
                mounted=profile/'mod-content/product'
                assert product_files=={p.relative_to(mounted).as_posix():p.read_bytes() for p in mounted.rglob('*') if p.is_file()}
                assert len(product_files)==52
                compiled=json.loads((profile/'mod-content/fixture/_case_contract.json').read_bytes())
                assert compiled['case']=='sect_presets' and len(compiled['required_markers'])==7
                assert len(compiled['config']['gui_phases'])==2 and compiled['config']['maximum_natural_days']==16
                assert compiled['config']['allow_actor_change'] is False
                assert compiled['whole_product_release_pass'] is False
                assert len(list(p for p in (profile/'mod-content/fixture').rglob('*') if p.is_file()))==6
                assert json.loads(Path(result['initial_plan']['path']).read_bytes())=={'steps':[]}
                assert manifest_path.read_bytes()==before
                print('actual Java fixture5/release52 -> public import and generic preparation; six corruption negatives PASS; engine_semantics_verified=false')
                """;
        python(program, List.of(repository().toString(), emitted.manifest().toString(),
                release.staging().toString(), temporary.resolve("consumer").toString()));
    }

    @Test
    void presetInputAstRetainsOnceDateScopeAndStockInputGuards() throws IOException, InterruptedException {
        FixtureEmitter.Emission emitted = FixtureEmitter.emit(repository(), temporary.resolve("ast-fixture"),
                "authored-machine", FixtureEmitter.CaseKind.SECT_PRESETS);
        String program = """
                from pathlib import Path
                import copy,io,json,sys
                repository,fixture=map(Path,sys.argv[1:])
                sys.path.insert(0,str(repository/'ck3_autonomous_player/src'))
                from xar_autoplayer.campaign_score_save_reader import melt_tokens
                sys.path.insert(0,str(repository/'tools/lyd_i3b_checkpoint_readback/reader/dependencies'))
                from bounded_save_parser import parse_block,one
                def read(name):
                    raw=(fixture/name).read_text(encoding='utf-8-sig').encode('utf-8')
                    return parse_block('{ '+' '.join(melt_tokens(io.BytesIO(raw)))+' }')
                decisions=read('common/decisions/des_preset_acceptance_decisions.txt')
                startup=read('common/on_action/des_preset_acceptance_on_actions.txt')
                steps=[('procreation_adopt','p_adopted','p1'),('procreation_leave','p_left','p2'),
                       ('procreation_return','p_returned','p3'),('vivhite_adopt','w_adopted','w1'),
                       ('old_procreation_reason','old_p_reason_input','w2'),('vivhite_join','w_joined','w3')]
                prefix='des_preset_fixture_'
                def row(key,value): return {'key':key,'value':value}
                def require(entries,key,value): assert row(key,value) in entries,(key,value)
                def walk(entries):
                    for item in entries:
                        yield item
                        if isinstance(item['value'],list): yield from walk(item['value'])
                def body(entries,name):
                    decision=one(entries,'des_preset_'+name+'_decision',required=True)
                    hidden=one(one(decision,'effect',required=True),'hidden_effect',required=True)
                    return decision,one(hidden,'if',required=True)
                def stock(entries): return [r for r in walk(entries) if r['key'] in ('set_character_faith','set_character_rite')]
                def validate(entries,start):
                    assert len(entries)==6
                    for index,(name,flag,tag) in enumerate(steps):
                        decision,branch=body(entries,name)
                        valid=one(decision,'is_valid',required=True);guard=one(branch,'limit',required=True)
                        assert valid==guard,'is_valid/effect guard drift'
                        for key,value in [('is_ai','no'),('is_alive','yes'),('this','var:'+prefix+'ref_actor'),
                                          ('has_character_flag',prefix+'armed'),('NOT',[row('has_character_flag',prefix+flag)])]:
                            require(guard,key,value)
                        assert branch[1]==row('add_character_flag',prefix+flag),'once flag must precede inputs'
                        positions={one(r['value'],'name',required=True):i for i,r in enumerate(branch) if r['key']=='set_variable'}
                        for suffix,value in [('date','current_date'),('actor','this'),('target','var:'+prefix+'ref_target')]:
                            require(branch,'set_variable',[row('name',prefix+tag+'_input_'+suffix),row('value',value)])
                        first=next(i for i,r in enumerate(branch) if stock([r]))
                        assert all(positions[prefix+tag+'_input_'+s]<first for s in ('date','actor','target'))
                        if index:
                            previous=steps[index-1]
                            require(guard,'has_character_flag',prefix+previous[1])
                            require(guard,'has_variable',prefix+previous[2]+'_input_date')
                            date_left=row(None,'var:'+prefix+previous[2]+'_input_date')
                            date_right=row('<',[row('value','current_date'),row('subtract','1')])
                            assert list(zip(guard,guard[1:])).count((date_left,date_right))==1
                        # Evaluate the only duplicate guard with the flag state produced by
                        # the first branch: the second call has no stock-input branch.
                        flags={prefix+flag}
                        assert any(r['key']=='NOT' and r['value']==[row('has_character_flag',next(iter(flags)))] for r in guard)
                    first=body(entries,'procreation_adopt')[1]
                    assert len([r for r in first if r['key']=='create_character'])==2
                    assert [r for r in first if r['key'] in ('set_character_faith','set_character_rite')]==[
                        row('set_character_faith','faith:des_procreation_faith'),row('set_character_rite','rite:des_procreation_rite')]
                    root_index=first.index(row('set_character_rite','rite:des_procreation_rite'))
                    assert all(i>root_index for i,r in enumerate(first) if r['key'] in ('var:'+prefix+'ref_observer','var:'+prefix+'ref_target'))
                    assert len(stock(first))==6
                    assert stock(body(entries,'vivhite_adopt')[1])==[
                        row('set_character_faith','faith:des_vivhite_faith'),row('set_character_rite','rite:des_vivhite_rite')]
                    assert len(stock(entries))==16
                    forbidden={'set_house','set_dynasty','set_house_head','set_dynasty_head','set_coa','set_player_character',
                               'set_head_of_rite','set_rite_head','des_sync_character_effect','add_opinion','add_character_interaction_flag'}
                    for r in walk(entries+start):
                        assert r['key'] not in forbidden,r
                        if r['key']=='set_variable': assert one(r['value'],'name',required=True).startswith(prefix),r
                        if r['key'] in ('set_global_variable','add_to_variable_list','remove_variable','add_trait','remove_trait'):
                            raise AssertionError('non-input state writer')
                        if r['key']=='debug_log': assert 'TEST PASS' not in r['value']
                        if r['key']=='create_character':
                            assert not any(c['key'] in ('house','dynasty') for c in r['value'])
                    refs={one(r['value'],'name'):one(r['value'],'value') for r in walk(start) if r['key']=='set_variable'}
                    for suffix,value in [('p_faith','faith:des_procreation_faith'),('p_rite','rite:des_procreation_rite'),
                                         ('w_faith','faith:des_vivhite_faith'),('w_rite','rite:des_vivhite_rite')]:
                        assert refs[prefix+'ref_'+suffix]==value
                validate(decisions,startup)
                def negative(label,mutation):
                    bad=copy.deepcopy(decisions);mutation(bad)
                    try: validate(bad,startup)
                    except (AssertionError,ValueError,KeyError,StopIteration): return
                    raise AssertionError('accepted AST corruption: '+label)
                def remove_once(entries,where):
                    decision,branch=body(entries,steps[0][0])
                    guard=one(decision,'is_valid',required=True) if where=='valid' else one(branch,'limit',required=True)
                    guard[:]=[r for r in guard if r['key']!='NOT']
                negative('stale-effect',lambda e:remove_once(e,'effect'))
                negative('stale-valid',lambda e:remove_once(e,'valid'))
                def missing_date(entries):
                    branch=body(entries,'procreation_leave')[1]
                    for guard in (one(body(entries,'procreation_leave')[0],'is_valid',required=True),one(branch,'limit',required=True)):
                        guard[:]=[r for r in guard if r!=row(None,'var:'+prefix+'p1_input_date')]
                negative('same-day',missing_date)
                def late_flag(entries):
                    branch=body(entries,'procreation_adopt')[1];branch.append(branch.pop(1))
                negative('late-once',late_flag)
                def product_write(entries): body(entries,'procreation_adopt')[1].append(row('set_house_head','root'))
                negative('product-setter',product_write)
                def wrong_order(entries):
                    branch=body(entries,'procreation_adopt')[1]
                    branch.insert(1,branch.pop(next(i for i,r in enumerate(branch) if r['key']=='var:'+prefix+'ref_observer')))
                negative('npc-first',wrong_order)
                print('actual emitted AST: six once/date/pin routes plus six negatives PASS; engine_semantics_verified=false')
                """;
        python(program, List.of(repository().toString(), emitted.fixture().toString()));
    }

    @Test
    void presetPackagedInputsRejectCurrentSourceDrift() throws IOException {
        for (int index = 0; index < ASSETS.size(); index++) {
            Path copied = temporary.resolve("source-" + index);
            Path source = repository().resolve("mod_dynastic_esotericism/tools/src/main");
            Path target = copied.resolve("mod_dynastic_esotericism/tools/src/main");
            Path emitter = Path.of("java/org/xar/ck3/dynastic/acceptance/FixtureEmitter.java");
            Files.createDirectories(target.resolve(emitter).getParent());
            Files.copy(source.resolve(emitter), target.resolve(emitter));
            try (Stream<Path> paths = Files.walk(source.resolve("resources/acceptance-fixture"))) {
                for (Path path : paths.filter(Files::isRegularFile).toList()) {
                    Path destination = target.resolve(source.relativize(path));
                    Files.createDirectories(destination.getParent());
                    Files.copy(path, destination, StandardCopyOption.REPLACE_EXISTING);
                }
            }
            Files.writeString(target.resolve("resources/acceptance-fixture").resolve(ASSETS.get(index)), "changed source");
            Path output = temporary.resolve("rejected-" + index);
            IOException failure = assertThrows(IOException.class,
                    () -> FixtureEmitter.emit(copied, output, "authored-machine", FixtureEmitter.CaseKind.SECT_PRESETS));
            assertEquals("packaged fixture resource differs from current source: " + ASSETS.get(index), failure.getMessage());
            assertFalse(Files.exists(output));
        }
    }
}
