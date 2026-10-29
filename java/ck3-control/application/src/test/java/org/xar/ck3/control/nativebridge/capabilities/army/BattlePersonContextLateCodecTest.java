package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonExternalCodec.Leaf;

/** Actual original fixture producers/normalizers and the installed external facade; no Native/Game qualification. */
final class BattlePersonContextLateCodecTest {
    private static final ObjectMapper JSON=new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private static final int MAX_CAPTURE=8*1024*1024;
    private static final Set<Leaf> DIRECT=Set.of(Leaf.QUALIFIER_28BC0D0,Leaf.LIST_PREDICATE_2530DD0,Leaf.GATED_TEMPORARY_TAIL_291C7A7,
            Leaf.AFTER_GATED_TAIL_326A8E0_2920310,Leaf.PROVIDER192_AND2920850,Leaf.FOLLOWING_2920B50,
            Leaf.FOLLOWING_2BCA620,Leaf.FOLLOWING_GOVERNMENT_LAND_312A950,Leaf.FOLLOWING_2921020);
    private static final List<String> CONTRACTS=List.of("qualifier_28bc0d0","list_predicate_2530dd0","gated_temporary_tail","after_gated_tail",
            "provider192_and2920850","following_2920b50","following_2bca620","following_312a950","following_2921020");
    private static final List<String> FIXTURES=List.of("test_battle_person_qualifier_28bc0d0_12003.py","test_battle_person_list_predicate_2530dd0_12003.py",
            "test_battle_person_gated_temporary_tail_12003.py","test_battle_person_after_gated_tail_12003.py",
            "test_battle_person_provider192_and2920850_12003.py","test_battle_person_following_2920b50_12003.py",
            "test_battle_person_following_2bca620_12003.py","test_battle_person_following_312a950_12003.py","following_2921020_fixture_inputs.py");

    @Test void everyLateLeafPreservesExplicitNullAndRejectsMissingOrUnownedContract() {
        for(Leaf leaf:List.of(Leaf.QUALIFIER_28BC0D0,Leaf.LIST_PREDICATE_2530DD0,Leaf.GATED_TEMPORARY_TAIL_291C7A7,
                Leaf.AFTER_GATED_TAIL_326A8E0_2920310,Leaf.PROVIDER192_AND2920850,Leaf.FOLLOWING_2920B50,Leaf.FOLLOWING_2BCA620,
                Leaf.FOLLOWING_GOVERNMENT_LAND_312A950,Leaf.FOLLOWING_2921350,Leaf.FOLLOWING_2921020,Leaf.FOLLOWING_DIAC_2920D60)) {
            assertSame(NullNode.instance,BattlePersonContextLateCodec.normalize(leaf,NullNode.instance,"fixture"));
            assertThrows(IllegalArgumentException.class,()->BattlePersonContextLateCodec.normalize(leaf,null,"fixture"));
        }
        assertThrows(IllegalArgumentException.class,()->BattlePersonContextLateCodec.normalize(Leaf.HELPER_291F0A0,NullNode.instance,"fixture"));
    }

    @Test void originalProducerToBothInstalledConsumersRejectsWrongFieldsTypesAndNumericVerdictsAndRoundTrips() throws Exception {
        String rootValue=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(rootValue,"NOT_EXECUTED: full migration CI must configure the actual original repository");
        assertNotNull(python,"NOT_EXECUTED: full migration CI must configure the original Python reference interpreter");
        Path root=Path.of(rootValue).toRealPath();List<String> sources=new ArrayList<>();
        for(String name:CONTRACTS)sources.add("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_"+name+"_contract.py");
        for(String name:FIXTURES)sources.add("ck3_autonomous_player/tests/unit/"+name);
        sources.add("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_context_source_inputs_contract.py");
        sources.add("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_trait_stage_291d460_contract.py");
        sources.add("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_remaining_helpers_contract.py");
        List<String> before=new ArrayList<>();for(String name:sources)before.add(sha(Files.readAllBytes(root.resolve(name))));
        ObjectNode input=JSON.createObjectNode();ArrayNode originalSources=input.putArray("sources");sources.forEach(originalSources::add);
        Process child=new ProcessBuilder(python,"-B","-X","utf8","-c",ORIGINAL,root.toString()).directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();byte[] capture;
        try(var readers=Executors.newVirtualThreadPerTaskExecutor()) {
            var output=readers.submit(()->child.getInputStream().readNBytes(MAX_CAPTURE+1));
            try(var sink=child.getOutputStream()){sink.write(JSON.writeValueAsBytes(input));}
            if(!child.waitFor(Duration.ofSeconds(90).toMillis(),TimeUnit.MILLISECONDS)){child.descendants().forEach(ProcessHandle::destroyForcibly);child.destroyForcibly();fail("actual original late PERSON reference fixture timed out");}
            capture=output.get(5,TimeUnit.SECONDS);
        } finally {if(child.isAlive())child.destroyForcibly();}
        assertEquals(0,child.exitValue());assertTrue(capture.length>0&&capture.length<=MAX_CAPTURE);
        JsonNode result=JSON.readTree(capture);Set<Leaf> seen=EnumSet.noneOf(Leaf.class);int accepted=0,rejected=0;
        for(JsonNode row:result.path("cases")) {
            Leaf leaf=Leaf.fromWire(row.path("leaf").textValue());seen.add(leaf);JsonNode raw=row.get("raw"),saved=raw.deepCopy();
            if(row.path("ok").booleanValue()) {
                JsonNode actual=BattlePersonExternalCodec.normalize(leaf,raw,"fixture");assertEquals(row.get("normalized"),actual,leaf+" actual original consumer differs");
                assertEquals(actual,BattlePersonContextLateCodec.normalize(leaf,raw,"fixture"));
                JsonNode serialized=JSON.readTree(JSON.writeValueAsBytes(actual));assertEquals(actual,BattlePersonExternalCodec.normalize(leaf,serialized,"fixture"));accepted++;
            } else {assertThrows(IllegalArgumentException.class,()->BattlePersonExternalCodec.normalize(leaf,raw,"fixture"),leaf+" accepted actual original rejection");rejected++;}
            assertEquals(saved,raw,"normalizer mutated actual retained Native JSON");
        }
        assertEquals(DIRECT,seen);assertTrue(accepted>=18);assertTrue(rejected>=100);
        for(int i=0;i<sources.size();i++){String name=sources.get(i);assertEquals(before.get(i),result.path("source_shas").path(name).textValue());assertEquals(before.get(i),sha(Files.readAllBytes(root.resolve(name))),"actual original source changed during compatibility capture");}
    }
    private static String sha(byte[] raw) throws Exception {return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}
    private static final String ORIGINAL="""
        import sys,json,copy,runpy,hashlib,importlib
        from pathlib import Path
        root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
        incoming=json.load(sys.stdin)
        before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in incoming['sources']}
        def fixture(name):return runpy.run_path(str(root/'ck3_autonomous_player/tests/unit'/name))
        q=fixture('test_battle_person_qualifier_28bc0d0_12003.py')
        evaluations=[q['evaluation'](i,[q['candidate'](0x1000)],key) for i,key in enumerate([0,0x80000001,0xffffffff,0x80000001])]
        qualifier=q['leaf']([q['definition'](0,0x1000,evaluations,[0,0x80000001])],4)
        p=fixture('test_battle_person_list_predicate_2530dd0_12003.py')
        predicate=p['leaf']([p['row'](0,0xffffffff),p['row'](1,0,0x1000,empty_pc=True),p['row'](2,0xab000001,0x2000,magic=0x4744624f,condition=0),p['row'](3,0xab000001,0x2000,fallback=True)])
        names={
          'qualifier_28bc0d0':('battle_person_qualifier_28bc0d0_contract','normalize_qualifier_28bc0d0',qualifier),
          'list_predicate_2530dd0':('battle_person_list_predicate_2530dd0_contract','normalize_list_predicate_2530dd0',predicate)}
        factories=[('gated_temporary_tail_291c7a7','test_battle_person_gated_temporary_tail_12003.py','gated_temporary_source','battle_person_gated_temporary_tail_contract','normalize_gated_temporary_tail_291c7a7'),
          ('after_gated_tail_326a8e0_2920310','test_battle_person_after_gated_tail_12003.py','after_gated_source','battle_person_after_gated_tail_contract','normalize_after_gated_tail_326a8e0_2920310'),
          ('provider192_and2920850','test_battle_person_provider192_and2920850_12003.py','provider192_and2920850_source','battle_person_provider192_and2920850_contract','normalize_provider192_and2920850'),
          ('following_2920b50','test_battle_person_following_2920b50_12003.py','following2920b50_source','battle_person_following_2920b50_contract','normalize_following_2920b50'),
          ('following_2bca620','test_battle_person_following_2bca620_12003.py','following2bca620_source','battle_person_following_2bca620_contract','normalize_following_2bca620'),
          ('following_government_land_312a950','test_battle_person_following_312a950_12003.py','following312a950_source','battle_person_following_312a950_contract','normalize_following_government_land_312a950')]
        for leaf,filename,function,module,normalizer in factories:
          actual=fixture(filename)[function]();names[leaf]=(module,normalizer,actual[leaf])
        legacy=fixture('following_2921020_fixture_inputs.py')['build_following2921020_positive_leaf']()
        names['following_2921020']=('battle_person_following_2921020_contract','normalize_following_2921020',legacy)
        def scalar_paths(value,path=()):
          if isinstance(value,dict):
            for key,item in value.items():yield from scalar_paths(item,path+(key,))
          elif isinstance(value,list):
            for index,item in enumerate(value):yield from scalar_paths(item,path+(index,))
          else:yield path
        def set_path(value,path,new):
          for key in path[:-1]:value=value[key]
          value[path[-1]]=new
        cases=[]
        for leaf,(module,function,raw) in names.items():
          normalize=getattr(importlib.import_module('xar_autoplayer.bridge.'+module),function)
          variants=[copy.deepcopy(raw),None]
          for key in list(raw):
            value=copy.deepcopy(raw);del value[key];variants.append(value)
          value=copy.deepcopy(raw);value['unmigrated_extra_field']=True;variants.append(value)
          paths=list(scalar_paths(raw));selected=paths[:20]+paths[-20:]
          for path in selected:
            actual=raw
            for key in path:actual=actual[key]
            wrong=1 if type(actual) is bool else True if type(actual) is int else '' if type(actual) is str else 1.0
            value=copy.deepcopy(raw);set_path(value,path,wrong);variants.append(value)
            if type(actual) is int:
              for replacement in (float(actual),1<<80):
                value=copy.deepcopy(raw);set_path(value,path,replacement);variants.append(value)
            elif type(actual) is bool:
              value=copy.deepcopy(raw);set_path(value,path,not actual);variants.append(value)
          # These alter the published arithmetic verdict while preserving its scalar type.
          for path in paths:
            if path[-1] in ('repeat_count','fresh_rank_raw','delta_raw','absolute_delta_raw','completed_months_raw','kind_raw','index_raw_i32'):
              actual=raw
              for key in path:actual=actual[key]
              if type(actual) is int:
                value=copy.deepcopy(raw);set_path(value,path,actual+1);variants.append(value)
          for value in variants:
            saved=copy.deepcopy(value);case={'leaf':leaf,'raw':value}
            try:case.update(ok=True,normalized=normalize(value,'fixture'))
            except (ValueError,TypeError,KeyError):case.update(ok=False)
            if value!=saved:raise RuntimeError('actual original normalizer mutated source')
            cases.append(case)
        after={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in incoming['sources']}
        if before!=after:raise RuntimeError('actual original source changed during fixture capture')
        print(json.dumps({'cases':cases,'source_shas':after},separators=(',',':'),allow_nan=False))
        """;
}
