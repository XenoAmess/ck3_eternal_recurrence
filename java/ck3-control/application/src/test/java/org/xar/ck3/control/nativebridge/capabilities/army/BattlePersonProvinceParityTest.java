package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
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
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.NativePropertyFold2303120.Block;

/** Original producer -> unique facade -> strict codec -> typed calculation -> roundtrip. */
final class BattlePersonProvinceParityTest {
    @TempDir static Path scratch;
    private static JsonNode oracle;
    private static int sequence;
    private record Pin(String relative, String sha256) { }
    private static final List<Pin> PINS = List.of(
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_following_2921350_contract.py", "2f17c42abf2824155a98375c8d6e4735c08567fa00f747052a091c8d6bb0ec8b"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_person_following_2921350_12003.py", "13f9b60fee055b70f22d80486e9fab26e91c0721ae14eff2835648ad4d489464"),
        new Pin("ck3_autonomous_player/tests/unit/_following_2921350_fixture.py", "193adc04de1e91c718f496b73d2152a5ab3d64b33d1baad6f8fb9459f5495e19"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_trait_materialized_prefix_12003.py", "ff270cfb75ce3f10f4f26b77bb99d9a7bdfeaa4e390f3e693cdf37d505351e23"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_trait_numeric_inputs_12003.py", "ae974dd51678fec9f05ea40c4991de30678ca356d30df298b97b88bb92a1810a"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_after_gated_tail_contract.py", "e5e44c2d9bab4904967327a66e8e8011c33d4c81ceca442204563edfc4e59c42"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_context_source_inputs_contract.py", "aef31456253ca7fd5160dfd73d244bc929c4284e621ca3a638eef38515a9d245"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_context_preparation_branch_291e210_12003.py", "70de9b44bcbc9f82d26d787abf408deef99cbf1d84e4a60645b56d61879e9cb6")
    );
    private static final String PROGRAM = """
        import dataclasses,json,pathlib,sys
        root=pathlib.Path(sys.argv[1]).resolve(strict=True)
        sys.path[:0]=[str(root/'ck3_autonomous_player'/'src'),str(root/'ck3_autonomous_player'/'tests'/'unit'),str(root)]
        from _following_2921350_fixture import following2921350_positive_leaf,following2921350_cold_leaf,following2921350_zero_leaf
        from xar_autoplayer.bridge.battle_person_following_2921350_contract import normalize_following_2921350
        from xar_autoplayer.simulation.battle_person_following_2921350_12003 import following_2921350_group_results_12003,emit_following_2921350_requests_12003,following_2921350_cold_normal_return_projections_12003,following_2921350_fnv1a_12003,following_2921350_tier_index_12003
        from xar_autoplayer.simulation.battle_trait_materialized_prefix_12003 import _fold_property_request
        if len(sys.argv)==3:
            values=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
            answer=[]
            for value in values:
                try: normalize_following_2921350(value); answer.append(True)
                except ValueError: answer.append(False)
            print(json.dumps(answer,separators=(',',':')))
            raise SystemExit(0)
        cases=[]
        seeds=[('positive',following2921350_positive_leaf()),('cold',following2921350_cold_leaf()),('zero',following2921350_zero_leaf())]
        partial=following2921350_positive_leaf()
        partial['title_walk'][-1].update(tier_raw_i32=None,definition_identity=None,collected=None,reason='title_input_unavailable')
        partial.update(status='partial',ready=False,reason='title_input_unavailable',provinces=partial['provinces'][:1])
        seeds.append(('partial_dfs',partial))
        rejected=following2921350_positive_leaf()
        rejected['provinces'][0].update(magic_u32=0,admitted=False,full_id_u32=None,source_count_raw=None,source_array_present=None,source_ids_u32=None,sources=[])
        seeds.append(('rejected_province',rejected))
        for name,raw in seeds:
            leaf=normalize_following_2921350(raw); modes=[]
            for project in (False,True):
                groups=following_2921350_group_results_12003(leaf,project_cold_initializer_normal_return=project)
                try:
                    requests=[dataclasses.asdict(value) for value in emit_following_2921350_requests_12003(leaf,project_cold_initializer_normal_return=project)]
                    rejected=False
                except ValueError: requests=[]; rejected=True
                modes.append({'project':project,'groups':groups,'requests':requests,'requests_rejected':rejected})
            cases.append({'name':name,'raw':raw,'normalized':leaf,'modes':modes,'cold_projections':following_2921350_cold_normal_return_projections_12003(leaf)})
        ids=[0,1,9,0xca000009,0xffffffff]
        tiers=[(2,[0,1000000],0),(2,[1],0),(2,[0],0),(0,[],0),(-1,[],0),(-2147483648,[],0),(None,None,0),(2,None,0)]
        folds=[]
        for destination,source,weight in [
            (([],[]),([0,5,65535],[-100000,200000,-300000]),100000),
            (([0,5,65535],[-100000,200000,-300000]),([0,5,65535],[-100000,200000,-300000]),100000),
            (([0],[9223372036854775807]),([0,4,65535],[-9223372036854775808,7,-3]),99999),
            (([],[]),([5,0,5,65535],[1,2,3,4]),0),
        ]:
            keys,values=list(destination[0]),list(destination[1]); updates=[]
            _fold_property_request(keys,values,tuple(source[0]),tuple(source[1]),weight,{},updates)
            folds.append({'destination':destination,'source':source,'weight':weight,'keys':keys,'values':values,'updates':updates})
        print(json.dumps({'cases':cases,'fnv':[{'id':value,'hash':following_2921350_fnv1a_12003(value)} for value in ids],
            'tiers':[{'count':n,'thresholds':t,'operand':v,'result':following_2921350_tier_index_12003(n,t,v)} for n,t,v in tiers],
            'folds':folds},separators=(',',':')))
        """;
    @BeforeAll static void loadActualProducer() throws Exception { verifyPins(); oracle=runOracle(Optional.empty()); verifyPins(); }
    @AfterAll static void sourcePostcheck() throws Exception { verifyPins(); }

    @Test void allActualPositiveColdAndZeroStreamsReachFacadeComputationAndRequests() {
        for(JsonNode scenario:oracle.get("cases")) {
            JsonNode normalized=normalize(scenario.get("raw"));
            assertEquals(canonical(scenario.get("normalized")),canonical(normalized),scenario.get("name").asText());
            assertEquals(canonical(normalized),canonical(normalize(canonical(normalized))));
            var evidence=BattlePersonProvinceCalculation.decode(normalized).orElseThrow();
            for(JsonNode mode:scenario.get("modes")) {
                boolean project=mode.get("project").booleanValue();ArrayNode groups=BattleContextJson.list();
                BattlePersonProvinceCalculation.groups(evidence,project,32).forEach(row->groups.add(row.toJson()));
                assertEquals(canonical(mode.get("groups")),canonical(groups));
                if(mode.get("requests_rejected").booleanValue())
                    assertThrows(IllegalArgumentException.class,()->BattlePersonProvinceCalculation.requests(evidence,project,32));
                else {
                    ArrayNode requests=BattleContextJson.list();
                    BattlePersonProvinceCalculation.requests(evidence,project,32).forEach(row->requests.add(row.toJson()));
                    assertEquals(canonical(mode.get("requests")),canonical(requests));
                    ObjectNode section=BattleContextJson.object();section.put("character_id",evidence.characterId());section.set("following_2921350",normalized);
                    assertEquals(BattlePersonProvinceCalculation.requests(evidence,project,32),
                            BattlePersonProvinceCalculation.requestsForCurrentSection(section,project,32));
                    assertThrows(IllegalArgumentException.class,()->BattlePersonProvinceCalculation.requestsForCurrentGroup(section,99,project,32));
                    section.put("character_id",evidence.characterId()+1);
                    assertThrows(IllegalArgumentException.class,()->BattlePersonProvinceCalculation.fromSection(section));
                }
            }
            ArrayNode cold=BattleContextJson.list();
            BattlePersonProvinceCalculation.coldNormalReturnProjections(evidence).forEach(row->cold.add(row.toJson()));
            assertEquals(canonical(scenario.get("cold_projections")),canonical(cold));
            for(JsonNode row:cold){assertFalse(row.get("native_initializer_invoked").booleanValue());assertFalse(row.get("raw_pc_observed").booleanValue());}
        }
    }
    @Test void originalFNVGenerationTierEqualityWrappingAndPropertyFoldMatch() {
        for(JsonNode row:oracle.get("fnv"))assertEquals(row.get("hash").longValue(),BattlePersonProvinceCodec.fnv1a(row.get("id").longValue()));
        assertNotEquals(BattlePersonProvinceCodec.fnv1a(9),BattlePersonProvinceCodec.fnv1a(0xca000009L));
        assertThrows(IllegalArgumentException.class,()->BattlePersonProvinceCodec.fnv1a(-1));
        for(JsonNode row:oracle.get("tiers")) {
            Optional<List<Long>> thresholds=row.get("thresholds").isNull()?Optional.empty():Optional.of(longs(row.get("thresholds")));
            var actual=BattlePersonProvinceCodec.tierIndex(new BattlePersonProvinceCodec.TierInput(
                    row.get("count").isNull()?OptionalInt.empty():OptionalInt.of(row.get("count").intValue()),thresholds,
                    row.get("operand").isNull()?OptionalLong.empty():OptionalLong.of(row.get("operand").longValue())));
            assertEquals(row.get("result").isNull()?OptionalInt.empty():OptionalInt.of(row.get("result").intValue()),actual);
        }
        for(JsonNode row:oracle.get("folds")) {
            var destination=new Block(ints(row.get("destination").get(0)),longs(row.get("destination").get(1)));
            var source=new Block(ints(row.get("source").get(0)),longs(row.get("source").get(1)));
            var result=NativePropertyFold2303120.fold(destination,source,row.get("weight").longValue());
            assertEquals(ints(row.get("keys")),result.block().keysU16());assertEquals(longs(row.get("values")),result.block().valuesQ64());
            ArrayNode updates=BattleContextJson.list();result.updates().forEach(row2->updates.add(row2.toJson()));
            assertEquals(canonical(row.get("updates")),canonical(updates));
        }
    }
    @Test void actualOriginalAndJavaRejectWrongFieldsWidthsDFSProbeAndTierInputs() throws Exception {
        ObjectNode positive=(ObjectNode)oracle.get("cases").get(0).get("raw"),cold=(ObjectNode)oracle.get("cases").get(1).get("raw");
        ArrayNode invalid=BattleContextJson.list();ObjectNode x=positive.deepCopy();x.put("unowned_extra",1);invalid.add(x);
        x=positive.deepCopy();x.remove("character_id");invalid.add(x);
        x=positive.deepCopy();x.put("character_id",true);invalid.add(x);
        x=positive.deepCopy();x.put("character_id",29829.0);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.get("title_source")).remove("array_present");invalid.add(x);
        x=positive.deepCopy();((ArrayNode)x.at("/title_source/full_ids_u32")).set(0,com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(java.math.BigInteger.ONE.shiftLeft(32)));invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/title_walk/1")).put("parent_index",99);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/title_walk/1")).put("collected",false);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/title_walk/1")).put("selected_full_id_u32",1);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/title_walk/1")).put("children_count_raw",0);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0")).put("magic_u32",0);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0/sources/0")).put("requested_full_id_u32",1);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0/sources/0/map/probes/0")).put("bucket_index_i64",1);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0/sources/0/map/probes/0")).put("distance_raw_u8",0);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0/sources/0/map/probes/0")).put("distance_raw_u8",256);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0/sources/0/map/probes/0")).put("key_raw_u32",false);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0/sources/0/map")).put("found",false);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0/sources/0/tiers")).put("selected_index_raw_i32",1);invalid.add(x);
        x=positive.deepCopy();((ArrayNode)x.at("/provinces/0/sources/0/tiers/thresholds_q64")).set(0,com.fasterxml.jackson.databind.node.LongNode.valueOf(1));invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/provinces/0/sources/0/tiers")).put("count_raw_i32",0);invalid.add(x);
        x=positive.deepCopy();((ObjectNode)x.at("/manager")).put("loaded",false);invalid.add(x);
        x=positive.deepCopy();x.put("ready",false);invalid.add(x);
        x=cold.deepCopy();((ObjectNode)x.at("/provinces/0/sources/2/tiers/pc")).set("property_block",Block.empty().toJson());invalid.add(x);
        JsonNode accepted=runOracle(Optional.of(invalid));assertEquals(invalid.size(),accepted.size());
        for(int i=0;i<invalid.size();i++){final JsonNode candidate=invalid.get(i);assertFalse(accepted.get(i).booleanValue(),"original accepted mutation"+i);
            assertThrows(IllegalArgumentException.class,()->normalize(candidate),"Java accepted original-rejected mutation"+i);}
    }
    @Test void sharedByteIngressAndTypedMaterializationKeepNullMissingAndActualAdmissionSeparate() {
        assertThrows(IllegalArgumentException.class,()->StrictJson.parse("{\"character_id\":1,\"character_id\":2}".getBytes(StandardCharsets.UTF_8),1048576));
        assertThrows(IllegalArgumentException.class,()->StrictJson.parse("{} {}".getBytes(StandardCharsets.UTF_8),1048576));
        assertTrue(normalize(com.fasterxml.jackson.databind.node.NullNode.instance).isNull());
        assertTrue(BattlePersonProvinceCalculation.decode(com.fasterxml.jackson.databind.node.NullNode.instance).isEmpty());
        var zero=BattlePersonProvinceCalculation.decode(oracle.get("cases").get(2).get("raw")).orElseThrow();
        assertTrue(BattlePersonProvinceCalculation.requests(zero,false,32).isEmpty());
        assertThrows(IllegalArgumentException.class,()->BattlePersonProvinceCalculation.groups(zero,false,2));
        ObjectNode section=BattleContextJson.object();section.put("character_id",29829);
        assertThrows(IllegalArgumentException.class,()->BattlePersonProvinceCalculation.fromSection(section));
        section.putNull("following_2921350");assertThrows(IllegalArgumentException.class,()->BattlePersonProvinceCalculation.fromSection(section));
    }
    private static JsonNode normalize(JsonNode raw){return BattlePersonExternalCodec.normalize(BattlePersonExternalCodec.Leaf.FOLLOWING_2921350,raw,"following_2921350");}
    private static JsonNode canonical(JsonNode raw){return StrictJson.parse(StrictJson.canonical(raw,1048576),1048576);}
    private static List<Integer> ints(JsonNode rows){List<Integer> result=new ArrayList<>();rows.forEach(row->result.add(row.bigIntegerValue().intValueExact()));return List.copyOf(result);}
    private static List<Long> longs(JsonNode rows){List<Long> result=new ArrayList<>();rows.forEach(row->result.add(row.bigIntegerValue().longValueExact()));return List.copyOf(result);}
    private static synchronized JsonNode runOracle(Optional<JsonNode> input) throws Exception {
        Path root=Path.of(required("xar.repository.root")).toAbsolutePath().normalize(),python=Path.of(required("xar.python"));
        assertTrue(python.isAbsolute()&&Files.isRegularFile(python),"explicit original interpreter missing");
        int id=++sequence;Path output=scratch.resolve("oracle-"+id+".json"),error=scratch.resolve("oracle-"+id+".err");
        List<String> argv=new ArrayList<>(List.of(python.toString(),"-B","-X","utf8","-c",PROGRAM,root.toString()));
        if(input.isPresent()){Path file=scratch.resolve("input-"+id+".json");Files.write(file,StrictJson.canonical(input.orElseThrow(),1048576));argv.add(file.toString());}
        ProcessBuilder builder=new ProcessBuilder(argv).directory(root.toFile()).redirectOutput(output.toFile()).redirectError(error.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONNOUSERSITE","1");
        builder.environment().remove("PYTHONHOME");builder.environment().remove("PYTHONPATH");Process process=builder.start();
        try {
            assertTrue(process.waitFor(30,TimeUnit.SECONDS),"original producer timeout");
            assertTrue(Files.size(error)<=1048576,"bounded original stderr required");
            assertEquals(0,process.exitValue(),()->{try{return Files.readString(error);}catch(Exception failure){return failure.toString();}});
            assertTrue(Files.size(output)>0&&Files.size(output)<=1048576,"bounded original producer output required");
            return StrictJson.parse(Files.readAllBytes(output),1048576);
        }finally{if(process.isAlive()){process.destroyForcibly();assertTrue(process.waitFor(5,TimeUnit.SECONDS),"child terminal not consumed");}}
    }
    private static void verifyPins() throws Exception {
        Path root=Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        for(Pin pin:PINS){byte[] bytes=Files.readAllBytes(root.resolve(pin.relative()));assertTrue(bytes.length>0&&bytes.length<=2097152);
            assertEquals(pin.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),pin.relative());}
    }
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,key+" required; never skip original parity");assertFalse(value.isBlank());return value;}
}
