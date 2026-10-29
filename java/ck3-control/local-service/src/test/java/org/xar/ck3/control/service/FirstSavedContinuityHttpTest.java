package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.math.BigInteger;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Actual pure HTTP consumer of the typed FIRST producer; synthetic inputs grant no physical/Game authority. */
@QuarkusTest
class FirstSavedContinuityHttpTest {
    @TestHTTPResource("/v1/continuity/saved-attachment") URI endpoint;
    private static final String MACHINE="first-http-software-fixture";
    private static ExactRef ref(String name,long size,char hash){return new ExactRef("/fixture-only/"+name,size,String.valueOf(hash).repeat(64));}
    private static Pin pin(ExactRef ref,String id){return new Pin(ref,new FileIdentity("1",id,"133000000000000001","2026-10-24T00:00:00Z",ref.bytes()));}
    private static GameGeneration game(long pid,String birth){ObjectNode row=StrictJson.object();row.put("pid",pid);row.put("creation_filetime",birth);return GameGeneration.fromJson(row);}
    private static ContinuityState committed(ContinuityState state,long sequence,String identity){ObjectNode row=state.toJson();row.put("sequence",sequence);row.put("last_event_identity",identity);return ContinuityState.fromJson(row,MACHINE);}
    private static ObjectNode request(){
        ObjectNode seed=StrictJson.object();seed.put("schema","root.ck3.continuity-window/v1");seed.put("machine_id",MACHINE);seed.put("sequence",1);seed.put("window_id",1);
        seed.put("status","running");seed.put("target_days",10958);seed.put("start_date_raw",1000);seed.put("target_date_raw",263992);seed.put("last_settled_cycles",2);seed.put("last_settled_date_raw",1000);
        seed.putObject("game_binding").put("pid",123).put("creation_date","2026-10-24T00:00:00Z");seed.putNull("unknown_actions");seed.putObject("unknown_requests").put("original","UNKNOWN");seed.put("NEXT",7);
        var old=game(123,"133000000000000001");var opening=game(456,"133000000000000002");var replacement=game(789,"133000000000000003");
        var begin=new EpisodeWindow.Begin("first-http-BEGIN",new EpisodeWindow.Identity(MACHINE,old,"old-session","old-episode",0,42,1000),
                new EpisodeWindow.Identity(MACHINE,opening,"opening-session","opening-episode",1,43,500),1,2,"next-parent",1,"1".repeat(64),ref("lifecycle.json",1,'1'),ref("adopted-driver.json",1,'2'),List.of());
        var waiting=committed(EpisodeWindow.reduce(ContinuityState.fromJson(seed,MACHINE),begin.request()),2,begin.request().identity());
        var began=new EpisodeWindow.CommittedBegin(begin,2,begin.request().identity(),ContinuityJson.digest(waiting.toJson()),pin(ref("begin.json",1,'3'),"9007199254740993"));
        var baseline=new EpisodeWindow.Baseline(began,"first-save",ref("pair.json",1,'4'),"4".repeat(64),ref("canonical-save.json",1,'5'),"a".repeat(64),begin.after());
        var active=committed(EpisodeWindow.reduce(waiting,baseline.request()),3,baseline.request().identity());
        var committedBaseline=new EpisodeWindow.CommittedBaseline(baseline,3,baseline.request().identity(),ContinuityJson.digest(active.toJson()),pin(ref("baseline.json",1,'6'),"9007199254740994"));
        var basis=new SavedContinuityAttachment.FirstBasis(MACHINE,active.origin(),new SavedContinuityAttachment.FirstBasis.Frame("original-save",new BigInteger("9007199254740993"),new BigInteger("18446744073709551615"),500,43,"opening-episode"),committedBaseline,
                ref("driver.json",11,'7'),new FileStatIdentity(BigInteger.valueOf(11),"9007199254740995","1792800000000000001"),ref("save.ck3",13,'8'),new FileStatIdentity(BigInteger.valueOf(13),"9007199254740996","1792800000000000002"),
                baseline.canonicalSaveReceiptRef(),baseline.pairRef(),ref("baselined-first-material.json",1,'9'),baseline.proofDigest(),"fixture-campaign",2);
        ObjectNode details=StrictJson.object();details.put("evidence_id","first-http-restore");details.put("source","explicit-FIRST-original");details.put("new_ordinary_cycle_credit",0);details.put("game_day_credit",0);details.put("original_actions_replayed",false);details.put("window_origin_reset",false);
        ObjectNode restored=StrictJson.object();restored.put("machine_id",MACHINE);restored.set("game",replacement.toJson());restored.put("session_id","replacement-session");restored.put("episode_run_id","opening-episode");
        restored.put("actor_character_id",43);restored.put("date_raw",500);restored.put("snapshot_id","restored-native-snapshot");restored.put("native_revision","18446744073709551615");ObjectNode progress=StrictJson.object();progress.put("ledger_cycles",0);progress.put("ledger_date_raw",500);
        ObjectNode wire=StrictJson.object();wire.put("schema",SavedContinuityAttachment.FIRST_REQUEST_SCHEMA);wire.set("previous",active.toJson());wire.set("expected_predecessor",active.toJson());wire.set("details",details);wire.set("expected_details",details.deepCopy());
        wire.set("basis",basis.toJson());wire.set("game",replacement.toJson());wire.set("opening",restored);wire.set("progress",progress);return wire;
    }
    private HttpResponse<byte[]> post(HttpClient client,ObjectNode body)throws Exception{
        return client.send(HttpRequest.newBuilder(endpoint).timeout(Duration.ofSeconds(20)).header("Content-Type","application/json")
                .POST(HttpRequest.BodyPublishers.ofByteArray(ContinuityJson.canonical(body,ContinuityJson.TRANSPORT_MAX_BYTES))).build(),HttpResponse.BodyHandlers.ofByteArray());
    }
    @Test void typedFirstProducerCrossesTheActualHttpConsumerWithItsExplicitRevisionAndNoNewCredit()throws Exception{
        ObjectNode request=request();try(HttpClient client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).followRedirects(HttpClient.Redirect.NEVER).build()){
            var response=post(client,request);assertEquals(200,response.statusCode());assertEquals(SavedContinuityResource.PRODUCER,response.headers().firstValue("X-Xar-Producer").orElseThrow());
            assertEquals(SavedContinuityAttachment.FIRST_REQUEST_SCHEMA,response.headers().firstValue("X-Xar-Contract-Revision").orElseThrow());
            ObjectNode after=ContinuityJson.parseObject(response.body(),ContinuityJson.DOCUMENT_MAX_BYTES);
            assertEquals("UNKNOWN",after.path("unknown_requests").path("original").textValue());assertTrue(after.get("unknown_actions").isNull());assertEquals(7,after.path("NEXT").longValue());
            assertEquals("18446744073709551615",after.path("latest_binding").path("native_revision").textValue());assertEquals(0,after.path("last_settled_cycles").longValue());
            assertEquals(request.path("basis").path("refs").path("first_save_receipt"),after.get("last_settled_source"));
            assertArrayEquals(ContinuityJson.canonical(SavedContinuityAttachment.reduce(SavedContinuityAttachment.decode(ContinuityJson.canonical(request,ContinuityJson.TRANSPORT_MAX_BYTES))).toJson()),response.body());
        }
    }
    @Test void ordinaryDowngradeAndNumericUInt64CannotAliasTheExplicitFirstHttpContract()throws Exception{
        try(HttpClient client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).followRedirects(HttpClient.Redirect.NEVER).build()){
            ObjectNode downgraded=request();downgraded.put("schema",SavedContinuityAttachment.REQUEST_SCHEMA);
            ObjectNode numeric=request();((ObjectNode)numeric.path("basis").path("frame")).put("native_revision",new BigInteger("18446744073709551615"));
            ObjectNode nativeNumeric=request();((ObjectNode)nativeNumeric.get("opening")).put("native_revision",new BigInteger("18446744073709551615"));
            for(ObjectNode invalid:List.of(downgraded,numeric,nativeNumeric)){
                var response=post(client,invalid);assertEquals(400,response.statusCode());assertEquals("rejected",StrictJson.parse(response.body()).path("status").textValue());
            }
        }
    }
}
