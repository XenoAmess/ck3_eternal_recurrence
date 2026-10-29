package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.OriginalPublicPlanningOracle;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.service.mcp.RootMcpPlanning;

/** Existing canonical software writer/receiver/archive and original Service boundaries.
 * These cases issue no Managed Root, installed Context, native scope or publication authority. */
final class RootPublicStepExecutionProducerParityTest {
    @TempDir Path temporary;
    private static PublicMcpDirectory directory(RootMcpPlanning.Backend backend)throws Exception {
        var bindings=new PublicBindings();
        new RootMcpPlanning(backend).register(bindings,OriginalPublicPlanningOracle.bindingSource());
        bindings.freeze(Set.of(PublicMethod.EXECUTE_STEP));
        var actualBinding=bindings.lookup(PublicMethod.EXECUTE_STEP).orElseThrow();
        if (!(actualBinding instanceof PublicBindings.TypedBinding<?,?> typedBinding))throw new AssertionError("actual EXECUTE binding must retain its typed route");
        return OriginalPublicPlanningOracle.directory("ck3_execute_step",typedBinding);
    }
    private static RawJson neverPlan(){throw new AssertionError("EXECUTE cannot dispatch PLAN");}
    private static JsonNode toolError(JsonNode response){
        assertFalse(response.has("error"));JsonNode result=response.get("result");assertNotNull(result);
        assertTrue(result.get("isError").booleanValue());assertFalse(result.has("structuredContent"));
        assertTrue(result.get("content").isArray());assertEquals("text",result.get("content").get(0).get("type").textValue());
        return result;
    }
    @Test void actualOriginalUnsupportedFacadeErrorsReachTheExistingSdkEnvelopeWithoutEnteringAnyProducer()throws Exception {
        var cases=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        for(String step:List.of("center-map-on-landed-title-v1","navigate-ingame-ui-v1","query-ingame-ui-window-v1"))cases.addObject().put("step",step);
        JsonNode original=OriginalPublicPlanningOracle.run("unsupported",cases,temporary.resolve("original-unsupported"));
        assertEquals(3,original.size());
        for(int index=0;index<cases.size();index++){
            var calls=new AtomicInteger();
            var directory=directory(new RootMcpPlanning.Backend(){
                public RootMcpPlanning.Admission admission(){return new RootMcpPlanning.Admission(false,true,List.of());}
                public RawJson plan(PublicPlanningCodec.PlanRequest caller){return neverPlan();}
                public RawJson execute(PublicPlanningCodec.ExecuteRequest caller)throws IOException {
                    calls.incrementAndGet();RootPublicStepExecution.select(List.of(),caller);
                    throw new AssertionError("original unsupported generic facade reached a product");
                }
            });
            String arguments=cases.get(index).toString();JsonNode expected=original.get(index);
            var failure=assertThrows(PublicMcpDirectory.ToolFailure.class,()->directory.invoke(OriginalPublicPlanningOracle.call("ck3_execute_step",arguments)));
            var typed=assertInstanceOf(PublicServiceFailure.class,failure.getCause());
            assertEquals(expected.get("kind").textValue(),typed.kind().pythonClassName());
            assertEquals(expected.get("message").textValue(),typed.getMessage());assertEquals(1,calls.get());
            JsonNode response=OriginalPublicPlanningOracle.rpc(directory,"ck3_execute_step",arguments);
            JsonNode result=toolError(response);
            assertEquals("Error executing tool ck3_execute_step: "+expected.get("message").textValue(),result.get("content").get(0).get("text").textValue());
            assertEquals(2,calls.get());
        }
    }

    @Test void actualUnknownCoordinatorArchiveAndColdReplayNeverBecomeAPublicResultOrSecondSubmission()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual-unknown"),true)) {
            var command=fixture.command("original-public-unknown-once");
            var seen=new AtomicReference<ActionReceipt>();var calls=new AtomicInteger();var projected=new AtomicInteger();
            var directory=directory(new RootMcpPlanning.Backend(){
                public RootMcpPlanning.Admission admission(){return new RootMcpPlanning.Admission(false,true,List.of());}
                public RawJson plan(PublicPlanningCodec.PlanRequest caller){return neverPlan();}
                public RawJson execute(PublicPlanningCodec.ExecuteRequest caller)throws IOException,InterruptedException {
                    calls.incrementAndGet();ActionReceipt actual=fixture.coordinator.execute(command);seen.set(actual);
                    try {
                        return fixture.writer.locked(same->{
                            try {
                                return RootPublicStepExecution.legacyResult(actual,fixture.archive.withSession(same),same,caller,
                                    (original,numeric)->{projected.incrementAndGet();throw new AssertionError("UNKNOWN has no committed original result to format");});
                            }catch(IOException failure){throw new UncheckedIOException(failure);}
                        });
                    }catch(UncheckedIOException failure){throw failure.getCause();}
                }
            });
            String arguments="{\"step\":\""+command.operation().value()+"\",\"expected_revision\":\"0\"}";
            JsonNode first=OriginalPublicPlanningOracle.rpc(directory,"ck3_execute_step",arguments);toolError(first);
            assertEquals(1,calls.get());assertEquals(0,projected.get());assertNotNull(seen.get());
            assertFalse(seen.get().settled());assertTrue(seen.get().applied().isEmpty());
            assertEquals(1,fixture.nativeActionWrites());int preparations=fixture.pendingPreparations.get();
            assertTrue(preparations>0);ActionReceipt retained=seen.get();byte[] ledger=fixture.ledgerBytes();
            JsonNode second=OriginalPublicPlanningOracle.rpc(directory,"ck3_execute_step",arguments);toolError(second);
            assertEquals(2,calls.get());assertEquals(retained,seen.get());assertEquals(0,projected.get());
            assertEquals(1,fixture.nativeActionWrites());assertEquals(preparations,fixture.pendingPreparations.get());
            assertArrayEquals(ledger,fixture.ledgerBytes());
            assertEquals(retained,fixture.reopenAndReturnExisting(command));
            assertEquals(1,fixture.nativeActionWrites());assertArrayEquals(ledger,fixture.ledgerBytes());
            // Malformed public revision fails before the actual coordinator callback.
            String malformed=arguments.replace("\"expected_revision\":\"0\"","\"expected_revision\":true");
            assertThrows(PublicMcpDirectory.ToolFailure.class,()->directory.invoke(OriginalPublicPlanningOracle.call("ck3_execute_step",malformed)));
            assertEquals(2,calls.get());assertEquals(1,fixture.nativeActionWrites());assertArrayEquals(ledger,fixture.ledgerBytes());
        }
    }
}
