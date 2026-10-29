package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionHolyKnowledge;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionHolyReads;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionHolyState;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract.*;

/** Original full-response differential; fixture DATA grants no current Core authority. */
final class ReligionCreationAdoptionKnowledgePythonParityTest {
    @TempDir Path temp;
    private static final String KNOWLEDGE_METHOD="ck3_query_holy_site_planning_knowledge_v1";
    private static final String ORIGINAL_STATE_INPUTS="/org/xar/ck3/control/religion/original-state-inputs-v1.json";
    private enum Expected { VALUE, REJECT }
    private record Input(String name,RawJson arguments,Expected expected) { }
    private record StateInput(String name,ObjectNode body,ObjectNode snapshot,BigInteger revision,
                              Optional<BigInteger> requested,Expected expected) { }
    private record NativeFixture(String name,ExactRef packet,ObjectNode original,ObjectNode body,
                                 ObjectNode snapshot,BigInteger revision,Optional<BigInteger> requested) { }
    private static final List<String> STATE_FIXTURES=List.of("window-selected.json","explicit-selected.json","stale-generation.json","faith-unavailable.json");
    private static final String KNOWLEDGE_ORACLE="""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();pins=json.loads(sys.argv[2]);requests=json.loads(sys.argv[3])
for pin in pins:
 path=Path(pin['path']).resolve();path.relative_to(root);data=path.read_bytes()
 if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']:
  raise RuntimeError('original planning source drift: '+pin['path'])
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from xar_autoplayer.holy_site_planning_knowledge import query_holy_site_planning_knowledge_v1
if Path(query_holy_site_planning_knowledge_v1.__code__.co_filename).resolve()!=root/'ck3_autonomous_player/src/xar_autoplayer/holy_site_planning_knowledge.py':raise RuntimeError('original knowledge import path drift')
rows=[]
for item in requests:
 try:
  value=query_holy_site_planning_knowledge_v1(**item['arguments'])
  rows.append({'name':item['name'],'accepted':True,'value':value})
 except (ValueError,TypeError) as error:
  rows.append({'name':item['name'],'accepted':False,'error_type':type(error).__name__,'error':str(error)})
print(json.dumps({'schema':'xar.religion.original-python-knowledge-differential/v1','cases':rows},ensure_ascii=False,separators=(',',':')))
""";
    private static final String STATE_ORACLE="""
import copy,hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();pins=json.loads(sys.argv[2]);requests=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
for pin in pins:
 path=Path(pin['path']).resolve();path.relative_to(root);data=path.read_bytes()
 if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']:
  raise RuntimeError('original HolySite normalization source drift: '+pin['path'])
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.player_holy_site_private_transport import normalize_player_holy_site_v1
if Path(normalize_player_holy_site_v1.__code__.co_filename).resolve()!=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_site_private_transport.py':raise RuntimeError('original state import path drift')
rows=[]
for item in requests:
 original=copy.deepcopy(item)
 try:
  value=normalize_player_holy_site_v1(item['body'],snapshot=item['snapshot'],requested_holy_site_id=item['requested'])
  rows.append({'name':item['name'],'accepted':True,'value':value,'input_unchanged':item==original})
 except (ValueError,TypeError) as error:
  rows.append({'name':item['name'],'accepted':False,'error_type':type(error).__name__,'error':str(error),'input_unchanged':item==original})
print(json.dumps({'schema':'xar.religion.original-python-holy-state-differential/v1','cases':rows},ensure_ascii=False,separators=(',',':')))
""";

    @Test void everyKnowledgeActionAndExactBuildUsesOriginalProducerAndCompletePublicResponse() throws Exception {
        List<Input> inputs=new ArrayList<>();
        for(ReligionHolyKnowledge.Action action:ReligionHolyKnowledge.Action.values()) {
            ObjectNode defaults=StrictJson.object();defaults.put("action",action.wire());inputs.add(new Input(action.wire()+"/default",ReligionCodec.raw(defaults),Expected.VALUE));
            for(String build:List.of("1.20.0.4","1.20.0.3","1.19.0.6","1.20.1.1","1.20.0.04")) {
                ObjectNode request=defaults.deepCopy();request.put("ck3_build",build);inputs.add(new Input(action.wire()+"/"+build,ReligionCodec.raw(request),Expected.VALUE));
            }
        }
        ObjectNode empty=StrictJson.object();empty.put("action","adopt");empty.put("ck3_build","");inputs.add(new Input("empty-build",ReligionCodec.raw(empty),Expected.REJECT));
        for(JsonNode token:List.of(JsonNodeFactory.instance.booleanNode(true),JsonNodeFactory.instance.numberNode(1),JsonNodeFactory.instance.numberNode(1.0),JsonNodeFactory.instance.nullNode())) {
            ObjectNode bad=StrictJson.object();bad.set("action",token);inputs.add(new Input("action-type-"+inputs.size(),ReligionCodec.raw(bad),Expected.REJECT));
            bad=StrictJson.object();bad.put("action","adopt");bad.set("ck3_build",token);inputs.add(new Input("build-type-"+inputs.size(),ReligionCodec.raw(bad),Expected.REJECT));
        }
        ObjectNode unknown=StrictJson.object();unknown.put("action","not-an-action");inputs.add(new Input("unknown-action",ReligionCodec.raw(unknown),Expected.REJECT));
        unknown=StrictJson.object();unknown.put("action","adopt");unknown.put("unexpected",true);inputs.add(new Input("unknown-argument",ReligionCodec.raw(unknown),Expected.REJECT));
        for(int first=0;first<inputs.size();first+=6)verifyKnowledgeInputs(inputs.subList(first,Math.min(first+6,inputs.size())),"knowledge-"+first);
    }

    private void verifyKnowledgeInputs(List<Input> inputs,String tag) throws Exception {
        ArrayNode requests=StrictJson.object().putArray("requests");
        for(Input input:inputs){ObjectNode row=StrictJson.object();row.put("name",input.name());row.set("arguments",ReligionCodec.object(input.arguments()));requests.add(row);}
        List<ExactRef> sourcePins=ReligionHolyKnowledge.originalSources();ObjectNode oracle=oracle(KNOWLEDGE_ORACLE,tag,sourcesJson(sourcePins),requests.toString());for(ExactRef source:sourcePins)verify(source);
        StrictJson.object(oracle,Set.of("schema","cases"));assertEquals("xar.religion.original-python-knowledge-differential/v1",oracle.get("schema").textValue());
        JsonNode rows=oracle.get("cases");assertTrue(rows.isArray());assertEquals(inputs.size(),rows.size());
        for(int index=0;index<inputs.size();index++) {
            Input input=inputs.get(index);ObjectNode expected=assertInstanceOf(ObjectNode.class,rows.get(index));assertEquals(input.name(),StrictJson.text(expected.get("name")));
            assertTrue(expected.get("accepted").isBoolean());
            if(input.expected()==Expected.REJECT) {
                StrictJson.object(expected,Set.of("name","accepted","error_type","error"));assertFalse(expected.get("accepted").booleanValue());
                assertThrows(RuntimeException.class,()->actualKnowledge(input.arguments()),input.name());continue;
            }
            StrictJson.object(expected,Set.of("name","accepted","value"));assertTrue(expected.get("accepted").booleanValue());
            RawJson actual=actualKnowledge(input.arguments());ObjectNode business=ReligionCodec.object(actual);
            assertEquals(expected.get("value"),business,"entire original response: "+input.name());
            assertTrue(business.get("read_only").booleanValue());for(String field:List.of("requires_ck3","executes_action","state_observed","action_ready"))assertFalse(business.get(field).booleanValue());
            assertTrue(business.get("native_legality").isNull());
            String requested=business.get("requested_build").textValue();
            if(requested.equals(ReligionHolyKnowledge.BUILD)){assertEquals("available",business.get("status").textValue());assertTrue(business.get("knowledge").isObject());}
            else{assertEquals("unavailable",business.get("status").textValue());assertEquals("unsupported_build",business.get("qualification").textValue());assertTrue(business.get("knowledge").isNull());}
            var request=ReligionCodec.decode(KNOWLEDGE_METHOD,input.arguments());
            assertEquals(business,ReligionCodec.object(ReligionCodec.encode(new Response(request.method(),actual))));
            assertEquals(business,ReligionCodec.object(ReligionCodec.raw(ReligionCodec.object(actual))));
        }
    }

    @Test void exactPublicRequestAndStrictResultSerdeRejectCoercionDuplicateFieldsAndTrailingDocuments() {
        String valid="{\"action\":\"adopt\",\"ck3_build\":\"1.20.0.4\"}";
        var request=ReligionCodec.decode(KNOWLEDGE_METHOD,utf8(valid));
        assertEquals(request,ReligionCodec.decode(KNOWLEDGE_METHOD,ReligionCodec.encode(request)));
        for(String raw:List.of("{\"action\":\"adopt\",\"action\":\"create\"}","{\"action\":\"adopt\"} {}","null","[]"))
            assertThrows(RuntimeException.class,()->ReligionCodec.decode(KNOWLEDGE_METHOD,utf8(raw)));
        for(String raw:List.of("{\"knowledge\":null,\"knowledge\":{}}","{} {}","[]","null"))
            assertThrows(RuntimeException.class,()->ReligionCodec.object(utf8(raw)));
    }

    @Test void compiledOriginalReaderPacketsFeedWholeOriginalNormalizerThenTypedStateAndPublicSerde() throws Exception {
        List<NativeFixture> fixtures=nativeFixtures();List<StateInput> inputs=new ArrayList<>();
        for(NativeFixture fixture:fixtures) {
            inputs.add(stateInput(fixture,fixture.name(),fixture.body().deepCopy(),fixture.requested(),Expected.VALUE));
            assertEquals(fixture.name().equals("faith-unavailable.json"),!fixture.body().get("available").booleanValue());
            if(fixture.body().get("available").booleanValue()) {
                JsonNode ids=fixture.body().get("current_faith_holy_site_ids");assertEquals(2,ids.size());
                assertEquals(new BigInteger("2164260866"),ids.get(0).bigIntegerValue());assertEquals(ids.get(0),ids.get(1));
                if(fixture.name().equals("stale-generation.json")) {
                    assertFalse(fixture.body().get("selected_holy_site").get("available").booleanValue());
                    assertEquals("holy_site_full_reference_unavailable",fixture.body().get("selected_holy_site").get("unavailable_reason").textValue());
                }
            }
        }
        NativeFixture available=fixtures.get(0),unavailable=fixtures.get(3);ObjectNode n;
        // Signed actor mutation from a genuine packet, not live evidence.
        n=available.body().deepCopy();n.put("played_character_id",Integer.MIN_VALUE);ObjectNode signedSnapshot=available.snapshot().deepCopy();((ObjectNode)signedSnapshot.get("played_character")).put("character_id",Integer.MIN_VALUE);
        inputs.add(new StateInput("signed-int32-actor-boundary",n,signedSnapshot,available.revision(),available.requested(),Expected.VALUE));
        n=available.body().deepCopy();n.put("capture_epoch",new BigInteger("18446744073709551615"));inputs.add(stateInput(available,"maximum-uint64-epoch",n,available.requested(),Expected.VALUE));
        n=available.body().deepCopy();n.put("uninterpreted_source_extension","preserve original DATA");inputs.add(stateInput(available,"retained-source-extension",n,available.requested(),Expected.VALUE));
        n=unavailable.body().deepCopy();for(String key:List.of("current_faith_holy_site_ids","current_faith_sites","window_model","selected_holy_site","loaded_registry_roster"))n.remove(key);
        inputs.add(stateInput(unavailable,"unavailable-unattempted-children-normalize-to-null",n,unavailable.requested(),Expected.VALUE));
        for(JsonNode token:wrongScalarTokens()) {
            n=available.body().deepCopy();n.set("capture_epoch",token);inputs.add(stateInput(available,"epoch-wrong-type-"+inputs.size(),n,available.requested(),Expected.REJECT));
        }
        n=available.body().deepCopy();n.put("capture_epoch",0);inputs.add(stateInput(available,"zero-epoch",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();n.remove("capture_epoch");inputs.add(stateInput(available,"missing-epoch",n,available.requested(),Expected.REJECT));
        for(JsonNode token:List.of(JsonNodeFactory.instance.booleanNode(true),JsonNodeFactory.instance.numberNode(1.0),JsonNodeFactory.instance.numberNode(new BigInteger("4294967295")),JsonNodeFactory.instance.nullNode())) {
            n=available.body().deepCopy();((ArrayNode)n.get("current_faith_holy_site_ids")).set(0,token);inputs.add(stateInput(available,"native-id-wrong-type-or-sentinel-"+inputs.size(),n,available.requested(),Expected.REJECT));
        }
        n=available.body().deepCopy();((ArrayNode)n.get("current_faith_holy_site_ids")).set(0,JsonNodeFactory.instance.numberNode(new BigInteger("2181038083")));inputs.add(stateInput(available,"source-order-identity-mismatch",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();n.put("game_version","1.20.0.3");inputs.add(stateInput(available,"foreign-version-with-original-sha",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();n.put("executable_sha256","0".repeat(64));inputs.add(stateInput(available,"foreign-sha-with-original-version",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();n.put("played_character_id",n.get("played_character_id").bigIntegerValue().add(BigInteger.ONE));inputs.add(stateInput(available,"cross-player",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();n.put("date_raw",n.get("date_raw").bigIntegerValue().add(BigInteger.ONE));inputs.add(stateInput(available,"cross-date",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();n.put("adoption_legality_observed",true);inputs.add(stateInput(available,"identity-read-does-not-grant-adoption-legality",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();n.put("read_only",false);inputs.add(stateInput(available,"read-only-required",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();n.put("registry_roster_is_native_adoption_candidates",true);inputs.add(stateInput(available,"registry-is-not-adoption-candidates",n,available.requested(),Expected.REJECT));
        n=available.body().deepCopy();((ObjectNode)n.get("selected_holy_site").get("inventory")).putNull("artifact_ids");inputs.add(stateInput(available,"available-inventory-null-is-not-empty",n,available.requested(),Expected.REJECT));
        inputs.add(stateInput(available,"explicit-request-does-not-match-original",available.body().deepCopy(),Optional.of(new BigInteger("2181038083")),Expected.REJECT));
        ArrayNode requests=StrictJson.object().putArray("requests");
        for(StateInput input:inputs) {
            ObjectNode row=StrictJson.object();row.put("name",input.name());row.set("body",input.body());row.set("snapshot",input.snapshot());
            if(input.requested().isPresent())row.put("requested",input.requested().orElseThrow());else row.putNull("requested");requests.add(row);
        }
        Path requestFile=temp.resolve("state-normalizer-inputs.json");Files.writeString(requestFile,requests.toString(),StandardCharsets.UTF_8);
        List<ExactRef> sourcePins=originalInputs("source_refs");ObjectNode expected=oracle(STATE_ORACLE,"holy-state",sourcesJson(sourcePins),requestFile.toString());for(ExactRef source:sourcePins)verify(source);
        StrictJson.object(expected,Set.of("schema","cases"));assertEquals("xar.religion.original-python-holy-state-differential/v1",expected.get("schema").textValue());
        JsonNode rows=expected.get("cases");assertTrue(rows.isArray());assertEquals(inputs.size(),rows.size());
        for(int i=0;i<inputs.size();i++) {
            StateInput input=inputs.get(i);ObjectNode row=assertInstanceOf(ObjectNode.class,rows.get(i));assertEquals(input.name(),StrictJson.text(row.get("name")));
            assertTrue(row.get("input_unchanged").isBoolean()&&row.get("input_unchanged").booleanValue());ObjectNode before=input.body().deepCopy();
            if(input.expected()==Expected.REJECT) {
                StrictJson.object(row,Set.of("name","accepted","error_type","error","input_unchanged"));assertFalse(row.get("accepted").booleanValue());
                assertThrows(RuntimeException.class,()->actualState(input),input.name());
            } else {
                StrictJson.object(row,Set.of("name","accepted","value","input_unchanged"));assertTrue(row.get("accepted").booleanValue());
                ReligionHolyState.State state=actualState(input);ObjectNode normalized=ReligionCodec.object(state.originalNormalized());
                assertEquals(row.get("value"),normalized,"whole original native component response: "+input.name());
                ObjectNode projected=ReligionHolyReads.publicProjection(normalized);assertTrue(projected.get("capture_epoch").isTextual());
                assertEquals(normalized.get("capture_epoch").bigIntegerValue().toString(),projected.get("capture_epoch").textValue());
                ObjectNode everyOtherField=projected.deepCopy();everyOtherField.set("capture_epoch",normalized.get("capture_epoch"));assertEquals(normalized,everyOtherField);
                var publicRequest=stateRequest(input);RawJson publicResult=ReligionCodec.encode(new Response(publicRequest.method(),ReligionCodec.raw(projected)));
                assertEquals(projected,ReligionCodec.object(publicResult));assertEquals(projected,ReligionCodec.object(new RawJson(publicResult.bytes())));
                assertEquals(normalized,ReligionCodec.object(state.originalNormalized()),"public projection cannot mutate retained normalized source");
                if(!normalized.get("available").booleanValue()) {
                    assertTrue(state.currentFaithIds().isEmpty());assertTrue(state.currentFaithSites().isEmpty());
                    for(String key:List.of("current_faith_holy_site_ids","current_faith_sites","window_model","selected_holy_site","loaded_registry_roster"))assertTrue(normalized.has(key)&&normalized.get(key).isNull(),key);
                }else assertEquals(state.currentFaithIds().orElseThrow(),state.currentFaithSites().orElseThrow().stream().map(ReligionHolyState.Site::id).toList());
            }
            assertEquals(before,input.body(),"actual Java normalizer cannot rewrite original input: "+input.name());
        }
        for(NativeFixture fixture:fixtures){verify(fixture.packet());ObjectNode retained=ReligionCodec.object(new RawJson(Files.readAllBytes(Path.of(fixture.packet().path()))));assertEquals(fixture.original(),retained);}
    }

    @Test void holyStatePublicInputsKeepUnsignedRevisionAndFullReferenceDomainsSeparate() {
        ObjectNode n=StrictJson.object();n.put("expected_revision","18446744073709551615");n.put("holy_site_id",new BigInteger("4294967294"));
        Request request=ReligionCodec.decode(ReligionHolyReads.STATE,ReligionCodec.raw(n));assertEquals(new BigInteger("18446744073709551615"),request.expectedRevision());
        assertEquals(request,ReligionCodec.decode(ReligionHolyReads.STATE,ReligionCodec.encode(request)));
        assertTrue(ReligionCodec.object(ReligionCodec.encode(request)).get("expected_revision").isTextual());
        assertTrue(ReligionCodec.nativeArguments(request).get("expected_revision").isIntegralNumber());
        for(JsonNode token:List.of(JsonNodeFactory.instance.booleanNode(true),JsonNodeFactory.instance.numberNode(1.0),JsonNodeFactory.instance.numberNode(new BigInteger("4294967295")),JsonNodeFactory.instance.textNode("2164260866"))) {
            ObjectNode bad=n.deepCopy();bad.set("holy_site_id",token);assertThrows(RuntimeException.class,()->ReligionCodec.decode(ReligionHolyReads.STATE,ReligionCodec.raw(bad)));
        }
        for(String revision:List.of("18446744073709551616","-1","01")){ObjectNode bad=n.deepCopy();bad.put("expected_revision",revision);assertThrows(RuntimeException.class,()->ReligionCodec.decode(ReligionHolyReads.STATE,ReligionCodec.raw(bad)));}
        ObjectNode explicitNull=n.deepCopy();explicitNull.putNull("holy_site_id");Request withNull=ReligionCodec.decode(ReligionHolyReads.STATE,ReligionCodec.raw(explicitNull));
        ObjectNode absent=n.deepCopy();absent.remove("holy_site_id");Request missing=ReligionCodec.decode(ReligionHolyReads.STATE,ReligionCodec.raw(absent));assertNotEquals(withNull,missing);
        assertTrue(ReligionCodec.object(ReligionCodec.encode(withNull)).get("holy_site_id").isNull());assertFalse(ReligionCodec.object(ReligionCodec.encode(missing)).has("holy_site_id"));
    }

    private static ReligionHolyState.State actualState(StateInput input) {
        Request request=stateRequest(input);Optional<BigInteger> selected=request.value(Field.HOLY_SITE_ID) instanceof IntegerValue id?Optional.of(id.value()):Optional.empty();
        return ReligionHolyState.body(input.body(),input.revision(),input.snapshot().get("date_raw").bigIntegerValue(),input.snapshot().get("played_character").get("character_id").bigIntegerValue(),selected);
    }
    private static Request stateRequest(StateInput input) {
        ObjectNode request=StrictJson.object();request.put("expected_revision",input.revision().toString());input.requested().ifPresent(id->request.put("holy_site_id",id));
        Request decoded=ReligionCodec.decode(ReligionHolyReads.STATE,ReligionCodec.raw(request)),restored=ReligionCodec.decode(ReligionHolyReads.STATE,ReligionCodec.encode(decoded));assertEquals(decoded,restored);return restored;
    }
    private static StateInput stateInput(NativeFixture fixture,String name,ObjectNode body,Optional<BigInteger> requested,Expected expected) {
        return new StateInput(name,body,fixture.snapshot().deepCopy(),fixture.revision(),requested,expected);
    }
    private static List<NativeFixture> nativeFixtures() throws IOException {
        ObjectNode manifest=pinnedJson("xar.religion.holy.native.fixture.manifest","xar.fullParity.fixture.RELIGION_HOLY_STATE_NATIVE_SET.bytes");
        StrictJson.object(manifest,Set.of("schema","machine_id","observed_at_utc","producer","run_receipt","producer_sources","packets"));
        assertEquals("xar.religion.compiled-holy-state-fixture-set/v1",StrictJson.text(manifest.get("schema")));
        assertNotEquals("unknown",StrictJson.text(manifest.get("machine_id")));StrictJson.utc(StrictJson.text(manifest.get("observed_at_utc")));
        verify(ExactRef.fromJson(manifest.get("producer")));verify(ExactRef.fromJson(manifest.get("run_receipt")));
        List<ExactRef> actualSources=references(manifest.get("producer_sources"));for(ExactRef source:actualSources)verify(source);
        assertTrue(actualSources.containsAll(originalInputs("producer_source_refs")),"actual native fixture build must bind the original reader/serializer/fixture sources");
        Path directory=null;JsonNode packets=manifest.get("packets");assertTrue(packets.isArray());assertEquals(STATE_FIXTURES.size(),packets.size());
        List<NativeFixture> result=new ArrayList<>();Set<String> unique=new HashSet<>();
        for(JsonNode row:packets) {
            ObjectNode n=StrictJson.object(row,Set.of("name","packet"));String name=StrictJson.text(n.get("name"));assertTrue(STATE_FIXTURES.contains(name)&&unique.add(name));
            ExactRef ref=ExactRef.fromJson(n.get("packet"));Path file=Path.of(ref.path()).toRealPath();assertEquals(name,file.getFileName().toString());if(directory==null)directory=file.getParent();assertEquals(directory,file.getParent());verify(ref);
            assertTrue(ref.bytes()<=StrictJson.EXPLICIT_MAX_BYTES);ObjectNode packet=ReligionCodec.object(new RawJson(Files.readAllBytes(file)));verify(ref);
            assertEquals("command_result",StrictJson.text(packet.get("type")));assertTrue(packet.get("ok").isBoolean()&&packet.get("ok").booleanValue());
            ObjectNode envelope=assertInstanceOf(ObjectNode.class,packet.get("result")),body=assertInstanceOf(ObjectNode.class,envelope.get("player_holy_site"));
            assertEquals("query-player-holy-site-v1",StrictJson.text(envelope.get("step")));assertTrue(envelope.get("accepted").isBoolean()&&envelope.get("accepted").booleanValue());
            BigInteger revision=StrictJson.integer(envelope.get("snapshot_revision"),BigInteger.ONE,StrictJson.UINT64_MAX);
            ObjectNode snapshot=StrictJson.object();snapshot.put("native_revision",revision);snapshot.set("date_raw",body.get("date_raw"));snapshot.putObject("played_character").set("character_id",body.get("played_character_id"));
            ObjectNode hello=snapshot.putObject("diagnostics").putObject("hello");hello.set("expected_ck3_version",body.get("game_version"));hello.set("expected_ck3_sha256",body.get("executable_sha256"));
            Optional<BigInteger> selected=body.get("requested_holy_site_id").isNull()?Optional.empty():Optional.of(StrictJson.integer(body.get("requested_holy_site_id"),BigInteger.ZERO,new BigInteger("4294967294")));
            result.add(new NativeFixture(name,ref,packet,body,snapshot,revision,selected));
        }
        assertEquals(Set.copyOf(STATE_FIXTURES),unique);result.sort(java.util.Comparator.comparingInt(f->STATE_FIXTURES.indexOf(f.name())));return List.copyOf(result);
    }
    private static List<ExactRef> originalInputs(String field) throws IOException {
        ObjectNode manifest;
        try(var resource=ReligionCreationAdoptionKnowledgePythonParityTest.class.getResourceAsStream(ORIGINAL_STATE_INPUTS)){
            StrictJson.require(resource!=null,"NOT_RUN_REQUIRED_ORIGINAL_INPUT: selected static original-state-inputs resource");
            byte[] bytes=resource.readNBytes(StrictJson.EXPLICIT_MAX_BYTES+1);StrictJson.require(bytes.length==2959&&ActionCodec.sha256(bytes).equals("43cf0c585e93888ddd61a55bb686e982a8c54a1d6dc16d8c112fb43dd4b2eea5"),"selected original state source-input resource drift");manifest=ReligionCodec.object(new RawJson(bytes));
        }
        StrictJson.object(manifest,Set.of("schema","machine_id","observed_at_utc","source_refs","producer_source_refs"));
        assertEquals("xar.religion.original-python-state-inputs/v1",StrictJson.text(manifest.get("schema")));assertNotEquals("unknown",StrictJson.text(manifest.get("machine_id")));StrictJson.utc(StrictJson.text(manifest.get("observed_at_utc")));
        List<ExactRef> sources=references(manifest.get(field));for(ExactRef source:sources)verify(source);return sources;
    }
    private static List<ExactRef> references(JsonNode rows) {
        assertTrue(rows.isArray()&&!rows.isEmpty());List<ExactRef> refs=new ArrayList<>();Set<String> paths=new HashSet<>();for(JsonNode row:rows){ExactRef ref=ExactRef.fromJson(row);assertTrue(paths.add(ref.path()));refs.add(ref);}return List.copyOf(refs);
    }
    private static ObjectNode pinnedJson(String prefix,String bytesProperty) throws IOException {
        ExactRef ref=new ExactRef(required(prefix),Long.parseLong(required(bytesProperty)),required(prefix+".sha256"));assertTrue(Path.of(ref.path()).isAbsolute());verify(ref);assertTrue(ref.bytes()<=StrictJson.EXPLICIT_MAX_BYTES);
        ObjectNode json=ReligionCodec.object(new RawJson(Files.readAllBytes(Path.of(ref.path()))));verify(ref);return json;
    }
    private static void verify(ExactRef ref) throws IOException {new FileRef(ref.path(),ref.bytes(),ref.sha256()).verify();}
    private static List<JsonNode> wrongScalarTokens(){return List.of(JsonNodeFactory.instance.booleanNode(true),JsonNodeFactory.instance.numberNode(1.0),JsonNodeFactory.instance.textNode("1"),JsonNodeFactory.instance.nullNode());}

    private static RawJson actualKnowledge(RawJson arguments) {
        Request request=ReligionCodec.decode(KNOWLEDGE_METHOD,arguments);
        Request restored=ReligionCodec.decode(KNOWLEDGE_METHOD,ReligionCodec.encode(request));assertEquals(request,restored);
        String action=textValue(restored,Field.ACTION,null),build=textValue(restored,Field.CK3_BUILD,ReligionHolyKnowledge.BUILD);
        RawJson actual=ReligionHolyKnowledge.query(ReligionHolyKnowledge.Action.parse(action),build);
        return ReligionCodec.encode(new Response(restored.method(),actual));
    }
    private static String textValue(Request request,Field field,String absent) {
        if(request.value(field) instanceof TextValue value)return value.value();
        if(request.value(field) instanceof Absent)return absent;
        throw new IllegalArgumentException("original text parameter required: "+field);
    }
    private ObjectNode oracle(String script,String tag,String... arguments) throws Exception {
        String python=required("xar.python"),root=required("xar.repository.root");
        StrictJson.require(Path.of(python).isAbsolute()&&Path.of(root).isAbsolute(),"absolute original Python and repository roots required");
        List<String> command=new ArrayList<>(List.of(python,"-I","-B","-X","utf8","-c",script,root));command.addAll(List.of(arguments));
        Path out=temp.resolve(tag+".json"),err=temp.resolve(tag+".stderr");
        ProcessBuilder builder=new ProcessBuilder(command).redirectOutput(out.toFile()).redirectError(err.toFile());
        builder.environment().put("PYTHONPATH",Path.of(root).resolve("ck3_autonomous_player/src").toString());builder.environment().put("XAR_SOURCE_REPOSITORY",root);builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();
        if(!process.waitFor(60,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original full-response oracle timed out: "+tag);}
        if(process.exitValue()!=0){try(var failure=Files.newInputStream(err)){throw new IOException("original full-response oracle failed: "+new String(failure.readNBytes(8192),StandardCharsets.UTF_8));}}
        StrictJson.require(Files.size(out)>0&&Files.size(out)<=StrictJson.EXPLICIT_MAX_BYTES,"bounded complete original response required");return ReligionCodec.object(new RawJson(Files.readAllBytes(out)));
    }
    private static String sourcesJson(List<ExactRef> sources) throws IOException {
        StrictJson.require(!sources.isEmpty(),"original complete source closure required");Set<String> unique=new HashSet<>();ArrayNode rows=StrictJson.object().putArray("sources");Path root=Path.of(required("xar.repository.root")).toRealPath();
        for(ExactRef source:sources){StrictJson.require(unique.add(source.path()),"original source repeated");StrictJson.require(Path.of(source.path()).toRealPath().startsWith(root),"oracle import root differs from pinned original source root");verify(source);rows.add(source.toJson());}
        return rows.toString();
    }
    private static RawJson utf8(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static String required(String property){String value=System.getProperty(property);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_INPUT: -D"+property);return value;}
}
