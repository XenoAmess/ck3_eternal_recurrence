package org.xar.ck3.control.application.capabilities;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;

public final class CampaignRootContextJsonTest {
 private static final String PRODUCER_SHA="06fa8e6399672106409a8f840ee96e8c1897b09688176a8704484bd18e6cb3f3";
 private static final String FIXTURE_SHA="602e8b19cfdca2af35bb8723bdb445114005695a3280390516b5a4fc30e8ce82";
 @Test void originalPythonProducerMatchesFullBaselineMaterialAbsentAndInvalidBranches() throws Exception {
  for(Value item:array(oracle().get("cases"),"cases")) {
   Obj row=object(item,"case");BigInteger date=integer(row.get("date"),"date"),revision=integer(row.get("revision"),"revision");
   if(bool(row.get("accepted"),"accepted")) {
    Obj normalized=CampaignRootContextJson.normalize(row.get("raw"),date,revision);
    assertEquals(row.get("normalized"),normalized,text(row.get("label"),"label"));
    assertEquals(normalized,DriverJson.object(encode(normalized),1_048_576));
   } else assertThrows(IllegalArgumentException.class,()->CampaignRootContextJson.normalize(row.get("raw"),date,revision),text(row.get("label"),"label"));
  }
 }
 @Test void actualNativeEnvelopeRequiresExactFieldsAndSnapshotBeforeTheCacheProducer() throws Exception {
  Obj example=object(array(oracle().get("cases"),"cases").getFirst(),"case");Obj root=object(example.get("raw"),"root");
  Obj nativeResult=new Obj(Map.of("step",new Text("query-campaign-root-context-v1"),"accepted",new Bool(true),"status",root.get("status"),
      "query_sequence",new IntegerValue(BigInteger.ONE),"snapshot_revision",root.get("snapshot_revision"),"campaign_root_context",root,"backend_id",new Text("native-headless")));
  BigInteger date=integer(root.get("date_raw"),"date_raw"),revision=integer(root.get("snapshot_revision"),"snapshot_revision");
  assertThrows(IllegalArgumentException.class,()->CampaignRootContextJson.normalize(root.with("schema_version",new Bool(true)),date,revision));
  assertEquals(root,CampaignRootContextJson.normalizeNativeResult(nativeResult,date,revision).get("campaign_root_context"));
  for(Obj invalid:List.of(nativeResult.with("accepted",new IntegerValue(BigInteger.ONE)),nativeResult.with("query_sequence",new Bool(true)),
      nativeResult.with("snapshot_revision",new IntegerValue(revision.add(BigInteger.ONE))),nativeResult.with("extra",Nil.INSTANCE)))
   assertThrows(IllegalArgumentException.class,()->CampaignRootContextJson.normalizeNativeResult(invalid,date,revision));
 }
 /** Original immutable test DATA for consumer regressions; this confers no native or writer authority. */
 public static Obj originalActual4RootFixture() throws Exception {
  for(Value item:array(oracle().get("cases"),"cases")) {
   Obj row=object(item,"case");
   if(new Text("full 1.20.0.4").equals(row.get("label")))return object(row.get("raw"),"original actual4 root");
  }
  throw new AssertionError("original actual4 root fixture is absent");
 }
 private static Obj oracle() throws Exception {
  Path repository=Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
  Path source=repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py");
  Path fixture=repository.resolve("ck3_autonomous_player/tests/unit/test_campaign_root_context_v1_bridge.py");
  assertEquals(PRODUCER_SHA,DriverJson.sha256(Files.readAllBytes(source)));assertEquals(FIXTURE_SHA,DriverJson.sha256(Files.readAllBytes(fixture)));
  String script="""
   import ast,copy,hashlib,json,pathlib,sys
   sys.dont_write_bytecode=True
   repo=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src'))
   from xar_autoplayer.bridge import campaign_root_context_contract as producer
   assert pathlib.Path(producer.__file__).resolve()==pathlib.Path(sys.argv[2]).resolve()
   fixture=ast.parse(pathlib.Path(sys.argv[3]).read_text(encoding='utf-8'))
   names={'_readiness','_provenance','_related_contexts','_council','_frame'}
   namespace=dict(vars(producer));namespace.update({'NATIVE_REVISION':17,'DATE_RAW':53182008,'PLAYER_CHARACTER_ID':12345})
   definitions=[n for n in fixture.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
   exec(compile(ast.Module(body=definitions,type_ignores=[]),str(sys.argv[3]),'exec'),namespace)
   base=namespace['_frame']();cases=[]
   def add(label,raw):
    row={'label':label,'raw':copy.deepcopy(raw),'date':53182008,'revision':17}
    try:row.update(accepted=True,normalized=producer.normalize_campaign_root_context_v1(raw,expected_date_raw=row['date'],expected_snapshot_revision=row['revision']))
    except (ValueError,TypeError,KeyError):row.update(accepted=False)
    cases.append(row)
   add('full original fixture',base)
   for build,provenance in producer._PROVENANCE_BY_BUILD.items():
    value=copy.deepcopy(base);value['provenance']=dict(provenance);add('full '+build,value)
    if build in producer._BASELINE_PROVENANCE_BY_BUILD:
     value={k:v for k,v in value.items() if k in producer._BASELINE_12002_FIELDS}
     value['provenance']=dict(producer._BASELINE_PROVENANCE_BY_BUILD[build]);value['readiness']={k:True for k in producer._BASELINE_12002_READINESS};add('baseline '+build,value)
   add('unavailable full',namespace['_frame']('unavailable'))
   for key,observation in [('player_legitimacy_v1',{'status':'available','value':{'raw':2**63-1,'scale':100000},'unavailable_reason':None}),('player_max_monthly_gold_maintenance_v1',{'status':'unavailable','value':None,'unavailable_reason':'getter_failed'}),('player_monthly_piety_v1',{'status':'available','value':{'raw':-(2**63),'scale':100000},'unavailable_reason':None})]:
    value=copy.deepcopy(base);value[key]=observation;add(key,value)
   value=copy.deepcopy(base)
   for row in value['held_title_partition']:row.pop('capital_province_id')
   add('legacy partition becomes explicit null',value)
   for component in [None,{},True,{'SDK_parse_status':'unknown','unavailable_reason':'kept original unavailable'}]:
    value=copy.deepcopy(base);value['player_heir_candidate_v1']=component;add('optional heir '+repr(component),value)
   mutations=[('schema_version',2),('date_raw',False),('snapshot_revision',17.0),('player_character_id',False),('player_domain_limit',0),('selected_game_rule_tokens',['z','a']),('native_selected_game_rule_token_count',False),('unavailable_reason','invented'),('primary_title',{'title_id':1,'tier_raw':6,'tier_key':'kingdom'})]
   for key,bad in mutations:
    value=copy.deepcopy(base);value[key]=bad;add('invalid '+key,value)
   for key in list(base):
    value=copy.deepcopy(base);del value[key];add('missing '+key,value)
   for path,bad in [(('player_health','scale'),True),(('readiness','same_frame_ready'),False),(('provenance','primary_title_rva'),'0x1'),(('government','native_flag_count'),2)]:
    value=copy.deepcopy(base);value[path[0]][path[1]]=bad;add('invalid nested '+'.'.join(path),value)
   print(json.dumps({'cases':cases},ensure_ascii=False,separators=(',',':')))
   """;
  ProcessBuilder builder=new ProcessBuilder(required("xar.native.producer.python"),"-I","-B","-c",script,repository.toString(),source.toString(),fixture.toString());
  builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Process child=builder.start();
  try {
   var output=java.util.concurrent.CompletableFuture.supplyAsync(()->read(child.getInputStream()));
   var error=java.util.concurrent.CompletableFuture.supplyAsync(()->read(child.getErrorStream()));
   assertTrue(child.waitFor(30,TimeUnit.SECONDS),"original campaign-root producer timed out");byte[] bytes=output.get(5,TimeUnit.SECONDS);
   assertEquals(0,child.exitValue(),new String(error.get(5,TimeUnit.SECONDS),StandardCharsets.UTF_8));return DriverJson.object(bytes,1_048_576);
  } finally {if(child.isAlive())child.destroyForcibly();}
 }
 private static byte[] read(java.io.InputStream in){try{return in.readAllBytes();}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}}
 private static String required(String key){String value=System.getProperty(key);assertTrue(value!=null&&!value.isBlank(),"original producer differential NOT RUN: missing "+key);return value;}
}
