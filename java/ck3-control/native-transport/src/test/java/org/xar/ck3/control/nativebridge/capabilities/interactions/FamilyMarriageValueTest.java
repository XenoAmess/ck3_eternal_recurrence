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
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Existing actual4 reader/serializer -> full Java value codec -> unchanged original Python producer. */
final class FamilyMarriageValueTest {
    @TempDir static Path directory;
    private static final List<String> SCENES=List.of("override","fallback","selector0","firstfail","subjectadjust",
            "uppermissing","upperreadfailure","heirunread","candidateunread","subjectwrap");
    private static final long ACTOR=0x03000001L;
    @BeforeAll static void actualNativeProductionFixtures() throws Exception {
        pins();
        Path log=directory.resolve("native-fixture.log");
        Path executable=verifiedFixtureExecutable();
        Process nativeProducer=new ProcessBuilder(executable.toString(),directory.toString())
                .redirectErrorStream(true).redirectOutput(log.toFile()).start();
        if(!nativeProducer.waitFor(30,TimeUnit.SECONDS)) {nativeProducer.destroyForcibly();throw new AssertionError("native value fixture timeout");}
        assertTrue(Files.size(log)<=65536,"bounded original fixture output");assertEquals(0,nativeProducer.exitValue(),Files.readString(log));
        JsonNode metadata=NativeWire.parse(Files.readAllBytes(directory.resolve("metadata.json")));
        assertEquals(10,metadata.get("cases").intValue());assertEquals(50,metadata.get("actual_reader_calls").intValue());
        assertEquals(0,metadata.get("native_candidate_score_calls").intValue());assertEquals(0,metadata.get("action_calls").intValue());
        assertFalse(metadata.get("live").booleanValue());for(String scene:SCENES)assertTrue(Files.isRegularFile(directory.resolve(scene+".json")));assertEquals(executable,verifiedFixtureExecutable());pins();
    }
    private static Context context() {
        Instant now=Instant.parse("2026-10-24T00:00:00Z");var source=new G2Source("synthetic-value-reader",now.toString(),Build.CROZIER4.version(),new ExactRef("synthetic/source",1,"a".repeat(64)));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(ACTOR),BigInteger.valueOf(11),BigInteger.valueOf(53327640)),"native:11",BigInteger.valueOf(56),"synthetic-value-episode");
        return new Context(new ObservationIdentity(source.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1),
                source,"synthetic-value-session",BigInteger.TWO,Build.CROZIER4,now.plusSeconds(30),new ControlFrame(true,true,true,1,19L,ACTOR,"synthetic-value-episode",false,null,null,List.of()));
    }
    private static FamilyMarriageValue.Binding binding(ObjectNode packet) {
        List<FamilyMarriageValue.Candidate> candidates=new java.util.ArrayList<>();
        for(JsonNode row:packet.get("rows"))candidates.add(new FamilyMarriageValue.Candidate(row.get("candidate_character_id").intValue(),row.get("recipient_character_id").intValue()));
        return new FamilyMarriageValue.Binding(FamilyMarriageValue.Mode.FIRST_HEIR,context(),BigInteger.valueOf(7),0x03000002,candidates,
                packet.get("rows").get(0).get("requested_matrilineal_option").booleanValue(),Optional.empty());
    }
    @Test void allFiftyActualReaderRowsPreserveCompleteSignedValuesAndOriginalBytes() throws Exception {
        for(String scene:SCENES) {
            ObjectNode packet=packet(scene);var actual=FamilyMarriageValue.decode(raw(packet),binding(packet));assertTrue(actual.available());assertEquals(5,actual.rows().size());
            for(var row:actual.rows()) {
                var value=row.value().orElseThrow();assertEquals(30000,value.heirFertility().effectiveRaw());assertEquals(20000,value.candidateFertility().effectiveRaw());
                assertEquals(10000,value.fertilityFloor().orElseThrow());assertEquals(3,value.possiblePairs().size());
                assertTrue(value.heirRelationship().spouses().isEmpty());assertEquals(200,value.heirLineage().dynasty().orElseThrow());
            }
            assertArrayEquals(raw(packet).bytes(),FamilyMarriageValue.verifyOriginal(actual).bytes());
        }
    }
    @Test void completeOriginalPythonPublicProducerMatchesAllTenDerivedBranchPackets() throws Exception {
        String script="""
                import copy,json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);directory=pathlib.Path(sys.argv[2]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.bridge.marriage_candidate_alliance_private_transport import query_first_heir_candidate_alliance_projection_private_v1
                result={}
                for scene in sys.argv[4:]:
                    original=json.loads((directory/(scene+'.json')).read_text(encoding='utf-8'));rows=original['result']['rows']
                    legality={'schema':'xar.ck3.observed-first-heir-marriage-legality.v1','status':'available','native_revision':11,'query_sequence':7,'observed_first_heir_character_id':50331650,'exact_ck3_build':'1.20.0.4','exe_sha256':sys.argv[3],'native_legal_candidates':[{'played_character_id':50331649,'subject_character_id':50331650,'candidate_character_id':r['candidate_character_id']} for r in rows]}
                    class Endpoint:
                        def send(self,request):self.request=request
                    class State:
                        def wait_for_command_result(self,request_id,timeout):return copy.deepcopy(original)
                    class Driver:
                        endpoint=Endpoint();state=State()
                        def take_snapshot(self):return {'native_revision':11,'revision':56,'snapshot_id':'native:11','date_raw':53327640,'paused':True,'map_ready':True,'played_character':{'character_id':50331649,'alive':True},'diagnostics':{'hello':{'game_version':'1.20.0.4','executable_sha256':sys.argv[3]}}}
                        take_snapshot_without_native_command_history=take_snapshot
                    result[scene]=query_first_heir_candidate_alliance_projection_private_v1(Driver(),legality=legality,candidate_character_ids=[r['candidate_character_id'] for r in rows])
                print(json.dumps(result,sort_keys=True,separators=(',',':')))
                """;
        var command=new java.util.ArrayList<>(List.of(required("xar.python"),"-B","-c",script,required("xar.repository.root"),directory.toString(),Build.CROZIER4.sha256()));command.addAll(SCENES);
        Path output=directory.resolve("python-value-oracle.json");var builder=new ProcessBuilder(command).redirectErrorStream(true).redirectOutput(output.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process oracle=builder.start();if(!oracle.waitFor(30,TimeUnit.SECONDS)){oracle.destroyForcibly();throw new AssertionError("original value producer timeout");}
        assertTrue(Files.size(output)<=1_048_576,"original producer output bounded");byte[] bytes=Files.readAllBytes(output);assertEquals(0,oracle.exitValue(),new String(bytes,StandardCharsets.UTF_8));
        JsonNode expected=NativeWire.parse(bytes);
        for(String scene:SCENES) {ObjectNode packet=packet(scene);assertEquals(expected.get(scene),OpportunityJson.toNode(FamilyMarriageValue.project(FamilyMarriageValue.decode(raw(packet),binding(packet)))),scene);}
        pins();
    }
    @Test void isolatedAgeBranchKeepsNullableOverridesSelectorBypassAndSignedWrap() throws Exception {
        JsonNode bypass=dto("selector0").get("rows").get(0);assertFalse(bypass.get("candidate_native_scorer_effective_age_v1").get("ready").booleanValue());
        assertTrue(bypass.get("candidate_native_scorer_age_branch_v1").get("passes").booleanValue());
        JsonNode missing=dto("uppermissing").get("rows").get(0).get("candidate_native_scorer_age_branch_v1");assertFalse(missing.get("ready").booleanValue());assertTrue(missing.get("passes").isNull());
        JsonNode firstFail=dto("firstfail").get("rows").get(0).get("candidate_native_scorer_age_branch_v1");assertFalse(firstFail.get("passes").booleanValue());assertFalse(firstFail.get("second_comparison").get("ready").booleanValue());
        JsonNode wrap=dto("subjectwrap").get("rows").get(0).get("candidate_native_scorer_age_branch_v1").get("second_comparison");
        assertTrue(wrap.get("ready").booleanValue());assertTrue(wrap.get("subject_adult_deficit_raw").intValue()<0,"native signed32 overflow is preserved rather than widened");
    }
    @Test void wrongTypesRolesIncompleteFieldsAndSelfReportedDerivedDataAreRefused() throws Exception {
        ObjectNode n=packet("override");row(n).put("candidate_character_id",true);reject(n);
        n=packet("override");row(n).put("candidate_native_scorer_age_override_raw",40.0);reject(n);
        n=packet("override");row(n).remove("heir_native_fertility");reject(n);
        n=packet("override");row(n).put("failure","NONE");reject(n);
        n=packet("override");row(n).put("native_candidate_scorer_age_upper_raw",BigInteger.ONE.shiftLeft(31));reject(n);
        n=packet("override");row(n).put("recipient_character_id",5);reject(n);
        n=packet("override");row(n).put("effective_matrilineal_if_accepted",!row(n).get("effective_matrilineal_if_accepted").booleanValue());reject(n);
        n=packet("override");row(n).putObject("candidate_native_scorer_age_branch_v1").put("ready",true);reject(n);
        n=packet("override");((ObjectNode)n.get("rows").get(1)).put("heir_house_id",999);reject(n);
    }
    @Test void unavailableValueRetainsPartialFinalLegalityAndDoesNotInventDerivedCredit() throws Exception {
        ObjectNode n=packet("override");var originalBinding=binding(n);ObjectNode first=row(n);first.put("status","unavailable").put("failure","projection_unavailable").put("projection_failure","binding_unavailable");n.put("status","unavailable");
        for(String key:List.of("generic_costs","predicted_outcome_if_accepted","heir_is_adult","candidate_is_adult","heir_adult_measure_raw","candidate_adult_measure_raw","heir_adult_threshold_raw","candidate_adult_threshold_raw","heir_native_fertility","candidate_native_fertility","native_candidate_fertility_floor_raw","heir_native_scorer_age_override_raw","candidate_native_scorer_age_override_raw","native_candidate_scorer_age_upper_raw","grand_wedding_option_selected","heir_betrothed_character_id","heir_primary_spouse_character_id","heir_spouse_character_ids","candidate_betrothed_character_id","candidate_primary_spouse_character_id","candidate_spouse_character_ids","played_house_id","played_dynasty_id","heir_house_id","heir_dynasty_id","candidate_house_id","candidate_dynasty_id","heir_sex_selector_raw","candidate_sex_selector_raw","effective_matrilineal_if_accepted","matrilineal_option_selected"))first.putNull(key);
        first.putArray("possible_alliance_pairs");var value=FamilyMarriageValue.decode(raw(n),originalBinding);assertFalse(value.available());assertTrue(value.rows().getFirst().value().isEmpty());
        assertTrue(value.rows().getFirst().finalLegality().sampled());assertTrue(value.rows().getFirst().finalLegality().aiAccept().isPresent());
        JsonNode projected=OpportunityJson.toNode(FamilyMarriageValue.project(value)).get("rows").get(0);assertFalse(projected.get("candidate_native_fertility_floor_comparison_v1").get("ready").booleanValue());
        first.put("native_candidate_fertility_floor_raw",10000);assertThrows(IllegalArgumentException.class,()->FamilyMarriageValue.decode(raw(n),originalBinding));
    }
    private static JsonNode dto(String scene)throws Exception {ObjectNode p=packet(scene);return OpportunityJson.toNode(FamilyMarriageValue.project(FamilyMarriageValue.decode(raw(p),binding(p))));}
    private static ObjectNode packet(String scene)throws Exception {Path p=directory.resolve(scene+".json");assertTrue(Files.size(p)<=131072);return ((ObjectNode)NativeWire.parse(Files.readAllBytes(p)).get("result")).deepCopy();}
    private static ObjectNode row(ObjectNode n){return (ObjectNode)n.get("rows").get(0);}
    private static RawJson raw(JsonNode n){return new RawJson(n.toString().getBytes(StandardCharsets.UTF_8));}
    private static void reject(ObjectNode n)throws Exception {var binding=binding(packet("override"));assertThrows(IllegalArgumentException.class,()->FamilyMarriageValue.decode(raw(n),binding));}
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"required CI property: "+key);assertFalse(value.isBlank());return value;}
    private static Path verifiedFixtureExecutable()throws Exception {
        Path path=Path.of(required("xar.family.scorer.age.native.fixture")).toAbsolutePath().normalize();String expected=required("xar.family.scorer.age.native.fixture.sha256");
        assertTrue(expected.matches("[0-9a-f]{64}"),"canonical lowerhex native fixture SHA256 required");long bytes=Files.size(path);assertTrue(bytes>0 && bytes<=67_108_864,"bounded actual native executable required");
        var digest=MessageDigest.getInstance("SHA-256");try(var stream=Files.newInputStream(path)){byte[] chunk=new byte[8192];int count;while((count=stream.read(chunk))>=0)if(count>0)digest.update(chunk,0,count);}
        assertEquals(expected,HexFormat.of().formatHex(digest.digest()),"actual native fixture changed");return path;
    }
    private static void pins()throws Exception {
        pin("ck3_autonomous_player/src/xar_autoplayer/bridge/marriage_candidate_alliance_private_transport.py",25484,"326dfb0bea0c13c9aabd1a76e991193f917318302c38fa27e0c3a43b1efef5bf");
        pin("ck3_autonomous_player/src/xar_autoplayer/bridge/player_child_marriage_value_private_transport.py",9423,"cc0e3b1c68ec71cbfa329543e927fe6337a008e3f4cf88f8a4f11a7f6e5ebfe8");
        pin("ck3_autonomous_player/native_bridge/src/ck3_12002_family_wire.cpp",16567,"7b9ef096ccc01bce3e773db946ff046b97b52c811c7144858fabeb88beb83c97");
        pin("ck3_autonomous_player/native_bridge/src/ck3_12004_first_heir_scorer_age_test.cpp",25040,"3b3ea7e064ef685aade43ff7c226eaee97681e0cd216916e1b3a13d6e2ee0348");
    }
    private static void pin(String name,long size,String sha)throws Exception {byte[] bytes=Files.readAllBytes(Path.of(required("xar.repository.root")).resolve(name));assertEquals(size,bytes.length,name);assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),name);}
}
