package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonExternalCodec.Leaf;

/** Actual retained Python normalizers -> every Java external facade consumer, using original native packets.
 * Native corpus availability is required. A source-shaped object or a skipped test cannot qualify this chain.
 */
final class BattlePersonCurrentExternalCodecTest {
    private record Source(String stem,long bytes,String sha) { }
    private record Case(Leaf leaf,JsonNode raw,String label) { }
    private record Corpus(List<Case> cases,List<JsonNode> custody) { }
    private static final List<Leaf> LEAVES=List.of(Leaf.CARRIER_1C8_B70_DIRECT,Leaf.FOLLOWING_2921A90,Leaf.FOLLOWING_2921A90_CONDITIONAL,
        Leaf.FOLLOWING_2921A90_OPINION,Leaf.FOLLOWING_2921A90_SCOPE_WEIGHTS,Leaf.FOLLOWING_2922680,Leaf.FOLLOWING_291CE01_GOVERNMENT_GATE,
        Leaf.FOLLOWING_291E3A0_LOCAL_TITLES,Leaf.FOLLOWING_291E3A0_FIRST_TITLE_VECTOR,Leaf.FOLLOWING_291E3A0_CAPTURED_TAIL);
    private static final List<Source> SOURCES=List.of(
        new Source("battle_person_carrier_direct_12004",6818,"b77aaa18590d6620c4c6c0a36d3c94b4bd17670106276f4858282abcbd74eb84"),
        new Source("battle_person_following_2921a90_12004",11318,"36e92af40ceab985112ba04025b742b28d5407ea32aa26c569ea3886558ea958"),
        new Source("battle_person_conditional_2921a90_12004",19481,"a5a3303ef0b620b3a3bcbeae30ad340d90ea0c961596ae54ea41dff61cf23695"),
        new Source("battle_person_conditional_opinion_12004",15342,"3e2092a665a0067b2c698d59797c5d479364445958400f60128640d73b4bc74d"),
        new Source("battle_person_conditional_scope_weights_12004",13973,"d6c004d83028e9164b71465d0f7e23b3ab1fc0ca3ac20022721ed482af8eab1c"),
        new Source("battle_person_following_2922680_12004",17599,"f21ee3070c63216b5265e2b633c10ebd63e4db8612f70fed58cc66cbea248b9b"),
        new Source("battle_person_government_gate_12004",4452,"549bd80bea509d108ff735b2829a583c45bf6cf2474a9a54c0dd528a60dfda1e"),
        new Source("battle_person_local_titles_12004",15190,"6c7a9ff3c35e20c299ed69ccb774aaf7785e94f4a574a260a38b63406505bf27"),
        new Source("battle_person_first_title_vector_12004",13933,"74b7f22cf25ffee1176530263cb5e814a062766f604e564e7ebcd31835d73aa9"),
        new Source("battle_person_title_tail_capture_12004",6371,"4acd69dfc5884275feef36d4338ef6b2f2890b26b9c5bb5c8fece3b913f85179"),
        new Source("battle_context_source_inputs_contract",50724,"aef31456253ca7fd5160dfd73d244bc929c4284e621ca3a638eef38515a9d245"),
        new Source("version_identity",2114,"9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"),
        new Source("battle_terminal_transition_contract",103208,"f8a0c5d4513eee9a0c918dfa244b72613f13479b2d2ecb68c225f02847dd81db")
    );
    private static final String ORACLE="""
import importlib,json,sys
names={
'carrier_1c8_b70_direct':('battle_person_carrier_direct_12004','normalize_carrier_direct_12004'),
'following_2921a90':('battle_person_following_2921a90_12004','normalize_person_following_2921a90_12004'),
'following_2921a90_conditional':('battle_person_conditional_2921a90_12004','normalize_person_conditional_2921a90_12004'),
'following_2921a90_opinion':('battle_person_conditional_opinion_12004','normalize_person_conditional_opinion_12004'),
'following_2921a90_scope_weights':('battle_person_conditional_scope_weights_12004','normalize_person_conditional_scope_weights_12004'),
'following_2922680':('battle_person_following_2922680_12004','normalize_person_following_2922680_12004'),
'following_291ce01_government_gate':('battle_person_government_gate_12004','normalize_person_government_gate_12004'),
'following_291e3a0_local_titles':('battle_person_local_titles_12004','normalize_person_local_titles_12004'),
'following_291e3a0_first_title_vector':('battle_person_first_title_vector_12004','normalize_person_first_title_vector_12004'),
'following_291e3a0_captured_tail':('battle_person_title_tail_capture_12004','normalize_person_title_tail_capture_12004')}
result=[]
for row in json.load(sys.stdin)['cases']:
    module,function=names[row['leaf']]
    producer=getattr(importlib.import_module('xar_autoplayer.bridge.'+module),function)
    try:result.append({'accepted':True,'normalized':producer(row['raw'])})
    except (ValueError,TypeError,OverflowError):result.append({'accepted':False})
print(json.dumps({'results':result},ensure_ascii=False,allow_nan=False))
""";
    @Test @Timeout(300)
    void originalNativePacketsAndAllTenActualOriginalProducersReachTheTypedFacade() throws Exception {
        List<Case> nativeCases=corpus().cases();Map<Leaf,Case> first=new EnumMap<>(Leaf.class);nativeCases.forEach(row->first.putIfAbsent(row.leaf(),row));assertEquals(10,first.size());
        List<Case> cases=new ArrayList<>(nativeCases);
        for(Leaf leaf:LEAVES){Case original=first.get(leaf);cases.add(new Case(leaf,NullNode.instance,"explicit-null"));
            ObjectNode unknown=original.raw().deepCopy();unknown.put("unknown_field",true);cases.add(new Case(leaf,unknown,"unknown-field"));
            List<String> keys=new ArrayList<>();original.raw().fieldNames().forEachRemaining(keys::add);
            for(String key:keys){ObjectNode missing=original.raw().deepCopy();missing.remove(key);cases.add(new Case(leaf,missing,"missing:"+key));
                ObjectNode nullable=original.raw().deepCopy();nullable.putNull(key);cases.add(new Case(leaf,nullable,"null:"+key));
                ObjectNode wrong=original.raw().deepCopy();JsonNode value=wrong.get(key);if(value.isBoolean())wrong.put(key,1);else if(value.isIntegralNumber())wrong.put(key,true);else if(value.isTextual())wrong.put(key,3.5);else wrong.put(key,"wrong-type");cases.add(new Case(leaf,wrong,"wrong-type:"+key));
            }
            for(String key:List.of("character_id","capture_sequence","weight_q100000"))if(original.raw().has(key)){ObjectNode floating=original.raw().deepCopy();floating.put(key,1.0);cases.add(new Case(leaf,floating,"float-integer:"+key));}
        }
        compare(cases);
    }
    @Test @Timeout(300)
    void completeOriginalCustodyProducerConsumesTheSameTenExtensionsThroughTheActualPersonIngress() throws Exception {
        Corpus corpus=corpus();assertFalse(corpus.custody().isEmpty(),"whole native packets must retain actual character_observations");verifySources();
        for(JsonNode rows:corpus.custody()){
            ObjectNode input=StrictJson.object();input.set("rows",rows);
            JsonNode expected=BattleOriginalOracle.call("""
import json,sys
from xar_autoplayer.bridge.battle_terminal_transition_contract import _normalize_character_custody_rows
request=json.load(sys.stdin)
print(json.dumps({'rows':_normalize_character_custody_rows(request['rows'],'character_observations',allow_current_person_state=True)},allow_nan=False))
""",input).get("rows");
            JsonNode actual=BattleTerminalPersonCodec.normalizeCustody(rows,"character_observations",true);
            assertEquals(normalizeTree(expected),normalizeTree(actual),"actual terminal custody -> current Person -> all external codecs");
            assertEquals(normalizeTree(actual),normalizeTree(BattleTerminalPersonCodec.normalizeCustody(StrictJson.parse(StrictJson.canonical(actual)),"character_observations",true)));
        }verifySources();
    }
    @Test @Timeout(90)
    void malformedTopLevelTokensAndExplicitNullsUseTheRealOriginalNormalizer() throws Exception {
        List<Case> cases=new ArrayList<>();for(Leaf leaf:LEAVES){cases.add(new Case(leaf,NullNode.instance,"null"));cases.add(new Case(leaf,StrictJson.object(),"empty"));cases.add(new Case(leaf,StrictJson.parse("true".getBytes(java.nio.charset.StandardCharsets.UTF_8)),"bool"));cases.add(new Case(leaf,StrictJson.parse("[]".getBytes(java.nio.charset.StandardCharsets.UTF_8)),"list"));}
        compare(cases);assertThrows(IllegalArgumentException.class,()->BattlePersonCurrentExternalCodec.normalize(Leaf.HELPER_291F0A0,StrictJson.object(),"outside"));
    }
    private static void compare(List<Case> cases) throws Exception {
        verifySources();int start=0;while(start<cases.size()){
            ArrayNode rows=StrictJson.object().putArray("cases");int end=start,bytes=0;
            while(end<cases.size()&&end<start+64){Case row=cases.get(end);ObjectNode request=StrictJson.object().put("leaf",row.leaf().wire());request.set("raw",row.raw());int size=StrictJson.canonical(request).length;if(end>start&&bytes+size>4*1024*1024)break;assertTrue(size<=4*1024*1024,"bounded single native leaf");rows.add(request);bytes+=size;end++;}
            ObjectNode request=StrictJson.object();request.set("cases",rows);JsonNode expected=BattleOriginalOracle.call(ORACLE,request).get("results");assertEquals(end-start,expected.size());
            for(int index=start;index<end;index++){Case row=cases.get(index);JsonNode response=expected.get(index-start);JsonNode actual=null;IllegalArgumentException failure=null;
                try{actual=BattlePersonExternalCodec.normalize(row.leaf(),row.raw(),row.leaf().wire());}catch(IllegalArgumentException rejected){failure=rejected;}
                String label=row.leaf()+":"+row.label();if(response.get("accepted").booleanValue()){
                    assertNull(failure,label+": "+(failure==null?"":failure.getMessage()));assertEquals(normalizeTree(response.get("normalized")),normalizeTree(actual),label);
                    assertEquals(normalizeTree(actual),normalizeTree(BattlePersonExternalCodec.normalize(row.leaf(),StrictJson.parse(StrictJson.canonical(actual)),row.leaf().wire())),label+" full serialization round trip");
                }else assertNotNull(failure,label+" original producer rejected this exact shape");
            }start=end;
        }verifySources();
    }
    private static JsonNode normalizeTree(JsonNode n){return StrictJson.parse(StrictJson.canonical(n));}
    private static void verifySources() throws Exception {
        String value=System.getProperty("xar.repository.root");if(value==null)throw new IllegalStateException("NOT_EXECUTED: xar.repository.root required for actual Person10 producers");Path root=Path.of(value).toRealPath();
        for(Source source:SOURCES){Path path=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/"+source.stem()+".py").toRealPath();assertTrue(path.startsWith(root));byte[] raw=Files.readAllBytes(path);assertEquals(source.bytes(),raw.length);assertEquals(source.sha(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)),source.stem());}
    }
    private static Corpus corpus() throws Exception {
        Person10CorpusManifest.Manifest manifest=Person10CorpusManifest.configured();
        List<Case> cases=new ArrayList<>();Map<String,Case> unique=new LinkedHashMap<>();Map<String,JsonNode> custody=new LinkedHashMap<>();
        for(Person10CorpusManifest.FileRef file:manifest.files())
            collect(StrictJson.parse(file.read(),1<<20),file.path(),unique,custody);
        Person10CorpusManifest.verify(manifest);
        cases.addAll(unique.values());for(Leaf leaf:LEAVES)assertTrue(cases.stream().anyMatch(row->row.leaf()==leaf&&!row.raw().isNull()),
            "pinned original native corpus lacks nonnull "+leaf);
        return new Corpus(List.copyOf(cases),List.copyOf(custody.values()));
    }
    private static void collect(JsonNode n,String label,Map<String,Case> found,Map<String,JsonNode> custody) throws Exception {
        if(n.isObject()){for(Leaf leaf:LEAVES)if(n.has(leaf.wire())&&!n.get(leaf.wire()).isNull()){
            JsonNode raw=n.get(leaf.wire());String digest=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(StrictJson.canonical(raw)));found.putIfAbsent(leaf.wire()+":"+digest,new Case(leaf,raw,label));}
            if(n.has("character_observations")&&n.get("character_observations").isArray()){JsonNode rows=n.get("character_observations");String digest=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(StrictJson.canonical(rows)));custody.putIfAbsent(digest,rows);}
            var fields=n.properties().iterator();while(fields.hasNext()){var row=fields.next();collect(row.getValue(),label+"/"+row.getKey(),found,custody);}
        }else if(n.isArray())for(int index=0;index<n.size();index++)collect(n.get(index),label+"/"+index,found,custody);
    }
}
