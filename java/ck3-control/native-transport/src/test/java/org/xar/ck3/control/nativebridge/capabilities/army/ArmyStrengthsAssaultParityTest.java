package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key;

/** Fresh unchanged Python service/fixture producers -> every current Java consumer, not fixture expected-value copies. */
class ArmyStrengthsAssaultParityTest {
    @TempDir Path temporary;
    private record Pin(String path,String sha256) { }
    private static final List<Pin> PINS=List.of(
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/service.py","a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_active_table_contract.py","f92755b2c8cdee8ac5e9df2806014feccc84b7797aedc23a8d69194dad7d8c52"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_active_table_projection.py","66cae307ffbb84b205163212ec34e65842369d12bbe84dc1175f359cb3444a5a"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_allocator_witness_contract.py","efa86f3e6232c27f9b7f3de66e4fd3a807d16837119ab1ab6abc1b29f7f2fcbf"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_release_header_contract.py","7112d4c65843ae351859f4edde434d6bc4de22891152137a7f5c5f066c625996"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_loss_inputs_contract.py","7b78d406bf0e5694665b026f5b510943a929391b2a3e1dea0a80d488a49964e6"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_loss_projection.py","8e928a06b6269e619589af76169a52b822821d7fa04458ecaf84860b186d42bf"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_queue_append_projection.py","30ce199f1cafc7d306f5542e69155042958c7411921620c4f4e4fcbd7691dab1"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_normal_return_release_projection.py","1eeb2ed9b05fc3aa7f7225d5cd12313f526e5a36c08ef3d40282e8be52c6a94e"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_assault_removal_reference_contract.py","def76225ba906f94a0ff00536642aeaa5643e8cf1ecc12b2c0e9c05222115872"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_assault_first_removal_projection.py","5f779632e02fc17938f19252f1fd0f9adfae270888780d2ad1a736b380663aa1"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_placement_inputs_projection.py","e49e2354dcb16d094f76ec06c30639152492eb073de364410e7218ff7fe9fdc9"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/assault_eligible_contributors_12004.py","aa1d295e56661f12867551000865f6bf35bd9b94da71c64627aade4c11f5fc1b"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_post_refill_besieging_current_projection.py","a9a352b0edeb118159cbc02064353d274054a389bf6a3e8d40c4a8afee14be5d"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_chunk_loss_writeback_projection.py","1332d13a9f4fb801db31b8458f79cd920cfa8761bbf5f4d51cdccde856fa19db"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_regiment_refresh_projection.py","ad9d96869a2a5ce910855d9e34500c6925e79753457ca4b7bdf3087cca31ef62"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_full_land_supply_rate_projection.py","149d98890289845182e76303e86173233ed1cc6b1761c9b476be1ca2855cc702"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/army_manager_cleanup_projection.py","a3fc0f4f0afe48a39a344ff2a9e6685aecc138c751b12c00bb33c3ade9791732"),
        new Pin("ck3_autonomous_player/tests/unit/test_current_daily_assault_loss_service.py","278184384d3a016268f365fd8ae56841924912fb6c30782ef37e12bfae29a6e4"),
        new Pin("ck3_autonomous_player/tests/unit/test_current_daily_assault_queue_append_service.py","c3aba4c1ec1923581ddf48410a84f5a56ade21d7013f8e291f6603ff13e02677"),
        new Pin("ck3_autonomous_player/tests/unit/test_current_daily_assault_normal_return_release_service.py","ae77e19527e9c92ed892d380715585d87b83f0d19c642b4283c0f42a0170e671"),
        new Pin("ck3_autonomous_player/tests/unit/test_current_assault_first_removal_context_service.py","2daab81484c9b5af60e9e6ec973f3f0eca72d4d0bf86858e08b80ace41e2d3ff"),
        new Pin("ck3_autonomous_player/tests/unit/test_current_daily_assault_table_service.py","853dda72360683f7105a6eccd1542cc86fa81694259a6ef6c61f4f412cdbd3ff"),
        new Pin("ck3_autonomous_player/tests/unit/test_post_refill_besieging_current_service.py","9e4cbf5b131c26a394481084b463f33c3f3001be57ec3f8d0a8f482c1b9024b1"),
        new Pin("ck3_autonomous_player/tests/unit/test_post_refill_land_rate_service_join.py","3cda3e3e59015b22ad1391cd3c65681d84b797b384e6466893c43d6bfbdd6910"),
        new Pin("ck3_autonomous_player/tests/unit/test_ordered_refill_besieging_assault_service.py","5ae704df84bf2f38a8efb997c7f09988b307d06ec509944e2d45bd5c7a8a558b")
    );
    private static final String PROGRAM="""
import copy, importlib, inspect, json, os, pathlib, sys, unittest
root=pathlib.Path(sys.argv[1]);sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
for key in list(os.environ):
    if key.startswith('XAR_') and key.endswith('FIRST_OUTPUT'): os.environ.pop(key)
names=['test_current_daily_assault_loss_service','test_current_daily_assault_queue_append_service','test_current_daily_assault_normal_return_release_service','test_current_assault_first_removal_context_service']
modules=[importlib.import_module(name) for name in names]
captured=[]
def capture(base):
    def invoke(source,*args,**kwargs):
        result,driver=base(source,*args,**kwargs)
        captured.append({'kind':'service','army':copy.deepcopy(result['army_strengths'][0]),'expected':copy.deepcopy(result)})
        return result,driver
    return invoke
for module in modules: module.query_with_fake_driver=capture(module.query_with_fake_driver)
for module in modules:
    for name,cls in inspect.getmembers(module,inspect.isclass):
        if cls.__module__==module.__name__ and issubclass(cls,unittest.TestCase):
            for method in unittest.defaultTestLoader.getTestCaseNames(cls): getattr(cls(method),method)()
assert len(captured)>=25,('whole service producer corpus unexpectedly shrank',len(captured))
for value in captured: print(json.dumps(value,separators=(',',':')))
from test_ordered_refill_besieging_assault_service import composed_row
from test_current_daily_assault_table_service import _state
from xar_autoplayer.bridge.assault_eligible_contributors_12004 import project_assault_eligible_contributors_12004
from xar_autoplayer.bridge.army_daily_assault_loss_inputs_contract import normalize_current_daily_assault_loss_inputs_v1
base=composed_row();family=base['current_province_besieging_contributors_v1'];scope=base['ordered_besieging_refill_inputs_v1']
family['native_province_unit_count']=len(family['occurrences'])
for ordinal,occurrence in enumerate(family['occurrences']):occurrence['stored_index']=ordinal
group={**_state(True),'native_index':0,'physical_slot_i64':4,'native_current_expected_loss':family['native_assault_expected_loss'],'province_magic_raw_u32':0x50726f76,'besieging_inputs_v1':family,'army_counts':[],'ordered_besieging_refill_inputs_v1':scope}
def normalized(g):
    return normalize_current_daily_assault_loss_inputs_v1({**_state(True),'schema_version':1,'source':'native_current_daily_assault_loss_inputs','stage':'observed_current_daily_assault_table','groups':[g],'target_regiments':[]})['groups'][0]
for index in range(18):
    g=copy.deepcopy(group);overlay=[];selection=copy.deepcopy(scope)
    if index==0:overlay=None
    elif index==1:selection=None
    elif index==2:g['province_magic_raw_u32']=0
    elif index==3:g['besieging_inputs_v1']['assault_context']['has_active_siege']=False
    elif index==4:g['besieging_inputs_v1']['assault_context']['breach_level_raw']=0
    elif index in (5,6):g['besieging_inputs_v1']['assault_context']['casualty_percentage_raw']=-(1<<63) if index==5 else (1<<63)-1
    elif index==7:selection['refresh_membership_ready']=False
    else:
        record=family['occurrences'][0]['regiments'][0]['replenishment_records_v1']['records'][0]
        p={'persistent_regiment_id':record['persistent_regiment_id'],'chunk_index':record['chunk_index'],'status':'available','current_soldiers':0 if index%2 else 33,'maximum_soldiers':400,'copied_context_provenance':{'unchanged_native_context':True}}
        if index%3==0:p['state_raw']=3
        if index==9:p['status']='unavailable'
        overlay=[p]
        if index==10:overlay.append(copy.deepcopy(p))
    g=normalized(g);before=copy.deepcopy((g,overlay,selection));expected=project_assault_eligible_contributors_12004(g,derived_physical_chunks=overlay,refresh_selection=selection)
    assert (g,overlay,selection)==before
    same_query_expected=project_assault_eligible_contributors_12004(g,derived_physical_chunks=[],refresh_selection=g.get('ordered_besieging_refill_inputs_v1'))
    print(json.dumps({'kind':'eligible','group':g,'physical':overlay,'refresh':selection,'expected':expected,'same_query_expected':same_query_expected},separators=(',',':')))
from xar_autoplayer.bridge.army_daily_assault_active_table_contract import normalize_current_daily_assault_table_v1
from xar_autoplayer.bridge.army_current_assault_removal_reference_contract import normalize_current_assault_removal_reference_inputs_v1
valid=captured[-1]['army'];normalizers={'table':normalize_current_daily_assault_table_v1,'loss':normalize_current_daily_assault_loss_inputs_v1,'removal':normalize_current_assault_removal_reference_inputs_v1}
keys={'table':'current_daily_assault_table_v1','loss':'current_daily_assault_loss_inputs_v1','removal':'current_assault_removal_reference_inputs_v1'}
for kind,fn in normalizers.items():
    source=next(item['army'][keys[kind]] for item in reversed(captured) if isinstance(item['army'].get(keys[kind]),dict))
    variants=[None,copy.deepcopy(source)]
    for key,value in [('schema_version',True),('schema_version',1.0),('schema_version','1'),('invented_native_field',0),('status','unknown'),('ready',1)]:
        bad=copy.deepcopy(source);bad[key]=value;variants.append(bad)
    for key in source:
        bad=copy.deepcopy(source);del bad[key];variants.append(bad)
    for value in variants:
        accepted=True
        try: normalized_value=fn(value)
        except (ValueError,TypeError,KeyError):accepted=False;normalized_value=None
        print(json.dumps({'kind':'contract','family':kind,'value':value,'accepted':accepted,'normalized':normalized_value},separators=(',',':')))
""";
    @Test void unchangedOriginalServiceToAllTypedConsumersAndWrongContracts() throws Exception {
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");assertNotNull(python,"-Dxar.python is required; missing original producer is RED");assertNotNull(repository,"-Dxar.repository.root is required");Path root=Path.of(repository).toAbsolutePath();
        assertFalse(PINS.isEmpty(),"original source pins must be installed");for(Pin pin:PINS)assertEquals(pin.sha256(),sha(Files.readAllBytes(root.resolve(pin.path()))),"original source changed: "+pin.path());
        Path witness=temporary.resolve("selected-java-source.fixture");byte[] source="controlled source identity for registry wiring; not runtime qualification".getBytes(StandardCharsets.UTF_8);Files.write(witness,source);ExactRef reference=new ExactRef(witness.toString(),source.length,sha(source));var registry=new ArmyStrengthsFamilies.Registry();var pipeline=new ArmyStrengthsPipeline();ArmyStrengthsAssault.install(registry,pipeline,reference);registry.freeze();pipeline.freeze();assertEquals(8,pipeline.coverage().installed().size());
        ArmyStrengths.Core core=new ArmyStrengths.Core(ArmyStrengths.Status.AVAILABLE,new PublicUnitId(0),new Present<>(new FullId(Integer.MIN_VALUE)),ArmyStrengths.Role.PLAYER,List.of(),new Present<>(0),new Present<>(0),new Present<>(0),new Present<>(0L),new NullValue<>());var context=new ArmyStrengths.RowContext(core,new Missing<>());
        ProcessBuilder builder=new ProcessBuilder(python,"-B","-X","utf8","-c",PROGRAM,root.toString());builder.directory(root.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src")+File.pathSeparator+root.resolve("ck3_autonomous_player/tests/unit"));builder.redirectError(ProcessBuilder.Redirect.INHERIT);Process child=builder.start();int[] counts={0,0,0};
        try {assertTimeoutPreemptively(Duration.ofMinutes(4),()->{try(BufferedReader reader=new BufferedReader(new InputStreamReader(child.getInputStream(),StandardCharsets.UTF_8))){String line;while((line=reader.readLine())!=null){ObjectNode example=ArmyJson.parse(line.getBytes(StandardCharsets.UTF_8));switch(example.get("kind").textValue()){
            case "service"->{counts[0]++;ObjectNode army=ArmyJson.object(example.get("army"));ObjectNode before=army.deepCopy();var table=ArmyStrengthsAssaultCodec.decodeTable(army.get("current_daily_assault_table_v1"));var lossInputs=ArmyStrengthsAssaultCodec.decodeLoss(army.get("current_daily_assault_loss_inputs_v1"));int id=ArmyJson.i32(army.get("army_id"));var loss=ArmyStrengthsAssaultLoss.project(id,table,lossInputs);List<Integer> pending=ArmyStrengthsAssaultBoundary.pending(army);var queue=ArmyStrengthsAssaultCurrent.queue(id,pending,loss);var release=ArmyStrengthsAssaultCurrent.release(id,table,queue);var removal=ArmyStrengthsAssaultRemoval.project(id,ArmyStrengthsAssaultRemoval.decode(army.get("current_assault_removal_reference_inputs_v1")),pending,release);JsonNode expected=example.get("expected");
                same(expected.get("same_input_current_daily_assault_loss_v1").get(0).get("projection"),ArmyStrengthsAssaultLoss.encode(loss));same(expected.get("same_input_current_daily_assault_queue_append_v1").get(0).get("projection"),ArmyStrengthsAssaultCurrent.encodeQueue(queue));same(expected.get("same_input_current_daily_assault_normal_return_release_v1").get(0).get("projection"),ArmyStrengthsAssaultCurrent.encodeRelease(release));same(expected.get("same_input_current_assault_first_removal_v1").get(0).get("projection"),ArmyStrengthsAssaultRemoval.encode(removal));same(expected.get("current_daily_assault_group_inputs_v1").get(0),ArmyStrengthsAssaultCurrent.encodeGroups(ArmyStrengthsAssaultCurrent.groups(id,table)));same(expected.get("current_daily_assault_placement_inputs_v1").get(0),ArmyStrengthsAssaultCurrent.encodePlacement(ArmyStrengthsAssaultCurrent.placement(table)));
                same(ArmyStrengthsAssaultCurrent.encodeQueue(queue),ArmyStrengthsAssault.queue(army,ArmyStrengthsAssaultLoss.encode(loss)));same(ArmyStrengthsAssaultCurrent.encodeRelease(release),ArmyStrengthsAssault.normalRelease(army,ArmyStrengthsAssaultCurrent.encodeQueue(queue)));
                for(Key key:List.of(Key.CURRENT_DAILY_ASSAULT_TABLE_V1,Key.CURRENT_DAILY_ASSAULT_LOSS_INPUTS_V1,Key.CURRENT_ASSAULT_REMOVAL_REFERENCE_INPUTS_V1,Key.CURRENT_DAILY_ASSAULT_ROSTER_ADMISSION_V1)){var input=ArmyJson.field(army,key.wire(),n->new RawJson(ArmyJson.bytes(n)));var normalized=registry.normalize(key,input,context);if(army.has(key.wire()))same(army.get(key.wire()),ArmyStrengthsCodec.parseValue(normalized.normalizedJson()));}
                same(before,army);
            }
            case "eligible"->{counts[1]++;ObjectNode before=example.deepCopy();var result=ArmyStrengthsAssault.eligible(example.get("group"),example.get("physical"),example.get("refresh"));same(example.get("expected"),result.toJson());ObjectNode copy=result.toJson();copy.removeAll();same(example.get("expected"),result.toJson());same(before,example);
                ObjectNode family=ArmyJson.empty().put("status","available").put("ready",true).putNull("unavailable_reason").put("schema_version",1).put("source","native_current_daily_assault_loss_inputs").put("stage","observed_current_daily_assault_table");family.putArray("groups").add(example.get("group"));family.putArray("target_regiments");var normalized=registry.normalize(Key.CURRENT_DAILY_ASSAULT_LOSS_INPUTS_V1,new Present<>(new RawJson(ArmyJson.bytes(family))),context);var selected=new ArmyStrengths.Row(core,List.of(),new Missing<>(),new Missing<>(),List.of(normalized));ObjectNode packet=ArmyJson.empty();packet.putArray("army_strengths").addObject().put("army_id",0).set("current_daily_assault_loss_inputs_v1",family);var input=sourceInput(packet,selected);var projections=pipeline.projectAvailable(input);var actual=projections.required(ArmyStrengthsPipeline.Stage.SAME_QUERY_CONDITIONAL_ASSAULT_GROUP_CONTRIBUTORS_12004,ArmyStrengthsAssaultInstaller.Eligibles.class);assertTrue(actual.values().getFirst().exact4());same(example.get("same_query_expected"),ArmyStrengthsAssaultEligible.encode(actual.values().getFirst().groups().getFirst()));
                if(counts[1]==1){ObjectNode invalidPacket=packet.deepCopy();invalidPacket.putObject("source").putNull("game_version").put("executable_sha256",ArmyStrengthsSourceTest.SHA);assertUnavailableSource(pipeline,sourceInput(invalidPacket,selected));invalidPacket=packet.deepCopy();invalidPacket.putObject("source").put("game_version",ArmyStrengthsSourceTest.VERSION).put("executable_sha256","a".repeat(64));assertUnavailableSource(pipeline,sourceInput(invalidPacket,selected));assertUnavailableSource(pipeline,new ArmyStrengthsPipeline.Input(input.snapshot(),input.original(),input.query(),input.selected()));}
            }
            case "contract"->{counts[2]++;JsonNode value=example.get("value");java.util.function.Supplier<ObjectNode> normalize=switch(example.get("family").textValue()){case "table"->()->ArmyStrengthsAssault.normalizeTable(value);case "loss"->()->ArmyStrengthsAssaultCodec.encodeLoss(ArmyStrengthsAssaultCodec.decodeLoss(value));case "removal"->()->ArmyStrengthsAssaultRemoval.encodeInputs(ArmyStrengthsAssaultRemoval.decode(value));default->throw new IllegalArgumentException("unknown original family");};if(example.get("accepted").booleanValue())same(example.get("normalized"),normalize.get());else assertThrows(IllegalArgumentException.class,normalize::get);}
            default->fail("unknown original producer corpus");
        }}}assertTrue(child.waitFor(10,TimeUnit.SECONDS),"original producer did not terminate");assertEquals(0,child.exitValue(),"unchanged original producer failed");});}finally{if(child.isAlive())child.destroyForcibly();}
        assertTrue(counts[0]>=25,"whole service corpus shrank");assertEquals(18,counts[1]);assertTrue(counts[2]>=50);
    }
    @Test void publicInt64IsExactAndMissingNullExtensionsRoundTrip(){
        ObjectNode loss=ArmyJson.empty().put("status","unavailable").put("ready",false).put("unavailable_reason","captured_unavailable").put("schema_version",1).put("source","native_current_daily_assault_loss_inputs").put("stage","observed_current_daily_assault_table");loss.putArray("groups");loss.putArray("target_regiments");same(loss,ArmyStrengthsAssaultCodec.encodeLoss(ArmyStrengthsAssaultCodec.decodeLoss(loss)));
        ObjectNode nativeJson=ArmyJson.empty();nativeJson.putArray("groups").addObject().put("physical_slot_i64",Long.MAX_VALUE);RawJson output=ArmyStrengthsAssaultInstaller.publicFamily(Key.CURRENT_DAILY_ASSAULT_LOSS_INPUTS_V1,new RawJson(ArmyJson.bytes(nativeJson)));assertEquals(Long.toString(Long.MAX_VALUE),ArmyStrengthsCodec.parseValue(output).get("groups").get(0).get("physical_slot_i64").textValue());assertTrue(nativeJson.get("groups").get(0).get("physical_slot_i64").isIntegralNumber());
        ObjectNode projection=nativeJson.deepCopy();var missing=projection.putArray("missing_inputs");missing.add("source_operand_unavailable");missing.addObject().put("physical_slot_i64",Long.MIN_VALUE);RawJson publicProjection=ArmyStrengthsPublicNumbers.encode(new RawJson(ArmyJson.bytes(projection)),ArmyStrengthsAssault.projectionPublicNumberRules(ArmyStrengthsPipeline.Stage.CURRENT_DAILY_ASSAULT_GROUP_INPUTS_V1,""));JsonNode decoded=ArmyStrengthsCodec.parseValue(publicProjection);assertEquals("source_operand_unavailable",decoded.get("missing_inputs").get(0).textValue());assertEquals(Long.toString(Long.MIN_VALUE),decoded.get("missing_inputs").get(1).get("physical_slot_i64").textValue());
    }
    private static void same(JsonNode expected,JsonNode actual){JsonNode left=expected==null||expected.isNull()?null:ArmyStrengthsCodec.parseValue(new RawJson(ArmyJson.bytes(expected)));JsonNode right=actual==null||actual.isNull()?null:ArmyStrengthsCodec.parseValue(new RawJson(ArmyJson.bytes(actual)));assertEquals(left,right);}
    private static ArmyStrengthsPipeline.Input sourceInput(ObjectNode packet,ArmyStrengths.Row selected) throws Exception {var actual=ArmyStrengthsSourceTest.input(packet,ArmyStrengthsSourceTest.projectedHello());var read=actual.original();var selectedRead=new ArmyStrengths.Read(read.profile(),read.status(),read.sequence(),read.backendId(),List.of(selected),read.timing(),read.publishedScopeStatus(),read.original());return new ArmyStrengthsPipeline.Input(actual.snapshot(),selectedRead,actual.query(),List.of(selected),actual.originalHello());}
    private static void assertUnavailableSource(ArmyStrengthsPipeline pipeline,ArmyStrengthsPipeline.Input input){var output=pipeline.projectAvailable(input).required(ArmyStrengthsPipeline.Stage.SAME_QUERY_CONDITIONAL_ASSAULT_GROUP_CONTRIBUTORS_12004,ArmyStrengthsAssaultInstaller.Eligibles.class).values().getFirst();assertFalse(output.exact4());assertTrue(output.groups().isEmpty());}
    private static String sha(byte[] bytes) throws Exception {return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
}
