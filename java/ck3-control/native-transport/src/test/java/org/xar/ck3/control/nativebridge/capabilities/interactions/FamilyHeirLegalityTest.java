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
import java.util.OptionalLong;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Closed historical .3 native packet; machine_id unknown. Synthetic root binding is no runtime qualification. */
final class FamilyHeirLegalityTest {
    private static final String FIXTURE="ck3_autonomous_player/tests/unit/fixtures/murchad_12003_absent_dynasty_comparison.json";
    private static final String PRODUCER="ck3_autonomous_player/src/xar_autoplayer/bridge/marriage_matchmaking_private_transport.py";
    private static Context context() {
        Instant now=Instant.parse("2026-10-24T00:00:00Z");
        G2Source source=new G2Source("synthetic-historical-replay",now.toString(),Build.CROZIER3.version(),new ExactRef("synthetic/source",1,"a".repeat(64)));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(31853),BigInteger.valueOf(12),
                BigInteger.valueOf(53327640)),"native:12",BigInteger.valueOf(56),"synthetic-text");
        var game=new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        return new Context(new ObservationIdentity(source.machineId(),game,frame,1),source,"synthetic-historical-session",BigInteger.TWO,
                Build.CROZIER3,now.plusSeconds(30),new ControlFrame(true,true,true,1,19L,31853,"synthetic-historical-episode",false,null,null,List.of()));
    }
    private static FamilyHeirLegality.Binding binding() {
        return new FamilyHeirLegality.Binding(context(),BigInteger.valueOf(7),OptionalLong.of(36403),new ExactRef("synthetic/root-original",1,"b".repeat(64)));
    }
    @Test void completeHistoricalNativePacketPreservesAllCountersRowsAndAbsentDynastySentinel() throws Exception {
        ObjectNode original=actual(); var value=FamilyHeirLegality.decode(raw(original),binding());
        assertTrue(value.availability().available()); assertEquals(9,value.candidates().size()); assertEquals(9,value.nativeLegalCandidates().size());
        assertEquals(BigInteger.valueOf(-1),value.candidates().getFirst().candidateDynasty());
        var d=value.diagnostics(); assertTrue(d.complete()); assertEquals(131072,d.storageCapacity()); assertEquals(53542,d.emptySlots());
        assertEquals(38005,d.liveCandidates()); assertEquals(39523,d.deadCandidates()); assertEquals(37996,d.nativeValidateFalse());
        assertEquals(38005,d.contextsConstructed()); assertArrayEquals(raw(original).bytes(),FamilyHeirLegality.verifyOriginal(value).bytes());
        var legacy=HeirMarriageCodec.decode(raw(original),context(),new HeirSubject(new CharacterId(36403),BigInteger.valueOf(7),binding().originalCampaignRoot()));
        assertEquals(value.candidates(),legacy.candidates()); assertEquals(value.querySequence(),legacy.frame().querySequence());
    }
    @Test void originalPythonProducerAndAllExistingJavaPublicConsumersObserveIdenticalDto() throws Exception {
        verifyPins();
        String script="""
                import copy,json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.bridge.marriage_matchmaking_private_transport import query_observed_first_heir_marriage_legality_v1
                value=json.loads((root/'ck3_autonomous_player/tests/unit/fixtures/murchad_12003_absent_dynasty_comparison.json').read_text(encoding='utf-8'))
                class Endpoint:
                    def send(self,request):self.request=request
                class State:
                    def wait_for_command_result(self,request_id,timeout):return copy.deepcopy(value['legality_command_result'])
                class Driver:
                    endpoint=Endpoint();state=State()
                    def take_snapshot(self):return {'native_revision':12,'revision':56,'snapshot_id':'native:12','date_raw':53327640,'paused':True,'map_ready':True,'played_character':{'character_id':31853,'alive':True},'diagnostics':{'hello':{'game_version':'1.20.0.3','executable_sha256':'94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'}}}
                    def _execute_campaign_root_context_v1_query(self,*,expected_revision):return {'status':'available','query_sequence':7,'held_title_partition':[{'primary':True,'first_heir_character_id':36403}]}
                driver=Driver();parsed=query_observed_first_heir_marriage_legality_v1(driver,expected_native_revision=12)
                packet={key:value for key,value in driver.endpoint.request.items() if key!='request_id'}
                print(json.dumps({'projection':parsed,'request_without_random_id':packet},sort_keys=True,separators=(',',':')))
                """;
        ProcessBuilder builder=new ProcessBuilder(required("xar.python"),"-B","-c",script,required("xar.repository.root"));
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1"); builder.redirectErrorStream(true); Process process=builder.start();
        if(!process.waitFor(30,TimeUnit.SECONDS)) { process.destroyForcibly(); throw new AssertionError("original family producer timeout"); }
        byte[] output=process.getInputStream().readNBytes(131_073);
        assertEquals(0,process.exitValue(),new String(output,StandardCharsets.UTF_8)); assertTrue(output.length<=131_072);
        JsonNode expected=NativeWire.parse(output);
        var value=FamilyHeirLegality.decode(raw(actual()),binding());
        assertEquals(expected.get("projection"),OpportunityJson.toNode(FamilyHeirLegality.project(value)));
        JsonNode packet=expected.get("request_without_random_id"); assertEquals(FamilyHeirLegality.STEP,packet.get("step").textValue());
        assertEquals(12,packet.get("expected_revision").intValue()); assertFalse(packet.has("subject_character_id")); verifyPins();
    }
    @Test void exactTypesFieldsLegalityAndCompleteDiagnosticsCannotBeWeakened() throws Exception {
        ObjectNode bool=actual(); row(bool).put("candidate_character_id",true); reject(bool);
        ObjectNode floating=actual(); row(floating).put("candidate_dynasty_id",2039.0); reject(floating);
        ObjectNode omitted=actual(); ((ObjectNode)omitted.get("arrange_marriage_diagnostics")).remove("dead_candidates"); reject(omitted);
        ObjectNode truncated=actual(); ((ObjectNode)truncated.get("arrange_marriage_diagnostics")).put("slots_scanned",131071); reject(truncated);
        ObjectNode invented=actual(); row(invented).put("native_rank",1); reject(invented);
        ObjectNode wrong=actual(); row(wrong).put("subject_character_id",1); reject(wrong);
        ObjectNode extra=actual(); row(extra).put("complete_fertility_catalog",true); reject(extra);
        ObjectNode shared=actual(); ((ObjectNode)shared.get("family_candidates").get(1)).put("heir_adult_measure_raw",40); reject(shared);
        ObjectNode duplicate=actual(); ((ObjectNode)duplicate.get("family_candidates").get(1)).put("candidate_character_id",row(duplicate).get("candidate_character_id").longValue()); reject(duplicate);
    }
    @Test void refusalRemainsEnumeratedButIsExcludedFromDerivedNativeLegalRows() throws Exception {
        ObjectNode n=actual(); row(n).put("recipient_answer_status_raw",2).put("recipient_answer_allows_send",false);
        var value=FamilyHeirLegality.decode(raw(n),binding()); assertEquals(9,value.candidates().size()); assertEquals(8,value.nativeLegalCandidates().size());
        JsonNode dto=OpportunityJson.toNode(FamilyHeirLegality.project(value)); assertEquals(9,dto.get("candidates").size()); assertEquals(8,dto.get("native_legal_candidates").size());
        row(n).put("recipient_answer_allows_send",true); reject(n);
    }
    @Test void absentRootHeirAndUnavailableNativeResultRetainUnknownWithoutInventingEmptyLegalSuccess() throws Exception {
        ObjectNode n=actual().put("status","unavailable").put("subject_character_id",-1).put("unavailable_reason","public_primary_first_heir_absent");
        n.putArray("family_candidates");
        var absent=new FamilyHeirLegality.Binding(context(),BigInteger.valueOf(7),OptionalLong.empty(),binding().originalCampaignRoot());
        var value=FamilyHeirLegality.decode(raw(n),absent); assertFalse(value.availability().available());
        JsonNode dto=OpportunityJson.toNode(FamilyHeirLegality.project(value)); assertTrue(dto.get("observed_first_heir_character_id").isNull());
        assertFalse(dto.has("query_sequence")); assertFalse(dto.has("candidates")); assertFalse(dto.has("native_legal_candidates"));
        n.put("status","available").putNull("unavailable_reason"); assertThrows(IllegalArgumentException.class,()->FamilyHeirLegality.decode(raw(n),absent));
    }
    private static ObjectNode actual() throws Exception { verifyPins(); return ((ObjectNode)NativeWire.parse(Files.readAllBytes(repository().resolve(FIXTURE))).get("legality_command_result").get("result")).deepCopy(); }
    private static ObjectNode row(ObjectNode value) { return (ObjectNode)value.get("family_candidates").get(0); }
    private static RawJson raw(JsonNode value) { return new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)); }
    private static void reject(ObjectNode value) { assertThrows(IllegalArgumentException.class,()->FamilyHeirLegality.decode(raw(value),binding())); }
    private static Path repository() { return Path.of(required("xar.repository.root")); }
    private static String required(String key) { String value=System.getProperty(key); assertNotNull(value,"required CI property: "+key); assertFalse(value.isBlank()); return value; }
    private static void verifyPins() throws Exception {
        pin(FIXTURE,21937,"88a4f006ac40ee58225e22a6c3e8556568e7b14a03abcfcf232f19e4a594d736");
        pin(PRODUCER,17426,"08c4dff41aacfdd242d36db6c718c3db202da2b68145b5b3c002efdd9de4eee6");
    }
    private static void pin(String name,long bytes,String sha) throws Exception { byte[] original=Files.readAllBytes(repository().resolve(name)); assertEquals(bytes,original.length,name); assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)),name); }
}
