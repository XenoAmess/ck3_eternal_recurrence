package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.commander.ArmyCommanderCandidatesCodec;
import org.xar.ck3.control.wave2.military.commander.CommanderQuality;
import org.xar.ck3.control.wave2.military.commander.CommanderQualityCodec;

/** Actual original callable differential on retained native baselines and explicitly derived target operands. No Game/assignment. */
public final class CommanderTargetOriginalProducerTest {
    private static ObjectNode captured;
    private static final String PROGRAM = """
            import ast,copy,hashlib,json,pathlib,sys
            m=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
            def pin(r):
                b=pathlib.Path(r['path']).read_bytes()
                if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('original commander source/fixture drift: '+r['path'])
            refs=m['source_refs']+[m['legacy_golden'],m['capacity_examples']]+m['native_originals']
            for r in refs:pin(r)
            sys.path.insert(0,m['python_source_root']);sys.path.insert(0,m['tools_root'])
            from xar_autoplayer.bridge.army_commander_candidates import normalize_army_commander_candidates_v1,query_army_commander_candidates_v1_step,QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY as BASE,QUERY_ARMY_COMMANDER_CANDIDATES_V1_FOR_TARGET_CAPABILITY as TARGET
            from xar_autoplayer.commander_quality_formal_proposal_v1 import propose_commander_quality_v1
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge import army_commander_conditional_capacity as capacity
            g=json.loads(pathlib.Path(m['legacy_golden']['path']).read_text(encoding='utf-8'));good=[];bad=[];wrappers=[]
            def wrapper(raw,snapshot,target):
                result=dict(step=query_army_commander_candidates_v1_step(raw['army_id'],target_province_id=target),accepted=True,status='completed',read_only=True,query_sequence=7,snapshot_revision=snapshot['native_revision'],date_raw=snapshot['date_raw'],army_commander_candidates=copy.deepcopy(raw))
                return dict(schema='xar.java.commander-quality-observed-query.v1',army_id=raw['army_id'],snapshot_before=copy.deepcopy(snapshot),snapshot_after=copy.deepcopy(snapshot),bridge_capabilities=[BASE,TARGET],expected_revision=snapshot['revision'],native_result=result)
            def original_service(w,target):
                service=object.__new__(GameplayBridgeService);calls=[]
                def snap():
                    calls.append('snapshot');return copy.deepcopy(w['snapshot_before'] if calls.count('snapshot')==1 else w['snapshot_after'])
                def execute(step,*,expected_revision):
                    if step!=w['native_result']['step'] or expected_revision!=w['snapshot_before']['revision']:raise RuntimeError('original service read port binding differs')
                    calls.append('execute');return copy.deepcopy(w['native_result'])
                service.snapshot=snap;service.capabilities=lambda:dict(bridge_capabilities=copy.deepcopy(w['bridge_capabilities']));service.execute_step=execute
                return service.query_army_commander_candidates_v1(w['army_id'],expected_revision=w['expected_revision'],target_province_id=target),calls
            def add(name,raw,snapshot,target,label):
                before=copy.deepcopy(raw);normal=normalize_army_commander_candidates_v1(raw,expected_army_id=raw['army_id'],expected_snapshot_revision=snapshot['native_revision'],expected_date_raw=snapshot['date_raw'],expected_target_province_id=target)
                proposal=propose_commander_quality_v1(normal,snapshot=snapshot,query_sequence=7);w=wrapper(raw,snapshot,target);service,calls=original_service(w,target)
                if service['army_commander_candidates']!=normal or service['commander_quality_proposal']!=proposal or calls.count('execute')!=1 or calls.count('snapshot')!=2 or raw!=before:raise RuntimeError('original producer/service preservation failed')
                good.append(dict(name=name,label=label,target=target,wrapper=w,normalized=normal,proposal=proposal,proposal_input=dict(schema='xar.java.commander-quality-input.v1',snapshot=snapshot,query_sequence=7,candidates=normal)))
            for index,case in enumerate(g['cases']):
                raw=copy.deepcopy(case['input']['candidates']);snapshot=copy.deepcopy(case['input']['snapshot']);add('base-'+case['name'],raw,snapshot,None,'retained_original_or_declared_legacy_quality_fixture')
                target=3200+index;raw['target_province_id']=target
                for ordinal,row in enumerate(raw['candidates']):row['target_roll_bounds']=dict(status='available',source='native_current_candidate_target_roll_context',source_target_province_id=target,effective_min_roll=-(ordinal+3),effective_max_roll=-(ordinal+9),unavailable_reason=None)
                add('target-'+case['name'],raw,snapshot,target,'explicitly_derived_target_inputs_not_native_target_wire')
            baseline=copy.deepcopy(g['cases'][0]['input']);base=baseline['candidates'];snapshot=baseline['snapshot'];target=1
            for name in ['missing-roll','null-roll','unavailable-roll','public-zero','native-phase-speed-extremes','partial-count-independent','unknown-extensions','large-complete-frame']:
                raw=copy.deepcopy(base);frame=copy.deepcopy(snapshot);raw['target_province_id']=target
                if name=='null-roll':raw['candidates'][0]['target_roll_bounds']=None
                if name=='unavailable-roll':raw['candidates'][0]['target_roll_bounds']=dict(status='unavailable',source='native_current_candidate_target_roll_context',source_target_province_id=target,effective_min_roll=None,effective_max_roll=None,unavailable_reason='actual_target_context_unavailable')
                if name=='public-zero':
                    raw.update(army_id=0,native_carmy_id=0,owner_character_id=0);frame['player_armies'][0]['army_id']=0;raw['current_commander']['character_id']=0
                    for key in ['current_native_ai_base_quality','current_total_martial']:raw['current_commander'][key]['source_character_id']=0
                    raw['current_movement_speed'].update(public_cunit_id=0,native_carmy_id=0,owner_character_id=0,current_commander_character_id=0)
                if name=='native-phase-speed-extremes':raw['candidates'][0]['siege_phase_time_modifier_raw']=-(1<<63);raw['current_movement_speed']['land']['raw']=(1<<63)-1;frame['revision']=(1<<64)-1;frame['native_revision']=(1<<64)-2;raw['snapshot_revision']=frame['native_revision'];raw['current_movement_speed']['snapshot_revision']=frame['native_revision']
                if name=='partial-count-independent':raw.update(status='partial',candidate_collection_complete=False,candidate_source_count=99)
                if name=='unknown-extensions':raw['future_root']={'opaque_decimal':1.25};raw['current_commander']['future_role']=[True,None,'observed'];raw['candidates'][0]['future_row']={'value':'keep'};raw['current_movement_speed']['land']['future_rate']=False
                if name=='large-complete-frame':frame['opaque_large_context']='x'*1200000;raw['future_complete_pool']='y'*160000
                add(name,raw,frame,target,'explicitly_derived_target_boundary_inputs_not_native_target_wire')
            raw=copy.deepcopy(base);raw['target_province_id']=(1<<31)-1;add('maximum-positive-province',raw,copy.deepcopy(snapshot),(1<<31)-1,'explicitly_derived_maximum_positive_native_province')
            raw=copy.deepcopy(base);raw.pop('target_province_id',None);raw['current_commander'].pop('unavailable_reason',None);row=raw['candidates'][0];row.update(available=False,final_eligibility_observable=False,quality_observable=False)
            for key in ['character_id','can_assign','native_ai_base_quality','generic_advantage_points','unavailable_reason']:row.pop(key,None)
            add('legacy-missing-fields',raw,copy.deepcopy(snapshot),None,'explicitly_derived_original_optional_field_absence')
            raw=copy.deepcopy(base);raw['schema']='ck3_12003_army_commander_candidates_v1';raw['current_movement_speed']=None;raw['current_commander']['current_native_ai_base_quality']=None;raw['candidates'][0].update(target_roll_bounds=None,conditional_supply_capacity_v1=None);add('legacy-null-independent-observations',raw,copy.deepcopy(snapshot),None,'explicitly_derived_original_null_observations')
            tree=ast.parse(pathlib.Path(m['capacity_examples']['path']).read_text(encoding='utf-8'));functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_leaf','_packet'}];ns={'capacity':capacity};exec(compile(ast.Module(body=functions,type_ignores=[]),'original-declared-capacity-examples','exec'),ns)
            vectors=[]
            for cls in [n for n in tree.body if isinstance(n,ast.ClassDef)]:
                for method in [n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_native_arithmetic_examples_include_slow_path_and_wrap']:
                    for statement in method.body:
                        if isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cases' for t in statement.targets):vectors=ast.literal_eval(statement.value)
            if len(vectors)!=9:raise RuntimeError('original native fixed multiply example set changed')
            for index,values in enumerate(vectors):
                raw=ns['_packet']();raw['target_province_id']=target;raw['candidates'][0]['conditional_supply_capacity_v1']=ns['_leaf'](*values);add('capacity-wrap-'+str(index),raw,copy.deepcopy(snapshot),target,'original_declared_capacity_examples_with_explicit_derived_target')
            raw=ns['_packet']();raw['target_province_id']=target;leaf=ns['_leaf']();leaf.update(status='unavailable',additive_modifier_raw=None,conditional_capacity_raw=None,unavailable_reason='candidate_aggregate_unavailable');raw['candidates'][0]['conditional_supply_capacity_v1']=leaf;add('capacity-partial-inputs',raw,copy.deepcopy(snapshot),target,'original_declared_capacity_partial_observation')
            seed=copy.deepcopy(good[15]);seed=next(v for v in good if v['target'] is not None);normal_seed=copy.deepcopy(seed['wrapper']['native_result']['army_commander_candidates'])
            def reject(name,raw,target_override=1):
                expected_target=seed['target'] if target_override==1 else target_override
                try:normalize_army_commander_candidates_v1(raw,expected_army_id=normal_seed['army_id'],expected_snapshot_revision=seed['wrapper']['snapshot_before']['native_revision'],expected_date_raw=seed['wrapper']['snapshot_before']['date_raw'],expected_target_province_id=expected_target)
                except (ValueError,TypeError):bad.append(dict(name=name,raw=raw,target=expected_target,army=normal_seed['army_id'],native_revision=seed['wrapper']['snapshot_before']['native_revision'],date_raw=seed['wrapper']['snapshot_before']['date_raw']))
                else:raise RuntimeError('original normalizer accepted negative '+name)
            for name,field,value in [('army-bool','army_id',True),('army-float','army_id',83886367.0),('native-negative','native_carmy_id',-(1<<31)),('target-zero','target_province_id',0),('wrong-target','target_province_id',3201),('native-revision-float','snapshot_revision',11.0)]:
                raw=copy.deepcopy(normal_seed);raw[field]=value;reject(name,raw)
            for name,field,value in [('roll-target','source_target_province_id',3201),('roll-min-float','effective_min_roll',1.0),('roll-max-bool','effective_max_roll',True),('roll-reason','unavailable_reason','not-null')]:
                raw=copy.deepcopy(normal_seed);raw['candidates'][0]['target_roll_bounds'][field]=value;reject(name,raw)
            raw=copy.deepcopy(normal_seed);reject('unrequested-target',raw,None)
            for name,field,value in [('capacity-number','loaded_full_raw',20000000),('capacity-negative-zero','loaded_full_raw','-0'),('capacity-derived-mismatch','conditional_capacity_raw','31250001')]:
                raw=copy.deepcopy(normal_seed);raw['candidates'][0]['conditional_supply_capacity_v1']=ns['_leaf']();raw['candidates'][0]['conditional_supply_capacity_v1'][field]=value;reject(name,raw)
            for name in ['missing-target-cap','wrong-step-target','after-revision-drift','after-unpaused','duplicate-player-scope']:
                w=copy.deepcopy(seed['wrapper'])
                if name=='missing-target-cap':w['bridge_capabilities']=[BASE]
                if name=='wrong-step-target':w['native_result']['step']=query_army_commander_candidates_v1_step(w['army_id'],target_province_id=3201)
                if name=='after-revision-drift':w['snapshot_after']['revision']+=1
                if name=='after-unpaused':w['snapshot_after']['paused']=False
                if name=='duplicate-player-scope':w['snapshot_before']['player_armies'].append(copy.deepcopy(w['snapshot_before']['player_armies'][0]))
                try:original_service(w,seed['target'])
                except Exception:wrappers.append(dict(name=name,wrapper=w,target=seed['target']))
                else:raise RuntimeError('actual original Service accepted negative '+name)
            for r in refs:pin(r)
            print(json.dumps(dict(good=good,bad=bad,rejected_wrappers=wrappers,scope='Original normalization/proposal/Service callables; four retained whole-native baseline pins, derived target operands explicitly labeled; no new native target capture, no assignment.'),separators=(',',':')))
            """;

    /** Shared only by application test consumers; never called from a production module. */
    public static synchronized JsonNode originalCorpus() throws Exception {
        JsonNode manifest = manifest(); verifyInputs(manifest);
        if (captured == null) {
            Process child = new ProcessBuilder(required("xar.python"), "-I", "-B", "-X", "utf8", "-c", PROGRAM, required("xar.commander.target.oracle.manifest")).redirectErrorStream(true).start();
            try (var executor = Executors.newSingleThreadExecutor()) {
                var output = executor.submit(() -> child.getInputStream().readNBytes(8_388_609));
                if (!child.waitFor(60, TimeUnit.SECONDS)) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); throw new IllegalStateException("actual commander original producer timeout"); }
                byte[] bytes = output.get(); assertEquals(0, child.exitValue(), new String(bytes, StandardCharsets.UTF_8)); assertTrue(bytes.length <= 8_388_608);
                captured = StrictJson.object(ArmyCommanderCandidatesCodec.parseJson(bytes), java.util.Set.of("good", "bad", "rejected_wrappers", "scope"));
            } finally { if (child.isAlive()) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); } }
        }
        verifyInputs(manifest); return captured.deepCopy();
    }
    @Test void realOriginalNormalizerProposalAndServiceAgreeWithCompleteBaseAndTargetAdmission() throws Exception {
        for (JsonNode sample : originalCorpus().get("good")) {
            byte[] raw = ArmyCommanderCandidatesCodec.encodeJson(sample.get("wrapper")); boolean target = !sample.get("target").isNull();
            var observed = target ? CommanderQualityCodec.admitObservedTargetObservation(raw, sample.get("target").intValue()) : CommanderQualityCodec.admitObservedObservation(raw);
            assertEquals(sample.get("normalized"), canonical(observed.normalizedJson()), sample.get("name").textValue());
            assertEquals(sample.get("proposal"), canonical(CommanderQualityCodec.encodeProposal(observed.proposal())), sample.get("name").textValue());
            var decoded = ArmyCommanderCandidatesCodec.normalize(ArmyCommanderCandidatesCodec.encode(observed.normalized()), expected(sample));
            assertEquals(observed.normalized(), decoded, sample.get("name").textValue());
            var pure = target ? CommanderQualityCodec.decodeTargetProposalInput(sample.get("proposal_input"), sample.get("target").intValue()) : CommanderQualityCodec.decodeProposalInput(sample.get("proposal_input"));
            assertEquals(observed.proposal(), pure); assertFalse(CommanderQualityCodec.encodeProposal(pure).get("assignment_executed").booleanValue());
            byte[] proposalInput = ArmyCommanderCandidatesCodec.encodeJson(sample.get("proposal_input"));
            assertEquals(sample.get("proposal"), ArmyCommanderCandidatesCodec.parseJson(target ? CommanderQualityCodec.proposeTarget(proposalInput, sample.get("target").intValue()) : CommanderQualityCodec.propose(proposalInput)));
        }
    }
    @Test void actualOriginalNegativeNormalizerAndServiceVectorsRemainRejected() throws Exception {
        JsonNode corpus = originalCorpus();
        for (JsonNode bad : corpus.get("bad")) {
            var context = new ArmyCommanderCandidatesCodec.Expected(new CommanderQuality.NativeId(bad.get("army").intValue()), bad.get("native_revision").bigIntegerValue(), bad.get("date_raw").bigIntegerValue(), bad.get("target").isNull() ? Optional.empty() : Optional.of(new ArmyCommanderCandidatesCodec.Province(bad.get("target").intValue())));
            assertThrows(IllegalArgumentException.class, () -> ArmyCommanderCandidatesCodec.normalize(bad.get("raw"), context), bad.get("name").textValue());
        }
        for (JsonNode bad : corpus.get("rejected_wrappers")) assertThrows(IllegalArgumentException.class, () -> CommanderQualityCodec.admitObservedTargetObservation(ArmyCommanderCandidatesCodec.encodeJson(bad.get("wrapper")), bad.get("target").intValue()), bad.get("name").textValue());
    }
    @Test void targetMissingNullAndObservedRollsStayIndependentOfQualityAndLegality() throws Exception {
        JsonNode corpus = originalCorpus(); JsonNode missing = find(corpus, "missing-roll"), explicitNull = find(corpus, "null-roll"), unavailable = find(corpus, "unavailable-roll");
        assertFalse(missing.get("normalized").get("candidates").get(0).has("target_roll_bounds")); assertTrue(explicitNull.get("normalized").get("candidates").get(0).get("target_roll_bounds").isNull());
        assertEquals(missing.get("proposal"), explicitNull.get("proposal")); assertEquals(missing.get("proposal"), unavailable.get("proposal"));
        for (JsonNode sample : corpus.get("good")) if (sample.get("name").textValue().startsWith("capacity-wrap-")) {
            assertFalse(sample.get("normalized").get("candidates").get(0).get("can_assign").booleanValue()); assertEquals("no_eligible_candidate", sample.get("proposal").get("status").textValue());
        }
    }
    @Test void fullFramesAndPublicWideDecimalsUseExactSeparateRepresentations() throws Exception {
        JsonNode corpus = originalCorpus(), large = find(corpus, "large-complete-frame"), extremes = find(corpus, "native-phase-speed-extremes");
        byte[] raw = ArmyCommanderCandidatesCodec.encodeJson(large.get("wrapper")); assertTrue(raw.length > 2000000);
        var observation = CommanderQualityCodec.admitObservedTargetObservation(raw, large.get("target").intValue()); assertEquals(160000, observation.normalizedJson().get("future_complete_pool").textValue().length());
        var wide = CommanderQualityCodec.admitObservedTargetObservation(ArmyCommanderCandidatesCodec.encodeJson(extremes.get("wrapper")), extremes.get("target").intValue());
        ObjectNode publicJson = wide.publicV2NormalizedJson(); assertEquals("18446744073709551614", publicJson.get("snapshot_revision").textValue());
        assertEquals(Long.toString(Long.MIN_VALUE), publicJson.at("/candidates/0/siege_phase_time_modifier_raw").textValue()); assertEquals(Long.toString(Long.MAX_VALUE), publicJson.at("/current_movement_speed/land/raw").textValue());
        assertTrue(wide.normalizedJson().at("/candidates/0/siege_phase_time_modifier_raw").isIntegralNumber()); assertEquals("18446744073709551615", CommanderQualityCodec.encodePublicV2Proposal(wide.proposal()).at("/frame/revision").textValue());
        ObjectNode changed = wide.normalizedJson(); changed.put("unknown_wide_identity", new BigInteger("9007199254740993"));
        var unknown = ArmyCommanderCandidatesCodec.normalize(changed, expected(extremes)); assertThrows(IllegalArgumentException.class, () -> ArmyCommanderCandidatesCodec.publicV2Node(unknown));
    }
    @Test void canonicalStepAndNativeIdentityDomainsFollowOriginalContract() {
        String good = "query-army-commander-candidates-v1-for-army-0-at-province-2147483647"; var request = ArmyCommanderCandidatesCodec.parseStep(good).orElseThrow(); assertEquals(good, request.step());
        assertEquals(ArmyCommanderCandidatesCodec.QUERY_TARGET_CAPABILITY, request.capability());
        for (String bad : List.of("query-army-commander-candidates-v1-for-army-00-at-province-1", "query-army-commander-candidates-v1-for-army-0-at-province-0", "query-army-commander-candidates-v1-for-army-0-at-province-+1", "query-army-commander-candidates-v1-for-army--1-at-province-1", "query-army-commander-candidates-v1-for-army-2147483648-at-province-1")) assertTrue(ArmyCommanderCandidatesCodec.parseStep(bad).isEmpty());
        assertEquals(0, new CommanderQuality.NativeId(0).value()); assertThrows(IllegalArgumentException.class, () -> new CommanderQuality.NativeId(Integer.MIN_VALUE));
    }
    @Test void selectedFormalContinuationAndOriginalSdkTokensRemainComplete() throws Exception {
        JsonNode manifest = manifest(); verifyInputs(manifest);
        JsonNode golden = ArmyCommanderCandidatesCodec.parseJson(Files.readAllBytes(Path.of(manifest.get("legacy_golden").get("path").textValue())));
        int count = 0;
        for (JsonNode sample : golden.get("plans")) {
            ObjectNode input = ((ObjectNode) sample.get("input")).deepCopy(); byte[] raw = ArmyCommanderCandidatesCodec.encodeJson(input);
            assertEquals(sample.get("expected"), ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.plan(raw)), sample.get("name").textValue());
            JsonNode finished = ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.continuePlan(raw)); assertEquals("completed", finished.get("status").textValue()); assertEquals(sample.get("expected"), finished.get("planned"));
            JsonNode originalQueries = input.get("queries");
            for (int prefix = 0; prefix < originalQueries.size(); prefix++) {
                ObjectNode partial = input.deepCopy(); ArrayNode queries = partial.putArray("queries"); for (int i = 0; i < prefix; i++) queries.add(originalQueries.get(i).deepCopy());
                JsonNode waiting = ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.continuePlan(ArmyCommanderCandidatesCodec.encodeJson(partial)));
                assertEquals("query", waiting.get("status").textValue()); assertEquals(originalQueries.get(prefix).get("army_id"), waiting.get("army_id")); assertEquals(input.get("planned").get("revision"), waiting.get("expected_revision"));
            }
            ObjectNode plan = (ObjectNode) input.get("planned").get("plan"); plan.put("source_signed_zero", -0.0d); plan.put("source_decimal", new java.math.BigDecimal("1.2300000000000000001"));
            String output = new String(CommanderQualityCodec.plan(ArmyCommanderCandidatesCodec.encodeJson(input)), StandardCharsets.UTF_8);
            assertTrue(output.contains("\"source_signed_zero\":-0.0")); assertTrue(output.contains("\"source_decimal\":1.2300000000000000001")); count++;
        }
        assertEquals(13, count); verifyInputs(manifest);
    }
    private static ArmyCommanderCandidatesCodec.Expected expected(JsonNode sample) { JsonNode wrapper = sample.get("wrapper"), before = wrapper.get("snapshot_before"); return new ArmyCommanderCandidatesCodec.Expected(new CommanderQuality.NativeId(wrapper.get("army_id").intValue()), before.get("native_revision").bigIntegerValue(), before.get("date_raw").bigIntegerValue(), sample.get("target").isNull() ? Optional.empty() : Optional.of(new ArmyCommanderCandidatesCodec.Province(sample.get("target").intValue()))); }
    private static JsonNode find(JsonNode corpus, String name) { for (JsonNode sample : corpus.get("good")) if (sample.get("name").textValue().equals(name)) return sample; throw new AssertionError("missing original case: " + name); }
    private static JsonNode canonical(JsonNode n) { return ArmyCommanderCandidatesCodec.parseJson(ArmyCommanderCandidatesCodec.encodeJson(n)); }
    private static JsonNode manifest() throws Exception { Path p = Path.of(required("xar.commander.target.oracle.manifest")); byte[] b = Files.readAllBytes(p); assertEquals(required("xar.commander.target.oracle.manifest.sha256"), digest(b)); return StrictJson.parse(b, 131072); }
    private static void verifyInputs(JsonNode m) throws Exception { for (JsonNode ref : m.get("source_refs")) pin(ref); pin(m.get("legacy_golden")); pin(m.get("capacity_examples")); for (JsonNode ref : m.get("native_originals")) pin(ref); }
    private static void pin(JsonNode ref) throws Exception { byte[] b = Files.readAllBytes(Path.of(ref.get("path").textValue())); assertEquals(ref.get("bytes").longValue(), b.length); assertEquals(ref.get("sha256").textValue(), digest(b)); }
    private static String digest(byte[] b) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)); }
    private static String required(String property) { String value = System.getProperty(property); if (value == null || value.isBlank()) throw new IllegalStateException("Mandatory original commander producer setting is missing: " + property); return value; }
}
