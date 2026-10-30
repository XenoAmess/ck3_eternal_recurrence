package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageResults.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Unchanged Python producer differential plus source-only authored receipt/replay regressions. Root executes. */
final class FamilyMarriageResultsTest {
    private static JsonNode CORPUS;
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final String PRODUCER="""
import copy,hashlib,importlib.machinery,json,pathlib,sys
sys.dont_write_bytecode=True
root=pathlib.Path(sys.argv[1]);manifest=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
for pin in manifest['original_sources']:
 p=pathlib.Path(pin['path']);b=p.read_bytes()
 assert len(b)==pin['bytes'] and hashlib.sha256(b).hexdigest()==pin['sha256'],str(p)
 if 'relative' in pin:assert (root/pin['relative']).resolve()==p.resolve()
def exact_source_code(loader,fullname):
 return loader.source_to_code(loader.get_data(loader.path),loader.path)
importlib.machinery.SourceFileLoader.get_code=exact_source_code
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from xar_autoplayer.bridge import observed_heir_marriage_private_action_v1 as family
from xar_autoplayer.bridge import player_child_matrilineal_private_action_v1 as child
from xar_autoplayer.bridge.version_identity import CK3_12004
snapshot={'native_revision':11,'revision':56,'snapshot_id':'native:11','date_raw':53219928,'paused':True,'map_ready':True,'played_character':{'character_id':29829,'alive':True},'diagnostics':{'hello':{'expected_ck3_version':CK3_12004.game_version,'expected_ck3_sha256':CK3_12004.executable_sha256}}}
cases=[]
for route in ['FAMILY','MATRILINEAL','DEFAULT']:
 for cold in [False,True]:
  for fulfillment in ([False,True] if route=='FAMILY' else [False]):
   statuses=['pending','marriage']+([] if fulfillment else ['betrothal'])
   if not cold:statuses+=['accepted_pending','refused','invalidated']
   if route=='DEFAULT' and cold:statuses+=['gone_unmaterialized']
   for status in statuses:
    states=['active','absent','ambiguous','unavailable'] if cold and status=='pending' else ['absent'] if status=='gone_unmaterialized' else ['not_applicable'] if cold else [None]
    for state in states:
     schema=family.SCHEMA if route=='FAMILY' else child.SCHEMA if route=='MATRILINEAL' else child.DEFAULT_SCHEMA
     step=family.RESULT_STEP if route=='FAMILY' else child.RESULT_STEP if route=='MATRILINEAL' else child.DEFAULT_RESULT_STEP
     pending={'schema':schema,'schema_version':1,'status':'receipt_pending','material_result':False,'played_character_id':29829,'heir_character_id':38822,'candidate_character_id':16778038,'recipient_character_id':38713,'pre_native_revision':10,'source_date_raw':53219920,'matrilineal_option_selected':route=='MATRILINEAL','fulfill_existing_betrothal':fulfillment,'episode_run_id':'result-test-episode'}
     raw={'step':step,'accepted':True,'private_build':True,'advertised':False,'status':status,'material_result':status in ['marriage','betrothal'],'cold_recovery':cold,'pre_native_revision':0 if cold else 10,'post_native_revision':11,'heir_character_id':38822,'candidate_character_id':16778038,'recipient_character_id':38713,'matrilineal_option_selected':route=='MATRILINEAL','fulfill_existing_betrothal':fulfillment,'original_extension':{'exact_large_integer':18446744073709551615,'empty':[],'null':None}}
     if state is not None:
      raw.update(outbound_pending_state=state,outbound_pending_id=-2013265918 if state=='active' else None,outbound_pending_age_days=6 if state=='active' else None,outbound_pending_ai_reply_cutoff_days=9 if state=='active' else None)
     if status=='gone_unmaterialized':
      raw.update(proposal_disposition_source='native_outbound_and_bilateral_pair',terminal_cause_available=False,terminal_cause='not_observed')
     class Driver:
      allow_private_player_child_matrilineal_action=True
      allow_private_player_child_default_action=True
      def __init__(self):self.endpoint=self;self.state=self;self.requests=[];self.root_reads=0;self.child_reads=0
      def take_snapshot(self):return copy.deepcopy(snapshot)
      take_snapshot_without_native_command_history=take_snapshot
      def send(self,request):self.requests.append(copy.deepcopy(request))
      def wait_for_command_result(self,request_id,timeout):return {'ok':True,'result':copy.deepcopy(raw)}
      def _execute_campaign_root_context_v1_query(self,**kw):self.root_reads+=1;return {'status':'available','held_title_partition':[{'primary':True,'first_heir_character_id':38822}]}
      def query_player_child_marriage_subject_private_v1(self,**kw):self.child_reads+=1;return {'player_child_verified':True}
     driver=Driver();original=copy.deepcopy(pending)
     expected=(family.query_observed_first_heir_marriage_cold_result_private_v1(driver,pending=pending) if cold else family.query_observed_first_heir_marriage_result_private_v1(driver,pending=pending)) if route=='FAMILY' else child.query_player_child_matrilineal_result_private_v1(driver,pending=pending,cold=cold,default_route=route=='DEFAULT')
     assert pending==original and len(driver.requests)==1
     request=driver.requests[0]
     cases.append({'route':route,'cold':cold,'pending':pending,'native':raw,'expected':expected,'payload':{k:v for k,v in request.items() if k not in ['type','protocol_version','request_id','step']},'root_reads':driver.root_reads,'child_reads':driver.child_reads})
     if route!='FAMILY' and cold and status=='pending' and state=='active':
      earlier=copy.deepcopy(pending);earlier['source_date_raw']=-1;driver=Driver()
      earlier_result=child.query_player_child_matrilineal_result_private_v1(driver,pending=earlier,cold=True,default_route=route=='DEFAULT')
      request=driver.requests[0]
      cases.append({'route':route,'cold':True,'pending':earlier,'native':raw,'expected':earlier_result,'payload':{k:v for k,v in request.items() if k not in ['type','protocol_version','request_id','step']},'root_reads':driver.root_reads,'child_reads':driver.child_reads})
assert len(cases)>=40
import runpy
fixture=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_campaign_root_context_v1_bridge.py'))
producer=fixture['_native_result'];producer.__globals__.update(NATIVE_REVISION=11,DATE_RAW=53219928,PLAYER_CHARACTER_ID=29829)
native_root=producer();body=native_root['campaign_root_context'];body['provenance']=copy.deepcopy(fixture['_PROVENANCE_BY_BUILD']['1.20.0.4'])
body['held_title_partition'][0]['first_heir_character_id']=38822;body['primary_title_succession_character_ids'][0]=38822
fixture['normalize_campaign_root_context_v1'](body,expected_date_raw=53219928,expected_snapshot_revision=11)
cases[0]['cold_root_native']=native_root
print(json.dumps(cases,sort_keys=True,separators=(',',':')))
""";
    private static synchronized JsonNode corpus()throws Exception {
        if(CORPUS!=null)return CORPUS;
        String root=required("xar.repository.root"),python=required("xar.python"),path=required("xar.family.result.source.manifest"),sha=required("xar.family.result.source.manifest.sha256");
        assertTrue(sha.matches("[a-f0-9]{64}"));byte[] bytes=Files.readAllBytes(Path.of(path));
        assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),"source manifest replaced");
        JsonNode manifest=NativeWire.parse(bytes);for(JsonNode pin:manifest.get("original_sources"))pin(pin);for(JsonNode pin:manifest.get("java_sources"))pin(pin);
        Path directory=Files.createTempDirectory("family-result-original-"),out=directory.resolve("out.json"),err=directory.resolve("err.txt");Process process=null;
        try{var builder=new ProcessBuilder(python,"-B","-c",PRODUCER,Path.of(root).toAbsolutePath().normalize().toString(),Path.of(path).toAbsolutePath().normalize().toString()).redirectOutput(out.toFile()).redirectError(err.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");process=builder.start();if(!process.waitFor(45,TimeUnit.SECONDS)){process.destroyForcibly();throw new AssertionError("original family result producer timeout");}assertEquals(0,process.exitValue(),()->read(err));assertTrue(Files.size(out)>0&&Files.size(out)<2*1024*1024);CORPUS=NativeWire.parse(Files.readAllBytes(out));assertTrue(CORPUS.isArray());return CORPUS;}finally{if(process!=null&&process.isAlive()){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);}Files.deleteIfExists(out);Files.deleteIfExists(err);Files.deleteIfExists(directory);}
    }
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"Required -D"+key+"; actual producer must not skip");assertFalse(value.isBlank());return value;}
    private static String read(Path path){try{return Files.readString(path);}catch(Exception e){return e.toString();}}
    private static void pin(JsonNode pin)throws Exception{byte[] bytes=Files.readAllBytes(Path.of(pin.get("path").textValue()));assertEquals(pin.get("bytes").longValue(),bytes.length);assertEquals(pin.get("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));}
    private static Context context(){var source=new G2Source("synthetic-result-machine",NOW.toString(),Build.CROZIER4.sha256(),ref("source"));var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(11),BigInteger.valueOf(53219928)),"native:11",BigInteger.valueOf(56),"result-test-episode");return new Context(new ObservationIdentity(source.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1),source,"synthetic-result-session",BigInteger.TWO,Build.CROZIER4,NOW.plusSeconds(30),new ControlFrame(true,true,true,1,19L,29829,"result-test-episode",false,null,null,List.of()));}
    private static ExactRef ref(String name){return new ExactRef("synthetic/"+name,1,"a".repeat(64));}
    private static Obj obj(JsonNode node){return InteractionArguments.app(object(node));}
    private static RawJson raw(JsonNode node){return encode(object(node));}
    private static Route route(JsonNode test){return Route.valueOf(test.get("route").textValue());}
    @Test void unchangedOriginalProducerAllThreeRoutesWarmColdFulfillmentAndGone()throws Exception {
        EnumSet<Route> routes=EnumSet.noneOf(Route.class);Set<String> states=new HashSet<>();boolean fulfillment=false,gone=false;
        for(JsonNode test:corpus()){
            Route route=route(test);routes.add(route);boolean cold=test.get("cold").booleanValue();Pending pending=decodePending(route,obj(test.get("pending")));
            var actual=FamilyMarriageResults.decode(raw(test.get("native")),context(),pending,cold);
            assertEquals(test.get("expected"),OpportunityJson.toNode(project(actual,context())));
            ObjectNode fields=object(NativeWire.parse(nativeFields(context(),pending,cold).bytes()));fields.put("expected_revision",context().revision());
            assertEquals(test.get("payload"),fields,"reserved wire revision plus exact original additional fields");
            assertEquals(test.get("pending"),OpportunityJson.toNode(verifyPending(pending)));
            assertEquals(actual,FamilyMarriageResults.decode(new RawJson(OpportunityJson.encode(obj(OpportunityJson.toNode(actual.original())))),context(),pending,cold));
            if(cold)states.add(test.get("native").get("outbound_pending_state").textValue());
            fulfillment|=pending.fulfillExistingBetrothal();gone|=actual.status()==Status.GONE_UNMATERIALIZED;
            assertEquals(cold&&route==Route.FAMILY?1:0,test.get("root_reads").intValue());
            assertEquals(cold&&route!=Route.FAMILY?1:0,test.get("child_reads").intValue());
        }
        assertEquals(EnumSet.allOf(Route.class),routes);assertEquals(Set.of("active","absent","ambiguous","unavailable","not_applicable"),states);assertTrue(fulfillment);assertTrue(gone);
    }
    @Test void missingFieldsWrongIntegerTokensCrossPairAndWrongMaterialFlagsAreRejected()throws Exception {
        for(Route route:Route.values()){
            JsonNode test=first(route,false);Pending pending=decodePending(route,obj(test.get("pending")));
            for(String key:List.of("step","accepted","private_build","advertised","status","material_result","cold_recovery","pre_native_revision","post_native_revision","heir_character_id","candidate_character_id")){
                ObjectNode malformed=object(test.get("native")).deepCopy();malformed.remove(key);assertThrows(IllegalArgumentException.class,()->FamilyMarriageResults.decode(raw(malformed),context(),pending,false),route+" missing "+key);
            }
            for(String key:List.of("pre_native_revision","post_native_revision","heir_character_id","candidate_character_id"))for(JsonNode bad:List.of(F.booleanNode(true),F.numberNode(1.0),F.textNode("11"))){
                ObjectNode malformed=object(test.get("native")).deepCopy();malformed.set(key,bad);assertThrows(IllegalArgumentException.class,()->FamilyMarriageResults.decode(raw(malformed),context(),pending,false),route+" wrong "+key);
            }
            ObjectNode wrong=object(test.get("native")).deepCopy().put("candidate_character_id",38823);assertThrows(IllegalArgumentException.class,()->FamilyMarriageResults.decode(raw(wrong),context(),pending,false));
            ObjectNode material=object(test.get("native")).deepCopy().put("material_result",!test.get("native").get("material_result").booleanValue());assertThrows(IllegalArgumentException.class,()->FamilyMarriageResults.decode(raw(material),context(),pending,false));
            ObjectNode uppercase=object(test.get("native")).deepCopy().put("status","PENDING");assertThrows(IllegalArgumentException.class,()->FamilyMarriageResults.decode(raw(uppercase),context(),pending,false));
        }
    }
    @Test void originalMissingNullAndUnknownDiagnosticExtensionsSurviveWithoutGrantingMaterialCredit()throws Exception {
        JsonNode test=first(Route.FAMILY,false);ObjectNode packet=object(test.get("native")).deepCopy();packet.remove("recipient_character_id");packet.remove("matrilineal_option_selected");packet.remove("fulfill_existing_betrothal");
        Pending pending=decodePending(Route.FAMILY,obj(test.get("pending")));Observation absent=FamilyMarriageResults.decode(raw(packet),context(),pending,false);
        assertEquals(Presence.MISSING,absent.recipientCharacterId().presence());assertFalse(OpportunityJson.toNode(project(absent,context())).has("recipient_character_id"));
        packet.putNull("recipient_character_id");Observation nil=FamilyMarriageResults.decode(raw(packet),context(),pending,false);assertEquals(Presence.NULL,nil.recipientCharacterId().presence());assertTrue(OpportunityJson.toNode(project(nil,context())).get("recipient_character_id").isNull());
        assertEquals("18446744073709551615",OpportunityJson.toNode(project(nil,context())).get("original_extension").get("exact_large_integer").bigIntegerValue().toString());
        assertFalse(nil.materialResult());assertThrows(IllegalArgumentException.class,()->decodeResolved(Route.FAMILY,project(nil,context())));
    }
    @Test void goneUnmaterializedRemainsOnlyTheActualColdDefaultAbsentDisposition()throws Exception {
        JsonNode test=null;for(JsonNode c:corpus())if(c.get("native").get("status").textValue().equals("gone_unmaterialized")){test=c;break;}assertNotNull(test);
        Pending pending=decodePending(Route.DEFAULT,obj(test.get("pending")));JsonNode original=test.get("native");
        for(String key:List.of("proposal_disposition_source","terminal_cause_available","terminal_cause","outbound_pending_state")){
            ObjectNode bad=object(original).deepCopy();if(key.equals("terminal_cause_available"))bad.put(key,true);else bad.put(key,"invented");
            assertThrows(IllegalArgumentException.class,()->FamilyMarriageResults.decode(raw(bad),context(),pending,true));
        }
        ObjectNode warm=object(original).deepCopy().put("cold_recovery",false).put("pre_native_revision",10);assertThrows(IllegalArgumentException.class,()->FamilyMarriageResults.decode(raw(warm),context(),pending,false));
        ObjectNode active=object(original).deepCopy().put("outbound_pending_state","active").put("outbound_pending_id",-2013265918).put("outbound_pending_age_days",6).put("outbound_pending_ai_reply_cutoff_days",9);assertThrows(IllegalArgumentException.class,()->FamilyMarriageResults.decode(raw(active),context(),pending,true));
    }
    @Test void materialViewPreservesFullLedgerIncludingEarlierAllianceAndRejectsForgedTypedPending()throws Exception {
        for(Route route:Route.values()){
            JsonNode test=null;for(JsonNode c:corpus())if(route(c)==route&&c.get("native").get("status").textValue().equals("marriage")){test=c;break;}assertNotNull(test);
            Pending pending=decodePending(route,obj(test.get("pending")));ObjectNode result=object(test.get("expected")).deepCopy();result.set("source_pending",test.get("pending"));result.putObject(route==Route.FAMILY?"alliance_result":"actual_alliance_result").put("retained","original");
            Resolved resolved=decodeResolved(route,obj(result));assertEquals(Relationship.MARRIAGE,resolved.relationship());assertEquals(result,OpportunityJson.toNode(verifyResolved(resolved)));
            Pending forged=new Pending(route,pending.playedCharacterId(),pending.subjectCharacterId(),pending.candidateCharacterId().add(BigInteger.ONE),pending.recipientCharacterId(),pending.preNativeRevision(),pending.sourceDateRaw(),pending.matrilinealOptionSelected(),pending.fulfillExistingBetrothal(),pending.original());
            assertThrows(IllegalArgumentException.class,()->nativeFields(context(),forged,false));
        }
    }
    private static JsonNode first(Route route,boolean cold)throws Exception{for(JsonNode test:corpus())if(route(test)==route&&test.get("cold").booleanValue()==cold&&!test.get("pending").get("fulfill_existing_betrothal").booleanValue())return test;throw new AssertionError("actual producer case missing");}
    private static FamilyMarriageResultQueries installation(AtomicInteger live,AtomicInteger archived) {
        var child=new ReadContract<Obj>("family:child-subject",new OperationKey(FamilyChildMarriageSubject.STEP),Optional.empty(),"allow_private_player_child_marriage_subject_query",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,ref("child-definition"),(r,id)->{throw new AssertionError("unexpected native child query");},r->{throw new AssertionError("unexpected live child decoder");},r->{throw new IllegalArgumentException("no controlled archived child proof in this warm test");});
        var authority=new FamilyMarriageResultQueries.Authority(){public void verifyCurrent(PlanningReadRequest r,Route route,Obj a){live.incrementAndGet();}public void verifyOriginal(PlanningReadReceipt r,Route route,Obj a){archived.incrementAndGet();}};
        var originals=new FamilyMarriageResultQueries.Originals(){public PlanningReadReceipt loadRead(ExactRef ref){throw new IllegalArgumentException("no actual original child in this controlled test");}public ExactRef referenceOf(PlanningReadReceipt receipt){throw new AssertionError("unexpected original lookup");}};
        return new FamilyMarriageResultQueries(new FamilyMarriageResultQueries.Sources(ref("family-source"),ref("child-source")),authority,r->{throw new IllegalArgumentException("no actual original root in this controlled test");},originals,child);
    }
    private static Obj arguments(JsonNode test,Optional<ExactRef> proof) {
        Route route=route(test);Slot slot=switch(route){case FAMILY->Slot.FAMILY;case MATRILINEAL->Slot.CHILD_MATRILINEAL;case DEFAULT->Slot.DEFAULT_MARRIAGE;};
        ObjectNode flat=F.objectNode().put("cold",test.get("cold").booleanValue()).put("expected_revision",56);flat.set("pending",test.get("pending"));
        flat.set("original_domain",OpportunityJson.toNode(new FamilyDomainReadBinding(slot,ref("domain"),7,"b".repeat(64)).toJson()));
        return FamilyMarriageResultQueries.canonicalArguments(context(),obj(flat),proof);
    }
    private static PlanningReadRequest request(Route route,Obj arguments){Context c=context();return new PlanningReadRequest(c.before(),c.source(),c.sessionId(),new OperationKey(route.step()),arguments,c.deadline());}
    private static PlanningReadReceipt receipt(Route route,PlanningReadRequest request,JsonNode result)throws Exception {return receipt(FamilyMarriageResultQueries.contractId(route),request,result);}
    private static PlanningReadReceipt receipt(String contractId,PlanningReadRequest request,JsonNode result)throws Exception {
        String id="synthetic-family-result";var e=new GuardEvidence(context().before(),context().source(),context().sessionId(),context().connectionGeneration(),request.operation(),ref("native"),ref("hello"),"synthetic-result-authority",NOW,NOW.plusSeconds(30));var g=new PlanningReadGuard(e,true,true,true,"c".repeat(64));
        ObjectNode frame=F.objectNode().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);frame.set("result",result);
        RawJson packet=raw(frame);return new PlanningReadReceipt(request,contractId,id,g,g,new NativeActionPort.AckReceived(id,true,Optional.of(raw(result)),packet,NativeWire.packet(packet.bytes())));
    }
    @Test void sameInstalledContractsPrepareExactWireAndExplicitReplayNeverCallsLiveAdmission()throws Exception {
        AtomicInteger live=new AtomicInteger(),archived=new AtomicInteger();var installation=installation(live,archived);
        for(Route route:Route.values()){
            JsonNode test=first(route,false);Obj args=arguments(test,Optional.empty());var request=request(route,args);var contract=installation.definitions().forRoute(route);
            assertTrue(contract.hasPureReplay());assertTrue(contract.requiredCapability().isEmpty());assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,contract.guardMode());
            NativeRequest prepared=contract.prepare(request,"synthetic-family-result");byte[] wire=NativeWire.execute("synthetic-family-result",route.step(),context().revision(),prepared.additionalFields().bytes());
            JsonNode encoded=NativeWire.parse(Arrays.copyOfRange(wire,4,wire.length));ObjectNode expected=object(test.get("payload")).deepCopy();expected.put("type","execute_step").put("protocol_version",1).put("request_id","synthetic-family-result").put("step",route.step());assertEquals(NativeWire.parse(raw(expected).bytes()),encoded);
            var original=receipt(route,request,test.get("native"));Obj replayed=contract.replay(original);assertEquals(test.get("expected").get("status"),OpportunityJson.toNode(replayed).get("status"));assertEquals(BigInteger.valueOf(56),OpportunityJson.toNode(replayed).get("queried_revision").bigIntegerValue());
            assertEquals(replayed,contract.replay(original));assertEquals(replayed,contract.decode(original));
            var wrong=receipt(route,request,object(test.get("native")).deepCopy().put("post_native_revision",12));assertThrows(IllegalArgumentException.class,()->contract.replay(wrong));
        }
        assertEquals(3,live.get());assertEquals(12,archived.get());
    }
    @Test void actualSharedCampaignRootProducerClosesColdFirstHeirReplayAndRefusesChangedHeir()throws Exception {
        Context c=context();JsonNode packet=corpus().get(0).get("cold_root_native");assertNotNull(packet);
        var rootRequest=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),new OperationKey("query-campaign-root-context-v1"),obj(F.objectNode()),c.deadline());
        PlanningReadReceipt rootReceipt=receipt("ordinary-finance-read:ROOT",rootRequest,packet);ExactRef rootRef=ref("actual-shared-campaign-root");
        Obj normalized=CampaignRootContextJson.normalizeNativeResult(obj(packet),c.date(),c.revision());ObjectNode value=object(OpportunityJson.toNode(normalized));
        value.put("queried_snapshot_id",c.before().frame().snapshotId()).put("queried_revision",c.before().frame().revision()).put("queried_native_revision",c.revision());
        var known=new PlanningReadResult.Known<>(obj(value),rootReceipt,rootRef);AtomicInteger reopened=new AtomicInteger();
        ExactRef futureRootRef=ref("future-shared-campaign-root");var futureKnown=new PlanningReadResult.Known<>(known.value(),laterProof(rootReceipt),futureRootRef);
        Map<ExactRef,PlanningReadResult.Known<Obj>> rootOriginals=Map.of(rootRef,known,futureRootRef,futureKnown);
        FamilyRootBinding.Originals roots=ref->{reopened.incrementAndGet();return Objects.requireNonNull(rootOriginals.get(ref));};
        var childArchive=new FamilyChildMarriageQueries.Originals(){public PlanningReadReceipt loadRead(ExactRef ref){throw new AssertionError("first-heir result must not read child");}public ExactRef referenceOf(PlanningReadReceipt receipt){throw new AssertionError("first-heir result must not read child");}};
        var child=new FamilyChildMarriageQueries(new FamilyChildMarriageQueries.Sources(ref("subject-native"),ref("value-native")),childArchive,r->{throw new AssertionError("first-heir replay cannot submit child query");});
        var authority=new FamilyMarriageResultQueries.Authority(){public void verifyCurrent(PlanningReadRequest request,Route route,Obj args){}public void verifyOriginal(PlanningReadReceipt receipt,Route route,Obj args){}};
        var originals=new FamilyMarriageResultQueries.Originals(){public PlanningReadReceipt loadRead(ExactRef ref){throw new AssertionError("first-heir must use actual shared Root projection");}public ExactRef referenceOf(PlanningReadReceipt receipt){throw new AssertionError("first-heir must use actual shared Root projection");}};
        var results=new FamilyMarriageResultQueries(new FamilyMarriageResultQueries.Sources(ref("family-native"),ref("child-native")),authority,roots,originals,child.subject());
        JsonNode test=first(Route.FAMILY,true);var request=request(Route.FAMILY,arguments(test,Optional.of(rootRef)));var contract=results.definitions().family();assertNotNull(contract.prepare(request,"cold-family-result"));
        Obj replay=contract.replay(receipt(Route.FAMILY,request,test.get("native")));assertEquals(test.get("expected").get("status"),OpportunityJson.toNode(replay).get("status"));assertEquals(2,reopened.get());
        var futureRequest=request(Route.FAMILY,arguments(test,Optional.of(futureRootRef)));assertThrows(IllegalArgumentException.class,()->contract.replay(receipt(Route.FAMILY,futureRequest,test.get("native"))),"same-frame root proof from after the original result is not its input");
        ObjectNode changed=object(test.get("pending")).deepCopy().put("heir_character_id",38823);ObjectNode flat=F.objectNode().put("cold",true).put("expected_revision",56);flat.set("pending",changed);flat.set("original_domain",OpportunityJson.toNode(new FamilyDomainReadBinding(Slot.FAMILY,ref("domain"),7,"b".repeat(64)).toJson()));
        var crossed=request(Route.FAMILY,FamilyMarriageResultQueries.canonicalArguments(c,obj(flat),Optional.of(rootRef)));assertThrows(IllegalArgumentException.class,()->contract.prepare(crossed,"changed-heir"));
    }

    @Test void actualChildSubjectProducerIsReplayedForBothColdChildResultRoutes()throws Exception {
        Context c=context();AtomicInteger subjectLive=new AtomicInteger(),loads=new AtomicInteger(),current=new AtomicInteger(),original=new AtomicInteger();
        var childArchive=new FamilyChildMarriageQueries.Originals(){public PlanningReadReceipt loadRead(ExactRef reference){throw new AssertionError("subject replay must not load unrelated value source");}public ExactRef referenceOf(PlanningReadReceipt receipt){throw new AssertionError("subject replay must not load unrelated value source");}};
        var child=new FamilyChildMarriageQueries(new FamilyChildMarriageQueries.Sources(ref("subject-native"),ref("value-native")),childArchive,r->{subjectLive.incrementAndGet();throw new AssertionError("cold result must use retained subject without another live query");});
        ObjectNode flat=F.objectNode().put("expected_native_revision",c.revision()).put("subject_character_id",38822);
        Obj subjectArgs=FamilyChildMarriageQueries.canonicalSubject(c,obj(flat));var subjectRequest=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),child.subject().operation(),subjectArgs,c.deadline());
        ObjectNode packet=F.objectNode().put("step",FamilyChildMarriageSubject.STEP).put("accepted",true).put("private_build",true).put("read_only",true).put("advertised",false).put("native_revision",c.revision()).put("query_sequence",7).put("subject_source","specified_player_child").put("subject_character_id",38822).put("status","available").put("player_child_verified",true).put("adult_measure_raw",20).put("adult_threshold_raw",16).put("adult",true).put("house_id",174).put("dynasty_id",174).put("bilateral_verified",true);
        packet.putNull("unavailable_reason").putNull("employer_character_id").putNull("betrothed_character_id").putNull("primary_spouse_character_id");packet.putArray("spouse_character_ids");packet.putArray("family_candidates");packet.putObject("arrange_marriage_diagnostics").put("storage_capacity",0).put("slots_scanned",0);
        PlanningReadReceipt proof=receipt(FamilyChildMarriageQueries.SUBJECT_ID,subjectRequest,packet);ExactRef proofRef=ref("actual-archived-subject");
        ExactRef futureProofRef=ref("future-archived-subject");Map<ExactRef,PlanningReadReceipt> retained=Map.of(proofRef,proof,futureProofRef,laterProof(proof));
        var archive=new FamilyMarriageResultQueries.Originals(){public PlanningReadReceipt loadRead(ExactRef reference){loads.incrementAndGet();return Objects.requireNonNull(retained.get(reference));}public ExactRef referenceOf(PlanningReadReceipt receipt){return retained.entrySet().stream().filter(row->row.getValue()==receipt).map(Map.Entry::getKey).findFirst().orElseThrow();}};
        var authority=new FamilyMarriageResultQueries.Authority(){public void verifyCurrent(PlanningReadRequest request,Route route,Obj args){current.incrementAndGet();}public void verifyOriginal(PlanningReadReceipt receipt,Route route,Obj args){original.incrementAndGet();}};
        var result=new FamilyMarriageResultQueries(new FamilyMarriageResultQueries.Sources(ref("family-native"),ref("child-native")),authority,r->{throw new AssertionError("child route must not read campaign root");},archive,child.subject());
        for(Route route:List.of(Route.MATRILINEAL,Route.DEFAULT)){
            JsonNode test=first(route,true);var request=request(route,arguments(test,Optional.of(proofRef)));var contract=result.definitions().forRoute(route);assertNotNull(contract.prepare(request,"cold-child-result"));
            Obj replay=contract.replay(receipt(route,request,test.get("native")));assertTrue(OpportunityJson.toNode(replay).get("cold_recovery").booleanValue());assertEquals(test.get("expected").get("status"),OpportunityJson.toNode(replay).get("status"));
        }
        assertEquals(0,subjectLive.get());assertEquals(4,loads.get());assertEquals(2,current.get());assertEquals(2,original.get());
        for(Route route:List.of(Route.MATRILINEAL,Route.DEFAULT)){JsonNode test=first(route,true);var future=request(route,arguments(test,Optional.of(futureProofRef)));assertThrows(IllegalArgumentException.class,()->result.definitions().forRoute(route).replay(receipt(route,future,test.get("native"))),"same-frame child proof from after the original result is not its input");}
        ObjectNode crossed=packet.deepCopy().put("subject_character_id",38823);PlanningReadReceipt wrong=receipt(FamilyChildMarriageQueries.SUBJECT_ID,subjectRequest,crossed);assertThrows(IllegalArgumentException.class,()->child.subject().replay(wrong));
    }

    private static PlanningReadReceipt laterProof(PlanningReadReceipt original) {
        GuardEvidence actual=original.before().binding();GuardEvidence later=new GuardEvidence(actual.origin(),actual.source(),actual.sessionId(),actual.connectionGeneration(),actual.operation(),actual.nativeEvidence(),actual.capabilityEvidence(),actual.authorityId(),actual.observedAt().plusSeconds(1),actual.validUntil().plusSeconds(1),actual.supportingEvidence());
        var guard=new PlanningReadGuard(later,true,true,true,"d".repeat(64));return new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),guard,guard,original.original());
    }
    @Test void coldRequiresActualArchivedRelationshipAndCannotSelfGrantFromPendingOrReference()throws Exception {
        AtomicInteger live=new AtomicInteger(),archived=new AtomicInteger();var installation=installation(live,archived);
        for(Route route:Route.values()){
            JsonNode test=first(route,true);assertThrows(IllegalArgumentException.class,()->arguments(test,Optional.empty()));
            Obj canonical=arguments(test,Optional.of(ref("unavailable-proof")));var req=request(route,canonical);var contract=installation.definitions().forRoute(route);
            assertThrows(IllegalArgumentException.class,()->contract.prepare(req,"cold-result"));
            assertThrows(IllegalArgumentException.class,()->contract.replay(receipt(route,req,test.get("native"))));
        }
    }
}


