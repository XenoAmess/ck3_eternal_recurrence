package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.*;
import java.math.BigInteger;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;

/** Mandatory unchanged Python producer and retained actual serializer packet differential. Authored source; Root executes. */
final class ArmyStrengthsPhasesParityTest {
 private static final ObjectMapper JSON=new ObjectMapper();
 private static JsonNode CORPUS,MANIFEST;
 private static final String PRODUCER="""
import copy,hashlib,importlib,json,runpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(sys.argv[1]); manifest=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
for item in manifest['original_sources']:
 p=Path(item['path']); data=p.read_bytes()
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],str(p)
 if 'relative' in item: assert (root/item['relative']).resolve()==p.resolve(),str(p)
# Read pinned source bytes rather than accepting an existing timestamp-based bytecode cache.
import importlib.machinery
def exact_source_code(loader,fullname):
 return loader.source_to_code(loader.get_data(loader.path),loader.path)
importlib.machinery.SourceFileLoader.get_code=exact_source_code
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
from xar_autoplayer.bridge.war_contract import normalize_actual_army_late_event_observations_v1 as late,normalize_actual_compiled_effect_observations_v1 as compiled
from xar_autoplayer.bridge.army_observed_phase_contract_12004 import FAMILIES,normalize_army_observed_phase_family_12004 as normal
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
cases=[]
def emit(name,source):
 original=copy.deepcopy(source); row=copy.deepcopy(source)
 full=row['native_carmy_id']
 for field in FAMILIES:
  if field in row: row[field]=normal(field,row[field],expected_carmy_id=full)
 for field,fn in [('actual_army_late_event_observations_v1',late),('actual_compiled_effect_observations_v1',compiled)]:
  if field in row: row[field]=fn(row[field],expected_carmy_id=full)
 raw={'army_strengths':[row],'query_sequence':37,'source':{'game_version':CK3_12004.game_version,'executable_sha256':CK3_12004.executable_sha256}}
 snapshot={'diagnostics':{'hello':{'expected_ck3_version':CK3_12004.game_version,'expected_ck3_sha256':CK3_12004.executable_sha256}}}
 outputs=GameplayBridgeService._native71_army_projection_rows(raw,[row],snapshot=snapshot)
 assert source==original
 cases.append({'name':name,'row':row,'original':source,'raw':raw,'outputs':outputs})
for item in manifest['original_sources']:
 if item.get('role')=='query_packet':
  packet=json.loads(Path(item['path']).read_text(encoding='utf-8'))
  for i,row in enumerate(packet['army_strengths']): emit('serializer:'+item['label']+':'+str(i),row)
 if item.get('role')=='owned_phase_packet':
  packet=json.loads(Path(item['path']).read_text(encoding='utf-8'))
  for i,subject in enumerate(packet['subjects']):
   full=subject['captured_subject_full_carmy_id_u32']
   row={'army_id':11,'native_carmy_id':full if full<0x80000000 else full-0x100000000}
   for field in FAMILIES:
    if field in subject: row[field]=subject[field]
   emit('owned-readout:'+str(i),row)
assert len(cases)>=4
monthly=[]
import xar_autoplayer.bridge.army_ordered_monthly_core_12004 as core
sys.modules['army_ordered_monthly_core_12004']=core
module=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_army_ordered_monthly_core_12004.py'))
g=module['stage'].__globals__; original=g['project_army_ordered_monthly_core_12004']
def capture(stage):
 before=copy.deepcopy(stage)
 try:
  result=original(stage)
 except ValueError:
  monthly.append({'stage':before,'reject':True}); raise
 assert stage==before
 monthly.append({'stage':before,'reject':False,'output':result})
 return result
g['project_army_ordered_monthly_core_12004']=capture
suite=module['OrderedMonthlyCore12004Tests']()
suite.test_all_manager_occurrences_share_physical_state_then_refresh_in_original_order()
assert len(monthly)>=5
print(json.dumps({'cases':cases,'monthly':monthly},separators=(',',':')))
""";
 private static synchronized JsonNode corpus() throws Exception {
  if(CORPUS!=null)return CORPUS;
  String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root"),manifest=System.getProperty("xar.phases.source.manifest"),manifestSha=System.getProperty("xar.phases.source.manifest.sha256");
  assertNotNull(python,"Required -Dxar.python; actual producer cannot be skipped");
  assertNotNull(repository,"Required -Dxar.repository.root");
  assertNotNull(manifest,"Required -Dxar.phases.source.manifest=.../ORIGINAL-SOURCES01.json");
  assertNotNull(manifestSha,"Required -Dxar.phases.source.manifest.sha256; manifest path cannot self-authorize");
  assertTrue(manifestSha.matches("[a-f0-9]{64}"),"manifest digest must be canonical lowercase SHA256");
  byte[] manifestBytes=Files.readAllBytes(Path.of(manifest));
  assertEquals(manifestSha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(manifestBytes)),"original source manifest was replaced");
  MANIFEST=JSON.readTree(manifestBytes);
  for(JsonNode pin:MANIFEST.get("original_sources"))assertPin(pin);
  for(JsonNode pin:MANIFEST.get("java_sources"))assertPin(pin);
  Path directory=Files.createTempDirectory("army-phases-original-"),out=directory.resolve("stdout.json"),err=directory.resolve("stderr.txt");Process child=null;
  try{child=new ProcessBuilder(python,"-B","-c",PRODUCER,Path.of(repository).toAbsolutePath().normalize().toString(),Path.of(manifest).toAbsolutePath().normalize().toString()).redirectOutput(out.toFile()).redirectError(err.toFile()).start();assertTrue(child.waitFor(60,TimeUnit.SECONDS),"actual unchanged original producer timed out");assertEquals(0,child.exitValue(),()->diagnostic(err));assertTrue(Files.size(out)>0&&Files.size(out)<=16L*1024*1024,"bounded original producer output required");CORPUS=JSON.readTree(Files.readAllBytes(out));return CORPUS;}finally{if(child!=null&&child.isAlive()){child.destroyForcibly();child.waitFor(5,TimeUnit.SECONDS);}Files.deleteIfExists(out);Files.deleteIfExists(err);Files.deleteIfExists(directory);}
 }
 private static void assertPin(JsonNode pin)throws Exception{byte[] b=Files.readAllBytes(Path.of(pin.get("path").textValue()));assertEquals(pin.get("bytes").longValue(),b.length,pin.get("path").textValue());assertEquals(pin.get("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)),pin.get("path").textValue());}
 private static String diagnostic(Path p){try{return Files.readString(p,StandardCharsets.UTF_8);}catch(Exception x){return x.toString();}}
 private static JsonNode domain(JsonNode v){if(v.isIntegralNumber())return BigIntegerNode.valueOf(v.bigIntegerValue());if(v.isArray()){ArrayNode a=JSON.createArrayNode();v.forEach(n->a.add(domain(n)));return a;}if(v.isObject()){ObjectNode o=JSON.createObjectNode();v.properties().iterator().forEachRemaining(e->o.set(e.getKey(),domain(e.getValue())));return o;}return v;}
 private static RawJson raw(JsonNode node){return new RawJson(ArmyJson.bytes(node));}
 private static List<ArmyStrengthsFamilies.Key> keys(){return List.of(ACTUAL_ARMY_LATE_EVENT_OBSERVATIONS_V1,ACTUAL_COMPILED_EFFECT_OBSERVATIONS_V1,ARMY_NATURAL_PHASE_OBSERVATIONS_V1,ACTUAL_ARMY_REGULAR_CORE_OBSERVATIONS_V1,ACTUAL_ARMY_DAILY_ASSAULT_PREPARATION_OBSERVATIONS_V1,ACTUAL_ARMY_ASSAULT_PLACEMENT_OBSERVATIONS_V1,ARMY_ACTUAL_ASSAULT_CONSUMER_OBSERVATIONS_V1,ACTUAL_ARMY_ASSAULT_GROUP_RELEASE_OBSERVATIONS_V1,NATIVE_GATHERING_DUE_NATURAL_STAGE_12004,ACTUAL_ARMY_CLEANUP_OBSERVATIONS_V1,ACTUAL_ARMY_PRE_DATE_PREFIX_OBSERVATIONS_V1);}
 private record Installed(ArmyStrengthsFamilies.Registry registry,ArmyStrengthsPipeline pipeline) { }
 private static Installed installed()throws Exception{corpus();JsonNode pin=null;for(JsonNode value:MANIFEST.get("java_sources"))if(value.get("path").textValue().endsWith("/ArmyStrengthsPhases.java"))pin=value;assertNotNull(pin);ExactRef source=new ExactRef(pin.get("path").textValue(),pin.get("bytes").longValue(),pin.get("sha256").textValue());var registry=new ArmyStrengthsFamilies.Registry();var pipeline=new ArmyStrengthsPipeline();ArmyStrengthsPhases.install(registry,pipeline,source);registry.freeze();pipeline.freeze();assertEquals(11,registry.coverage().installed().size()-1);assertEquals(4,pipeline.coverage().installed().size());return new Installed(registry,pipeline);}
 private static Row row(JsonNode normalized,Installed installed){int army=normalized.get("army_id").intValue(),nativeId=normalized.get("native_carmy_id").intValue();Core core=new Core(Status.AVAILABLE,new PublicUnitId(army),new Present<>(new FullId(nativeId)),Role.PLAYER,List.of(),new Present<>(0),new Present<>(0),new Present<>(0),new Present<>(0L),new NullValue<>());var context=new RowContext(core,new Missing<>());List<FamilyValue<?>> families=new ArrayList<>();for(var key:keys()){JsonNode value=normalized.get(key.wire());Field<RawJson> actual=value==null?new Missing<>():value.isNull()?new NullValue<>():new Present<>(raw(value));families.add(installed.registry().normalize(key,actual,context));}return new Row(core,List.of(),new Missing<>(),new Missing<>(),families);}
 private static ArmyStrengthsPipeline.Input input(ObjectNode original,Row row)throws Exception{var base=ArmyStrengthsSourceTest.input(original,ArmyStrengthsSourceTest.projectedHello());Read read=new Read(base.original().profile(),base.original().status(),BigInteger.valueOf(37),base.original().backendId(),List.of(row),base.original().timing(),base.original().publishedScopeStatus(),base.original().original());return new ArmyStrengthsPipeline.Input(base.snapshot(),read,base.query(),List.of(row),base.originalHello());}
 @Test void retainedActualSerializerThroughEveryTypedNormalizerAndAllFourConsumers()throws Exception{var installed=installed();for(JsonNode test:corpus().get("cases")){JsonNode original=test.get("row"),untouched=original.deepCopy();Row row=row(original,installed);ObjectNode roundTrip=ArmyStrengthsCodec.rowJson(row);for(var key:keys()){JsonNode expected=original.get(key.wire());if(expected==null)assertFalse(roundTrip.has(key.wire()),test.get("name").asText()+key);else assertEquals(domain(expected),domain(roundTrip.get(key.wire())),test.get("name").asText()+key);if(expected!=null&&!expected.isNull()){var f=row.families().stream().filter(v->v.key()==key).findFirst().orElseThrow();assertEquals(domain(expected),domain(ArmyStrengthsCodec.parseValue(f.normalizedJson())));assertTrue(ArmyStrengthsCodec.parseValue(f.publicV2Json()).isObject());}}
   var results=installed.pipeline().projectAvailable(input((ObjectNode)test.get("raw"),row));ObjectNode actual=results.topLevelJson();for(var stage:ArmyStrengthsPipeline.Stage.values())if(stage.ordinal()>=ArmyStrengthsPipeline.Stage.EXPLICIT_OBSERVED_ARMY_STAGE_PROJECTIONS_12004.ordinal()){assertEquals(domain(test.get("outputs").get(stage.wire())),domain(actual.get(stage.wire())),test.get("name").asText()+stage);assertNotNull(results.topLevelPublicV2Json().get(stage.wire()));}
   assertEquals(domain(untouched),domain(original),"original owned source changed");}}
 @Test void unchangedOriginalMonthlyProducerCoversDuplicatesFallbackAndIndependentRefresh()throws Exception{for(JsonNode item:corpus().get("monthly")){ObjectNode before=((ObjectNode)item.get("stage")).deepCopy();if(item.get("reject").booleanValue())assertThrows(IllegalArgumentException.class,()->ArmyMonthlyCore.project(before));else assertEquals(domain(item.get("output")),domain(ArmyMonthlyCore.project(before).json()));assertEquals(domain(item.get("stage")),domain(before),"historical stage was mutated");}}
 @Test void missingExtraBooleanAndFloatingTokensCannotCrossAnyOwnedBoundary()throws Exception{var installed=installed();Set<ArmyStrengthsFamilies.Key> covered=EnumSet.noneOf(ArmyStrengthsFamilies.Key.class);for(JsonNode test:corpus().get("cases")){Row row=row(test.get("row"),installed);var context=new RowContext(row.core(),row.regiments());for(var key:keys()){JsonNode value=test.get("row").get(key.wire());if(value==null||value.isNull()||!covered.add(key))continue;ObjectNode actual=(ObjectNode)value;List<String> fields=new ArrayList<>();actual.fieldNames().forEachRemaining(fields::add);for(String field:fields){ObjectNode missing=actual.deepCopy();missing.remove(field);assertThrows(IllegalArgumentException.class,()->installed.registry().normalize(key,new Present<>(raw(missing)),context),key+" missing "+field);}ObjectNode extra=actual.deepCopy().put("unexpected_owned_field",1);assertThrows(IllegalArgumentException.class,()->installed.registry().normalize(key,new Present<>(raw(extra)),context));List<String> path=numberPath(actual,new ArrayList<>());assertNotNull(path,key+" must expose at least one numeric field");for(JsonNode bad:List.of(BooleanNode.TRUE,DoubleNode.valueOf(1.0))){ObjectNode malformed=actual.deepCopy();replace(malformed,path,bad);assertThrows(IllegalArgumentException.class,()->installed.registry().normalize(key,new Present<>(raw(malformed)),context),key+" wrong integer token");}var nil=installed.registry().normalize(key,new NullValue<>(),context);assertInstanceOf(NullValue.class,nil.value());var absent=installed.registry().normalize(key,new Missing<>(),context);assertInstanceOf(Missing.class,absent.value());}}
  assertEquals(11,covered.size(),"retained actual producers must cover all eleven owned families");}
 private static List<String> numberPath(JsonNode n,List<String> prefix){if(n.isIntegralNumber())return prefix;if(n.isObject()){var fields=n.properties().iterator();while(fields.hasNext()){var e=fields.next();List<String> p=new ArrayList<>(prefix);p.add(e.getKey());var found=numberPath(e.getValue(),p);if(found!=null)return found;}}if(n.isArray())for(int i=0;i<n.size();i++){List<String> p=new ArrayList<>(prefix);p.add(Integer.toString(i));var found=numberPath(n.get(i),p);if(found!=null)return found;}return null;}
 private static void replace(JsonNode root,List<String> path,JsonNode value){JsonNode at=root;for(int i=0;i<path.size()-1;i++)at=at.isArray()?at.get(Integer.parseInt(path.get(i))):at.get(path.get(i));String key=path.getLast();if(at.isArray())((ArrayNode)at).set(Integer.parseInt(key),value);else ((ObjectNode)at).set(key,value);}
 @Test void publicUnsigned64RetainsExactMaximumAndDoesNotChangeNativeDomain()throws Exception{corpus();ObjectNode journal=JSON.createObjectNode().put("source","native_natural_late_event_dispatch_entry_return").put("membership_basis","current_full_carmy_id_join").put("observer_installed",false).put("oldest_available_sequence",BigInteger.ONE.shiftLeft(64).subtract(BigInteger.valueOf(256))).put("latest_sequence",BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)).put("overwritten_events",BigInteger.ONE.shiftLeft(64).subtract(BigInteger.valueOf(257))).put("unattributed_capture_failures",0).put("event_count",0);journal.putArray("events");var decoded=ArmyNaturalEffectJournals.late(journal,11);assertEquals(domain(journal),domain(decoded.toJson()));RawJson nativeValue=raw(decoded.toJson());JsonNode publicValue=ArmyStrengthsCodec.parseValue(ArmyPhasePublicNumbers.late(nativeValue));assertEquals("18446744073709551615",publicValue.get("latest_sequence").textValue());assertTrue(ArmyStrengthsCodec.parseValue(nativeValue).get("latest_sequence").isIntegralNumber());}
}
