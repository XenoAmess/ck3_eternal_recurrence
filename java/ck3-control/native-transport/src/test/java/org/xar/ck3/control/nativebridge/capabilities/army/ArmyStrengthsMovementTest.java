package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.military.prestore.PrestoreCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMovement.*;

/** Executes unchanged Python producers on declared synthetic operands. No native packet, callback or Game qualification. */
final class ArmyStrengthsMovementTest {
    private static final String ORACLE = """
            import ast,copy,hashlib,json,pathlib,sys
            m=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
            def pin(r):
                b=pathlib.Path(r['path']).read_bytes()
                if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('actual original source drift: '+r['path'])
            for r in m['original_sources']:pin(r)
            pin(m['builder_source']);pin(m['java_bundle_source'])
            sys.path.insert(0,m['python_source_root']);sys.path.insert(0,m['tools_root'])
            from xar_autoplayer.bridge.war_contract import normalize_army_strengths
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.army_current_first_route_target_supply_contributors_projection import project_current_first_route_target_supply_contributors_v1 as target
            source=pathlib.Path(m['builder_source']['path']).read_text(encoding='utf-8')
            program=source.split('private static final String PROGRAM = '+chr(34)*3,1)[1].rsplit(chr(34)*3+';',1)[0]
            tree=ast.parse(program);selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'movement','row'}]
            if len(selected)!=2:raise RuntimeError('original declared operand builder unavailable')
            ns={};exec(compile(ast.Module(body=selected,type_ignores=[]),'original-declared-builder','exec'),ns)
            cases=[]
            names=['baseline','not_scheduled','route_zero','normalize_state3','negative_route_count','predicate_false','state1_bypass','missing_rate','overflow_add','provider_equal_zero','provider_equal_nonzero','provider_missing','missing_cost','missing_target_type','loaded_rule_negative','loaded_rule_missing','context_drift','enemy_context_only','public_zero_full_highbit','duplicate_target_subject','no_committed_target','entry_absent','schedule_unavailable']
            for name in names:
                row=ns['row']();a=row['army_id'];c=row['native_carmy_id'];move=row['current_movement_progress'];entry=row['current_unit_new_date_callback_entry_inputs_v1'];schedule=row['current_unit_new_date_schedule_inputs_v1']
                context=dict(army_id=a,current_province_id=1,route_province_ids=[2,3],route_source_count=2,route_read_status='complete_nonempty')
                query=dict(queried_snapshot_id='movement:42',queried_revision=42,queried_native_revision=7)
                if name=='not_scheduled':schedule.update(subject_stored_id_positions=[],subject_stored_id_occurrence_count_i32=0)
                if name in {'route_zero','normalize_state3','no_committed_target'}:entry['unit_route_count_i32']=0;context.update(route_province_ids=[],route_source_count=0,route_read_status='complete_empty')
                if name=='normalize_state3':row['monthly_loss_budget_inputs_v1']['unit_native_170_raw']=3
                if name=='negative_route_count':entry['unit_route_count_i32']=-1
                if name in {'predicate_false','state1_bypass'}:row['native_army_resolution_v1']['raw_reference']=c;move['native_army_movement_admission']=False
                if name=='state1_bypass':row['monthly_loss_budget_inputs_v1']['unit_native_170_raw']=1
                if name=='missing_rate':move.update(cached_edge_speed_raw=0,current_edge_movement_rate_raw=None)
                if name=='overflow_add':move.update(accumulated_movement_weight_raw=(1<<63)-1,cached_edge_speed_raw=2)
                if name in {'provider_equal_zero','provider_equal_nonzero','provider_missing'}:move['first_route_edge_weight_cost_raw']=107;move['first_edge_arrival_provider_byte_e_u8']=None if name=='provider_missing' else 1 if name=='provider_equal_nonzero' else 0
                if name=='missing_cost':move['first_route_edge_weight_cost_raw']=None
                if name=='missing_target_type':move['first_route_target_province_type_tag_u32']=None
                if name=='loaded_rule_negative':move['loaded_disembark_penalty_days_rule_i32']=-(1<<31)
                if name=='loaded_rule_missing':move['loaded_disembark_penalty_days_rule_i32']=None
                if name=='public_zero_full_highbit':
                    a=0;c=-(1<<31);row.update(army_id=a,native_carmy_id=c);context['army_id']=a
                    for v in (entry,schedule):v.update(subject_army_id_u32=a,subject_carmy_id_u32=c&0xffffffff)
                if name=='entry_absent':row.pop('current_unit_new_date_callback_entry_inputs_v1')
                if name=='schedule_unavailable':schedule.update(status='unavailable',ready=False,unavailable_reason='actual_schedule_unavailable',subject_stored_id_positions=None,subject_stored_id_occurrence_count_i32=None)
                nested=dict(source='native_current_province_mode0',status='available',unavailable_reason=None,current_usage_ready=True,contributors_ready=True,soldiers_scale=1,province_id=2,subject_army_id=a,subject_carmy_id=c,owner_character_id=29829,native_province_unit_count=0,native_supply_limit_soldiers=1000,native_supply_usage_soldiers=0,occurrences=[])
                if name=='duplicate_target_subject':
                    nested['occurrences']=[dict(stored_index=i,army_id=a,status='available',unavailable_reason=None,owner_character_id=29829,included=True,inclusion_basis='same_owner',native_carmy_id=c,native_eligible_current_soldiers=0,regiments=[]) for i in range(2)];nested['native_province_unit_count']=2
                family=dict(source='native_current_first_route_target_supply_contributors_12004',status='available',unavailable_reason=None,current_target_inputs_ready=True,subject_army_id=a,subject_carmy_id=c,current_province_id=1,first_route_target_province_id=2,route_source_count=2,target_contributors_v1=nested,subject_matching_occurrence_indices=[0,1] if name=='duplicate_target_subject' else [],subject_included_occurrence_count=2 if name=='duplicate_target_subject' else 0,input_basis='captured_committed_first_route_target',actual_arrival_observed=False,actual_after_arrival_usage_observed=False,full_arrival_supply_transition_ready=False)
                if name in {'route_zero','normalize_state3','no_committed_target'}:family.update(status='no_committed_target',current_target_inputs_ready=False,first_route_target_province_id=None,route_source_count=0,target_contributors_v1=None,subject_matching_occurrence_indices=[],subject_included_occurrence_count=None)
                row['current_first_route_target_supply_contributors_v1']=family
                normalized=normalize_army_strengths([row],expected_scope=[dict(army_id=a,scope_role='player',war_ids=[])])[0]
                snapshot=dict(snapshot_id='movement:42',revision=42,native_revision=7,player_armies=[copy.deepcopy(context)],active_wars=[])
                same=name!='context_drift'
                if not same:query['queried_revision']=43
                if name=='enemy_context_only':snapshot['player_armies']=[];snapshot['active_wars']=[dict(war_id=1,allied_armies=[],enemy_armies=[copy.deepcopy(context)])]
                outputs=GameplayBridgeService._unit_next_movement_projection_rows(query,[normalized],snapshot=snapshot)
                outputs['current_unit_new_date_entry_normalization_v1']=GameplayBridgeService._unit_new_date_entry_normalization_rows(query,[normalized])
                outputs['current_first_route_target_supply_contributors_v1']=[dict(army_id=a,projection=target(normalized,armycontext=context))]
                cases.append(dict(name=name,row=normalized,snapshot=snapshot,same_query=same,expected=outputs))
            for r in m['original_sources']:pin(r)
            pin(m['builder_source']);pin(m['java_bundle_source'])
            print(json.dumps(cases,separators=(',',':')))
            """;

    @Test void realOriginalServiceProducersAgreeWithAllSixTypedJavaConsumers() throws Exception {
        for (JsonNode sample : oracle()) {
            JsonNode row = sample.get("row"); int army = row.get("army_id").intValue(); var contexts = contexts(sample.get("snapshot"), sample.get("same_query").booleanValue());
            EntryProjection entry = entryProjection(row); Prefix prefix = prefix(row, entry); Edge edge = edge(prefix); Arrival arrival = arrival(army, edge, contexts.player(army));
            TargetInput target = target(row.get("current_first_route_target_supply_contributors_v1"), army, row.get("native_carmy_id").intValue(), contexts.target(army));
            var expected = sample.get("expected"); String name = sample.get("name").textValue();
            assertEquals(body(expected, "current_first_route_target_supply_contributors_v1"), canonical(targetProjectionNode(new TargetProjection(target, contexts.target(army)))), name);
            assertEquals(body(expected, "current_unit_new_date_entry_normalization_v1"), canonical(entryProjectionNode(entry)), name);
            assertEquals(body(expected, "current_unit_next_movement_prefix_v1"), canonical(prefixNode(prefix)), name);
            assertEquals(body(expected, "current_unit_next_first_edge_selection_v1"), canonical(edgeNode(edge)), name);
            assertEquals(body(expected, "current_unit_next_arrival_transition_v1"), canonical(arrivalNode(arrival)), name);
            assertEquals(body(expected, "current_unit_arrival_prestore_disembark_write_v1"), canonical(PrestoreCodec.node(prestore(row, arrival))), name);
            assertEquals(target, target(targetNode(target), army, row.get("native_carmy_id").intValue(), contexts.target(army)), name);
            Schedule schedule = schedule(row.get("current_unit_new_date_schedule_inputs_v1"), army, row.get("native_carmy_id").intValue());
            if (schedule != null) assertEquals(schedule, schedule(scheduleNode(schedule), army, row.get("native_carmy_id").intValue()), name);
        }
    }
    @Test void installedFamiliesAndStagesHaveTheExactRequestedCoverage() throws Exception {
        JsonNode manifest = manifest(); ExactRef source = ExactRef.fromJson(manifest.get("java_bundle_source"));
        var registry = new ArmyStrengthsFamilies.Registry(); var pipeline = new ArmyStrengthsPipeline(); install(registry, pipeline, source);
        assertTrue(registry.coverage().installed().containsAll(List.of(ArmyStrengthsFamilies.Key.CURRENT_FIRST_ROUTE_TARGET_SUPPLY_CONTRIBUTORS_V1,
                ArmyStrengthsFamilies.Key.CURRENT_UNIT_NEW_DATE_SCHEDULE_INPUTS_V1, ArmyStrengthsFamilies.Key.CURRENT_UNIT_NEW_DATE_CALLBACK_ENTRY_INPUTS_V1)));
        assertEquals(6, pipeline.coverage().installed().size()); registry.freeze(); pipeline.freeze();
        assertFalse(registry.coverage().complete()); assertThrows(IllegalArgumentException.class, pipeline::requireComplete);
    }
    @Test void inputTokenKindsUnknownFieldsAndStoredPositionDomainAreRejectedAtRealDecoders() throws Exception {
        JsonNode sample = oracle().get(0); ObjectNode row = (ObjectNode) sample.get("row"); int army = row.get("army_id").intValue(), carmy = row.get("native_carmy_id").intValue();
        ObjectNode schedule = (ObjectNode) row.get("current_unit_new_date_schedule_inputs_v1");
        assertThrows(IllegalArgumentException.class, () -> schedule(schedule.deepCopy().put("subject_army_id_u32", true), army, carmy));
        assertThrows(IllegalArgumentException.class, () -> schedule(schedule.deepCopy().put("schema_version", 1.0), army, carmy));
        assertThrows(IllegalArgumentException.class, () -> schedule(schedule.deepCopy().put("extra", 0), army, carmy));
        ObjectNode duplicate = schedule.deepCopy(); duplicate.putArray("subject_stored_id_positions").add(1).add(1);
        assertThrows(IllegalArgumentException.class, () -> schedule(duplicate, army, carmy));
        assertThrows(IllegalArgumentException.class, () -> schedule(schedule, army + 1, carmy));
        ObjectNode entry = (ObjectNode) row.get("current_unit_new_date_callback_entry_inputs_v1"); ObjectNode missing = entry.deepCopy(); missing.remove("unit_route_count_i32");
        assertThrows(IllegalArgumentException.class, () -> entry(missing, army, carmy));
        ObjectNode target = (ObjectNode) row.get("current_first_route_target_supply_contributors_v1");
        assertThrows(IllegalArgumentException.class, () -> target(target.deepCopy().put("actual_arrival_observed", true), army, carmy, null));
        assertThrows(IllegalArgumentException.class, () -> target(target, army, carmy, new org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.RouteContext(army, 1, "complete_nonempty", 2, List.of(999, 3))));
    }
    @Test void decimalPublicEncodingKeepsNativeSigned64AndUnsignedIdentityExact() {
        ObjectNode n = ArmyJson.empty(); n.putArray("rows").addObject().put("weight", Long.MIN_VALUE).put("revision", new java.math.BigInteger("18446744073709551615"));
        RawJson original = new RawJson(ArmyJson.bytes(n)); RawJson encoded = ArmyStrengthsPublicNumbers.encode(original, List.of(
                new ArmyStrengthsPublicNumbers.Rule("/rows/*/weight", ArmyStrengthsPublicNumbers.Domain.SIGNED_64),
                new ArmyStrengthsPublicNumbers.Rule("/rows/*/revision", ArmyStrengthsPublicNumbers.Domain.UNSIGNED_64)));
        JsonNode actual = ArmyStrengthsCodec.parseValue(encoded); assertEquals(Long.toString(Long.MIN_VALUE), actual.at("/rows/0/weight").textValue());
        assertEquals("18446744073709551615", actual.at("/rows/0/revision").textValue()); assertEquals(n, ArmyStrengthsCodec.parseValue(original));
    }
    private static JsonNode body(JsonNode all, String key) { return all.get(key).get(0).get("projection"); }
    private static JsonNode canonical(JsonNode n) { return fullJson(ArmyJson.bytes(n), RawJson.MAXIMUM_BYTES); }
    private static JsonNode manifest() throws Exception {
        Path path = Path.of(required("xar.army.strengths.movement.oracle.manifest")); byte[] raw = Files.readAllBytes(path);
        assertEquals(required("xar.army.strengths.movement.oracle.manifest.sha256"), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)), "original manifest drift");
        return fullJson(raw, 1_048_576);
    }
    private static JsonNode oracle() throws Exception {
        manifest(); String executable = required("xar.python"), input = required("xar.army.strengths.movement.oracle.manifest");
        Process process = new ProcessBuilder(executable, "-I", "-B", "-X", "utf8", "-c", ORACLE, input).redirectErrorStream(true).start();
        try (var pool = Executors.newSingleThreadExecutor()) {
            var output = pool.submit(() -> process.getInputStream().readNBytes(2_097_153));
            if (!process.waitFor(60, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("actual movement original-producer timeout"); }
            byte[] bytes = output.get(); assertEquals(0, process.exitValue(), new String(bytes, StandardCharsets.UTF_8)); assertTrue(bytes.length <= 2_097_152);
            return fullJson(bytes, 2_097_152);
        } finally { if (process.isAlive()) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); } }
    }
    /** The sole Army native-token boundary permits its requested budget; StrictJson's map cap remains unchanged. */
    private static JsonNode fullJson(byte[] raw, int maximumBytes) {
        return ArmyJson.parseValue(raw, maximumBytes);
    }
    private static String required(String property) { String value = System.getProperty(property); if (value == null || value.isBlank()) throw new IllegalStateException("Mandatory original-producer setting is missing: " + property); return value; }
}
