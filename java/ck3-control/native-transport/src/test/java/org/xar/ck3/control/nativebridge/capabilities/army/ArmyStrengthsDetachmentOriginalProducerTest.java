package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.math.BigInteger;
import java.time.Instant;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDetachmentFixtures.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Real retained Python functions are the oracle; required configuration fails instead of skipping. No native qualification. */
final class ArmyStrengthsDetachmentOriginalProducerTest {
    private static final String BRIDGE="ck3_autonomous_player/src/xar_autoplayer/bridge/";
    private record Pin(String file,long bytes,String sha) { }
    private static final List<Pin> PINS=List.of(
        new Pin("army_current_candidate_detachment_mapper_contract.py",6958,"c46598b1d3f1cb9393c8ba3e219402c28de42e5aa4956ef15a52af97b5fe35a4"),
        new Pin("army_current_candidate_detachment_mapper_builder.py",725,"57102bc21e1db4f5121147c2d6e95331d5acb9de6f40988c25aa7d482fab99a6"),
        new Pin("army_current_candidate_detachment_mapper_projection.py",14013,"69a0184df08be5cf2c83bd26283a40e90718ce72dadfd86105bac9746ad0a64d"),
        new Pin("army_current_detachment_data_contract.py",12287,"acb8a9d0cddef6d7d2fb48b6e83fcd3930c7e6ecfa3c9ff491c81910b498b4fe"),
        new Pin("army_current_detachment_data_builder.py",1258,"69fc784ebb3dd686419ce4143ebf00f7cf3333b2edaf64c91094dbfe1242fc92"),
        new Pin("army_current_detachment_data_projection.py",31344,"50f55aa6cde3ffd60c52fbdc0fe73c853a4c31429c05e2c423cd1536a69b389a"),
        new Pin("army_current_detachment_callback_inputs_contract.py",5907,"f65d535ffd217e1a1ad2dcac578a1c760f326c48c035c8fbda153b1533051808"),
        new Pin("army_current_detachment_callback_projection.py",13889,"d1a21b11813cba6d81d20573d8b02849deff7004a3ab789541995a6edca66e51"),
        new Pin("army_current_detachment_store_inputs_contract.py",5983,"3c2aeb3b911e8a5f681469c5a4a0e09e9d62c9813a7e77501983be8b9690652d"),
        new Pin("army_current_detachment_store_projection.py",10524,"7ad888b729c8d5b5ef59b8bd4160df454000cc780db31c24d02b1f08fe0cf559"),
        new Pin("army_current_character_detachment_inputs_contract.py",5440,"31102c263e52ce1478ced575bb2a48186e1cf31a0fec7b0224a908c1c01273dc"),
        new Pin("army_current_character_detachment_projection.py",9387,"5e824895de9b790243a083a232bf2306e9f34695708ecc639c9ed8555ac371ab"),
        new Pin("army_daily_assault_active_table_contract.py",15117,"f92755b2c8cdee8ac5e9df2806014feccc84b7797aedc23a8d69194dad7d8c52"),
        new Pin("army_daily_assault_allocator_witness_contract.py",2474,"efa86f3e6232c27f9b7f3de66e4fd3a807d16837119ab1ab6abc1b29f7f2fcbf"),
        new Pin("army_daily_assault_release_header_contract.py",1586,"7112d4c65843ae351859f4edde434d6bc4de22891152137a7f5c5f066c625996"),
        new Pin("war_contract.py",241556,"b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937"));
    private static final String SCRIPT="""
        import hashlib,json,pathlib,sys
        root=pathlib.Path(sys.argv[1]);payload=json.load(sys.stdin)
        def pin():
            for p in payload['pins']:
                b=(root/p['path']).read_bytes()
                if len(b)!=p['bytes'] or hashlib.sha256(b).hexdigest()!=p['sha256']:raise RuntimeError('original producer drift: '+p['path'])
        pin();sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
        from xar_autoplayer.bridge.army_current_candidate_detachment_mapper_contract import normalize_current_candidate_detachment_mapper_inputs_v1 as nm
        from xar_autoplayer.bridge.army_current_detachment_data_contract import normalize_current_detachment_data_inputs_v1 as nd
        from xar_autoplayer.bridge.army_current_detachment_callback_inputs_contract import normalize_current_detachment_callback_inputs_v1 as nc
        from xar_autoplayer.bridge.army_current_detachment_store_inputs_contract import normalize_current_detachment_store_inputs_v1 as ns
        from xar_autoplayer.bridge.army_current_character_detachment_inputs_contract import normalize_current_character_detachment_inputs_v1 as nh
        from xar_autoplayer.bridge.army_current_candidate_detachment_mapper_projection import project_current_candidate_detachment_mapper as pm
        from xar_autoplayer.bridge.army_current_detachment_callback_projection import project_current_detachment_callback_inputs_v1 as pc
        from xar_autoplayer.bridge.army_current_detachment_store_projection import project_current_detachment_store_inputs_v1 as ps
        from xar_autoplayer.bridge.army_current_character_detachment_projection import project_current_character_detachment_inputs_v1 as ph
        from xar_autoplayer.bridge.army_current_candidate_detachment_mapper_builder import build_current_candidate_detachment_mapper_preview as bm
        from xar_autoplayer.bridge.war_contract import normalize_army_strengths
        normalizers={'MAPPER':nm,'DATA':nd,'CALLBACK':nc,'STORE':ns,'CHARACTER':nh}
        projections={'MAPPER':pm,'CALLBACK':pc,'STORE':ps,'CHARACTER':ph}
        out=[]
        for c in payload['cases']:
            try:normalized=normalizers[c['family']](c['raw'])
            except (ValueError,TypeError):out.append({'accepted':False});continue
            value={'accepted':True,'normalized':normalized}
            if c['family']!='DATA':value['projection']=projections[c['family']](normalized)
            if c['family']=='MAPPER':
                row=dict(status='available',army_id=0,native_carmy_id=-2147483647,scope_role='player',war_ids=[],regiment_count=0,current_soldiers=0,maximum_soldiers=0,ai_base_power_raw=0,ai_base_power_scale=100000,unavailable_reason=None,current_candidate_detachment_mapper_inputs_v1=normalized)
                normalized_row=normalize_army_strengths([row],expected_scope=[dict(army_id=0,scope_role='player',war_ids=[])])[0]
                value['builder']=bm(normalized_row)
            out.append(value)
        pin();print(json.dumps(out,separators=(',',':')))
        """;
    private record Sample(Family family,String name,JsonNode raw) { }
    @Test void allFiveStrictContractsAndFourOriginalProducersAgreeAcrossEveryFieldMutation() throws Exception {
        List<Sample> samples=corpus();JsonNode expected=oracle(samples);assertEquals(samples.size(),expected.size());int accepted=0,rejected=0;
        for(int index=0;index<samples.size();index++) {
            Sample s=samples.get(index);JsonNode answer=expected.get(index);String label=s.family()+":"+s.name();
            if(!answer.get("accepted").booleanValue()) { assertThrows(IllegalArgumentException.class,()->normalize(s.family(),s.raw()),label);rejected++;continue; }
            accepted++;JsonNode actual=normalize(s.family(),s.raw());assertEquals(answer.get("normalized"),canonical(actual),label+" native codec round trip");
            if(s.family()!=Family.DATA)assertEquals(answer.get("projection"),canonical(project(s.family(),s.raw())),label+" producer projection");
            if(s.family()==Family.MAPPER)assertEquals(answer.get("builder"),canonical(mapperBuilder(s.raw())),label+" actual typed Row consumer");
        }
        assertTrue(accepted>50,"partial and null source cases must execute");assertTrue(rejected>200,"full strict matrix must execute");
    }
    @Test void installedRegistryKeepsMissingNullPublicWidthsAndExactBindings() throws Exception {
        ExactRef source=source();ArmyStrengthsFamilies.Registry registry=new ArmyStrengthsFamilies.Registry();ArmyStrengthsPipeline pipeline=new ArmyStrengthsPipeline();ArmyStrengthsDetachment.install(registry,pipeline,source);
        assertEquals(5,registry.coverage().installed().size()-1);assertEquals(4,pipeline.coverage().installed().size());assertFalse(pipeline.coverage().installed().contains(ArmyStrengthsPipeline.Stage.SAME_INPUT_CURRENT_DETACHMENT_DATA_PREFIX_V1));
        registry.freeze();pipeline.freeze();var context=new ArmyStrengths.RowContext(core(),new Missing<>());
        for(Family f:Family.values()) {
            var key=key(f);var absent=registry.normalize(key,new Missing<>(),context);assertInstanceOf(Missing.class,absent.value());
            var nullable=registry.normalize(key,new NullValue<>(),context);assertInstanceOf(NullValue.class,nullable.value());
            var present=registry.normalize(key,new Present<>(new RawJson(json(f).toString().getBytes(StandardCharsets.UTF_8))),context);assertInstanceOf(Present.class,present.value());assertEquals(canonical(json(f)),ArmyStrengthsCodec.parseValue(present.normalizedJson()));
            JsonNode publicJson=ArmyStrengthsCodec.parseValue(present.publicV2Json());if(f!=Family.MAPPER)assertTrue(publicJson.get("current_date_storage_raw64").isTextual());
            if(f==Family.DATA) { assertEquals(Long.toString(Long.MIN_VALUE),publicJson.at("/incoming/0/physical_chunks/0/date_1c_raw64").textValue());assertEquals(Long.toString(Long.MAX_VALUE),publicJson.at("/incoming/0/date_inputs/0/output_date_raw64").textValue()); }
        }
        ExactRef bad=new ExactRef(source.path(),source.bytes(),"0".repeat(64));assertThrows(IllegalArgumentException.class,()->ArmyStrengthsDetachment.install(new ArmyStrengthsFamilies.Registry(),new ArmyStrengthsPipeline(),bad));
        ArmyStrengths.Row empty=new ArmyStrengths.Row(core(),List.of(),new Missing<>(),new Missing<>(),List.of());assertNull(ArmyStrengthsDetachment.monthlyDate(empty));
        assertFalse(ArmyStrengthsDetachment.projectStore(store()).requests().getFirst().updates().isEmpty());assertEquals(4294967295L,ArmyStrengthsDetachment.projectStore(store()).requests().getFirst().updates().getFirst().after());
        assertEquals(ArmyStrengthsDetachment.projectStore(store()).requests().getFirst().updates(),ArmyStrengthsDetachment.projectStore(store()).requests().get(1).updates());
    }
    @Test void callbackPartialsKeepCompletedCleanupAndCharacterResetUsesFreshReload() {
        ObjectNode callback=(ObjectNode)json(Family.CALLBACK);((ObjectNode)callback.at("/incoming/1")).putNull("data_allocator_identity");
        var projected=ArmyStrengthsDetachment.projectCallback(ArmyDetachmentInputsCodec.decodeCallback(callback));assertFalse(projected.ready());assertTrue(projected.incoming().get(1).cleanupReady());assertEquals(2,projected.incoming().get(1).cleanup().completed());assertFalse(projected.incoming().get(1).resourceReady());assertNotNull(projected.incoming().get(1).after());
        JsonNode character=ArmyStrengthsDetachment.characterJson(ArmyStrengthsDetachment.projectCharacter(character()));assertTrue(character.at("/requests/2/current_extension_branch_ready").booleanValue());assertTrue(character.at("/requests/2/source_defined_reset_descriptors/1/target_identity").isNull());assertFalse(character.at("/requests/2/source_defined_reset_descriptors/1/fresh_target_observed").booleanValue());assertEquals(0xFFFFFFFF029C77F8L,character.at("/requests/2/source_defined_reset_descriptors/1/source_defined_after_raw64").longValue());
    }
    @Test void actualRegisteredFamiliesFeedAllFourInstalledPipelineConsumers() throws Exception {
        ArmyStrengthsFamilies.Registry registry=new ArmyStrengthsFamilies.Registry();ArmyStrengthsPipeline pipeline=new ArmyStrengthsPipeline();ArmyStrengthsDetachment.install(registry,pipeline,source());registry.freeze();pipeline.freeze();
        List<ArmyStrengths.FamilyValue<?>> values=new ArrayList<>();var context=new ArmyStrengths.RowContext(core(),new Missing<>());for(Family f:Family.values())values.add(registry.normalize(key(f),new Present<>(new RawJson(json(f).toString().getBytes(StandardCharsets.UTF_8))),context));
        ArmyStrengths.Row row=new ArmyStrengths.Row(core(),List.of(),new Missing<>(),new Missing<>(),values);ArmyStrengths.Snapshot snapshot=snapshot();
        ArmyStrengths.Read read=new ArmyStrengths.Read(ArmyStrengths.Profile.ORDINARY_CORE_V1,ArmyStrengths.Status.AVAILABLE,BigInteger.ONE,"synthetic-detachment",List.of(row),new Missing<>(),new Missing<>(),receipt(snapshot));
        ArmyStrengths.Query query=new ArmyStrengths.Query(ArmyStrengths.Profile.ORDINARY_CORE_V1,ArmyStrengths.Mode.EXPLICIT_RICH,new Missing<>(),ArmyStrengths.EntryMode.OBSERVED_PREPARED,ArmyStrengths.EntryMode.OBSERVED_PREPARED);
        var results=pipeline.projectAvailable(new ArmyStrengthsPipeline.Input(snapshot,read,query,List.of(row)));assertEquals(4,results.values().size());
        for(var projection:results.values()) { JsonNode encoded=ArmyStrengthsCodec.parseValue(projection.json());assertEquals(0,encoded.at("/0/army_id").intValue());assertTrue(encoded.at("/0/projection").isObject());
            JsonNode publicJson=ArmyStrengthsCodec.parseValue(projection.publicV2Json());if(projection.stage()!=ArmyStrengthsPipeline.Stage.SAME_INPUT_CURRENT_CANDIDATE_DETACHMENT_MAPPER_V1)assertTrue(publicJson.at("/0/projection/current_date_storage_raw64").isTextual());
            if(projection.stage()==ArmyStrengthsPipeline.Stage.CURRENT_CHARACTER_DETACHMENT_SUFFIX_V1)assertEquals(Long.toString(0xFFFFFFFF029C77F8L),publicJson.at("/0/projection/requests/2/source_defined_reset_descriptors/1/source_defined_after_raw64").textValue());
            if(projection.stage()==ArmyStrengthsPipeline.Stage.SAME_INPUT_CURRENT_CANDIDATE_DETACHMENT_MAPPER_V1)assertEquals(-2147483647,encoded.at("/0/projection/subject_native_carmy_id").intValue());
        }
        assertThrows(IllegalArgumentException.class,pipeline::requireComplete);
    }
    private static JsonNode normalize(Family f,JsonNode n) { return switch(f) { case MAPPER->ArmyDetachmentInputsCodec.encodeMapper(ArmyDetachmentInputsCodec.decodeMapper(n));case CALLBACK->ArmyDetachmentInputsCodec.encodeCallback(ArmyDetachmentInputsCodec.decodeCallback(n));case STORE->ArmyDetachmentInputsCodec.encodeStore(ArmyDetachmentInputsCodec.decodeStore(n));case CHARACTER->ArmyDetachmentInputsCodec.encodeCharacter(ArmyDetachmentInputsCodec.decodeCharacter(n));case DATA->ArmyStrengthsDetachment.encodeData(ArmyStrengthsDetachment.decodeData(n)); }; }
    private static JsonNode project(Family f,JsonNode n) { return switch(f) { case MAPPER->ArmyStrengthsDetachment.mapperJson(ArmyStrengthsDetachment.projectMapper(ArmyDetachmentInputsCodec.decodeMapper(n)));case CALLBACK->ArmyStrengthsDetachment.callbackJson(ArmyStrengthsDetachment.projectCallback(ArmyDetachmentInputsCodec.decodeCallback(n)));case STORE->ArmyStrengthsDetachment.storeJson(ArmyStrengthsDetachment.projectStore(ArmyDetachmentInputsCodec.decodeStore(n)));case CHARACTER->ArmyStrengthsDetachment.characterJson(ArmyStrengthsDetachment.projectCharacter(ArmyDetachmentInputsCodec.decodeCharacter(n)));case DATA->throw new IllegalArgumentException("DATA has its separate sole kernel oracle"); }; }
    private static ArmyStrengths.Core core() { return new ArmyStrengths.Core(ArmyStrengths.Status.AVAILABLE,new PublicUnitId(0),new Present<>(new FullId((int)2147483649L)),ArmyStrengths.Role.PLAYER,List.of(),new Present<>(0),new Present<>(0),new Present<>(0),new Present<>(0L),new NullValue<>()); }
    private static ArmyStrengths.Snapshot snapshot() {
        Instant now=Instant.now();ExactRef ref=new ExactRef("declared-detachment-fixture",1,"a".repeat(64));var source=new org.xar.ck3.control.g2.common.G2Source("synthetic-fixture",now.toString(),"synthetic-only",ref);
        var frame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.ZERO,BigInteger.valueOf(11),BigInteger.valueOf(53238336)),"native:11",BigInteger.valueOf(7),"fixture-episode");
        var context=new Context(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(),new org.xar.ck3.control.contracts.GameGeneration(42,new org.xar.ck3.control.contracts.PythonOnlyUInt64(BigInteger.ONE)),frame,1),source,"fixture-session",now.plusSeconds(60));
        ObjectNode raw=JsonNodeFactory.instance.objectNode();raw.put("snapshot_id","native:11");raw.put("revision",7);raw.put("native_revision",11);raw.put("date_raw",53238336);raw.put("episode_run_id","fixture-episode");raw.put("paused",true);raw.put("map_ready",true);raw.putObject("played_character").put("character_id",0).put("alive",true);raw.putObject("diagnostics").put("connection_generation",5);raw.putArray("player_armies").addObject().put("army_id",0);raw.putArray("active_wars");return ArmyStrengthsCodec.snapshot(context,new RawJson(raw.toString().getBytes(StandardCharsets.UTF_8)));
    }
    private static org.xar.ck3.control.application.action.PlanningReadReceipt receipt(ArmyStrengths.Snapshot snapshot) throws Exception {
        var c=snapshot.context();var operation=new org.xar.ck3.control.application.action.OperationKey(ArmyStrengths.STEP);var request=new org.xar.ck3.control.application.action.PlanningReadRequest(c.before(),c.source(),c.sessionId(),operation,new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),c.deadline());
        var guard=new org.xar.ck3.control.application.action.PlanningReadGuard(new org.xar.ck3.control.application.action.GuardEvidence(c.before(),c.source(),c.sessionId(),snapshot.binding().connectionGeneration(),operation,c.source().sourceRef(),c.source().sourceRef(),"synthetic-only",Instant.now(),c.deadline()),true,true,true,"b".repeat(64));
        byte[] body="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"synthetic-detachment\",\"ok\":true,\"result\":{}}".getBytes(StandardCharsets.UTF_8);
        return new org.xar.ck3.control.application.action.PlanningReadReceipt(request,"synthetic-detachment","synthetic-detachment",guard,guard,new org.xar.ck3.control.application.action.NativeActionPort.AckReceived("synthetic-detachment",true,Optional.of(new RawJson("{}".getBytes(StandardCharsets.UTF_8))),new RawJson(body),org.xar.ck3.control.nativebridge.NativeWire.packet(body)));
    }
    private static JsonNode mapperBuilder(JsonNode input) {
        var decoded=ArmyDetachmentInputsCodec.decodeMapper(input);Field<ArmyDetachmentInputsCodec.MapperInputs> field=decoded==null?new NullValue<>():new Present<>(decoded);
        var value=new ArmyStrengths.FamilyValue<>(key(Family.MAPPER),ArmyDetachmentInputsCodec.MapperInputs.class,field,new RawJson(input.toString().getBytes(StandardCharsets.UTF_8)));
        var row=new ArmyStrengths.Row(core(),List.of(),new Missing<>(),new Missing<>(),List.of(value));var actual=ArmyStrengthsDetachment.buildMapper(row);ObjectNode result=(ObjectNode)ArmyStrengthsDetachment.mapperJson(actual.projection());result.put("subject_army_id",actual.army().value());if(actual.nativeArmy() instanceof Present<FullId> p)result.put("subject_native_carmy_id",p.value().value());else result.putNull("subject_native_carmy_id");return result;
    }
    private static ArmyStrengthsFamilies.Key key(Family f) { return switch(f) { case MAPPER->ArmyStrengthsFamilies.Key.CURRENT_CANDIDATE_DETACHMENT_MAPPER_INPUTS_V1;case CALLBACK->ArmyStrengthsFamilies.Key.CURRENT_DETACHMENT_CALLBACK_INPUTS_V1;case STORE->ArmyStrengthsFamilies.Key.CURRENT_DETACHMENT_STORE_INPUTS_V1;case CHARACTER->ArmyStrengthsFamilies.Key.CURRENT_CHARACTER_DETACHMENT_INPUTS_V1;case DATA->ArmyStrengthsFamilies.Key.CURRENT_DETACHMENT_DATA_INPUTS_V1; }; }
    private static List<Sample> corpus() {
        List<Sample> samples=new ArrayList<>();for(Family f:Family.values()) { JsonNode base=json(f);samples.add(new Sample(f,"complete",base));samples.add(new Sample(f,"null-family",JsonNodeFactory.instance.nullNode()));List<List<String>> paths=new ArrayList<>();collect(base,List.of(),paths);
            for(List<String> path:paths) { String name=String.join("/",path);for(JsonNode replacement:List.of(JsonNodeFactory.instance.booleanNode(true),JsonNodeFactory.instance.numberNode(0.5),JsonNodeFactory.instance.nullNode())) { JsonNode copy=base.deepCopy();set(copy,path,replacement);samples.add(new Sample(f,name+"="+replacement,copy)); }
                JsonNode parent=get(base,path.subList(0,path.size()-1));if(parent.isObject()) { JsonNode copy=base.deepCopy();((ObjectNode)get(copy,path.subList(0,path.size()-1))).remove(path.getLast());samples.add(new Sample(f,name+" missing",copy)); }
            }
            List<List<String>> objects=new ArrayList<>();collectObjects(base,List.of(),objects);for(List<String> path:objects) { JsonNode copy=base.deepCopy();((ObjectNode)get(copy,path)).put("unexpected_contract_field",1);samples.add(new Sample(f,String.join("/",path)+" extra",copy)); }
        }
        ObjectNode noCall=(ObjectNode)json(Family.MAPPER);noCall.put("selection_branch","not_called");samples.add(new Sample(Family.MAPPER,"not-called-unused-operands",noCall));
        for(int count:List.of(-3,0)) { ObjectNode mapper=(ObjectNode)json(Family.MAPPER);mapper.put("roster_count_raw_i32",count);samples.add(new Sample(Family.MAPPER,"nonpositive-roster-"+count,mapper));ObjectNode callback=(ObjectNode)json(Family.CALLBACK);((ObjectNode)callback.at("/incoming/1")).put("data_count_2c_raw_i32",count);samples.add(new Sample(Family.CALLBACK,"nonpositive-cleanup-"+count,callback)); }
        ObjectNode blocked=(ObjectNode)json(Family.STORE);blocked.put("store_48_raw_u8",255);samples.add(new Sample(Family.STORE,"nonzero-store-short-circuit",blocked));
        for(String identity:List.of("native:0","native:0000","native:18446744073709551615","native:18446744073709551616")) { ObjectNode callback=(ObjectNode)json(Family.CALLBACK);callback.put("known_core_identity",identity);samples.add(new Sample(Family.CALLBACK,"opaque-identity-"+identity,callback)); }
        return List.copyOf(samples);
    }
    private static void collect(JsonNode node,List<String> path,List<List<String>> out) { if(node.isObject())node.properties().iterator().forEachRemaining(e->{List<String> next=append(path,e.getKey());out.add(next);collect(e.getValue(),next,out);});else if(node.isArray())for(int i=0;i<node.size();i++) { List<String> next=append(path,Integer.toString(i));out.add(next);collect(node.get(i),next,out); } }
    private static void collectObjects(JsonNode node,List<String> path,List<List<String>> out) { if(node.isObject()) { out.add(path);node.properties().iterator().forEachRemaining(e->collectObjects(e.getValue(),append(path,e.getKey()),out)); }else if(node.isArray())for(int i=0;i<node.size();i++)collectObjects(node.get(i),append(path,Integer.toString(i)),out); }
    private static List<String> append(List<String> path,String key) { List<String> result=new ArrayList<>(path);result.add(key);return List.copyOf(result); }
    private static JsonNode get(JsonNode root,List<String> path) { JsonNode value=root;for(String key:path)value=value.isArray()?value.get(Integer.parseInt(key)):value.get(key);return value; }
    private static void set(JsonNode root,List<String> path,JsonNode value) { JsonNode parent=get(root,path.subList(0,path.size()-1));String key=path.getLast();if(parent instanceof ObjectNode o)o.set(key,value);else ((ArrayNode)parent).set(Integer.parseInt(key),value); }
    private static JsonNode canonical(JsonNode value) { return StrictJson.parse(value.toString().getBytes(StandardCharsets.UTF_8),64*1024*1024); }
    private static String required(String key) { String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("mandatory actual original producer configuration missing: "+key);return value; }
    private static ExactRef source() throws Exception { Path path=Path.of(required("xar.detachment.java.source"));byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
    private static JsonNode oracle(List<Sample> samples) throws Exception {
        Path root=Path.of(required("xar.repository.root"));ObjectNode payload=JsonNodeFactory.instance.objectNode();ArrayNode pins=payload.putArray("pins");for(Pin p:PINS) { byte[] bytes=Files.readAllBytes(root.resolve(BRIDGE+p.file()));assertEquals(p.bytes(),bytes.length,p.file());assertEquals(p.sha(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),p.file());ObjectNode n=pins.addObject();n.put("path",BRIDGE+p.file());n.put("bytes",p.bytes());n.put("sha256",p.sha()); }
        ArrayNode cases=payload.putArray("cases");for(Sample s:samples) { ObjectNode n=cases.addObject();n.put("family",s.family().name());n.set("raw",s.raw()); }
        Process process=new ProcessBuilder(required("xar.python"),"-c",SCRIPT,root.toString()).start();try(var threads=Executors.newVirtualThreadPerTaskExecutor()) { var stdout=threads.submit(()->process.getInputStream().readAllBytes());var stderr=threads.submit(()->process.getErrorStream().readAllBytes());try(var stdin=process.getOutputStream()) { stdin.write(payload.toString().getBytes(StandardCharsets.UTF_8)); }
            if(!process.waitFor(60,TimeUnit.SECONDS)) { process.destroyForcibly();fail("original producer oracle timed out"); }byte[] errors=stderr.get(10,TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(errors,StandardCharsets.UTF_8));return StrictJson.parse(stdout.get(10,TimeUnit.SECONDS),64*1024*1024);
        }finally { if(process.isAlive())process.destroyForcibly(); }
    }
}
