package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsRefillProjections.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsRefillComposition.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsRefillBesieging.*;

/** Fresh original producer -> registered typed families -> all eight Java consumers.
 * This is an offline differential, not native/Game or complete public-route qualification. */
final class ArmyStrengthsRefillOriginalParityTest {
    @TempDir Path temporary;
    private static final List<ArmyStrengthsFamilies.Key> KEYS=List.of(
        ArmyStrengthsFamilies.Key.REGIMENT_REPLENISHMENT,ArmyStrengthsFamilies.Key.REGIMENT_REPLENISHMENT_RECORDS_V1,
        ArmyStrengthsFamilies.Key.FIXED_CHUNK0_PREPARATION_INPUTS_V1,ArmyStrengthsFamilies.Key.CURRENT_PROVINCE_BESIEGING_CONTRIBUTORS_V1,
        ArmyStrengthsFamilies.Key.CURRENT_LAND_SUPPLY_RATE_INPUTS_V1,ArmyStrengthsFamilies.Key.SCOPED_ORDERED_REFILL_INPUTS_V1,
        ArmyStrengthsFamilies.Key.ORDERED_BESIEGING_REFILL_INPUTS_V1,ArmyStrengthsFamilies.Key.ORDERED_BESIEGING_FIXED_CHUNK0_PREPARATION_INPUTS_V1,
        ArmyStrengthsFamilies.Key.NEXT_ROUTE_REPLENISHMENT_POSITION_INPUTS_V1);
    @Test void freshCompleteOriginalServiceAndBothEntryModesMatchAllRefillConsumers() throws Exception {
        ObjectNode capture=capture();verifySources(capture);var registry=new ArmyStrengthsFamilies.Registry();var pipeline=new ArmyStrengthsPipeline();
        ArmyStrengthsRefill.install(registry,pipeline,actualSource());registry.freeze();pipeline.freeze();
        assertEquals(8,pipeline.coverage().installed().size());assertFalse(pipeline.coverage().complete());
        for(JsonNode example:capture.withArray("cases")){
            String label=example.get("name").textValue();ObjectNode actual=ArmyJson.object(example.get("result"));
            ObjectNode original=ArmyJson.object(example.get("input"));ObjectNode normalized=ArmyJson.object(actual.get("army_strengths").get(0));
            Row row=row(registry,original,normalized,label);ObjectNode before=normalized.deepCopy();
            var land=postLand(row,normalized);var monthly=selectedMonthly(row,normalized,land);var prep=preparation(row,false);var bprep=preparation(row,true);
            boolean fixed=example.get("refill_mode").textValue().equals("fixed_chunk0_prepare");boolean bfixed=example.get("besieging_mode").textValue().equals("fixed_chunk0_prepare");
            var scoped=scoped(row,source(row,ArmyStrengthsRefill.ScopedOrdered.class,ArmyStrengthsFamilies.Key.SCOPED_ORDERED_REFILL_INPUTS_V1),fixed?prep:null);
            assertStage(actual,ArmyStrengthsPipeline.Stage.SAME_INPUT_CONDITIONAL_POST_REFILL_LAND_SUPPLY_RATE_V1,encodeLand(land),label);
            assertStage(actual,ArmyStrengthsPipeline.Stage.SAME_INPUT_CONDITIONAL_SELECTED_REFILL_MONTHLY_ASSEMBLY_V1,encodeMonthly(monthly),label);
            assertStage(actual,ArmyStrengthsPipeline.Stage.SAME_INPUT_CONDITIONAL_POST_REFILL_BESIEGING_CURRENT_V1,encodePost(post(row,monthly.union()==null?null:monthly.union().projection().chunks())),label);
            assertStage(actual,ArmyStrengthsPipeline.Stage.SAME_INPUT_CONDITIONAL_FIXED_CHUNK0_PREPARATION_V1,encodePreparationProjection(prep),label);
            assertStage(actual,ArmyStrengthsPipeline.Stage.SAME_INPUT_CONDITIONAL_SCOPED_ORDERED_REFILL_CURRENT_V1,encodeScopedProjection(scoped),label);
            assertStage(actual,ArmyStrengthsPipeline.Stage.NEXT_ROUTE_POSITION_SCOPED_ORDERED_REFILL_V1,encodeNext(next(row)),label);
            assertStage(actual,ArmyStrengthsPipeline.Stage.SAME_INPUT_CONDITIONAL_ORDERED_BESIEGING_FIXED_CHUNK0_PREPARATION_V1,encodePreparationProjection(bprep),label);
            assertStage(actual,ArmyStrengthsPipeline.Stage.SAME_INPUT_CONDITIONAL_ORDERED_REFILL_BESIEGING_ASSAULT_V1,encodeOrdered(ordered(row,bfixed?bprep:null)),label);
            assertEquals(before,normalized,label+" immutable held frame");
        }
        assertTrue(capture.withArray("cases").size()>=18);
    }
    @Test void nativeInputRejectsBooleanFloatOverflowNullAndUnknownFieldsBeforeTypedPublication() throws Exception {
        ObjectNode capture=capture();var registry=new ArmyStrengthsFamilies.Registry();var pipeline=new ArmyStrengthsPipeline();
        ArmyStrengthsRefill.install(registry,pipeline,actualSource());registry.freeze();
        ObjectNode input=ArmyJson.object(capture.withArray("cases").get(0).get("input"));Core core=ArmyStrengthsCodec.core(input);RowContext context=new RowContext(core,new Present<>(ArmyJson.array(input.get("regiment_strengths"),ArmyStrengthsCodec::regiment)));
        var key=ArmyStrengthsFamilies.Key.SCOPED_ORDERED_REFILL_INPUTS_V1;
        for(JsonNode wrong:List.of(ArmyJson.empty().booleanNode(true),ArmyJson.empty().numberNode(1.0),ArmyJson.empty().numberNode(new java.math.BigInteger("9223372036854775808")))){
            ObjectNode bad=ArmyJson.object(input.get(key.wire())).deepCopy();ArmyJson.object(bad.withArray("persistent_regiments").get(0)).set("prepared_fraction_raw",wrong);
            assertThrows(IllegalArgumentException.class,()->registry.normalize(key,new Present<>(raw(bad)),context));
        }
        ObjectNode unknown=ArmyJson.object(input.get(key.wire())).deepCopy().put("unknown",0);
        assertThrows(IllegalArgumentException.class,()->registry.normalize(key,new Present<>(raw(unknown)),context));
        for(var arrayKey:List.of(ArmyStrengthsFamilies.Key.REGIMENT_REPLENISHMENT,ArmyStrengthsFamilies.Key.REGIMENT_REPLENISHMENT_RECORDS_V1))
            assertThrows(IllegalArgumentException.class,()->registry.normalize(arrayKey,new NullValue<>(),context));
        ObjectNode ordered=ArmyJson.object(capture.withArray("cases").get(4).get("input").get("ordered_besieging_refill_inputs_v1")).deepCopy();
        ordered.putNull("target_persistent_ids_complete");assertThrows(IllegalArgumentException.class,()->ArmyStrengthsRefill.decodeNativeOrderedBesieging(ordered));
        var normalizedLegacy=ArmyStrengthsRefill.decodeOrderedBesieging(ordered);assertNull(normalizedLegacy.targetPersistentIdsComplete());
    }
    private static Row row(ArmyStrengthsFamilies.Registry registry,ObjectNode original,ObjectNode normalized,String label){
        Core core=ArmyStrengthsCodec.core(original);Field<List<Regiment>> regiments=original.has("regiment_strengths")?new Present<>(ArmyJson.array(original.get("regiment_strengths"),ArmyStrengthsCodec::regiment)):new Missing<>();
        RowContext context=new RowContext(core,regiments);List<FamilyValue<?>> families=new ArrayList<>();
        for(var key:KEYS){if(!original.has(key.wire())&&!key.defaultNullWhenMissing())continue;Field<RawJson> input=!original.has(key.wire())?new Missing<>():original.get(key.wire()).isNull()?new NullValue<>():new Present<>(raw(original.get(key.wire())));
            var value=registry.normalize(key,input,context);JsonNode encoded=ArmyStrengthsCodec.parseValue(value.normalizedJson());
            assertEquals(normalized.get(key.wire()),encoded,label+" family "+key);families.add(value);
            if(value.value() instanceof Present<?> present) {
                if(key==ArmyStrengthsFamilies.Key.ORDERED_BESIEGING_REFILL_INPUTS_V1)assertEquals(present.value(),ArmyStrengthsRefill.decodeOrderedBesieging(encoded),label+" legacy optional flag typed roundtrip");
                else {var roundtrip=registry.normalize(key,new Present<>(value.normalizedJson()),context);assertEquals(value.value(),roundtrip.value(),label+" immutable typed roundtrip "+key);}
            }
            assertEquals(ArmyStrengthsCodec.parseValue(ArmyStrengthsRefill.publicFamily(key,value.normalizedJson())),ArmyStrengthsCodec.parseValue(value.publicV2Json()),label+" public family encoder "+key);
            if(key==ArmyStrengthsFamilies.Key.REGIMENT_REPLENISHMENT&&encoded.isArray()&&!encoded.isEmpty()){
                JsonNode wide=encoded.get(0).get("chunks").get(0).get("persistent_monthly_replenishment_fraction_raw");
                JsonNode publicWide=ArmyStrengthsCodec.parseValue(value.publicV2Json()).get(0).get("chunks").get(0).get("persistent_monthly_replenishment_fraction_raw");
                assertTrue(wide.isIntegralNumber());assertEquals(wide.bigIntegerValue().toString(),publicWide.textValue(),label+" signed64 native/public exact value");
            }
        }
        List<Supply> supply=new ArrayList<>();for(var key:SupplyKey.values())if(original.has(key.rawKey()))supply.add(new Supply(key,original.get(key.rawKey()).isNull()?new NullValue<>():new Present<>(ArmyJson.i64(original.get(key.rawKey())))));
        return new Row(core,supply,new Missing<>(),regiments,families);
    }
    private static void assertStage(ObjectNode original,ArmyStrengthsPipeline.Stage stage,ObjectNode projected,String label){
        assertEquals(original.get(stage.wire()).get(0),projected,label+" complete stage "+stage);
        ArrayNode singleton=ArmyJson.empty().arrayNode().add(projected);RawJson wire=raw(singleton);
        JsonNode publicWire=ArmyStrengthsCodec.parseValue(ArmyStrengthsRefillBesieging.publicStages(stage,wire));
        assertEquals(singleton,ArmyStrengthsCodec.parseValue(wire),label+" native wire retained");
        assertEquals(publicWire,ArmyStrengthsCodec.parseValue(raw(publicWire)),label+" public wire roundtrip");
    }
    private ObjectNode capture() throws Exception {
        String repoSetting=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repoSetting,"xar.repository.root is required; original producer must run");assertNotNull(python,"xar.python is required; original producer must run");
        Path repo=Path.of(repoSetting).toRealPath(),out=temporary.resolve("original-"+System.nanoTime()+".json"),log=temporary.resolve("python-"+System.nanoTime()+".log");
        Process process=new ProcessBuilder(python,"-B","-c",PYTHON,repo.toString(),out.toString()).directory(repo.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        if(!process.waitFor(180,TimeUnit.SECONDS)){process.destroyForcibly();fail("original REFILL service timed out; no golden replay permitted");}
        assertEquals(0,process.exitValue(),()->{try{return Files.readString(log);}catch(Exception e){return e.toString();}});
        assertTrue(Files.size(out)<16*1024*1024,"bounded original capture");return ArmyJson.object(ArmyStrengthsCodec.parseValue(new RawJson(Files.readAllBytes(out))));
    }
    private static void verifySources(ObjectNode capture) throws Exception {
        assertEquals("xar.refill.original-service-differential/v1",capture.get("schema").textValue());assertFalse(capture.get("actual_game_observed").booleanValue());
        assertFalse(capture.get("machine_id").textValue().isBlank());assertTrue(capture.withArray("sources").size()>15);
        Path repo=Path.of(System.getProperty("xar.repository.root")).toRealPath();for(JsonNode ref:capture.withArray("sources")){Path path=Path.of(ref.get("path").textValue()).toRealPath();assertTrue(path.startsWith(repo));byte[] body=Files.readAllBytes(path);assertEquals(ref.get("bytes").longValue(),body.length);assertEquals(ref.get("sha256").textValue(),sha(body));}
    }
    private static ExactRef actualSource() throws Exception {
        Path module=Path.of(ArmyStrengthsRefill.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath();
        for(Path cursor=module;cursor!=null;cursor=cursor.getParent()){
            for(String relative:List.of("src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/ArmyStrengthsRefill.java","application/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/ArmyStrengthsRefill.java")){
                Path source=cursor.resolve(relative);if(Files.isRegularFile(source)){byte[] bytes=Files.readAllBytes(source);return new ExactRef(source.toRealPath().toString(),bytes.length,sha(bytes));}
            }
        }throw new IllegalStateException("actual selected REFILL Java source must accompany compiled test");
    }
    private static String sha(byte[] bytes) throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    private static RawJson raw(JsonNode value){return new RawJson(ArmyJson.bytes(value));}
    private static final String PYTHON="""
import sys,json,hashlib
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
repo=Path(sys.argv[1]).resolve();out=Path(sys.argv[2])
sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit'),str(repo/'tools')]
import ck3_live_run_id
from test_scoped_ordered_refill_service import row as scoped_row,MemoryRoute
from test_ordered_refill_besieging_assault_service import composed_row
from test_selected_refill_monthly_assembly_service import assembly_packet
from test_explicit_preparation_scoped_core_mcp import prepared_packet
from test_fixed_chunk0_preparation_service import preparation_row
from test_fresh_ordered_b_preparation_mcp import outside_subject_packet
cases=[]
def query(name,source,refill='observed_prepared',besieging='observed_prepared'):
    frozen=deepcopy(source);service=MemoryRoute(source)
    result=service.query_army_strengths([11],expected_revision=42,ordered_refill_entry_mode=refill,ordered_besieging_entry_mode=besieging)
    assert source==frozen and service.calls==[('query-army-strengths-v1',42)]
    cases.append(dict(name=name,input=frozen,result=result,refill_mode=refill,besieging_mode=besieging))
for name,fraction in [('repeated-observed',10000),('qualified-zero',1),('nonpositive',0),('negative',-1)]:query(name,scoped_row(fraction))
query('repeated-B-target',composed_row())
partial=composed_row();partial['ordered_besieging_refill_inputs_v1'].update(refresh_membership_ready=False,status='partial',unavailable_reason='actual_refresh_membership_unknown')
query('B-unavailable-membership',partial)
query('full-monthly-crossing',assembly_packet())
partial=assembly_packet();partial['current_land_supply_rate_inputs_v1'].update(status='unavailable',current_observation_ready=False,loaded_min_loss_raw=None,unavailable_reason='loaded_min_loss_unavailable')
query('independent-missing-rate',partial)
partial=assembly_packet();partial['regiment_replenishment_records_v1']=partial['regiment_replenishment_records_v1'][:1]
query('independent-missing-subject',partial)
partial=assembly_packet();partial['monthly_loss_budget_inputs_v1']['unit_native_170_raw']=3
for key in ('current_land_supply_rate_inputs_v1','current_land_resupply_v1','current_province_supply_contributors_v1'):del partial[key]
query('rejected-updater',partial)
ready=preparation_row(50001,guard=0,magic=0,permission=False,fresh=10000)
query('fresh-subject',prepared_packet(0,ready),'fixed_chunk0_prepare')
query('fresh-missing-subject',prepared_packet(10000,None),'fixed_chunk0_prepare')
query('fresh-partial-subject',prepared_packet(10000,preparation_row(50001,guard=None,magic=None,permission=None,fresh=None)),'fixed_chunk0_prepare')
target=preparation_row(50002,guard=0,magic=0,permission=False,fresh=10000)
query('fresh-external-B',outside_subject_packet(target),besieging='fixed_chunk0_prepare')
query('fresh-missing-external-B',outside_subject_packet(None),besieging='fixed_chunk0_prepare')
query('fresh-incomplete-B-coverage',outside_subject_packet(target,target_ids_complete=False),besieging='fixed_chunk0_prepare')
for eligible in (True,False):
    packet=scoped_row();packet['next_route_replenishment_position_inputs_v1']=dict(source='native_current_next_route_replenishment_position_12004',status='available',unavailable_reason=None,unit_full_id=11,route_read_status='complete_nonempty',route_province_ids=[7],route_source_count=1,current_province_id=1,first_target_province_id=7,owner_requested_full_id=777,owner_resolved_full_id=777,holder_requested_full_id=777,holder_resolved_full_id=777,owner_used_fallback=False,holder_used_fallback=False,native_owner_holder_eligible=eligible,native_first_target_position_eligible=eligible,first_target_province_magic_raw=0x50726f76)
    query('next-first-target-'+str(eligible),packet)
packet=scoped_row();record=packet['regiment_replenishment_records_v1'][0]['records'][0]
chunk={key:record[key] for key in ('persistent_regiment_id','chunk_index','current_soldiers','maximum_soldiers','state_raw','native_can_replenish','native_chunk_can_replenish','persistent_monthly_replenishment_fraction_raw','persistent_monthly_replenishment_fraction_scale')}
chunk['persistent_monthly_replenishment_fraction_raw']=-(1<<63)
packet['regiment_replenishment']=[dict(army_regiment_id=11001,native_data_record_count=2,status='available',source='native_first_record',unavailable_reason=None,chunks=[chunk])]
query('first-record-wide-boundary',packet)
sources={}
for name,module in tuple(sys.modules.items()):
    file=getattr(module,'__file__',None)
    if file:
        path=Path(file).resolve()
        if path.is_file() and path.is_relative_to(repo) and path.suffix=='.py':
            body=path.read_bytes();sources[str(path)]=dict(path=str(path),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
receipt=dict(schema='xar.refill.original-service-differential/v1',machine_id=ck3_live_run_id.current_machine_id(),observed_at_utc=datetime.now(timezone.utc).isoformat(),actual_game_observed=False,sources=sorted(sources.values(),key=lambda ref:ref['path']),cases=cases)
out.write_text(json.dumps(receipt,ensure_ascii=False)+chr(10),encoding='utf-8')
""";
}
