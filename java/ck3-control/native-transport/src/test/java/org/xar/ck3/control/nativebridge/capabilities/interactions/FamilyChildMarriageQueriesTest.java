package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Unchanged original Python producers -> complete Java child codecs -> installed-contract archival replay. */
final class FamilyChildMarriageQueriesTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef REF=new ExactRef("controlled/child-source",1,"a".repeat(64));
    @TempDir static Path directory;
    private static JsonNode cases;
    @BeforeAll static void originalProducerFixtures()throws Exception{
        pins();Path log=directory.resolve("native-reader.log");Process nativeReader=new ProcessBuilder(required("xar.family.scorer.age.native.fixture"),directory.toString()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        complete(nativeReader,log,30,65536);JsonNode metadata=NativeWire.parse(Files.readAllBytes(directory.resolve("metadata.json")));assertEquals(50,metadata.get("actual_reader_calls").intValue());assertFalse(metadata.get("live").booleanValue());
        String script="""
                import copy,importlib.util,json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.bridge.player_child_marriage_subject_private_transport import query_player_child_marriage_subject_private_v1 as qs
                from xar_autoplayer.bridge.player_child_marriage_value_private_transport import query_player_child_marriage_value_private_v1 as qv
                spec=importlib.util.spec_from_file_location('original_child_subject_test',root/'ck3_autonomous_player/tests/unit/test_player_child_marriage_subject_private_transport.py');unit=importlib.util.module_from_spec(spec);spec.loader.exec_module(unit)
                versions=json.loads(sys.argv[3]);result={'subjects':[],'values':[]}
                class Driver:
                    allow_private_player_child_marriage_subject_query=True
                    def __init__(self,packet,frame):self.packet=packet;self.frame=frame;self.endpoint=self;self.state=self;self.request=None
                    def send(self,request):self.request=request
                    def wait_for_command_result(self,request_id,timeout):return copy.deepcopy(self.packet)
                    def take_snapshot(self):return copy.deepcopy(self.frame)
                def snapshot(version,actor=29829,native=3,date=53215920):
                    value=unit._frame();value.update(native_revision=native,revision=56,date_raw=date,snapshot_id='native:'+str(native));value['played_character']['character_id']=actor
                    value['diagnostics']={'hello':{'game_version':version,'executable_sha256':versions[version]}};return value
                def emit_subject(name,version,packet,diagnose=False,frame=None):
                    frame=frame or snapshot(version);native=packet['result'];driver=Driver(packet,frame)
                    public=qs(driver,expected_native_revision=frame['native_revision'],subject_character_id=native['subject_character_id'],diagnose_family_arrays=diagnose)
                    item={'name':name,'version':version,'frame':frame,'diagnose':diagnose,'raw':native,'public':public};result['subjects'].append(item);return item
                for version in versions:
                    for answer in (0,1,2):emit_subject(version+'-answer'+str(answer),version,unit._reply(family_candidates=[unit._row(answer)]))
                    packet=unit._reply(status='unavailable',unavailable_reason='not_player_child',player_child_verified=False,family_candidates=[],family_array_diagnostic=unit._probe())
                    if version in ('1.20.0.2','1.20.0.3'):
                        probe=packet['result']['family_array_diagnostic'];probe['slots']=probe['slots'][:2];probe['slots'][1]['offset']=0x38
                    emit_subject(version+'-unavailable-probe',version,packet,True)
                scenes=('override','fallback','selector0','firstfail','subjectadjust','uppermissing','upperreadfailure','heirunread','candidateunread','subjectwrap')
                for scene in scenes:
                    original=json.loads((out/(scene+'.json')).read_text(encoding='utf-8'));raw=original['result'];row=copy.deepcopy(raw['rows'][0]);actor=row['actor_character_id'];subject=row['heir_character_id'];frame=snapshot('1.20.0.4',actor,11,53327640)
                    candidate=unit._row();candidate.update(played_character_id=actor,subject_character_id=subject,candidate_character_id=row['candidate_character_id'],recipient_matchmaker_character_id=row['recipient_character_id'],intermediary_character_id=actor,native_rank=None,heir_adult_measure_raw=row['heir_adult_measure_raw'],candidate_adult_measure_raw=row['candidate_adult_measure_raw'],played_dynasty_id=row['played_dynasty_id'],heir_dynasty_id=row['heir_dynasty_id'],candidate_dynasty_id=row['candidate_dynasty_id'],realm_backed_actor_recipient=True)
                    diag={key:0 for key in ('empty_slots','live_candidates','dead_candidates','self_candidates','generation_mismatch_candidates','contexts_constructed','context_construct_failures','native_validate_true','native_validate_false')};diag.update(storage_capacity=1,slots_scanned=1,live_candidates=1,contexts_constructed=1,native_validate_true=1,validation_false_samples=[])
                    packet=unit._reply(native_revision=11,query_sequence=7,subject_character_id=subject,adult_measure_raw=row['heir_adult_measure_raw'],adult_threshold_raw=16,adult=row['heir_adult_measure_raw']>=16,house_id=row['heir_house_id'],dynasty_id=row['heir_dynasty_id'],employer_character_id=actor,betrothed_character_id=row['heir_betrothed_character_id'],primary_spouse_character_id=row['heir_primary_spouse_character_id'],spouse_character_ids=row['heir_spouse_character_ids'],family_candidates=[candidate],arrange_marriage_diagnostics=diag)
                    observed=emit_subject('reader-'+scene,'1.20.0.4',packet,frame=frame)
                    child=copy.deepcopy(raw);child['step']='query-player-child-marriage-value-v1-private';child['rows']=[row];driver=Driver({'ok':True,'result':child},frame);requested=row['requested_matrilineal_option']
                    public=qv(driver,legality=observed['public'],candidate_character_id=row['candidate_character_id'],request_matrilineal_option=requested)
                    result['values'].append({'name':scene,'subject':observed,'raw':child,'requested':requested,'public':public})
                print(json.dumps(result,sort_keys=True,separators=(',',':')))
                """;
        ObjectNode versions=InteractionJson.F.objectNode();for(Build build:Build.values())versions.put(build.version(),build.sha256());
        Path output=directory.resolve("original-python-oracle.json");var builder=new ProcessBuilder(required("xar.python"),"-B","-c",script,required("xar.repository.root"),directory.toString(),versions.toString()).redirectErrorStream(true).redirectOutput(output.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");complete(builder.start(),output,30,2_097_152);
        cases=NativeWire.parse(Files.readAllBytes(output));assertEquals(26,cases.get("subjects").size());assertEquals(10,cases.get("values").size());pins();
    }
    @Test void allOriginalSubjectOutputsMatchStrictTypedProjectionAndByteRoundTrip(){
        for(JsonNode item:cases.get("subjects")){Context context=context(item);var binding=new FamilyChildMarriageSubject.Binding(context,item.get("raw").get("subject_character_id").intValue(),item.get("diagnose").booleanValue());RawJson raw=raw(item.get("raw"));var observation=FamilyChildMarriageSubject.decode(raw,binding);
            assertEquals(item.get("public"),OpportunityJson.toNode(FamilyChildMarriageSubject.project(observation)),item.get("name").textValue());assertArrayEquals(raw.bytes(),FamilyChildMarriageSubject.verifyOriginal(observation).bytes());
            assertEquals(observation,FamilyChildMarriageSubject.decode(new RawJson(raw.bytes()),binding));var publicValue=FamilyChildMarriageSubject.project(observation);assertEquals(publicValue,OpportunityJson.parse(OpportunityJson.encode(publicValue)));
        }
    }
    @Test void actualSharedNativeReaderRowsFlowThroughBothInstalledContractsAndPureReplay()throws Exception{
        for(JsonNode item:cases.get("values")){
            Fixture f=fixture(item);assertTrue(f.queries.subject().hasPureReplay());assertTrue(f.queries.value().hasPureReplay());
            assertEquals(item.get("subject").get("public"),OpportunityJson.toNode(f.queries.subject().decode(f.subject)));
            assertEquals(item.get("public"),OpportunityJson.toNode(f.queries.value().decode(f.value)));
            assertEquals(f.queries.value().decode(f.value),f.queries.value().replay(f.value));assertEquals(0,f.admissions[0],"archive replay must not call live admission");
            var prepared=f.queries.subject().prepare(f.subject.request(),"controlled-subject");JsonNode nativeSubject=NativeWire.parse(prepared.additionalFields().bytes());assertFalse(nativeSubject.has("expected_revision"));assertEquals(2,nativeSubject.size());
            var valuePrepared=f.queries.value().prepare(f.value.request(),"controlled-value");JsonNode nativeValue=NativeWire.parse(valuePrepared.additionalFields().bytes());assertFalse(nativeValue.has("expected_revision"));assertEquals(4,nativeValue.size());assertEquals(item.get("requested"),nativeValue.get("request_matrilineal_option"));assertEquals(2,f.admissions[0]);
            assertEquals(item.get("subject").get("raw").get("subject_character_id").intValue(),FamilyChildMarriageQueries.decodeSubject(f.subject).binding().subject());
        }
    }
    @Test void falseLegalityWrongArchiveFrameAndMalformedNativeFieldsAreRefused()throws Exception{
        JsonNode item=cases.get("values").get(0);Fixture f=fixture(item);ObjectNode flat=valueFlat(item,f.ref);((ObjectNode)flat.get("legality")).put("player_child_verified",false);
        assertThrows(IllegalArgumentException.class,()->f.queries.canonicalValue(f.context,InteractionArguments.app(flat)));
        ObjectNode wrongCandidate=valueFlat(item,f.ref).put("candidate_character_id",true);assertThrows(IllegalArgumentException.class,()->f.queries.canonicalValue(f.context,InteractionArguments.app(wrongCandidate)));
        ObjectNode crossed=valueFlat(item,new ExactRef("controlled/other-read",1,"b".repeat(64)));assertThrows(IllegalArgumentException.class,()->f.queries.canonicalValue(f.context,InteractionArguments.app(crossed)));
        ObjectNode subjectRaw=((ObjectNode)item.get("subject").get("raw")).deepCopy();subjectRaw.put("query_sequence",true);assertThrows(IllegalArgumentException.class,()->FamilyChildMarriageSubject.decode(raw(subjectRaw),FamilyChildMarriageQueries.decodeSubject(f.subject).binding()));
        ObjectNode missing=((ObjectNode)item.get("subject").get("raw")).deepCopy();missing.remove("bilateral_verified");assertThrows(IllegalArgumentException.class,()->FamilyChildMarriageSubject.decode(raw(missing),FamilyChildMarriageQueries.decodeSubject(f.subject).binding()));
        ObjectNode floating=((ObjectNode)item.get("subject").get("raw")).deepCopy();((ObjectNode)floating.get("family_candidates").get(0)).put("candidate_character_id",50331651.0);assertThrows(IllegalArgumentException.class,()->FamilyChildMarriageSubject.decode(raw(floating),FamilyChildMarriageQueries.decodeSubject(f.subject).binding()));
        ObjectNode valueRaw=((ObjectNode)item.get("raw")).deepCopy();((ObjectNode)valueRaw.get("rows").get(0)).put("recipient_character_id",1);PlanningReadReceipt wrong=receipt(f.value.request(),FamilyChildMarriageQueries.VALUE_ID,valueRaw);assertThrows(IllegalArgumentException.class,()->f.queries.value().replay(wrong));
        var before=f.subject.before();var after=new PlanningReadGuard(before.binding(),true,true,true,"b".repeat(64));var drift=new PlanningReadReceipt(f.subject.request(),f.subject.contractId(),f.subject.requestId(),before,after,f.subject.original());assertThrows(IllegalArgumentException.class,()->FamilyChildMarriageQueries.decodeSubject(drift));
    }
    private record Fixture(Context context,FamilyChildMarriageQueries queries,ExactRef ref,PlanningReadReceipt subject,PlanningReadReceipt value,int[] admissions){}
    private static Fixture fixture(JsonNode item)throws Exception{
        JsonNode s=item.get("subject");Context context=context(s);ObjectNode flat=InteractionJson.F.objectNode().put("expected_native_revision",context.revision()).put("subject_character_id",s.get("raw").get("subject_character_id").intValue());
        var subjectArgs=FamilyChildMarriageQueries.canonicalSubject(context,InteractionArguments.app(flat));var subjectRequest=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),new OperationKey(FamilyChildMarriageSubject.STEP),subjectArgs,context.deadline());PlanningReadReceipt subject=receipt(subjectRequest,FamilyChildMarriageQueries.SUBJECT_ID,s.get("raw"));
        ExactRef ref=new ExactRef("controlled/subject-read",1,"c".repeat(64));int[] admissions={0};var originals=new FamilyChildMarriageQueries.Originals(){public PlanningReadReceipt loadRead(ExactRef reference){InteractionJson.need(reference.equals(ref),"unknown exact original");return subject;}public ExactRef referenceOf(PlanningReadReceipt receipt){assertEquals(subject,receipt);return ref;}};
        var queries=new FamilyChildMarriageQueries(new FamilyChildMarriageQueries.Sources(REF,REF),originals,request->admissions[0]++);
        var valueArgs=queries.canonicalValue(context,InteractionArguments.app(valueFlat(item,ref)));var valueRequest=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),queries.value().operation(),valueArgs,context.deadline());return new Fixture(context,queries,ref,subject,receipt(valueRequest,FamilyChildMarriageQueries.VALUE_ID,item.get("raw")),admissions);
    }
    private static ObjectNode valueFlat(JsonNode item,ExactRef ref){ObjectNode flat=InteractionJson.F.objectNode().put("candidate_character_id",item.get("raw").get("rows").get(0).get("candidate_character_id").intValue()).put("request_matrilineal_option",item.get("requested").booleanValue());flat.set("legality",item.get("subject").get("public").deepCopy());InteractionArguments.ref(flat.putObject("subject_read"),ref);return flat;}
    private static Context context(JsonNode item){JsonNode frame=item.get("frame");Build build=java.util.Arrays.stream(Build.values()).filter(b->b.version().equals(item.get("version").textValue())).findFirst().orElseThrow();BigInteger actor=frame.get("played_character").get("character_id").bigIntegerValue();var source=new G2Source("controlled-child-codec",NOW.toString(),build.version(),REF);var proposal=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,frame.get("native_revision").bigIntegerValue(),frame.get("date_raw").bigIntegerValue()),frame.get("snapshot_id").textValue(),frame.get("revision").bigIntegerValue(),"controlled-child-episode");var identity=new ObservationIdentity(source.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),proposal,1);return new Context(identity,source,"controlled-child-session",BigInteger.TWO,build,NOW.plusSeconds(30),new ControlFrame(true,true,true,1,19L,actor.longValueExact(),"controlled-child-episode",false,null,null,List.of()));}
    private static PlanningReadReceipt receipt(PlanningReadRequest request,String id,JsonNode result)throws Exception{String requestId="controlled-child-read";ObjectNode frame=InteractionJson.F.objectNode().put("type","command_result").put("protocol_version",1).put("request_id",requestId).put("ok",true);frame.set("result",result);RawJson original=raw(frame);var ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(raw(result)),original,NativeWire.packet(original.bytes()));var evidence=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.TWO,request.operation(),REF,REF,"controlled-child-authority",NOW,NOW.plusSeconds(30));var guard=new PlanningReadGuard(evidence,true,true,true,"1".repeat(64));return new PlanningReadReceipt(request,id,requestId,guard,guard,ack);}
    private static RawJson raw(JsonNode node){return new RawJson(node.toString().getBytes(StandardCharsets.UTF_8));}
    private static void complete(Process process,Path output,int seconds,long max)throws Exception{if(!process.waitFor(seconds,TimeUnit.SECONDS)){process.destroyForcibly();throw new AssertionError("original producer timeout");}assertTrue(Files.size(output)<=max,"bounded original producer output");assertEquals(0,process.exitValue(),Files.readString(output));}
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"required CI property: "+key);assertFalse(value.isBlank());return value;}
    private static void pins()throws Exception{pin("ck3_autonomous_player/src/xar_autoplayer/bridge/player_child_marriage_subject_private_transport.py",9993,"e6c581d470ca8715b4d7cad6df52ee6975b5a650fdf8adc7f88fb233fffa196d");pin("ck3_autonomous_player/src/xar_autoplayer/bridge/player_child_marriage_value_private_transport.py",9423,"cc0e3b1c68ec71cbfa329543e927fe6337a008e3f4cf88f8a4f11a7f6e5ebfe8");pin("ck3_autonomous_player/tests/unit/test_player_child_marriage_subject_private_transport.py",10031,"44845189939a3fd5efd51491e7b62377d294bf012baf686a298c46a4be9f827f");pin("ck3_autonomous_player/native_bridge/src/ck3_12002_family_wire.cpp",16567,"7b9ef096ccc01bce3e773db946ff046b97b52c811c7144858fabeb88beb83c97");pin("ck3_autonomous_player/native_bridge/src/ck3_12004_first_heir_scorer_age_test.cpp",25040,"3b3ea7e064ef685aade43ff7c226eaee97681e0cd216916e1b3a13d6e2ee0348");}
    private static void pin(String name,long count,String sha)throws Exception{byte[] bytes=Files.readAllBytes(Path.of(required("xar.repository.root")).resolve(name));assertEquals(count,bytes.length,name);assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),name);}
}
