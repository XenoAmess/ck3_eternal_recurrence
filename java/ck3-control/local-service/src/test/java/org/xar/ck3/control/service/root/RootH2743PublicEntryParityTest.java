package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.*;
import static org.junit.jupiter.api.Assertions.*;

/** Original H2743 Service/Driver error products and the existing public decoder/Directory/RPC consumers.
 * These DATA tests issue no private Source, Native permit, current frame or Managed Root. */
final class RootH2743PublicEntryParityTest {
    private static final String STEP=PublicPlanningCodec.H2743_STEP;
    private static JsonNode frame(){return StrictJson.parse(("{\"snapshot_id\":\"native:1\",\"revision\":1,\"native_revision\":1,"
            +"\"date_raw\":53217264,\"actor_character_id\":29829,\"episode_run_id\":\"test-only-h2743-claim\","
            +"\"war_id\":16777231,\"connection_generation\":1}").getBytes(StandardCharsets.UTF_8));}
    private static com.fasterxml.jackson.databind.node.ObjectNode valid(){
        var row=StrictJson.object().put("step",STEP).put("expected_revision",1);row.set("expected_h2743_frame",frame());return row;
    }
    private static Path run(String label)throws IOException {
        String value=System.getProperty("xar.test.output.root");
        if(value==null||value.isBlank())throw new IOException("NOT_RUN_REQUIRED: xar.test.output.root");
        Path root=Path.of(value);if(!root.isAbsolute())throw new IOException("explicit absolute test output root required");
        return Files.createTempDirectory(root,label);
    }
    private static PublicMcpDirectory directory(AtomicInteger calls)throws Exception {
        var registry=new PublicBindings();
        new RootMcpPlanning(new RootMcpPlanning.Backend(){
            public RootMcpPlanning.Admission admission(){return new RootMcpPlanning.Admission(false,true,List.of());}
            public RawJson plan(PublicPlanningCodec.PlanRequest ignored){throw new AssertionError("EXECUTE cannot plan");}
            public RawJson execute(PublicPlanningCodec.ExecuteRequest caller)throws IOException {
                calls.incrementAndGet();RootPublicStepExecution.select(List.of(),caller);
                throw new AssertionError("an absent H2743 reader was treated as executable");
            }
        }).register(registry,OriginalPublicPlanningOracle.bindingSource());
        registry.freeze(Set.of(PublicMethod.EXECUTE_STEP));
        if (!(registry.lookup(PublicMethod.EXECUTE_STEP).orElseThrow() instanceof PublicBindings.TypedBinding<?,?> binding))
            throw new AssertionError("actual RootMcpPlanning registration must retain its typed binding");
        return OriginalPublicPlanningOracle.directory("ck3_execute_step",binding);
    }
    private static void assertOriginalError(PublicMcpDirectory directory,String arguments,JsonNode original)throws Exception {
        var wrapped=assertThrows(PublicMcpDirectory.ToolFailure.class,
                ()->directory.invoke(OriginalPublicPlanningOracle.call("ck3_execute_step",arguments)));
        var failure=assertInstanceOf(PublicServiceFailure.class,wrapped.getCause());
        assertEquals(original.path("kind").textValue(),failure.kind().pythonClassName());
        assertEquals(original.path("message").textValue(),failure.getMessage());
        for(String protocol:List.of(PublicMcpSession.MODERN,PublicMcpSession.LEGACY.getLast())) {
            JsonNode reply=OriginalPublicPlanningOracle.rpc(directory,"ck3_execute_step",arguments,protocol);
            assertFalse(reply.has("error"));var result=reply.path("result");
            assertTrue(result.path("isError").booleanValue());assertFalse(result.has("structuredContent"));
            assertEquals("Error executing tool ck3_execute_step: "+failure.getMessage(),
                    result.path("content").get(0).path("text").textValue());
        }
    }
    @Test void originalExplicitClaimFailuresRemainTypedBeforeAnyReaderAndThroughBothRpcFamilies()throws Exception {
        var cases=StrictJson.object().arrayNode();cases.addObject().put("step",STEP);
        cases.add(valid().putNull("expected_revision"));cases.add(valid().put("expected_revision",true));
        cases.add(valid().put("expected_revision",1.0));cases.add(valid().put("step","pause-map"));
        for(String excluded:List.of("center-map-on-landed-title-v1","navigate-ingame-ui-v1","query-ingame-ui-window-v1"))
            cases.add(valid().put("step",excluded));
        var original=OriginalPublicPlanningOracle.run("h2743_entry",cases,run("h2743-claims-"));
        var calls=new AtomicInteger();var directory=directory(calls);
        for(int i=0;i<cases.size();i++)assertOriginalError(directory,cases.get(i).toString(),original.get(i));
        assertEquals(0,calls.get(),"no malformed explicit H2743 claim may reach a backend");
    }
    @Test void absentInstalledH2743ReaderPreservesOriginalBridgeUnavailableInsteadOfGenericUnsupported()throws Exception {
        var cases=StrictJson.object().arrayNode().add(valid());
        var original=OriginalPublicPlanningOracle.run("h2743_entry",cases,run("h2743-reader-"));
        var calls=new AtomicInteger();assertOriginalError(directory(calls),valid().toString(),original.get(0));
        assertEquals(3,calls.get(),"each invocation selects the actual empty reader roster once, with no native submission");
    }
    @Test void originalDedicatedH2743CatchAndSharedEarlyDataSerdeKeepFalseNoResultAndTheExactError()throws Exception {
        Path root=run("h2743-dedicated-");var input=StrictJson.object().arrayNode();var item=input.addObject().put("step",STEP).put("revision",1);item.set("frame",frame());
        var original=OriginalPublicPlanningOracle.run("h2743_native_failure",input,root.resolve("original")).get(0);
        assertEquals(1,original.path("attempts").intValue());assertTrue(original.path("same_error").booleanValue());
        var rows=original.path("rows");assertEquals(1,rows.size());var row=rows.get(0);
        assertEquals(STEP,row.path("command").textValue());assertFalse(row.path("ok").booleanValue());assertTrue(row.get("result").isNull());
        var thrown=new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"actual H2743 entry failure",Optional.empty());
        var error=RootPublicStepFailureOriginals.earlyError(thrown);
        assertEquals(row.path("error").textValue(),error.className()+": "+error.message().orElse(""));
        byte[] caller=PublicPlanningCodec.encodeExecute(PublicPlanningCodec.decodeExecute(PublicBindings.present(new RawJson(valid().toString().getBytes(StandardCharsets.UTF_8))))).bytes();
        Path callerPath=root.resolve("caller.json");Files.write(callerPath,caller);
        var callerRef=new ExactRef(callerPath.toString(),caller.length,ActionCodec.sha256(caller));
        byte[] opaque="{\"schema\":\"test-only-opaque-historical-pointer\"}".getBytes(StandardCharsets.UTF_8);
        Path pointer=root.resolve("opaque-pointer.json");Files.write(pointer,opaque);var historical=new ExactRef(pointer.toString(),opaque.length,ActionCodec.sha256(opaque));
        var data=new DriverEarlyExecuteFailure.InvocationData(new OperationKey(STEP),error,Optional.empty(),Optional.empty(),
                new DriverEarlyExecuteFailure.AbsentData(new DriverEarlyExecuteFailure.Missing(List.of("no actual cached Known in this DATA test"))),
                callerRef,historical,Optional.empty(),Optional.empty(),0,"b".repeat(64),List.of(callerRef));
        assertEquals(data,DriverEarlyExecuteFailureRowProducer.decodeInvocation(DriverJson.encode(DriverEarlyExecuteFailureRowProducer.invocationJson(data))));
        assertThrows(IllegalArgumentException.class,()->new DriverEarlyExecuteFailureRowProducer.RawHistoryRow(1,
                new DriverEarlyExecuteFailureRowProducer.Source(data,callerRef),Optional.empty()));
    }
}
