package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original Python differential DATA and real budget tests; no copied DATA can mint a live retry proof. */
public final class ReadonlyPlanningRetryTest {
    private static final String SHA="a761179ca74f576950cdeda76649af9f39d8f1c831af21941753b622696cb24f";
    private static final String PROGRAM="""
            import hashlib,json,pathlib,sys
            root=pathlib.Path(sys.argv[1])
            p=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/readonly_planning_retry_v1.py'
            assert hashlib.sha256(p.read_bytes()).hexdigest()==sys.argv[2]
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
            from xar_autoplayer.bridge.readonly_planning_retry_v1 import classify_readonly_planning_error_v1
            v=json.load(sys.stdin); r=v['result']; error=r['error']
            if isinstance(r.get('typed_query_failure_v1'),dict):
                error+='; typed_query_failure_v1='+json.dumps(r['typed_query_failure_v1'],sort_keys=True,separators=(',',':'))
            e=_NativeCommandRejectedError(error,native_request_id=v['request']['request_id'],
                native_request_frame=v['request'],native_command_result_frame=r)
            print(json.dumps({'result':classify_readonly_planning_error_v1(e)},separators=(',',':')))
            """;
    private static Obj obj(String json) { return DriverJson.object(json.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES); }
    private static Obj request() { return obj("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"original-root-read\",\"step\":\"query-campaign-root-context-v1\",\"expected_revision\":11}"); }
    private static Obj executor() { return obj("""
            {"type":"command_result","protocol_version":1,"request_id":"original-root-read","ok":false,
             "error":"application-main typed query failed or its snapshot changed","result":null,
             "typed_query_failure_v1":{"executor_enter":false,"executor_exception":{"code":0,"image":"none","rva":null},
               "executor_finish":null,"executor_typed_result":null,"final_equal":null,"final_read":null,
               "frame_stable":null,"query_type":"campaign","stage":"wait","typed_result":null,
               "wait_completed":false,"wait_result":"executor_failed"}}
            """); }
    private static Obj revision() { return obj("""
            {"type":"command_result","protocol_version":1,"request_id":"original-root-read","ok":false,
             "error":"state_changed","campaign_root_preflight_failure_v1":{
               "query_type":"campaign","stage":"preflight_revision_changed","request_native_revision":11,
               "worker_native_revision":12,"read_attempted":false,"cached_scalars":"actual scalars",
               "observed_scalars":null,"differing_fields":null,"truncated":false,
               "predicates":{"revision_matches":false,"worker_ready":true,"previous_present":true,
                 "observed_read":false,"observed_equal":false}}}
            """); }
    private static Obj snapshot() { return obj("""
            {"type":"command_result","protocol_version":1,"request_id":"original-root-read","ok":false,
             "error":"state_changed","campaign_root_preflight_failure_v1":{
               "query_type":"campaign","stage":"preflight_native_snapshot_changed","request_native_revision":11,
               "worker_native_revision":11,"read_attempted":true,"cached_scalars":"actual scalars",
               "observed_scalars":"fresh scalars","differing_fields":["paused"],"truncated":false,
               "predicates":{"revision_matches":true,"worker_ready":true,"previous_present":true,
                 "observed_read":true,"observed_equal":false}}}
            """); }
    private static void original(Obj request,Obj result) throws Exception {
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(python,"MISSING_NOT_RUN: actual Python oracle executable is required");
        assertNotNull(repository,"MISSING_NOT_RUN: actual unchanged repository oracle is required");
        assertTrue(Files.isDirectory(Path.of(repository)));
        Process process=new ProcessBuilder(python,"-X","utf8","-c",PROGRAM,repository,SHA).redirectErrorStream(true).start();
        process.getOutputStream().write(DriverJson.encode(new Obj(Map.of("request",request,"result",result))));
        process.getOutputStream().close();
        assertTrue(process.waitFor(30,TimeUnit.SECONDS),"original retry oracle timed out");
        byte[] output=process.getInputStream().readAllBytes();
        assertEquals(0,process.exitValue(),new String(output,StandardCharsets.UTF_8));
        Value expected=obj(new String(output,StandardCharsets.UTF_8)).get("result");
        Value actual=ReadonlyPlanningRetry.classifyCampaign(request,result).<Value>map(value->value).orElse(Nil.INSTANCE);
        assertEquals(expected,actual);
        Obj wrapped=new Obj(Map.of("result",actual));
        assertEquals(wrapped,obj(new String(DriverJson.encode(wrapped),StandardCharsets.UTF_8)));
    }
    private static Obj changeFailure(Obj result,String key,Value value) {
        return result.with("campaign_root_preflight_failure_v1",
                OpportunityJson.object(result.get("campaign_root_preflight_failure_v1"),"actual failure").with(key,value));
    }
    @Test void threeActualNativeRejectionShapesMatchOriginalClassificationAndSerde() throws Exception {
        original(request(),executor());original(request(),revision());original(request(),snapshot());
        var absentResult=new java.util.LinkedHashMap<String,Value>(executor().members());absentResult.remove("result");
        original(request(),new Obj(absentResult));
    }
    @Test void actualWrongRequestOkStageAndNativeFailureFieldsKeepOriginalNonRetryClassification() throws Exception {
        original(request().with("step",new Text("death-terminal")),executor());
        original(request(),executor().with("ok",new Bool(true)));
        original(request(),executor().with("request_id",new Text("different")));
        Obj failure=OpportunityJson.object(executor().get("typed_query_failure_v1"),"failure");
        original(request(),executor().with("typed_query_failure_v1",failure.with("executor_enter",new Bool(true))));
        original(request(),executor().with("typed_query_failure_v1",failure.with("unexpected",Nil.INSTANCE)));
        original(request(),changeFailure(revision(),"read_attempted",new Bool(true)));
        original(request(),changeFailure(revision(),"worker_native_revision",new IntegerValue(java.math.BigInteger.TEN)));
        original(request(),changeFailure(snapshot(),"truncated",new Bool(true)));
        original(request(),revision().with("typed_query_failure_v1",obj("{\"stage\":\"unexpected\"}")));
        original(request(),changeFailure(snapshot(),"worker_native_revision",new IntegerValue(java.math.BigInteger.TEN)));
    }
    @Test void wrongIntegerTypesCannotEnterRetryClassification() {
        for(Value malformed:List.of(new Bool(true),obj("{\"v\":11.0}").get("v"),new Text("11"))) {
            assertTrue(ReadonlyPlanningRetry.classifyCampaign(request().with("expected_revision",malformed),revision()).isEmpty());
            assertTrue(ReadonlyPlanningRetry.classifyCampaign(request(),changeFailure(revision(),"request_native_revision",malformed)).isEmpty());
        }
        assertTrue(ReadonlyPlanningRetry.classifyCampaign(request().with("protocol_version",new Bool(true)),executor()).isEmpty());
    }
    @Test void actualWholePlanBudgetIsPrivateNestedAndClearedWithoutGenericIoOrUnknownRetry() throws Exception {
        AtomicInteger calls=new AtomicInteger();
        assertFalse(ReadonlyPlanningRetry.sink().active());
        IOException actual=new IOException("ordinary IO failure has no consumed-READ proof");
        assertSame(actual,assertThrows(IOException.class,()->ReadonlyPlanningRetry.plan(()->{
            calls.incrementAndGet();assertTrue(ReadonlyPlanningRetry.sink().active());throw actual;
        })));
        assertEquals(1,calls.get());assertFalse(ReadonlyPlanningRetry.sink().active());
        RawJson raw=new RawJson("{\"snapshot_id\":\"actual-data\",\"revision\":\"7\",\"plan\":{}}".getBytes(StandardCharsets.UTF_8));
        assertEquals(raw,ReadonlyPlanningRetry.plan(()->{
            assertTrue(ReadonlyPlanningRetry.claimGuardedCampaignRootRetry());
            assertFalse(ReadonlyPlanningRetry.claimGuardedCampaignRootRetry());
            return ReadonlyPlanningRetry.plan(()->{
                assertFalse(ReadonlyPlanningRetry.claimGuardedCampaignRootRetry());return raw;
            });
        }));
        assertFalse(ReadonlyPlanningRetry.sink().active());
        assertTrue(ReadonlyPlanningRetry.claimGuardedCampaignRootRetry());
    }
}
