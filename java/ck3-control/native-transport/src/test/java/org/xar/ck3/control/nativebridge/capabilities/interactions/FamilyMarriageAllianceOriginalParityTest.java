package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding.Selection;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageResults.*;

/** Executes unmodified original Python query producers. Native/world/material authority remain separately unqualified. */
final class FamilyMarriageAllianceOriginalParityTest {
    @TempDir Path temporary;
    @Test void originalThreeRoutesBothRelationshipsAndEveryBilateralStateMatchTypedCodecAndWire() throws Exception {
        ObjectNode capture=capture();verifySources(capture);assertEquals(30,capture.withArray("cases").size());
        for(JsonNode row:capture.withArray("cases")){
            FamilyMarriageAlliance.Binding binding=binding(row);RawJson original=encode(object(row.get("native")));
            var typed=FamilyMarriageAlliance.decodeNative(original,binding);
            assertEquals(row.get("native"),parse(FamilyMarriageAlliance.encodeNative(typed)),row.get("name").textValue());
            assertEquals(row.get("normalized"),OpportunityJson.toNode(FamilyMarriageAlliance.normalized(typed)),row.get("name").textValue());
            assertEquals(row.get("native_fields"),parse(FamilyMarriageAllianceQueries.nativeFields(binding)),"actual original request payload");
            byte[] packet=NativeWire.execute("alliance-parity",FamilyMarriageAlliance.step(binding.route()),binding.nativeRevision(),FamilyMarriageAllianceQueries.nativeFields(binding).bytes());
            ObjectNode wire=object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)));wire.remove("request_id");assertEquals(row.get("native_request"),wire,"complete original outer request and exact revision");
            assertEquals(typed,FamilyMarriageAlliance.decodeNormalized(FamilyMarriageAlliance.normalized(typed),binding,false));
            Obj projected=FamilyMarriageAlliance.project(typed);assertEquals(typed,FamilyMarriageAlliance.decodeNormalized(projected,binding,true));
            JsonNode tuple=OpportunityJson.toNode(projected);assertEquals(binding.snapshotId(),tuple.get("queried_snapshot_id").textValue());
            assertEquals(binding.publicRevision(),tuple.get("queried_revision").bigIntegerValue());assertEquals(binding.nativeRevision(),tuple.get("queried_native_revision").bigIntegerValue());
        }
        for(JsonNode row:capture.withArray("rejections"))assertFalse(row.get("accepted").booleanValue(),row.get("name").textValue());
    }
    @Test void malformedWireAndFalseOneDirectionCannotPublishTypedAlliance() throws Exception {
        ObjectNode capture=capture();JsonNode example=capture.withArray("cases").get(0);var binding=binding(example);ObjectNode good=object(example.get("native"));
        for(String field:List.of("native_revision","played_character_id","recipient_character_id","heir_character_id","candidate_character_id")){
            for(JsonNode invalid:List.of(F.booleanNode(true),F.numberNode(1.0),F.textNode("1"))){ObjectNode bad=good.deepCopy();bad.set(field,invalid);assertThrows(IllegalArgumentException.class,()->FamilyMarriageAlliance.decodeNative(encode(bad),binding));}
            ObjectNode missing=good.deepCopy();missing.remove(field);assertThrows(IllegalArgumentException.class,()->FamilyMarriageAlliance.decodeNative(encode(missing),binding));
        }
        ObjectNode extra=good.deepCopy().put("unreviewed",0);assertThrows(IllegalArgumentException.class,()->FamilyMarriageAlliance.decodeNative(encode(extra),binding));
        ObjectNode oneWay=good.deepCopy().put("alliance_status","allied").put("played_has_recipient_alliance",true).put("recipient_has_played_alliance",false);
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageAlliance.decodeNative(encode(oneWay),binding));
        oneWay.put("alliance_status","unknown");assertEquals(FamilyMarriageAlliance.AllianceStatus.UNKNOWN,FamilyMarriageAlliance.decodeNative(encode(oneWay),binding).status());
        for(String field:List.of("accepted","private_build","read_only")){ObjectNode bad=good.deepCopy().put(field,false);assertThrows(IllegalArgumentException.class,()->FamilyMarriageAlliance.decodeNative(encode(bad),binding));}
        ObjectNode wrongRoute=good.deepCopy().put("step",FamilyMarriageAlliance.step(Route.DEFAULT));assertThrows(IllegalArgumentException.class,()->FamilyMarriageAlliance.decodeNative(encode(wrongRoute),binding));
        ObjectNode wrongToken=good.deepCopy().put("alliance_status","ALLIED");assertThrows(IllegalArgumentException.class,()->FamilyMarriageAlliance.decodeNative(encode(wrongToken),binding));
        Obj normalized=FamilyMarriageAlliance.normalized(FamilyMarriageAlliance.decodeNative(encode(good),binding));
        ObjectNode changed=object(OpportunityJson.toNode(normalized)).deepCopy().put("exe_sha256","0".repeat(64));
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageAlliance.decodeNormalized(application(changed),binding,false));
    }
    @Test void threeInstalledDefinitionsHaveExplicitPureReplayAndNoFabricatedAdvertisedCapability() throws Exception {
        Path repo=repository();Path cpp=repo.resolve("ck3_autonomous_player/native_bridge/src/bridge.cpp");ExactRef source=reference(cpp);
        var authority=new FamilyDomainReadBinding.Authority(){
            @Override public FamilyDomainReadBinding current(Session same,Slot slot,Selection selection,Obj selected)throws IOException{throw new AssertionError("registration cannot acquire material custody");}
            @Override public Obj verifyCurrent(PlanningReadRequest request,FamilyDomainReadBinding binding,Selection selection,Obj selected)throws IOException{throw new AssertionError("registration cannot grant live admission");}
            @Override public Obj verifyOriginal(PlanningReadReceipt receipt,FamilyDomainReadBinding binding,Selection selection,Obj selected)throws IOException{throw new AssertionError("registration cannot replay a missing receipt");}
        };
        var definitions=new FamilyMarriageAllianceQueries.Definitions(source,source,source);var contracts=FamilyMarriageAllianceQueries.contracts(definitions,authority);
        assertEquals(3,contracts.all().size());for(Route route:Route.values()){
            var contract=contracts.forRoute(route);assertEquals(FamilyMarriageAllianceQueries.query(route).operation(),contract.operation());
            assertTrue(contract.hasPureReplay());assertTrue(contract.requiredCapability().isEmpty());assertEquals(ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,contract.permissionMode());
            assertEquals(ReadContract.WireProfile.EXECUTE_STEP,contract.wireProfile());assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,contract.guardMode());assertEquals(source,contract.sourceRef());
        }
        assertNotSame(contracts.family(),contracts.matrilineal());assertNotSame(contracts.defaultAlliance(),contracts.matrilineal());
    }
    @Test void completeResolvedMaterialKeepsItsActualLargePendingHistoryAcrossSharedIngress() {
        ObjectNode pending=F.objectNode().put("schema",Route.FAMILY.schema()).put("status","receipt_pending").put("material_result",false)
            .put("played_character_id",29829).put("recipient_character_id",32266).put("heir_character_id",38822).put("candidate_character_id",38710)
            .put("pre_native_revision",692).put("source_date_raw",53215919);
        var history=pending.putArray("prior_attempted_candidate_ids");for(int identity=70000;identity<100000;identity++)history.add(identity);
        ObjectNode resolved=F.objectNode().put("status","betrothal").put("material_result",true).put("heir_character_id",38822).put("candidate_character_id",38710);
        resolved.set("source_pending",pending);Obj complete=application(resolved);assertTrue(resolved.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length>128*1024);
        var typed=FamilyMarriageResults.decodeResolved(Route.FAMILY,complete);assertEquals(complete,typed.original());
        assertEquals(30000,OpportunityJson.toNode(typed.pending().original()).get("prior_attempted_candidate_ids").size());
        assertEquals(resolved,InteractionArguments.parseApp(complete));
    }
    private static FamilyMarriageAlliance.Binding binding(JsonNode row){
        return new FamilyMarriageAlliance.Binding(Route.valueOf(row.get("route").textValue()),Build.CROZIER4,"alliance-offline-fixture",BigInteger.valueOf(1001),BigInteger.valueOf(693),BigInteger.valueOf(53215920),
            BigInteger.valueOf(29829),BigInteger.valueOf(32266),BigInteger.valueOf(38822),BigInteger.valueOf(38710),Relationship.valueOf(row.get("relationship").textValue()));
    }
    private ObjectNode capture() throws Exception {
        Path repo=repository();String python=System.getProperty("xar.python");assertNotNull(python,"xar.python required; actual original producer is mandatory");
        Path out=temporary.resolve("original-"+System.nanoTime()+".json"),log=temporary.resolve("python-"+System.nanoTime()+".log");
        Process child=new ProcessBuilder(python,"-B","-c",PYTHON,repo.toString(),out.toString()).directory(repo.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        if(!child.waitFor(90,TimeUnit.SECONDS)){child.destroyForcibly();fail("original alliance producer timed out");}
        assertEquals(0,child.exitValue(),()->{try{return Files.readString(log);}catch(IOException failed){return failed.toString();}});assertTrue(Files.size(out)<1024*1024);
        return parse(new RawJson(Files.readAllBytes(out)));
    }
    private static Path repository() throws Exception {String root=System.getProperty("xar.repository.root");assertNotNull(root,"xar.repository.root required; no original golden fallback");return Path.of(root).toRealPath();}
    private static void verifySources(ObjectNode capture) throws Exception {
        assertEquals("xar.family-alliance.original-producers/v1",text(capture,"schema"));assertFalse(bool(capture,"actual_game_observed"));assertFalse(text(capture,"machine_id").isBlank());Path repo=repository();
        assertTrue(capture.withArray("sources").size()>=4);for(JsonNode ref:capture.withArray("sources")){Path path=Path.of(text(ref,"path")).toRealPath();assertTrue(path.startsWith(repo));byte[] body=Files.readAllBytes(path);assertEquals(body.length,ref.get("bytes").longValue());assertEquals(text(ref,"sha256"),digest(body));}
    }
    private static ExactRef reference(Path path)throws Exception{byte[] body=Files.readAllBytes(path);return new ExactRef(path.toRealPath().toString(),body.length,digest(body));}
    private static String digest(byte[] value)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
    private static Obj application(ObjectNode value){return org.xar.ck3.control.application.driver.DriverJson.object(value.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);}
    private static final String PYTHON="""
import sys,json,hashlib
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
repo=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'tools')]
import ck3_live_run_id
from xar_autoplayer.bridge import observed_heir_marriage_private_action_v1 as family
from xar_autoplayer.bridge import player_child_matrilineal_private_action_v1 as child
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.driver import BridgeUnavailableError
paths=[Path(family.__file__).resolve(),Path(child.__file__).resolve(),repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py',repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py',repo/'ck3_autonomous_player/native_bridge/src/bridge.cpp']
def pin(path):
 body=path.read_bytes();return dict(path=str(path),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
sources=[pin(path) for path in paths]
def frame():return dict(native_revision=693,paused=True,map_ready=True,revision=1001,date_raw=53215920,played_character=dict(character_id=29829,alive=True),diagnostics=dict(hello=dict(expected_ck3_version=CK3_12004.game_version,expected_ck3_sha256=CK3_12004.executable_sha256)))
class Driver:
 allow_private_player_child_default_action=True
 def __init__(self,result,after=None):self.result=result;self.frames=[frame(),after or frame()];self.requests=[];self.endpoint=self;self.state=self
 def take_snapshot(self):return self.frames.pop(0)
 def send(self,request):self.requests.append(deepcopy(request))
 def wait_for_command_result(self,request_id,timeout):return dict(ok=True,result=self.result)
def sample(route,relationship,status,sides):
 schema=family.SCHEMA if route=='FAMILY' else child.SCHEMA if route=='MATRILINEAL' else child.DEFAULT_SCHEMA
 step=family.ALLIANCE_RESULT_STEP if route=='FAMILY' else child.ALLIANCE_RESULT_STEP if route=='MATRILINEAL' else child.DEFAULT_ALLIANCE_RESULT_STEP
 pending=dict(schema=schema,played_character_id=29829,recipient_character_id=32266,heir_character_id=38822,candidate_character_id=38710,matrilineal_option_selected=route=='MATRILINEAL')
 resolved=dict(status=relationship,material_result=True,heir_character_id=38822,candidate_character_id=38710,source_pending=pending)
 result=dict(step=step,accepted=True,private_build=True,advertised=False,read_only=True,native_revision=693,played_character_id=29829,recipient_character_id=32266,heir_character_id=38822,candidate_character_id=38710,relationship_status=relationship,alliance_status=status,played_has_recipient_alliance=sides[0],recipient_has_played_alliance=sides[1])
 return resolved,result
def invoke(route,driver,resolved):
 if route=='FAMILY':return family.query_observed_first_heir_marriage_alliance_result_private_v1(driver,resolved=resolved,recipient_character_id=32266)
 return child.query_player_child_matrilineal_alliance_private_v1(driver,resolved=resolved,default_route=route=='DEFAULT')
cases=[];rejections=[]
for route in ('FAMILY','MATRILINEAL','DEFAULT'):
 for relationship in ('marriage','betrothal'):
  for status,sides in (('allied',(True,True)),('not_allied',(False,False)),('unknown',(None,None)),('unknown',(True,False)),('unknown',(False,True))):
   resolved,native=sample(route,relationship,status,sides);driver=Driver(native);normalized=invoke(route,driver,resolved)
   assert len(driver.requests)==1 and not driver.frames
   wire={key:value for key,value in driver.requests[0].items() if key not in ('type','protocol_version','request_id','step','expected_revision')}
   request={key:value for key,value in driver.requests[0].items() if key!='request_id'}
   cases.append(dict(name=route+'-'+relationship+'-'+status+'-'+str(sides),route=route,relationship=relationship.upper(),native=native,normalized=normalized,native_fields=wire,native_request=request))
 for kind in ('nonmaterial','wrong-pair','one-way-claimed-allied','native-revision-drift','post-frame-drift'):
  resolved,native=sample(route,'betrothal','allied',(True,True));after=None
  if kind=='nonmaterial':resolved['material_result']=False
  elif kind=='wrong-pair':native['candidate_character_id']=1
  elif kind=='one-way-claimed-allied':native['recipient_has_played_alliance']=False
  elif kind=='native-revision-drift':native['native_revision']=694
  elif kind=='post-frame-drift':after={**frame(),'native_revision':694}
  try:invoke(route,Driver(native,after),resolved);accepted=True
  except BridgeUnavailableError:accepted=False
  rejections.append(dict(name=route+'-'+kind,accepted=accepted))
assert sources==[pin(path) for path in paths]
receipt=dict(schema='xar.family-alliance.original-producers/v1',machine_id=ck3_live_run_id.current_machine_id(),observed_at_utc=datetime.now(timezone.utc).isoformat(),actual_game_observed=False,sources=sources,cases=cases,rejections=rejections)
out.write_text(json.dumps(receipt,ensure_ascii=False)+chr(10),encoding='utf-8')
""";
}
