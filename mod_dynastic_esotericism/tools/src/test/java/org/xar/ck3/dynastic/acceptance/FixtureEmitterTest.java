package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class FixtureEmitterTest {
    @TempDir Path temporary;

    private static Path repository() {
        return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
    }

    @Test
    void realProducerWritesExactManifestAndSeparateFixture() throws IOException, NoSuchAlgorithmException {
        FixtureEmitter.Emission result = FixtureEmitter.emit(repository(), temporary.resolve("fixture"), "authored-machine");
        JsonNode decoded = new ObjectMapper().readTree(result.manifest().toFile());
        assertEquals("ck3-mod-acceptance-prebuilt-fixture-v1", decoded.path("schema").textValue());
        assertEquals("dynastic-esotericism", decoded.path("product").textValue());
        assertEquals("core", decoded.path("case_id").textValue());
        assertEquals("authored-machine", decoded.path("machine_id").textValue());
        assertEquals(13, decoded.path("files").size());
        assertEquals(14, decoded.path("producer_source_pins").size());
        assertEquals(24, decoded.path("receipt").path("required_markers").size());
        assertTrue(decoded.path("receipt").path("fixture_contains_business_effects").booleanValue());
        for (var entry : result.payload().files().entrySet()) {
            byte[] bytes = Files.readAllBytes(result.fixture().resolve(entry.getKey()));
            assertEquals(bytes.length, entry.getValue().bytes());
            assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),
                    entry.getValue().sha256());
            if (entry.getKey().equals("descriptor.mod")) {
                assertEquals('n', bytes[0]);
            } else {
                assertArrayEquals(new byte[]{(byte) 0xef, (byte) 0xbb, (byte) 0xbf},
                        new byte[]{bytes[0], bytes[1], bytes[2]});
            }
        }
        assertFalse(Files.exists(result.fixture().resolve("_case_contract.json")));
        String events = Files.readString(result.fixture().resolve("events/des_acceptance_events.txt"), StandardCharsets.UTF_8);
        assertTrue(events.contains("rite_has_doctrine = des_doctrine_none"));
        assertTrue(events.contains("des_has_active_binding_trigger = yes"));
        String decisions = Files.readString(result.fixture().resolve("common/decisions/des_acceptance_decisions.txt"), StandardCharsets.UTF_8);
        assertTrue(decisions.contains("set_character_rite = rite:byzantine_rite"));
        assertFalse(events.contains("add_trait = des_apostate"));
        assertFalse(events.contains("des_sync_character_effect = yes"));
        assertThrows(IllegalArgumentException.class,
                () -> FixtureEmitter.emit(repository(), result.fixture(), "authored-machine"));
    }

    @Test
    void passiveColdAndBootstrapKeepNoColdRegistrarAndSeedHasNoProductState() throws IOException {
        for (FixtureEmitter.CaseKind kind : new FixtureEmitter.CaseKind[]{
                FixtureEmitter.CaseKind.COLD_RELOAD, FixtureEmitter.CaseKind.OLD_SAVE_BOOTSTRAP}) {
            FixtureEmitter.Emission result = FixtureEmitter.emit(repository(), temporary.resolve(kind.wireValue()), "authored-machine", kind);
            assertEquals(kind.wireValue(), result.payload().caseId());
            assertEquals(12, result.payload().files().size());
            for (String name : result.payload().files().keySet()) {
                if (name.endsWith(".txt")) {
                    assertFalse(Files.readString(result.fixture().resolve(name)).contains("on_game_start_after_lobby"));
                }
            }
        }
        FixtureEmitter.Emission seed = FixtureEmitter.emit(repository(), temporary.resolve("seed"), "authored-machine", FixtureEmitter.CaseKind.PRE_PRODUCT_SEED);
        assertEquals(2, seed.payload().files().size());
        assertFalse(seed.payload().receipt().containsBusinessEffects());
        String input = Files.readString(seed.fixture().resolve("common/on_action/des_acceptance_pre_product_seed.txt"));
        assertFalse(input.contains("set_variable"));
        assertFalse(input.contains("des_initialized"));
    }

    @Test
    void rejectsChangedFixtureSourcesBeforeEmittingFromPackagedResources() throws IOException {
        List<String> changedResources = List.of(
                "descriptor.mod",
                "common/on_action/des_acceptance_on_actions.txt",
                "common/decisions/des_acceptance_decisions.txt",
                "common/scripted_effects/des_acceptance_effects.txt",
                "common/scripted_effects/des_acceptance_extended_effects.txt",
                "common/decisions/des_acceptance_extended_decisions.txt",
                "common/on_action/des_acceptance_extended_on_actions.txt",
                "events/des_acceptance_events.txt",
                "events/des_acceptance_extended_events.txt",
                "localization/english/des_acceptance_l_english.yml",
                "localization/simp_chinese/des_acceptance_l_simp_chinese.yml",
                "localization/english/des_acceptance_extended_l_english.yml",
                "localization/simp_chinese/des_acceptance_extended_l_simp_chinese.yml");
        for (int index = 0; index < changedResources.size(); index++) {
            String relative = changedResources.get(index);
            Path copiedRepository = temporary.resolve("changed-source-" + index);
            copyFixtureInputs(copiedRepository);
            Path changed = copiedRepository.resolve("mod_dynastic_esotericism/tools/src/main/resources/acceptance-fixture")
                    .resolve(relative);
            Files.writeString(changed, "\n", StandardCharsets.UTF_8, StandardOpenOption.APPEND);
            Path output = temporary.resolve("rejected-fixture-" + index);

            IOException failure = assertThrows(IOException.class,
                    () -> FixtureEmitter.emit(copiedRepository, output, "authored-machine"));

            assertEquals("packaged fixture resource differs from current source: " + relative, failure.getMessage());
            assertFalse(Files.exists(output));
            assertFalse(Files.exists(Path.of(output + ".fixture.json")));
        }
    }

    @Test
    void realFixtureDefinesLiteralMarkersAndRetainsTheActualR0004Guards()
            throws IOException, InterruptedException, NoSuchAlgorithmException {
        FixtureEmitter.Emission current = FixtureEmitter.emit(repository(), temporary.resolve("literal-markers"), "authored-machine");
        Path baseline = temporary.resolve("r0004-guard-baseline.json");
        copyTestResource("guard-baseline.json", baseline);
        ProbeResult accepted = probeFixture(current, baseline);
        assertEquals(0, accepted.exitCode(), accepted.output());
        JsonNode observation = new ObjectMapper().readTree(accepted.output());
        assertEquals(current.payload().receipt().requiredMarkers().size(), observation.path("required_marker_count").intValue());
        assertEquals(2, observation.path("unchanged_guard_count").intValue());
        assertTrue(observation.path("original_rite_readback_only_observes").booleanValue());
        assertEquals(24, observation.path("successor_reference_transfer_count").intValue());
        assertEquals(21, observation.path("successor_history_transfer_count").intValue());
        assertFalse(observation.path("engine_semantics_verified").booleanValue());
        assertTrue(observation.path("heir_minimum_day_guard_validated").booleanValue());
        assertTrue(observation.path("separate_prisoner_control_custody_validated").booleanValue());

        for (String mutation : List.of("missing-head", "product-write", "pardon-copy",
                "date-literal", "date-no-source", "date-same-day",
                "prison-main-target", "prison-no-reason", "prison-product-write")) {
            ProbeResult forbidden = probeFixture(current, baseline, mutation);
            assertNotEquals(0, forbidden.exitCode(), forbidden.output());
            assertEquals(switch (mutation) {
                case "missing-head" -> "SUCCESSOR_IDENTITY_GUARD_MISSING";
                case "product-write" -> "SUCCESSOR_REFERENCE_TRANSFER_OUTSIDE_CONTRACT";
                case "date-literal" -> "INVALID_DATE_LITERAL_VARIABLE_TRIGGER";
                case "date-no-source" -> "MISSING_HEIR_INPUT_DATE_GUARD";
                case "date-same-day" -> "HEIR_MINIMUM_DAY_GUARD_CHANGED";
                case "prison-main-target" -> "PRISON_CUSTODY_TARGET_CHANGED";
                case "prison-no-reason" -> "PRISON_PRE_CUSTODY_REASON_MISSING";
                case "prison-product-write" -> "PRISON_UNDECLARED_EFFECT";
                default -> "SUCCESSOR_FLAG_TRANSFER_OUTSIDE_CONTRACT";
            }, new ObjectMapper().readTree(forbidden.output()).path("reason").textValue());
        }

        FixtureEmitter.Emission failedR0004 = FixtureEmitter.emit(repository(), temporary.resolve("original-r0004"), "authored-machine");
        JsonNode sources = new ObjectMapper().readTree(baseline.toFile()).path("original_fixture_sources");
        for (JsonNode source : sources) {
            String relative = source.path("path").textValue();
            Path restored = failedR0004.fixture().resolve(relative);
            copyTestResource("original/" + relative, restored);
            byte[] raw = Files.readAllBytes(restored);
            assertEquals(source.path("bytes").longValue(), raw.length);
            assertEquals(source.path("sha256").textValue(),
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        }
        ProbeResult rejected = probeFixture(failedR0004, baseline);
        assertNotEquals(0, rejected.exitCode(), rejected.output());
        JsonNode failure = new ObjectMapper().readTree(rejected.output());
        assertEquals("NON_LITERAL_DEBUG_LOG", failure.path("reason").textValue());
        assertEquals(4, failure.path("non_literal_count").intValue());
    }

    private static void copyTestResource(String relative, Path destination) throws IOException {
        try (InputStream source = FixtureEmitterTest.class.getResourceAsStream("/acceptance-r0004/" + relative)) {
            if (source == null) throw new IOException("missing actual R0004 regression resource: " + relative);
            Files.copy(source, destination, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private static ProbeResult probeFixture(FixtureEmitter.Emission fixture, Path baseline)
            throws IOException, InterruptedException {
        return probeFixture(fixture, baseline, "none");
    }

    private static ProbeResult probeFixture(FixtureEmitter.Emission fixture, Path baseline, String mutation)
            throws IOException, InterruptedException {
        String program = """
                import io,json,sys
                from pathlib import Path
                repository,fixture,manifest,baseline=map(Path,sys.argv[1:5])
                mutation=sys.argv[5]
                sys.path.insert(0,str(repository/'ck3_autonomous_player/src'))
                from xar_autoplayer.campaign_score_save_reader import melt_tokens
                sys.path.insert(0,str(repository/'tools/lyd_i3b_checkpoint_readback/reader/dependencies'))
                from bounded_save_parser import parse_block,one
                def reject(reason,**details):
                    print(json.dumps({'status':'REJECTED','reason':reason,**details}))
                    sys.exit(1)
                def script(path):
                    raw=path.read_text(encoding='utf-8-sig').encode('utf-8')
                    return parse_block('{ '+' '.join(melt_tokens(io.BytesIO(raw)))+' }')
                literals=[]
                non_literal=[]
                def logs(entries,source):
                    for row in entries:
                        value=row['value']
                        if row['key']=='debug_log':
                            if not isinstance(value,str) or not value.startswith(chr(34)) or not value.endswith(chr(34)):
                                non_literal.append({'source':source,'value':value})
                            else:
                                literals.append(json.loads(value))
                        if isinstance(value,list):
                            logs(value,source)
                parsed={}
                for path in sorted(fixture.rglob('*.txt')):
                    relative=path.relative_to(fixture).as_posix()
                    parsed[relative]=script(path)
                    logs(parsed[relative],relative)
                if non_literal:
                    reject('NON_LITERAL_DEBUG_LOG',non_literal_count=len(non_literal),arguments=non_literal)
                events=parsed['events/des_acceptance_events.txt']
                prepare_key='des_acceptance_prepare_original_rite_input_effect'
                def calls(entries):
                    found=[]
                    for row in entries:
                        if row['key']==prepare_key and row['value']=='yes':
                            found.append(row)
                        if isinstance(row['value'],list):
                            found.extend(calls(row['value']))
                    return found
                setup=one(one(events,'des_acceptance.1',required=True),'immediate',required=True)
                setup_calls=[row for row in setup if row['key']==prepare_key and row['value']=='yes']
                extended_decisions=parsed['common/decisions/des_acceptance_extended_decisions.txt']
                edit_prepare=one(extended_decisions,'des_acceptance_edit_input_prepare_decision',required=True)
                edit_body=one(one(edit_prepare,'effect',required=True),'hidden_effect',required=True)
                if len(setup_calls)!=1 or len(calls(edit_body))!=1 or sum(len(calls(entries)) for entries in parsed.values())!=2:
                    reject('ORIGINAL_RELATION_PREPARATION_OUTSIDE_DECLARED_ROUTES')
                effects=parsed['common/scripted_effects/des_acceptance_effects.txt']
                decisions=parsed['common/decisions/des_acceptance_decisions.txt']
                readback=one(effects,'des_acceptance_read_original_rite_input_effect',required=True)
                def readback_effects(entries):
                    for row in entries:
                        key,value=row['key'],row['value']
                        if key in ('if','else'):
                            readback_effects([entry for entry in value if entry['key']!='limit'])
                        elif key in ('add_character_flag','remove_character_flag'):
                            if value not in ('des_test_original_rite_input_ready','des_test_original_edit_input_ready','des_test_original_rite_relation_ready'):
                                reject('READBACK_WRITES_NON_FIXTURE_FLAG',key=key,value=value)
                        elif key=='des_acceptance_read_original_rite_relation_effect' and value=='yes':
                            readback_effects(one(effects,key,required=True))
                        elif key not in ('save_scope_as','debug_log'):
                            reject('READBACK_HAS_MUTATING_EFFECT',key=key)
                readback_effects(readback)
                readback_effects(one(effects,'des_acceptance_read_original_edit_input_effect',required=True))
                decision=one(decisions,'des_acceptance_original_rite_input_readback_decision',required=True)
                invoked=one(one(decision,'effect',required=True),'hidden_effect',required=True)
                if invoked != [{'key':'des_acceptance_read_original_rite_input_effect','value':'yes'}]:
                    reject('INDEPENDENT_READBACK_HAS_OTHER_EFFECTS')
                edit_readback=one(extended_decisions,'des_acceptance_edit_input_readback_decision',required=True)
                if one(one(edit_readback,'effect',required=True),'hidden_effect',required=True)!=[{'key':'des_acceptance_read_original_edit_input_effect','value':'yes'}]:
                    reject('INDEPENDENT_EDIT_READBACK_HAS_OTHER_EFFECTS')
                def require(entries,key,value,reason):
                    if {'key':key,'value':value} not in entries:
                        reject(reason,key=key)
                # The real emitted route must prepare a distinct initial NPC,
                # observe product reasons before custody, and invoke one stock
                # custody writer. These are AST contracts, not engine verdicts.
                control='des_test_prison_control'
                ref='des_test_ref_prison_control'
                control_scope='scope:'+control
                def walk(entries):
                    for row in entries:
                        yield row
                        if isinstance(row['value'],list):
                            yield from walk(row['value'])
                created=[row['value'] for row in setup if row['key']=='create_character' and one(row['value'],'save_scope_as')==control]
                if len(created)!=1:
                    reject('PRISON_CONTROL_NOT_UNIQUE_INITIAL_NPC')
                for key,value in [('employer','root'),('age','30'),('faith','root.faith'),('rite','root.rite'),('culture','root.culture'),('dynasty','none'),('random_traits','no')]:
                    require(created[0],key,value,'PRISON_CONTROL_NOT_ORDINARY_INITIAL_COURTIER')
                require(setup,'set_variable',[{'key':'name','value':ref},{'key':'value','value':control_scope}],'PRISON_CONTROL_REFERENCE_NOT_SAVED')
                capture=one(one(one(decisions,'des_acceptance_capture_created_decision',required=True),'effect',required=True),'hidden_effect',required=True)
                if any(row['key'] in (control_scope,'var:'+ref) for row in walk(capture)):
                    reject('PRISON_CONTROL_UI_CONVERSION_BYPASSED')
                prison_decision=one(decisions,'des_acceptance_prisoner_control_decision',required=True)
                shown=one(prison_decision,'is_shown',required=True)
                stage=one(one(one(prison_decision,'effect',required=True),'hidden_effect',required=True),'if',required=True)
                valid=one(prison_decision,'is_valid',required=True)
                stage_guard=one(stage,'limit',required=True)
                if stage_guard!=valid:
                    reject('PRISON_DISPATCH_IDENTITY_NOT_REVALIDATED')
                for rows in (shown,valid):
                    require(rows,'has_character_flag','des_test_same_verified','PRISON_WRONG_PHASE')
                    require(rows,'NOT',[{'key':'has_character_flag','value':'des_test_prison_control_started'}],'PRISON_REPLAY_NOT_BLOCKED')
                    require(rows,'NOT',[{'key':'has_character_flag','value':'des_test_cross_started'}],'PRISON_WRONG_PHASE')
                for key,value in [('exists','global_var:des_test_extended_owner'),('this','global_var:des_test_extended_owner'),('exists','var:'+ref),('exists','var:des_test_ref_target'),('rite','var:des_test_primary_rite'),('dynasty','var:des_test_bound_dynasty')]:
                    require(valid,key,value,'PRISON_CONTROL_IDENTITY_NOT_BOUND')
                control_guard=one(valid,'var:'+ref,required=True)
                for key,value in [('is_alive','yes'),('is_adult','yes'),('is_ai','yes'),('is_landed','no'),('is_imprisoned','no'),('is_courtier_of','root'),('faith','root.faith'),('rite','root.var:des_test_primary_rite'),('dynasty','root.var:des_test_bound_dynasty')]:
                    require(control_guard,key,value,'PRISON_CONTROL_IDENTITY_NOT_BOUND')
                for other in ('root','root.var:des_test_ref_target'):
                    require(control_guard,'NOT',[{'key':'this','value':other}],'PRISON_CONTROL_IS_MAIN_TARGET')
                require(stage,control_scope,[{'key':'set_character_rite','value':'scope:des_test_source_rite'}],'PRISON_WRONG_APOSTASY_INPUT')
                require(stage,'trigger_event',[{'key':'id','value':'des_acceptance.8'},{'key':'days','value':'1'}],'PRISON_CUSTODY_NOT_DELAYED')
                require(stage,'add_character_flag','des_test_prison_control_started','PRISON_REPLAY_NOT_BLOCKED')
                custody=one(one(one(events,'des_acceptance.8',required=True),'immediate',required=True),'if',required=True)
                custody_guard=one(custody,'limit',required=True)
                require(custody_guard,'this','global_var:des_test_extended_owner','PRISON_CONTROL_IDENTITY_NOT_BOUND')
                require(custody_guard,'NOT',[{'key':'exists','value':'scope:use_strife_not_tyranny'}],'PRISON_CONSUMING_OPTION_NOT_EXCLUDED')
                require(custody_guard,'basic_allowed_to_imprison_character_trigger',[{'key':'CHARACTER','value':'var:'+ref}],'PRISON_CUSTODY_PRECONDITION_MISSING')
                prisoner=one(custody_guard,'var:'+ref,required=True)
                for key,value in [('is_alive','yes'),('is_imprisoned','no'),('is_courtier_of','root'),('rite','root.var:des_test_source_rite')]:
                    require(prisoner,key,value,'PRISON_CUSTODY_PRECONDITION_MISSING')
                penalty=one(custody,'if',required=True)
                pre=one(penalty,'limit',required=True)
                stock=one(penalty,'imprison_character_effect',required=True)
                if mutation=='prison-main-target':
                    one(stock,'TARGET',required=True)
                    stock[0]['value']='scope:des_test_target'
                elif mutation=='prison-no-reason':
                    pre[:]=[row for row in pre if row['key']!='has_execute_reason']
                elif mutation=='prison-product-write':
                    penalty.append({'key':'add_trait','value':'des_apostate'})
                require(pre,control_scope,[{'key':'des_is_apostate_trigger','value':'yes'}],'PRISON_PRE_CUSTODY_REASON_MISSING')
                for reason in ('has_imprisonment_reason','has_banish_reason','has_execute_reason'):
                    require(pre,reason,control_scope,'PRISON_PRE_CUSTODY_REASON_MISSING')
                require(pre,'has_opinion_modifier',[{'key':'target','value':control_scope},{'key':'modifier','value':'des_apostasy_opinion'}],'PRISON_PRE_CUSTODY_REASON_MISSING')
                require(pre,'des_is_penalty_pair_trigger',[{'key':'TARGET','value':control_scope}],'PRISON_PRE_CUSTODY_REASON_MISSING')
                if stock!=[{'key':'TARGET','value':control_scope},{'key':'IMPRISONER','value':'root'}]:
                    reject('PRISON_CUSTODY_TARGET_CHANGED')
                stock_calls=[row for value in parsed.values() for row in walk(value) if row['key']=='imprison_character_effect']
                if len(stock_calls)!=1:
                    reject('PRISON_CUSTODY_WRITER_NOT_UNIQUE')
                allowed={'limit','debug_log','save_scope_as',control_scope,'imprison_character_effect','if','else'}
                if any(row['key'] not in allowed for row in penalty):
                    reject('PRISON_UNDECLARED_EFFECT')
                require(penalty,control_scope,[{'key':'save_scope_as','value':'recipient'}],'PRISON_RECIPIENT_SCOPE_NOT_BOUND')
                for name in ('actor','puppet_or_actor'):
                    require(penalty,'save_scope_as',name,'PRISON_ACTOR_SCOPE_NOT_BOUND')
                ready=one(penalty,'if',required=True)
                if next(i for i,row in enumerate(penalty) if row['key']=='imprison_character_effect') >= next(i for i,row in enumerate(penalty) if row['key']=='if'):
                    reject('PRISON_READY_BEFORE_STOCK_CUSTODY')
                ready_guard=one(ready,'limit',required=True)
                require(ready_guard,control_scope,[{'key':'is_alive','value':'yes'},{'key':'is_imprisoned_by','value':'root'}],'PRISON_CUSTODY_READBACK_MISSING')
                for reason in ('has_banish_reason','has_execute_reason'):
                    require(ready_guard,reason,control_scope,'PRISON_CUSTODY_READBACK_MISSING')
                require(ready,'add_character_flag','des_test_prison_control_ready','PRISON_CUSTODY_READBACK_MISSING')
                require(ready,'debug_log',json.dumps('DESAF: TEST PASS prisoner_control_ready'),'PRISON_CUSTODY_READBACK_MISSING')
                heir_readback=one(extended_decisions,'des_acceptance_primary_heir_readback_decision',required=True)
                heir_branch=one(one(one(heir_readback,'effect',required=True),'hidden_effect',required=True),'if',required=True)
                heir_guard=one(heir_branch,'limit',required=True)
                if mutation=='date-literal':
                    # Reintroduce the actual R0008 loader failure in the parsed
                    # producer output, without teaching a new script parser.
                    heir_guard[:0]=parse_block('{ current_date > var:des_test_heir_input_date }')
                elif mutation=='date-no-source':
                    heir_guard[:]=[row for row in heir_guard if row!={'key':'has_variable','value':'des_test_heir_input_date'}]
                elif mutation=='date-same-day':
                    one(heir_guard,'<',required=True)[1]['value']='0'
                if {'key':None,'value':'current_date'} in heir_guard:
                    reject('INVALID_DATE_LITERAL_VARIABLE_TRIGGER')
                require(heir_guard,'has_variable','des_test_heir_input_date','MISSING_HEIR_INPUT_DATE_GUARD')
                date_left={'key':None,'value':'var:des_test_heir_input_date'}
                date_right={'key':'<','value':[{'key':'value','value':'current_date'},{'key':'subtract','value':'1'}]}
                pairs=list(zip(heir_guard,heir_guard[1:]))
                # The existing AST keeps '<=' as an anonymous left value and
                # a '<' assignment block. Check its order and exact day offset.
                if pairs.count((date_left,date_right))!=1:
                    reject('HEIR_MINIMUM_DAY_GUARD_CHANGED')
                original_prepare=one(effects,prepare_key,required=True)
                prepare_branches=[row['value'] for row in original_prepare if row['key']=='if']
                if len(prepare_branches)!=2:
                    reject('ORIGINAL_RELATION_PREPARATION_CHANGED')
                missing_priest=one(prepare_branches[0],'limit',required=True)
                require(missing_priest,'NOT',[{'key':'exists','value':'cp:councillor_court_chaplain'}],'PRIEST_ASSIGNMENT_WITHOUT_MISSING_GUARD')
                empty_slot=one(prepare_branches[1],'limit',required=True)
                require(empty_slot,'exists','cp:councillor_court_chaplain','PUPPET_WITHOUT_ACTUAL_CHAPLAIN')
                require(empty_slot,'NOT',[{'key':'exists','value':'puppet:theological_agent_puppet'}],'PUPPET_WITHOUT_EMPTY_SLOT')
                # The unchanged save AST represents optional cp ?= as an
                # anonymous cp token followed by the '?' block; no new parser.
                require(empty_slot,None,'cp:councillor_court_chaplain','PUPPET_WITHOUT_ACTUAL_CHAPLAIN')
                cp=one(empty_slot,'?',required=True)
                require(cp,'NOT',[{'key':'exists','value':'puppeteer'}],'PUPPET_WITH_CONFLICTING_RELATION')
                require(prepare_branches[1],'set_puppet',[{'key':'target','value':'scope:recipient'},{'key':'type','value':'theological_agent_puppet'}],'CHANGED_STOCK_PUPPET_INPUT')
                extended_effects=parsed['common/scripted_effects/des_acceptance_extended_effects.txt']
                transfer=one(extended_effects,'des_acceptance_successor_readback_effect',required=True)
                if [row['key'] for row in transfer]!=['if','else'] or any(row['key']!='debug_log' for row in one(transfer,'else',required=True)):
                    reject('SUCCESSOR_EFFECT_OUTSIDE_IDENTITY_GUARD')
                anchored=one(transfer,'if',required=True)
                if [row['key'] for row in anchored]!=['limit','global_var:des_test_extended_owner','if','else']:
                    reject('SUCCESSOR_EFFECT_OUTSIDE_IDENTITY_GUARD')
                if one(anchored,'global_var:des_test_extended_owner',required=True)!=[{'key':'save_scope_as','value':'des_test_predecessor'}]:
                    reject('SUCCESSOR_PREDECESSOR_ANCHOR_CHANGED')
                branch=one(anchored,'if',required=True)
                guard=one(branch,'limit',required=True)
                if mutation=='missing-head':
                    rite_guard=next(row['value'] for row in guard if row['key']=='rite' and isinstance(row['value'],list))
                    rite_guard[:]=[row for row in rite_guard if row['key']!='head_of_rite']
                elif mutation=='product-write':
                    branch.append({'key':'set_variable','value':[{'key':'name','value':'des_bound_dynasty'},{'key':'value','value':'scope:des_test_predecessor.var:des_bound_dynasty'}]})
                elif mutation=='pardon-copy':
                    branch.append({'key':'add_character_flag','value':'des_test_pardon_stable'})
                elif mutation not in ('none','prison-main-target','prison-no-reason','prison-product-write'):
                    reject('UNKNOWN_TEST_MUTATION')
                identity_reason='SUCCESSOR_IDENTITY_GUARD_MISSING'
                require(one(anchored,'limit',required=True),'exists','global_var:des_test_extended_owner',identity_reason)
                for key,value in [('is_ai','no'),('is_alive','yes'),('is_adult','yes'),('this','scope:des_test_predecessor.var:des_test_ref_primary_heir'),('primary_title','scope:des_test_predecessor.var:des_test_ref_primary_title'),('rite','scope:des_test_predecessor.var:des_test_primary_rite'),('dynasty','scope:des_test_predecessor.var:des_test_bound_dynasty'),('house','scope:des_test_predecessor.var:des_test_primary_rite.var:des_join_house')]:
                    require(guard,key,value,identity_reason)
                require(guard,'NOT',[{'key':'has_variable','value':'has_edited_a_rite'}],identity_reason)
                rite_guard=next(row['value'] for row in guard if row['key']=='rite' and isinstance(row['value'],list))
                require(rite_guard,'head_of_rite','root',identity_reason)
                require(rite_guard,'exists','head_of_rite',identity_reason)
                require(rite_guard,'rite_has_doctrine','des_doctrine_none',identity_reason)
                require(one(guard,'scope:des_test_predecessor.var:des_test_ref_primary_title',required=True),'holder','root',identity_reason)
                predecessor=[row['value'] for row in guard if row['key']=='scope:des_test_predecessor' and isinstance(row['value'],list)]
                predecessor=next(rows for rows in predecessor if {'key':'is_alive','value':'no'} in rows)
                for key,value in [('is_alive','no'),('has_character_flag','des_test_primary_death_staged'),('has_character_flag','des_test_primary_heir_ready'),('has_variable','has_edited_a_rite')]:
                    require(predecessor,key,value,identity_reason)
                refs='des_test_primary_rite des_test_bound_dynasty des_test_source_rite des_test_source_dynasty des_test_ref_target des_test_ref_peer des_test_ref_child des_test_ref_outsider des_test_ref_birth_father des_test_ref_birth_mother des_test_ref_newborn des_test_ref_old_descendant des_test_old_descendant_house des_test_old_descendant_dynasty des_test_cadet_house des_test_ref_generated des_test_ref_second_founder des_test_ref_second_observer des_test_ref_second_target des_test_second_rite des_test_second_dynasty des_test_second_house des_test_second_creation_path des_test_ref_after_death'.split()
                flags='des_test_ready des_test_members_verified des_test_same_verified des_test_cross_verified des_test_repent_verified des_test_closed_verified des_test_extended_armed des_test_extended_started des_test_actual_birth_seen des_test_birth_verified des_test_descendant_verified des_test_generated_verified des_test_membership_correction_verified des_test_timer_verified des_test_second_verified des_test_cross_rites_verified des_test_cross_migration_verified des_test_founder_death_verified des_test_after_death_join_verified des_test_stock_crime_seen des_test_stock_retained'.split()
                for name in refs:
                    require(predecessor,'has_variable',name,'SUCCESSOR_SOURCE_VALUE_MISSING')
                for name in flags:
                    require(predecessor,'has_character_flag',name,'SUCCESSOR_HISTORY_NOT_PROVEN')
                expected_writes={name:'scope:des_test_predecessor.var:'+name for name in refs}
                expected_writes.update(des_test_ref_predecessor='scope:des_test_predecessor',des_test_ref_primary_heir='this',des_test_ref_primary_title='primary_title')
                actual_writes={}
                actual_flags=[]
                for row in branch:
                    key,value=row['key'],row['value']
                    if key=='set_variable':
                        name=one(value,'name',required=True)
                        actual=one(value,'value',required=True)
                        if name in actual_writes or name not in expected_writes or expected_writes[name]!=actual:
                            reject('SUCCESSOR_REFERENCE_TRANSFER_OUTSIDE_CONTRACT',name=name)
                        actual_writes[name]=actual
                    elif key=='add_character_flag':
                        if value not in flags+['des_test_successor_verified'] or value in actual_flags:
                            reject('SUCCESSOR_FLAG_TRANSFER_OUTSIDE_CONTRACT',name=value)
                        actual_flags.append(value)
                    elif key not in ('limit','debug_log'):
                        reject('SUCCESSOR_UNDECLARED_EFFECT',key=key)
                if actual_writes!=expected_writes or set(actual_flags)!=set(flags+['des_test_successor_verified']):
                    reject('SUCCESSOR_FINITE_TRANSFER_INCOMPLETE')
                stage=one(extended_decisions,'des_acceptance_primary_death_stage_decision',required=True)
                staged=one(one(one(stage,'effect',required=True),'hidden_effect',required=True),'if',required=True)
                for name in flags:
                    require(one(staged,'limit',required=True),'has_character_flag',name,'DEATH_BEFORE_OLD_OBSERVERS_FINISH')
                require(staged,'trigger_event',[{'key':'id','value':'des_acceptance_extended.80'},{'key':'days','value':'1'}],'DEATH_NOT_STAGED_NEXT_DAY')
                death=one(parsed['events/des_acceptance_extended_events.txt'],'des_acceptance_extended.80',required=True)
                death=one(one(death,'immediate',required=True),'if',required=True)
                require(death,'death',[{'key':'death_reason','value':'death_natural_causes'}],'CHANGED_STOCK_DEATH_INPUT')
                require(one(death,'limit',required=True),'primary_heir','var:des_test_ref_primary_heir',identity_reason)
                forbidden_names={'des_bound_dynasty','des_bound_rite','des_join_house','des_penalty_targets','des_observers','des_apostate_rite','has_edited_a_rite','has_created_a_faith'}
                def forbidden_writes(entries):
                    for row in entries:
                        key,value=row['key'],row['value']
                        if key in ('set_variable','remove_variable','set_global_variable','remove_global_variable','add_to_variable_list','remove_list_variable'):
                            name=one(value,'name',required=True) if isinstance(value,list) else value
                            if name in forbidden_names:
                                reject('FORBIDDEN_PRODUCT_OR_STOCK_WRITE',name=name)
                        if key in ('set_player_character','set_player','set_head_of_rite','set_rite_head','set_dynasty_head','set_house_head','clear_puppet','remove_puppet'):
                            reject('FORBIDDEN_IDENTITY_OR_RELATION_WRITE',key=key)
                        if isinstance(value,list):
                            forbidden_writes(value)
                for entries in parsed.values():
                    forbidden_writes(entries)
                required=json.loads(manifest.read_bytes())['receipt']['required_markers']
                if len(required)!=24 or literals.count('DESAF: TEST PASS actual_primary_heir_successor')!=1 or literals.count('DESAF: TEST PASS prisoner_control_ready')!=1:
                    reject('SUCCESSOR_MARKER_CONTRACT_CHANGED')
                missing=sorted(set(required)-set(literals))
                if missing:
                    reject('MISSING_LITERAL_REQUIRED_MARKER',markers=missing)
                expected=json.loads(baseline.read_bytes())['events']
                for event,guard in expected.items():
                    immediate=one(one(events,event,required=True),'immediate',required=True)
                    branch=one(immediate,'if',required=True)
                    if one(branch,'limit',required=True)!=guard['limit'] or one(immediate,'else',required=True)!=guard['else']:
                        reject('CHANGED_OBSERVER_OR_OUTSIDER_GUARD',event=event)
                    observer=json.loads(one(branch,'debug_log',required=True))
                    outsider=json.loads(one(one(branch,'scope:des_test_outsider',required=True),'debug_log',required=True))
                    if [observer,outsider]!=guard['success_logs']:
                        reject('CHANGED_SCOPED_SUCCESS_MARKERS',event=event)
                print(json.dumps({'status':'ACCEPTED','required_marker_count':len(required),'unchanged_guard_count':len(expected),'original_rite_readback_only_observes':True,'successor_reference_transfer_count':len(refs),'successor_history_transfer_count':len(flags),'heir_minimum_day_guard_validated':True,'separate_prisoner_control_custody_validated':True,'engine_semantics_verified':False}))
                """;
        Process process = new ProcessBuilder("python", "-B", "-X", "utf8", "-c", program,
                repository().toString(), fixture.fixture().toString(), fixture.manifest().toString(), baseline.toString(), mutation)
                .redirectErrorStream(true).start();
        assertTrue(process.waitFor(30, TimeUnit.SECONDS), "existing lexer/AST fixture probe timed out");
        return new ProbeResult(process.exitValue(), new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8));
    }

    private record ProbeResult(int exitCode, String output) { }

    private static void copyFixtureInputs(Path destinationRepository) throws IOException {
        Path sourceMain = repository().resolve("mod_dynastic_esotericism/tools/src/main");
        Path destinationMain = destinationRepository.resolve("mod_dynastic_esotericism/tools/src/main");
        Path emitter = Path.of("java/org/xar/ck3/dynastic/acceptance/FixtureEmitter.java");
        Files.createDirectories(destinationMain.resolve(emitter).getParent());
        Files.copy(sourceMain.resolve(emitter), destinationMain.resolve(emitter));
        Path resources = sourceMain.resolve("resources/acceptance-fixture");
        try (Stream<Path> sources = Files.walk(resources)) {
            for (Path source : sources.filter(Files::isRegularFile).toList()) {
                Path target = destinationMain.resolve("resources/acceptance-fixture").resolve(resources.relativize(source));
                Files.createDirectories(target.getParent());
                Files.copy(source, target);
            }
        }
    }

    @Test
    void rejectsMissingSourcesInvalidMachineAndIncompleteOptions() {
        assertThrows(IOException.class,
                () -> FixtureEmitter.emit(temporary, temporary.resolve("missing-sources"), "authored-machine"));
        assertThrows(IllegalArgumentException.class,
                () -> FixtureEmitter.emit(repository(), temporary.resolve("invalid-machine"), ""));
        assertEquals(1, FixtureEmitter.run(new String[]{"--output", temporary.resolve("no-output").toString()}));
        assertFalse(Files.exists(temporary.resolve("no-output")));
    }
}
